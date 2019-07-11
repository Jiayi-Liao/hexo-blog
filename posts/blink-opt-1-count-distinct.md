---
title: Blink Optimization(1) - Count Distinct In Streaming
date: 2019-04-29 23:25:11
tags: 
  - Blink
  - Flink
  - Calcite
keywords: 
  - Blink
  - Flink
  - Calcite
  - SQL
description:
categories: Apache Flink
---

Blink作为Flink的分支已经开源一段时间了，在读了一些源码之后，决定写一个Blink Optimization的系列来分享一些有意思的改进。这次选用Count Distinct是因为它一定程度上改善了数据倾斜造成的影响，这个improvement对于很多人应该都是还比较重要的。这个优化方式也是我们常用的方式，但是Blink以更加抽象形式实现了，理论上对于Streaming和Batch都是适用的，但是目前在Batch中还没有使用这个优化。

## Data Skew（数据倾斜）

流式处理中常常会遇到Data Skew，常见的解决思路就是将数据以加盐的方式再一次打散，更大程度的分散到各个流中，然后分两次聚合，完成指标统计。以一个实时统计人数的代码为例:

```
select city,count(distinct userId) from table group by city
```

这种情况下，当某个city对应人数过多时，就会产生数据倾斜，此时，我们往往会这样做(以1024作为salt将数据打散)：

```
select
    city,sum(e1)
from
    (select city, userId % 1024, count(distinct userId) e1 from table group by city, userId % 1024) tbl
group by 
    city    
```

当然这只是userId出现倾斜的情况，如果在此时你还要针对商品SKU进行去重计算，那么当userId和SKU都出现数据倾斜时，你的SQL应该如何处理呢？又要将SQL增加若干层才能达到这样的效果。


## How to Optimize

Blink使用SplitAggregateRule作为Calcite Rule的补充，以更加抽象的形式完成了对上述场景的支持。现在我们只涉及SplitAggregateRule这个规则，暂时不考虑其他的一些优化（比如Count Distinct可能被优化成Group和Count等）。

我们先看针对userId出现倾斜时，这个规则如何去优化？

```
select
    city,sum(e1)
from
    (select city, userId % 1024, count(distinct userId) e1 from table group by city, userId % 1024) tbl
group by 
    city    
```

对应的逻辑计划为：

```
FlinkLogicalAggregate(group=[{0}], agg#0=[$SUM0($2)])
+- FlinkLogicalAggregate(group=[{0, 2}], agg#0=[COUNT(DISTINCT $1)])
   +- FlinkLogicalCalc(select=[city, userId, MOD(HASH_CODE(userId), 1024) AS $f2])
      +- FlinkLogicalCalc(select=[city, userId])
         +- FlinkLogicalNativeTableScan(table=[[builtin, default, _DataStreamTable_0]])
```

增加了一个字段MOD(HASH_CODE(userId), 1024)作为salt，然后分两步聚合实现count distinct。那么对于SKU和userId同时倾斜的情况，那么如何处理呢？通过上面可以推断出这行中需要新增两个个字段：

* salt UserId: 为了将UserId打散
* salt SKU: 为了将SKU打散

```
+---------+--------+-----+-------------+----------+
| City    | UserId | SKU | Salt-UserId | Salt-SKU |
+---------+--------+-----+-------------+----------+
| Beijing | 1      | 1   | 1           | 1        |
| Jinan   | 2      | 3   | 2           | 3        |
+---------+--------+-----+-------------+----------+
```

可以想到，我们在Group By (City, Salt-UserId, Salt-SKU)之后，没有办法在第二步计算出Count(Distinct UserId)和Count(Distinct SKU)，那么为了解决这个问题，采用空间换时间的做法，将一行输出为多行(这不属于Blink的优化，但是为了方便还是一并描述一下)，让我们把一条记录变成多条，加上Group字段试试：


```
+---------+--------+-----+-------------+----------+-------+
| City    | UserId | SKU | Salt-UserId | Salt-SKU | Group |
+---------+--------+-----+-------------+----------+-------+
| Beijing | 1      | 1   | 1           | null     | 1     |
| Beijing | 1      | 1   | null        | 1        | 2     |
| Jinan   | 2      | 3   | 2           | null     | 1     |
| Jinan   | 2      | 3   | null        | 3        | 2     |
+---------+--------+-----+-------------+----------+-------+
```

*Group: 表示聚合的编号，1表示只对Salt-UserId的聚合，2表示只对Salt-SKU的聚合*  

这样的话，我们就可以在Group By (City, Salt-UserId, Salt-SKU)之后，过滤Group=1的数据然后Group By City得到Count(Distinct UserId)，过滤Group=2的数据然后Group By City得到Count(Distinct SKU)。
  
最后生成出来的逻辑计划是这样的：

```
FlinkLogicalAggregate(group=[{0}], agg#0=[$SUM0($3)], agg#1=[$SUM0($4)])
+- FlinkLogicalAggregate(group=[{0, 3, 4}], agg#0=[COUNT(DISTINCT $1) FILTER $5], agg#1=[COUNT(DISTINCT $2) FILTER $6])
   +- FlinkLogicalCalc(select=[city, userId, sku, $f3, $f4, =($e, 1) AS $g_1, =($e, 2) AS $g_2])
      +- FlinkLogicalExpand(projects=[{city=[$0], userId=[$1], sku=[$2], $f3=[$3], $f4=[null], $e=[1]}, {city=[$0], userId=[$1], sku=[$2], $f3=[null], $f4=[$4], $e=[2]}])
         +- FlinkLogicalCalc(select=[city, userId, sku, MOD(HASH_CODE(userId), 1024) AS $f3, MOD(HASH_CODE(sku), 1024) AS $f4])
            +- FlinkLogicalNativeTableScan(table=[[builtin, default, _DataStreamTable_0]])
```

FlinkLogicalExpand表达了一行Expand成多行的逻辑：

```
{city=[$0], userId=[$1], sku=[$2], $f3=[$3], $f4=[null], $e=[1]}
{city=[$0], userId=[$1], sku=[$2], $f3=[null], $f4=[$4], $e=[2]}
```

这两行的前三个字段没有区别，$e=[1]表示Group=1，$e=[2]表示Group=2。

## Some Thoughts

当然这样的做法只适用于某些场景，如果在数据量小的情况下这么做完全是多余的，尤其是在流式场景中产生的数据相对离线数据来说要小好几个数量级。这次看Blink的这个规则，还顺带的看了看Spark、Calcite对于Count Distinct的一些做法，发现这个算子简简单单，但是实现方法从容易想到的Map到高阶的BitMap和算子转换，都有各自的特点，收获还是蛮大的。

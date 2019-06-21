---
title: Apache Calcite Paper Notes
date: 2019-05-11 14:47:41
tags: calcite
keywords: calcite
description:
categories: Big Data Computation Engine
---
最近在搭建一个SQL引擎，正好再次拜读了一下Calcite的paper(不得不吐槽一下calcite的相关资料确实有些少)。[原文地址](https://arxiv.org/abs/1802.10233)。以前也写过calcite相关的代码解析，不过有些浅显了，[SQL解析框架 - Calcite](http://www.liaojiayi.com/calcite/)。


## Introduction 

随着NoSQL数据库的流行，不少OLAP相关的开发者会遇到以下的问题：

* 对于多种数据库，不得不开发多套类似的优化逻辑来实现对不同NoSQL数据库查询的支持。
* 对于跨数据库的查询，没有很好的方式做出合适的抽象，经常需要定制化开发。

Apache Calcite就是为了解决这些问题。简单来说，Calcite是一个使用SQL作为交互语言，实现了SQL的解析、优化、执行为一体的可定制化框架。大致的流程如下：

1. 用户使用JDBC Client发起SQL请求。
2. Calcite接收到SQL后使用SQLParser和Validator做解析和校验生成SQL树。
3. 使用系统提供的表达式规则遍历SQL树在不同的节点上生成对应的表达式。
4. 使用Optimizer对表达式树进行优化（基于cost和rules）。
5. 根据表达式树，转变成执行计划，执行相应代码获取结果。


## Query Algebra

主要是解释了一个Calcite中几个比较关键的概念。

* Operators：属于Relational Algrbra，代码里是RelNode，如Project/Filter/Join。
* Traits：用来标记Operator的特征。比如数据库本身数据集的Scan已经有序，那么在TableScan这个Operator中，就可以带上有序相关的特征，这样在最后生成执行计划的时候可以根据特征去做一些执行上优化（在这个例子中，如果TableScan后面是Sort Operator，那么可以直接跳过Sort这个Operator）。
* Convention: 属于特征的一种，常用于表示不同的数据处理系统（当然你也可以用自定义的Trait来代替）。比如在Apache Flink中，用了Convention来区分流和批，这样可以在流批都使用同一套SQL的情况下，根据不同的Convention来实现不同的执行。


## Adapters      

Adapter是Calcite开放给开发者的组件，开发者可以基于Calcite对Adapter的定义来基于自己的data source去实现查询的逻辑。Calcite源码中提供了csv的example。

## Query Processing And Optimization

讲了几个可以扩展的几个组件：

* Planner Rule: 这里的rule包括对Logical Plan和Execution Plan的优化。
* Metadata Provider: 提供了一些原始数据表的metadata，可以用来计算cost。
* Planner Engines: 两种Planner，目前有VolcanoPlanner和HepPlanner，可以基于这个去扩展。
* Materialized Views: 多个存储的结果可以变成View？

## Extending Calcite


1. 支持半结构化数据。
2. Calcite也支持流式数据的SQL解析，使用标识符STREAM来区分，如：
    ```
    SELECT STREAM rowtime , productId , units FROM Orders
    WHERE units > 25;
    ```
3. 支持Geo的相关查询，如经纬度。


title: SparkSQL写入Hive动态分区的优化
author: Liao Jiayi
tags:
  - Spark
articleId: spark-hive-dynamic
categories:
  - Apache Spark
date: 2019-04-12 00:33:09
---

实际业务中，我们通常会以时间作为分区来建立Hive表，然后在SparkSQL中以动态分区的形式插入，发现一个优化空间。

## 业务背景
以行为数据接收为例，由于终端SDK和数据接收存在着时间误差，我们并不想丢弃这些应该存在的历史数据，所以我们会选择类似这样的SQL来完成入仓的过程。

```
// 假设time的时间单位是天
insert into table user_behaviours partition(time)
select
    *,
    toDate(time)
from
    user_behaviours_table    
```

实际业务中，绝大部分数据都来自同一天，小部分的脏数据会来自于历史，那么这种情况下，Spark对于这种动态分区插入的操作是如何执行的？

*** 

## SparkPlan
（建议打开相关源码阅读）关于Spark的执行计划，我们可以直接定位到**InsertIntoHiveTable.scala**，根据doExecute方法，可以知道sideEffectResult变量是整个任务执行的入口。跳过前面多余的步骤，可以发现针对插入Hive的情况，Spark根据numDynamicPartitions的数量提供了两类写入方式：

* SparkHiveWriterContainer (numDynamicPartitions = 0)
* SparkHiveDynamicPartitionWriterContainer (numDynamicPartitions > 0)

#### SparkHiveWriterContainer
由于已知写入的partition名字，所以直接初始化Hive的相关Writer写入即可。

#### SparkHiveDynamicPartitionWriterContainer
我在源码中贴了相关注释可以借鉴阅读

```
// 新建external sorter以key进行排序
val sorter: UnsafeKVExternalSorter = new UnsafeKVExternalSorter(
  StructType.fromAttributes(partitionOutput),
  StructType.fromAttributes(dataOutput),
  SparkEnv.get.blockManager,
  SparkEnv.get.serializerManager,
  TaskContext.get().taskMemoryManager().pageSizeBytes,
  SparkEnv.get.conf.getLong("spark.shuffle.spill.numElementsForceSpillThreshold",
    UnsafeExternalSorter.DEFAULT_NUM_ELEMENTS_FOR_SPILL_THRESHOLD))

while (iterator.hasNext) {
  val inputRow = iterator.next()
  val currentKey = getPartitionKey(inputRow)
  sorter.insertKV(currentKey, getOutputRow(inputRow))
}

logInfo(s"Sorting complete. Writing out partition files one at a time.")

// 排序结束，开始写入文件
val sortedIterator = sorter.sortedIterator()
try {
  while (sortedIterator.next()) {
    // 由于sortedIterator根据key有序(key就是动态分区的值)，所以当key不等于上一个key时，表示应该写入一个新文件，且旧文件的输出流可以关闭。
    if (currentKey != sortedIterator.getKey) {
      if (currentWriter != null) {
        currentWriter.close(false)
      }
      currentKey = sortedIterator.getKey.copy()
      logDebug(s"Writing partition: $currentKey")
      // 根据新的currentKey新建HiveWriter
      currentWriter = newOutputWriter(currentKey)
    }

    // 写入数据
    var i = 0
    while (i < fieldOIs.length) {
      outputData(i) = if (sortedIterator.getValue.isNullAt(i)) {
        null
      } else {
        wrappers(i)(sortedIterator.getValue.get(i, dataTypes(i)))
      }
      i += 1
    }
    currentWriter.write(serializer.serialize(outputData, standardOI))
  }
} finally {
  if (currentWriter != null) {
    currentWriter.close(false)
  }
}
commit()
```

> 可以看到Spark在输出前对Key进行排序，这是为什么呢？  

很容易推测，Spark默认动态分区插入的场景是会产生大量分区，如果不进行排序，那么同时写入多个文件，会造成了磁盘的随机IO，降低写性能。而使用排序后的数据，每次写入文件时都能保证是顺序写入。

***

## 改进
很容易想到，如果你的数据本身大部分存在于某个分区，那么其实不排序，也能保证大部分时间在顺序写入，反而，排序的性能消耗大于了偶尔的随机读写。所以在这里，可以引入一个新的参数:

> spark.sql.hive.useDynamicPartitionWriter

用户可以自定义是否启动DynamicPartitionWriter的功能，如果关闭，那么新建一个Map来缓存对所有不同的Key对应的Writer。改动如下：

```
logInfo("UseDynamicPartitionContains is false, skip sorting.")
val keyWriterMap: mutable.Map[InternalRow, FileSinkOperator.RecordWriter] = mutable.Map()
try {
  while (iterator.hasNext) {
    val internalRow = iterator.next()
    val key = getPartitionKey(internalRow)
    if (currentKey != key) {
      currentKey = key.copy()
      logDebug(s"Writing partition: $currentKey")
      currentWriter = keyWriterMap.getOrElseUpdate(currentKey, newOutputWriter(currentKey))
    }

    var i = 0
    while (i < fieldOIs.length) {
      outputData(i) = internalRow.get(i, dataTypes(i))
      i += 1
    }
    currentWriter.write(serializer.serialize(outputData, standardOI))
  }
} finally {
  keyWriterMap.values.foreach(writer => {
    if (writer != null) {
      writer.close(false)
    }
  })
}
commit()
```


![Jiayi Blog](https://user-gold-cdn.xitu.io/2019/4/2/169d9ebd3e053fd7?w=2876&h=1522&f=png&s=471461)

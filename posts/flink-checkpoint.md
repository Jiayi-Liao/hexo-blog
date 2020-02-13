title: 如何在无Checkpoint时初始化Flink程序的状态？
author: Liao Jiayi
tags:
  - Flink
  - Checkpoint
articleId: flink-checkpoint
categories:
  - Apache Flink
keywords:
  - Checkpoint
  - Flink Checkpoint
  - Savepoint
  - Flink Savepoint
  - Flink容错性
description: 本文针对Apache Flink中Checkpoint/Savepoint无法从0恢复的缺点，给出了三种解决方案。
date: 2018-10-25 10:42:04
---
其实这个功能需求在Flink的开发和产品迭代中非常常见，情形如下：

* 首次启动Flink时需要加载状态。
* 修改了Flink状态的相关类代码无法重新加载。
* Checkpoint意外损毁无法被反序列化。

毫无疑问，这是一个生产环境必须要具备的能力，否则之后的开发和迭代都收到了很大的限制。之前也在这方面从不同的角度做了不少的探索，方法途径多样，在这里记录一下。社区的邮件讨论可以点击[这里](http://mail-archives.apache.org/mod_mbox/flink-dev/201808.mbox/%3CCAMZk55au_G3F5_eREPCr59n5BbROS3W_4FN_TjVY4_PPtBK4pQ@mail.gmail.com%3E)。

***

#### ConnectedStream
利用ConnectedStream是一个不需要二次开发并且很取巧的方法。

```
val recoverStream = env.addSource(sourceA)
val dataStream = env.addSource(sourceB)
recoverStream.connect(dataStream)
```
这里将恢复的数据流和正常数据流connect，意味着后续的聚合操作需要同时对聚合数据和明细数据做分别处理，例如：

```
override def add(value: IN, accumulator: ACC): ACC = {
    value match {
        case AGG(x) => accumulator.merege(value)
        case RECORD(x) => accumulator.add(value)
        case _ => accumulator
    }
}
```
这种方法直接使用了Flink的ConnectedStream来实现两种数据的合并，简单易实现但是不够优雅:)，是一个可行的方式同时又会带来以下影响。

1. 增加了一条数据流，增加了相应parallelism数量的Task，并且这个数据流在状态恢复以后并没有任何作用。
2. 在后续ETL中需要对数据类型做出判断，分别处理，ETL链路过长的话略有繁琐。

***

#### Bravo
[Bravo](https://github.com/king/bravo)是一个和Flink State有关的开源项目。
> Bravo is a convenient state reader and writer library leveraging the Flink’s batch processing capabilities. It supports processing and writing Flink streaming snapshots. At the moment it only supports processing RocksDB snapshots but this can be extended in the future for other state backends.

它可以对Flink的savepoint目录进行read&write，目前只支持RocksDB。基本原理是基于Flink中RocksDBStateBackend的restore/snapshot的方法的序列化以及反序列化逻辑，提取出了一些基于KeyedState/OperatorState的方法。  

这个项目不好的地方在于它独立于Flink而存在，所以需要重写很多Flink内部对savepoint的处理和读取的逻辑。我曾经尝试过在[bravo](https://github.com/king/bravo)中加入FsStateBackend的Reader/Writer，但是因为Flink在FsStateBackend的代码结构涉及到的类过多，逻辑也略复杂，导致在完成Reader之后不得不放弃。  

不过基于RocksDB的Backend还是可以使用它来操作savepoint的。

*** 

#### Queryable State
从Flink 1.6开始引入了[Queryable State](https://ci.apache.org/projects/flink/flink-docs-release-1.6/dev/stream/state/queryable_state.html)这个概念。通过stateDescriptor.setQueryable(String queryableStateName)来让State可查，原理如下：

1. 在TaskManager中如果检测到可查询的State，会启动一个KvStateServer。
2. 使用[说明文档](https://ci.apache.org/projects/flink/flink-docs-release-1.6/dev/stream/state/queryable_state.html)中的示例代码对State进行查询，依次通过ClientProxy,ServerProxy,Server，检验有效性成功之后，使用StateTable中的get(K key, N namespace)获得State的值并返回。

了解这个原理之后，其实写一个对应的Writable State的接口就非常简单了，在KvStateServer加入接口，调用StateTable中的写方法即可完成。需要改动以下文件：
注意这里对StateTable的操作必须要加锁。  

```
QueryableStateClient.java
KvStateRequest.java
KvStateClientProxyHandler.java
KvStateInternalRequest.java
KvStateServerHandler.java
StateTable.java
```

这样做的好处是相对灵活，日后如果有类似的需求可以通过调整接口实现。同时，这也破坏了Flink的容错性，因为在写入State时，若在下一个checkpoint完成前出现失败情况，Flink是无法恢复这个State的。

*** 
最优雅最正确的方式应该是使用外部构建savepoint的方式，既没有破坏现有程序中State的完整性，也没有加入不必要的代码。Flink社区目前也在朝这个方向努力，只是由于不同StateBackend序列化的格式与逻辑大相径庭，导致要兼容所有的StateBackend显得略有困难。




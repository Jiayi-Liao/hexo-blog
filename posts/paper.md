---
title: Paper Notebook
date: 2018-05-08 22:29:10
tags: Data
keywords: data
categories: Notes
---
记录一下自己读的Paper。

## Apache Calcite

* [Apache Calcite: A Foundational Framework for Optimized Query Processing Over Heterogeneous Data Sources](https://arxiv.org/abs/1802.10233)：资料比较少，写了一篇[博客](http://www.liaojiayi.com/calcite-paper/)。

***

## Spark 存储计算分离

* [taking-advantage-of-a-disaggregated-storage-and-compute-architecture](https://databricks.com/session/taking-advantage-of-a-disaggregated-storage-and-compute-architecture): Facebook关于存储和计算分离的实践，将HDFS/S3/LocalFs抽象成了GenericFile，统一放在存储端，通过配置不同的机型来实现成本的最优化，改进了Spark中对于存储分离不友好的一些地方，比如External Service需要拉两次数据等问题。

***

## LSM 模型下的优化

* [WiscKey: Separating Keys from Values
in SSD-conscious Storage](https://www.usenix.org/system/files/conference/fast16/fast16-papers-lu.pdf): 基于SSD和小key大value的事实：

	* LSM file内部不再排序，更好的利用SSD的随机读的性能，减少了排序的代价。  
	* 引入Vlog的结构，减少写放大，定时检查vlog中数据的有效性。

***

* [HashKV: Enabling Efficient Updates in KV Storage via Hashing](https://www.usenix.org/system/files/conference/atc18/atc18-chan.pdf): 基于 WiscKey 的结构做了一些优化：

	* 通过对数据进行分区，将数据分为了热区和冷区，这样因为热区有频繁的update，可以及时的触发热区的gc。
	* 小value的数据可以直接写入到LSM file中。

	
***

## Spark 大规模 Shuffle 优化

* [SOS: Optimizing Shuffle I/O](https://vimeo.com/274418771): 基于大规模shuffle做了一些优化，主要是针对map多，数据小而碎，在 map 和 reduce 的中间加入了一些组件和 failover 的一些操作。

***

## 基于 Ray 的计算引擎

* [基于融合计算的在线学习](https://47.96.246.115/community/activities/698/review/839): 基于规则的机器学习无法满足实时的在线学习需求。希望将计算和机器学习一体化。现有系统下，阿里使用 Blink + Tensorflow，中间使用 Queue 来实现连接，这样系统割裂，中间的成本高昂。把训练和样本放在一起来做。 Straming / Training / Serving。

![ray](http://www.liaojiayi.com/assets/ray.jpg)
![ray](http://www.liaojiayi.com/assets/ray-target.jpg)

***

## GFS

* [The Google File System](https://pdos.csail.mit.edu/6.824/papers/gfs.pdf)

背景:

1. 在集群中，机器故障变得常见。
2. 文件很大。
3. 场景多为 append-only。

和 HDFS 不一样的是，GFS 支持多个 client 同时写入同一个文件。支持 snapshot / checkpoint，采用 copy-on-write 的方式来实现。

Master 对目录的修改采用目录级别的读写锁。

***

## Kafka

* [Exactly once Semantics are Possible: Here’s How Kafka Does it](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/)
* [Transactions in Apache Kafka](https://www.confluent.io/blog/transactions-apache-kafka/)


## Pulsar

这个项目整体是围绕着 Apache Bookeeper 这个 Storage 去做一些事情，包括消息队列、轻量流式处理以及文件系统等。

pulsar 如何处理 Disk Failure？ 在 Bookeeper 中使用其他 Bookie 的数据来修复 Failed Disk 中的 Segment。Segment 粒度较小，相对 kafka 会快一些。

和其他消息队列的对比：

* 多租户
* 分层架构设计
* 批处理更有优势


* [Pulsar + Flink](https://www.slidestalk.com/ApachePulsar/190831WAICPulsarFlinkpptx13461)
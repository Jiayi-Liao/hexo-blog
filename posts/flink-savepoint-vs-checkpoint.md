title: 【译】Flink - Savepoint vs Checkpoint
author: Liao Jiayi
articleId: flink-savepoint-vs-checkpoint
tags:
  - Flink
  - Checkpoint
categories:
  - Big Data Computation Engine
keywords:
  - Flink
  - Savepoint
  - Checkpoint
description: 本文译自Data Artisans博客，比较了Apache Flink中Savepoint和Checkpoint的异同点。
date: 2018-11-04 15:06:38
---
> 译自dataArtisans博客：[3 differences between Savepoints and Checkpoints in Apache Flink](https://data-artisans.com/blog/differences-between-savepoints-and-checkpoints-in-flink)。
> 不少开发者在Flink开发时都会混淆这两个概念，那么这两个表面看起来相似的东西，有什么不同呢？

#### 相关概念
Apache Flink Savepoint允许你生成一个当前流式程序的快照。这个快照记录了整个程序的状态，包括数据处理的具体位置，如Kafka的offset信息。Flink采用了[Chandy-Lamport](https://en.wikipedia.org/wiki/Chandy-Lamport_algorithm)的快照算法来生成具有一致性的Savepoint。Savepoints包括两个主要元素：

1. 一个记录了当前流式程序所有状态的二进制文件（通常很大）。
2. 一个相对较小的Metadata文件。它存储在你所指定的分布式文件系统或者数据存储中，包括了Savepoints的所有文件指针（路径）。

关于Savepoint的细节可以阅读我们早期的博客：[step-by-step guide on how to enable Savepoints](https://data-artisans.com/blog/turning-back-time-savepoints)。  

上述关于Savepoints的讲解听起来很像我们早期博客中涉及到的Checkpoint。Checkpoint是Apache Flink中的内部机制，它负责故障恢复，状态拷贝（持久化）和记录消费位置。如果程序失败，Flink可以利用Checkpoint中的状态恢复，并继续从失败前的位置开始处理（好像没事一样）。  

可以参考[How Apache Flink manages Kafka Consumer offsets](https://data-artisans.com/blog/how-apache-flink-manages-kafka-consumer-offsets)

![flink-savepoint-3][1]


Checkpoints和Savepoints都是Apache Flink流式处理框架中比较特别的功能。它们在实现上类似，但在以下三个地方有些不同：

1. **目标**：从概念上讲，Savepoints和Checkpoints的不同之处类似于传统数据库中备份和恢复日志的不同。Checkpoints的作用是确保程序有潜在失败可能的情况下（如网络暂时异常），可以正常恢复。相反，Savepoints的作用是让用户手动触发备份后，通过重启来恢复程序。
2. **实现**：Checkpoints和Savepoints在实现上有所不同。Checkpoints轻量并且快速，它可以利用底层状态存储的各种特性，来实现快速备份和恢复。例如，以RocksDB作为状态存储，状态将会以RocksDB的格式持久化而不是Flink原生的格式，同时利用RocksDB的特性实现了增量Checkpoints。这个特性加速了checkpointing的过程，也是Checkpointing机制中第一个更轻量的实现。相反，Savepoints更注重数据的可移植性，并且支持任何对任务的修改，同时这也让Savepoints的备份和恢复成本相对更高。
3. **生命周期**：Checkpoints本身是定时自动触发的。它们的维护、创建和删除都由Flink自身来操作，不需要任何用户的干预。相反，Savepoints的触发、删除和管理等操作都需要用户手动触发。

| 维度 | Checkpoints | Savepoints |
| - | - | - |
| 目标 | 任务失败的恢复/故障转移机制 | 手动备份/重启/恢复任务 |
| 实现 | 轻量快速 | 注重可移植性，成本较高 |
| 生命周期 | Flink自身控制 | 用户手动控制 |

#### 什么时候在流式程序中使用Savepoints？
虽然流式程序处理的是无止境的流数据，但实际上，可能会有消费之前的已经被消费过的数据的需求。Savepoints可以帮助你满足一下场景：

* 更新生产环境的程序，包括新功能、bug修复或者更好的机器学习模型
* 在程序中引入A/B测试，从同一个数据源的同一个时间点开始消费，测试不同版本的效果
* 扩容，使用更多的集群资源
* 使用新版本的Flink，或者升级到新版本的Flink集群。

#### 结论
Checkpoints和Savepoints是两个不同的功能，但它们都是为了保证Flink的一致性，容错性。其中，Checkpoints适用于程序潜在的失败，Savepoints适用于程序升级、bug修复、迁移和A/B测试。这两个功能结合使用可以在不同场景下将程序的状态持久化并恢复。  


> 注：
> 1. 为了翻译方便，我将原文中的图片换成了表格。
> 2. 原文某些内容直译后有些抽象，我加入了一些自己的想法。

  [1]: http://www.liaojiayi.com/assets/flink-savepoint-3.png

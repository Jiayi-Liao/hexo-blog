title: Flink - Network Buffer
author: Liao Jiayi
tags:
  - Flink
  - network
articleId: flink-network-buffer
categories: Apache Flink StateBackend
keywords:
  - Flink
  - network
date: 2020-06-12 07:08:40
---
Flink 中 Network Buffer 相关知识。

# 问题

如果你是带着以下问题来到这里的，那么我相信这篇文章可以给你答案。

* Network Buffer、或者 Network Segment 的作用是什么？在很多地方看到这个名词但是不知道是做什么用的
* Network Buffer 占用的内存是哪一块？应该如何去调整这一块内存？
* 为什么每次扩大并发后重启，就会报出 `insufficient number of network buffers` 的错误？为什么复杂的拓扑需要的 network buffers 会这么大？network buffers 的数量应该如何计算？
* 如何合理地设置 network buffers 的数量？

# 用途

Network Buffer，顾名思义，就是在网络传输中使用到的 Buffer（实际非网络传输也会用到）。了解 Flink 网络栈的同学应该会比较清楚，Flink 经过网络传输的上下游 Task 的设计会比较类似生产者 - 消费者模型。如果没有这个缓冲区，那么生产者或消费者会消耗大量时间在等待下游拿数据和上游发数据的环节上。加上这个缓冲区，生产者和消费者解耦开，任何一方短时间内的抖动理论上对另一方的数据处理都不会产生太大影响。

![Flink network 生产者消费者模型](http://www.liaojiayi.com/assets/flink-network-buffer-p-c.png)

这是对于单进程内生产者-消费者模型的一个图示，事实上，如果两个 Task 在同一个 TaskManager 内，那么使用的就是上述模型，那么对于不同 TM 内、或者需要跨网络传输的 TM 之间，是如何利用生产者-消费者模型来进行数据传输的呢？

如果之前看过 [credit-based 机制介绍](https://flink.apache.org/2019/06/05/flink-network-stack.html) 的同学可能对接收端的 buffer 池会比较了解，我们将发送端和接收端连起来看看，

![Flink 网络栈介绍](http://www.liaojiayi.com/assets/flink-network-credit.png)

可以看到，在 Netty Server 端，buffer 只存在 LocalBufferPool 中，subpartition 自己并没有缓存 buffer 或者独享一部分 buffer（这样的问题我在 [Flink网络栈中反压机制的优化](http://www.liaojiayi.com/flink-network-stack-opt/) 中有提到过），而在接收端，channel 有自己独享的一部分 buffer(Exclusive Buffers)，也有一部分共享的 buffer(Floating Buffers)，所以，Network Buffer 的使用同时存在于发送端和接收端。





# 使用


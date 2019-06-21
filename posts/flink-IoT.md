title: 【译】在物联网中使用Apache Flink的7个原因
author: Liao Jiayi
tags:
  - IoT
  - Flink
articleId: flink-IoT
categories:
  - Big Data Computation Engine
keywords:
  - Flink
  - 物联网
  - IOT
description: 本文译自Data Artisans博客，讲解了在物联网中使用Apache Flink的7个原因。
date: 2018-11-24 13:59:20
---
> 译自dataArtisans博客：[7 Reasons to use stream processing & Apache Flink in the IoT industry](https://data-artisans.com/blog/differences-between-savepoints-and-checkpoints-in-flink)。

这是Freeport Metrics的技术总监的一篇关于流式数据处理和Apache Flink在物联网领域应用的文章。这篇文章出自[Freeport Metrics Blog](https://freeportmetrics.com/blog/7-reasons-to-use-real-time-data-streaming-and-flink-for-your-iot-project/#%23)。  

物联网领域的数据处理，由于一些特有的挑战，使得采用Flink做流式数据处理成为了一个可靠的选择。物联网领域中遇到的问题如：

* 设备产生的数据远比用户要多。由于这种流式数据远比终端带来的多，所以传统数据库在处理这类大数据时有些力不从心。
* 物联网用户需要更实时的数据。他们需要基于这些数据，立刻计算出之后的行为。所以，ETL(extract-transform-load)处理或者批处理并不能满足上述的要求。
* 通过蜂窝网络从终端传输数据时连接的稳定性无法保证。

Freeport Metrics借助Flink已经在物联网领域中的若干个项目中实现了流式数据处理，如太阳能监测和计费平台，优化风电场数据处理，并搭建一个大规模、实时的射频设备追踪平台。以下是推荐你在物联网领域中使用Apache Flink的7个原因：
![此处输入图片的描述][1]


#### 1. 实时性
物联网领域需要实时获取设备行为的信息。例如，在有风的时候，风力涡轮却没有产生能量；贵重的设备在无预兆的情况下离开了工厂，在这两种情况下，从商业利益角度来说，都必须马上知道这些信息。以流式处理代替批处理，从根本上改变了工程的思维结构，并且在这种模式下还支持针对数据使用触发器，设置定时告警，监测事件行为规律。

#### 2. 支持事件时间
当移动设备通过蜂窝网络上传数据，我们需要考虑延迟和网络传输失败的情况。即使我们能保证网络稳定，也无法确定用户的设备的可用性和网络传输的物理距离。  
例如，工厂中的机器或汽车零部件在生产线上移动，传感器通过网络传输带来的数据是无法保证有序性的。不仅这样，使用事件时间而不是服务器接收数据的时间，来处理物联网相关的数据是更加合理的。所以在选择数据处理框架中，事件时间是必须要有的一个功能。  

关于事件时间和处理时间以及接收时间的比较可以参考[event time in Apache Flink](https://data-artisans.com/blog/stream-processing-introduction-event-time-apache-flink)。

#### 3. 处理杂乱数据的工具
数据处理过程中最困难的是特殊情况下的数据预处理，尤其是在物联网领域这种无法控制数据源的数据的情况下，导致你使用大量的清理代码和特殊的处理逻辑。  
流式处理虽然不会帮你解决这些问题，但是它给你提供了很多工具，其中最有帮助的是[windowing](https://flink.apache.org/news/2015/12/04/Introducing-windows.html)，它将无限的数据流通过一定的条件（如时间、计数器）整合成一个数据集。  
例如，模拟传感器或GPS的数据杂乱无章，但使用[window processing function](https://ci.apache.org/projects/flink/flink-docs-stable/dev/stream/operators/windows.html)的功能可以通过平均数的方式将这些复杂数据简化。  
电力中心发送数据较快，但是由于[Modbus](https://en.wikipedia.org/wiki/Modbus)协议会出现故障频发的情况，所以只在每天凌晨产生准确的数据文件。在这种情况下，你可以使用Modbus数据来计算实时的近似数据，然后在每天凌晨使用准确的数据文件来计算准确的账单。这可以通过一个trigger来实现，当拿到数据文件时，关闭正在输入输出的窗口。  
有些情况下，无法知道是否所有的数据都已经被接收，这时候可以使用启发式的watermark来触发window输出，watermark可以是一个根据经验计算的值或者是数据接收的timeout。Flink也支持定义[allowed lateness of elements](https://ci.apache.org/projects/flink/flink-docs-stable/dev/stream/operators/windows.html#allowed-lateness)并提供[side outputs](https://ci.apache.org/projects/flink/flink-docs-stable/dev/stream/operators/windows.html#triggers)来处理迟到的数据。

#### 4. 并行处理分群
物联网领域中常有对某个子数据集做计算的情况。假设你搭建了一个平台来让主人监控猫的行为，每个主人都只需要他们自己的猫的数据。Flink引入了[grouping by key](https://ci.apache.org/projects/flink/flink-docs-release-1.6/dev/api_concepts.html#specifying-keys)来实现这样的功能，一旦数据被分流，他们可以并行处理，所以你可以横向扩展。分流的key不需要绑定在具体的设备或者位置上，例如在舰队管理中，你希望将舰队通过不同的维度来分组（如GPS，硬件传感器，执照）。  
我们也推荐大家去探索[data Artisans Streaming Ledger](https://data-artisans.com/streaming-ledger)，它支持了在不同并行的数据流中，通过共享状态和数据表来实现分布式的事物管理（已经在River Edition中实现）。

#### 5. 本地状态性能优化
随着硬件和基础设施的进步，大家对于延迟的认知也在变化，但有些基本的原则是不变的：

* 越快收到数据，越快处理完
* 磁盘I/O损耗性能

ApacheFlink帮助在使用[local state](https://ci.apache.org/projects/flink/flink-docs-release-1.6/dev/stream/state/)时保证数据的准确性。更重要的是，这个状态在使用[lightweight checkpointing](https://ci.apache.org/projects/flink/flink-docs-release-1.6/internals/stream_checkpointing.html#checkpointing)时，也保证了[fault tolerant](https://ci.apache.org/projects/flink/flink-docs-release-1.6/internals/stream_checkpointing.html)，同时优化了I/O性能。不要简单地认为local state是一个只读的本地缓存，当你使用新数据做实时计算并更新它时，就能感受到它很多的好处。很多人甚至质疑是否需要新增一个存储层并将Flink作为单一的数据接收源。如果你想要深入了解，可以看看Lightbend的Viktor Klang的文章[talk about the convergence of streaming and microservice architecture](https://data-artisans.com/flink-forward-berlin/resources/the-convergence-of-stream-processing-and-microservice-architecture)。

#### 6. Flink支持消息队列
当你想到流式处理，你通常也会想到一些针对大数据的高度可扩展并稳定的消息队列组件，如Apache Kafka，AWS Kinesis或者RabbitMQ。Flink对这些组件提供了非常强的支持，不仅在生产和消费上，同时也基于它们分布式的特性，实现了如分区和分片的功能，来提升处理数据的性能。如果业务需要，端到端的绝对一次数据，也从Flink扩展到了这些外部系统。  
我们之前的一篇早期博客提到了这些细节[how Apache Flink manages Kafka consumer offsets](https://data-artisans.com/blog/how-apache-flink-manages-kafka-consumer-offsets)。

#### 7. 简单的数据处理（适应期之后）
最后，也是很重的一点，一旦采用了一个新的流式处理框架，它用起来应该是非常合理并自然的。尽管可能你的团队在学习Flink或者适应算子并行度上有一个陡峭的学习曲线，但一旦习惯后，你可以专注于业务的核心逻辑而不是一些被框架处理的繁杂冗余的工作。  
在Freeport Metrics，我们从批处理迁移到Flink的流式处理，和大多数技术框架的升级迁移，都有类似的情况。在某些时候，你会明白这是一个正确的工具并且后悔没有早些采用它。  

*** 
这些看法，使我们坚信了在物联网领域，真正有使用像Apache Flink这种流式数据处理框架的需求。Flink的功能、连接器、容错性和可靠性，使得它在处理流式大数据时，成为了众多可以选择的框架之一。  


  [1]: http://www.liaojiayi.com/assets/flink-IoT.png

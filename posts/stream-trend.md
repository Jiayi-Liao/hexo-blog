title: 流式计算未来的发展趋势
author: Liao Jiayi
tags:
  - 流式计算
    - streaming
articleId: streaming-trend
categories: Apache Flink
keywords:
  - 流式计算
date: 2020-09-13 07:08:40
---

受 SIGMOD 会议的论文 [Beyond Analytics: The Evolution of Streaming Processing Systems](https://cda-group.github.io/papers/SIGMOD-streams.pdf) 的启发，聊一下流式计算未来的趋势。

有兴趣的同学可以读一下论文，论文前半部分主要讲的是流式计算的发展，说了很多流计算里特有的概念，在这里略过，从第 4 节开始看。

# 4.1 Emerging Applications

1. Cloud Application
2. Machine Learning
3. Streaming Graphs

第一点，云原生的概念火热的飞起，不过确实，过往经验中使用过 AWS 的云服务和 IDC 的物理机，维护成本完全是不能比。随着资本从互联网向其他方向转移，融资困难的情况下，互联网公司的硬件成本想必也会在创业初期成为很重要的一个考虑因素。在以前使用 AWS 云服务的过程中，举两个简单的例子：

* 对象存储按量收费，对象存储有点类似于冷存，因为云服务提供商有全局视角，所以可以很合理地来配置存储资源，使得资源利用率非常高，所以对象存储的存储费用极低，但是每次访问占用的带宽和 CPU 是要按量付费。我觉得这个就很合理了，将历史的明细数据作为冷存放入到对象存储中，只需要将近期数据和热点数据放在 HDFS 或者其他 OLAP 存储里，可以极大地压低大数据量公司的存储成本
* 廉价的不稳定机型，这也是当时让我很吃惊的点。AWS 的机型中有一种很廉价，但是稳定性保证很差的机型，不适合常驻的服务，但是在做好推测执行、Shuffle Service 的情况下，非常适合跑 BATCH 任务，因为 BATCH 任务本身就是离线任务，且 DAG 的任务天生可以通过拓扑之间的关系进行容错。

第二点不说了，机器学习，深度学习，我也不懂。。。

第三点是流式计算中特有的概念，值得说一下。

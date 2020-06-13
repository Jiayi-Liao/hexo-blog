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


# 使用

1. Network Buffer 如何计算？
2. Network Buffer 存在哪里？
3. Network Buffer 存在的意义？
4. Network Buffer 过去是如何指定的，以及现在是如何指定的？
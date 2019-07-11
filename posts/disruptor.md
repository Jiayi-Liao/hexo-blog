---
title: Disruptor
date: 2019-06-16 18:38:16
tags: Disruptor
keywords: Disruptor
categories: 未分类技术文章
---



Disruptor是2011年由LMAX提出的一个无锁消息队列，在短短45分钟的视频分享中，有很多的信息可以分享和深究。


## Background

我们先来看看多线程编程中各种"锁"带来的性能损耗有多大，以一个计数器为例：

```
static long counter = 0

private static void increment() {
	for (long l = 0; l < 500000000L; l++) {
		counter++;
	}
}
```

我们以各种多线程常见的方式重新定义 counter，得到如下结果：

| 线程数 | 方案                        | 损耗   |
| ------ | ----------------------------- | -------- |
| 1      | 无                           | 300ms    |
| 1      | 使用volatile修饰counter   | 4700ms   |
| 1      | 使用AtomicLong作为counter类型 | 5700ms   |
| 1      | 使用lock给counter的操作加锁 | 10000ms  |
| 2      | 使用AtomicLong作为counter类型 | 30000ms  |
| 2      | 使用lock给counter的操作加锁 | 224000ms |

"锁"的性能损耗，有时候可以达到真正业务性能损耗的数倍甚至数百倍。而我们常用的消息队列如 ArrayListQueue，当有一个 Producer 和一个 Consumer时，它的消费场景如图所示：


![queue architecture](http://www.liaojiayi.com/assets/queue.png)

Producer 在往队列中添加数据，而 Consumer 在队列中获取并移除数据，两个线程同时改变消息队列的状态，这必然存在一个"锁"来保证生产者和消费者之间的一致性，而这个"锁"恰恰成为了使用队列经常遇到的性能瓶颈。这里存在着两个资源竞争：

* 数据的竞争，生产者需要添加，而消费者需要删除。
* 元数据的竞争，如剩余队列大小，最新数据索引等。

## Contention Free Design

刚刚提到消费者改变状态的原因是因为需要把数据从队列中取走，那么，如果不需要取走，设置一个 cursor 来控制消费的位置，是否就可以避免带来性能损耗的"锁"呢？事实上 Disruptor 采用了 RingBuffer 的数据结构来存储数据，Producer 维护一个 Sequence 作为消息的索引，而 Consumer 维护自己的一个 index 来记录消费 RingBuffer 的位置。整体的结构图如下：



![disruptor architecture](http://www.liaojiayi.com/assets/disruptor-architecture.png)


生产者和消费者唯一存在竞争的变量就是 sequence，因为消费者需要保证自己的 index 小于目前队列中最大的 sequence。那么为了方便，这个 sequence 变量自然可以使用 volatile 来修饰。但是有没有可能再进一步地去优化？


## Optimization

如果想在 volatile 的层面上进一步优化，我们先要看看 volatile 为什么会让性能产生损耗。图中显示了一个多核CPU的架构图，这里需要提到，cpu 对指令的执行会有一系列的优化来达到充分利用 cpu 缓存的目的，比如 cpu 会将执行指令 pipeline 起来然后重排顺序，让缓存命中达到最大化。根据 jvm 的 happen-before 原则，volatile 的写操作必须要在读操作之前，所以 jvm 对执行的命令已经规定了顺序，那么此时 cpu 无法再进行重排序，同时为了让其他的 cpu 读取到 volatile 的最新值，在读取时会插入一个 Load Barrier，目的是更新缓存中 volatile 变量的值，相当于每次从 RAM 中读取，没有利用任何的 cpu 缓存。  

![cpu architecture](http://www.liaojiayi.com/assets/cpu.png)


从消息队列的角度来讲，如果不是非常在意每次读取都要读取 sequence 的最新值，那么完全可以不需要 Load Barrier，直接读取缓存中的旧值即可（当写入操作完成时，cpu 会将数据从 Store Buffer 更新到 Load Buffer中），这样的话，相当于每次都是从 cpu 缓存中读取数据。那么提供这种方式的代码就是 AtomicLong 中的 lazySet。


## 参考

* [Understanding the Disruptor, a Beginner's Guide to Hardcore Concurrency -Trisha Gee & Mike Barker](https://www.youtube.com/watch?v=DCdGlxBbKU4)
* [Memory Barriers/Fences](https://mechanical-sympathy.blogspot.com/2011/07/memory-barriersfences.html)



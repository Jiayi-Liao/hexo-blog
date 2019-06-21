---
title: Linux性能优化实战笔记
date: 2019-05-27 21:15:42
tags: Linux
keywords: Linux
categories: Linux
---
之前被推荐了极客时间的这个课程，想想也是蛮需要的，在这里记录一下自己对每节的总结和思考。

## 性能调优图谱

![linux-tools](http://www.liaojiayi.com/assets/linux-tools.png)

## 如何理解平均负载？

登录到 Linux 服务器上执行 uptime 命令，得到如下输出：

```
 21:17:08 up 81 days, 22:30,  1 user,  load average: 0.15, 0.11, 0.07
```

分别为当前时间、系统运行时间、登陆用户数、1min/5min/15min的系统平均负载。关于平均负载的定义，执行 man uptime 可以看到：

```
System load averages is the average number of processes that are either in a runnable or uninterruptable state.  A process in a runnable state is either using the CPU or waiting to use the CPU.
A  process  in uninterruptable state is waiting for some I/O access, eg waiting for disk.  The averages are taken over the three time intervals.  Load averages are not normalized for the number
of CPUs in a system, so a load average of 1 means a single CPU system is loaded all the time while on a 4 CPU system it means it was idle 75% of the time.
```

系统平均负载为单位时间内活跃进程数。其中，活跃进程数分为两种：

* Runnable Process: 正在使用CPU或者等待CPU的进程。
* Uninterruptable Process: 不可中断进程，如在等待磁盘IO的进程。

所以，不能把 avg load 高当做是 CPU 高。平均负载过高可能是如下情况导致：

* CPU密集型：频繁使用CPU，导致单位时间内 Runnable Process 过多。
* IO密集型：频繁读写磁盘，导致单位时间内 Uninterruptable Process 过多。
* 大量等待 CPU 的进程调度也会导致平均负载过高。（什么情况下会导致大量等待 CPU 调度的进程？）


**实操工具**：

* stress: 可以模拟 cpu/io/memory 等负载情况。
* mpstat: 监测 processor 的情况。
* pidstat: 监测进程级别对各个资源的使用情况。




## CPU上下文切换

经常听到人提起上下文切换会影响性能这句话...  
CPU 使用寄存器来暂存指令、数据和地址，使用计数器来记录指令的地址，这些可以标识 CPU 当前状态和环境的因素构成了 CPU 的上下文。

上下文切换本质上是 CPU 的任务切换，这种任务切换分为三种：

* 进程间上下文切换
* 线程间上下文切换
* 中断上下文切换

> 进程间上下文切换

进程空间被 Linux 系统分为多层，其中 Ring0 层具有最高权限，为内核空间，Ring3 层只能访问受限资源，为用户空间。通常在内核空间运行被称为内核态，在用户空间运行被称为用户态。从用户态变成内核态，需要记录用户态下的指令位置，但这种上下文切换并没有涉及到用户态的资源，所以我们通常称这种上下文切换为特权模式切换。

> 线程间上下文切换

进程间切换本质上也是线程之间的切换，线程间切换分为两种：同一进程和非同一进程的线程间切换，区别在于是否需要切换虚拟内存、全局变量等资源。

> 中断上下文切换

硬件中断导致的内核态上下文切换，即使进程处在用户态，也会马上进行切换，优先级最高。

使用vmstat可以查看CPU上下文切换的信息。

如果自愿上下文切换多了，那么可能是有很多线程在等待IO，非自愿上下文切换多了，那么是多线程在争抢CPU资源。

**实操工具**：

* sysbench：多线程基准测试工具
* /proc/interrupts



## 从系统级别排查CPU问题

常用工具:

* perf: [Perf In Netflix](https://www.youtube.com/watch?time_continue=1286&v=UVM3WX8Lq2k)，查看CPU状态的工具，功能非常强大。
* pstree: 查看进程之间的父子关系。

常用的 top 命令：

Tasks有若干种：

* running
* sleeping
* stopped
* zombie

CPU也有若干种：

* us: user
* sy: system
* ni: nice time
* id: idle
* wa: IO-wait
* hi: hardware interrupt
* si: software interrupt



进程状态：

* R: Running 
* D: Disk Sleep 一般表示在和硬件交互
* Z: Zombie 
* S: Interruptible Sleep 可中断状态睡眠
* I: Idle

## 中断

处于性能考虑，一个中断会被拆为两个部分，上半部（硬中断）和下半部（软中断）：

* 硬中断：跟硬件交互，一般比较快。
* 软中断：由内核触发，一般比较慢。

软中断本身分为很多种，在 /proc/softirqs 中可以看到，针对网络带来的软中断，下面两个工具可以分析：

* sar: 查看系统的网络收发情况，不仅可以观察网络收发的吞吐量（BPS，每秒收发的字节数），还可以观察网络收发FPS。
* tcpdump: 抓包工具。













---
title: 编程基础
date: 2016-08-23 09:02:23
tags: Algorithm
keywords: Algorithm
description: 
categories: 编程基础
---

一些平时不常接触但是很重要的基础知识。

## JVM

### LOCK

* Fat Lock: 多线程访问资源，资源被竞争，性能消耗最大。
* Thin Lock: 多线程访问资源，但是不存在同时访问的情况，没有竞争。
* Recursive Lock: 资源被同一线程多次访问。
* Bias Lock: 只有一个线程会对资源进行访问。

### JVM 内存模型

* 堆：堆是java虚拟机管理内存最大的一块内存区域，因为堆存放的对象是线程共享的，所以多线程的时候也需要同步机制。
* 方法区：类信息，常量。
* 栈：线程私有。存储局部变量表，操作栈，动态链接，方法出口等信息。每一个方法被调用的过程就对应一个栈帧在虚拟机栈中从入栈到出栈的过程。
* 程序计数器：线程独享，记录线程运行的位置。
* 本地方法栈：native层使用。


### GC



GC基础：

stw 时，所有线程需要进入 safepoint。但是要保证 safepoint 前所有的线程对某些对象的操作保持一致，这个很困难。有时候 GC 导致的 stw 很短，但是进入 safepoint 的时间会很长。具体的详细信息可以加入相关的 GC 参数来看。

* Mark Reachable Objects: GC 会定义一些对象作为 GC Roots，如静态对象等，然后根据 GC Roots 的引用，不断迭代标记相关的对象，被标记过的就是存活对象。在标记的过程中，会出现 stw，stw 的时长和 Heap 中存活的对象有关系。
* Remove Unused Objects: 在做完标记之后，JVM 需要回收没有用到的对象。
	* Sweep：清除之后，JVM 的内存空间里会出现断层，不利于之后的空间分配。
	* Compact：清除后，整理剩余存活的对象，解决了 Sweep 的问题但是增加了 GC Pause 的时间。
	* Copy：清除后，剩余存活的对象被 Copy 到另一块内存空间中。

GC 种类：
[minor-gc-vs-major-gc-vs-full-gc](https://plumbr.io/blog/garbage-collection/minor-gc-vs-major-gc-vs-full-gc)

[GC 具体的算法实现](https://plumbr.io/handbook/garbage-collection-algorithms-implementations)  

* Serial GC：新生代使用 mark-copy 老年代使用 mark-sweep-compact，单线程收集器，效率低，无法利用多核计算机的优势，过时算法，stw时间长。
* Parallel GC： 同上，但是多线程。
* Concurrent Mark and Sweep（CMS）：新生代使用 mark-copy，老年代使用 mark-sweep，主要是想降低 GC Pause 的时间，他本身分为 7 个阶段：
	1. Initial Mark: 开始标记老年代中 GC Roots，这点很重要，可能会扫描年轻代中的对象。（stw）。可能是本来就存在于老年代的 GC Roots，也有可能是从年轻代引用过来的对象。
	2. Concurrent Mark: 根据已经标记的老年代 Roots，开始标记老年代存活对象，不会 stw。因为没有做 stw，所以不是所有存活的对象都会被标记。 
	3. Concurrent Preclean: 再做一次刚刚的事情，从 GC Roots 标记老年代存活对象，因为上一步没有做 stw，所以这一次把上一步引用发生变化的对象找出来，重新再标记一遍。
	4. Concurrent Abortable Preclean: 不知道在干什么。。。
	5. Final Remark: 会发生 stw。保证之前的 Preclean 已经跟上了 Application 运行的进度。
	6. Concurrent Sweep: 移除不需要的对象，不需要 stw。
	7. Concurrent Reset: 最后做 reset。

* G1: Garbage First。将 Eden、Survivor、Tenured 三个区的内存打散，组成 Colelction 的单元结构，每次 GC 时以 Collection 的单元进行 GC，用户可以动态设置一些属性如 stw 最大时长，这样 G1 收集器会尽最大努力去做 GC。


### 引用

* Strong Reference：日常声明的对象就属于强引用，在没有对象对其进行引用时，通过 GC 消除。
* Weak Reference：除了 Weak Reference 之外，没有其他对象对其进行引用时，通过 GC 消除，并放在 weak reference 特有的 referenceQueue 中。
* Soft Reference：软引用，在内存空间不足时通过 GC 消除，可以用来做缓存使用。


## 分布式计算

* 数据倾斜问题


## 文件格式

* Parquet: 自身是基于 Dremel 来实现的，支持结构化数据。如下：![dremel](http://www.liaojiayi.com/assets/dremel.png)

* Orc: 采取的是行存+列存的方式，基本的存储单元是行，但是每个文件里分成了多个 strip，每个 strip 里有每列的一些元数据，可以加速过滤。如下 ![orc](http://www.liaojiayi.com/assets/orc.png)


* RCFile: 有些类似 Parquet，但是不能像 Parquet 一样支持结构化的数据。












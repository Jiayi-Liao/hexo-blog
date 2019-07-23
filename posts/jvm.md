---
title: JVM基础
date: 2018-03-16 18:38:16
keywords: Disruptor
categories: JVM
---



JVM 基础知识.

## Lock

JVM 提供了几种锁:

* Fat locks
* Thin locks
* Recursive locks
* Bias locks

## GC

stw 时，所有线程需要进入 safepoint。但是要保证 safepoint 前所有的线程对某些对象的操作保持一致，这个很困难。有时候 GC 导致的 stw 很短，但是进入 safepoint 的时间会很长。
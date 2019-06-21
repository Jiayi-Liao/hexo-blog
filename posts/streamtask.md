---
title: Flink - StreamTask With Mailbox
date: 2019-05-13 23:00:19
tags: Flink
keywords: Flink
categories: Big Data Computation Engine
---


前两天看到Flink的dev邮件列表里有一个对StreamTask的重构，今天研读了一下，觉得Flink的开发者们在处理问题上，确实是有点大道至简的感觉。具体的Proposal地址点击[这里](https://docs.google.com/document/d/1eDpsUKv2FqwZiS1Pm6gYO5eFHScBHfULKmH1-ZEWB4g/edit#heading=h.me9nb71lvmah)。

## Backgroud

读过Flink源码的都见过checkpointLock，这个主要是用来隔离不同线程对状态的操作，但是这种使用object lock的做法，使得main thread不得不将这个object传递给所有需要操作状态的线程，一来二去，就会发现源代码里出现大量的synchronize(lock)。这样对于开发和调试和源码阅读，都是及其不方便的。目前checkpoint lock主要使用在以下三个地方：

* Event Processing: Operator在初始化时使用lock来隔离TimerService的触发，在process element时隔离异步snapshot线程对状态的干扰，总之，很多地方都使用了这个checkpoint lock。
* Checkpoint: 自然不用说，在performCheckpoint中使用了lock。
* Processing Time Timers: 这个线程触发的callback常常对状态进行操作，所以也需要获取lock。

不得不说，如果没有清晰地理清楚这些组件的关系以及使用，那么checkpoint lock对大多数人来说，就是一个black box，即使出了故障，也很难定位到。

## Refactor

在重构这里，社区提议使用Mailbox加单线程的方式来替代checkpoint lock。那么Mailbox就成为了StreamTask的信息来源，（大多数情况下）替代了StreamTask#run():

```
BlockingQueue<Runnable> mailbox = ...

void runMailboxProcessing() {
    //TODO: can become a cancel-event through mailbox eventually
    Runnable letter;
    while (isRunning()) { 
        while ((letter = mailbox.poll()) != null) {
            letter.run();
        }

        defaultAction();
    }
}

void defaultAction() {
    // e.g. event-processing from an input
}

```


那么对于上面三者，异步的checkpoint和processing timer会将checkpoint lock中的逻辑变成一个Runnable，放入到Mailbox中，这样我们就将并发变成了基于Mailbox的单线程模型，整个StreamTask看起来会更加轻量。

checkpoint lock的接口还暴露给了用户自定义的Source Function，所以Proposal中还涉及到一些向后兼容的处理，在这里就暂不展开。

## Thoughts

checkpoint lock在写自定义Source时还是需要经常被用到的，有一次给patch写单测的时候好像还被坑过...所以在我看到这个Proposal之后有点豁然开朗的感觉。当然，这个问题我之前没有思考过，但是因为这个proposal我也对这些混乱的互相lock的机制有了明确的理解和想法。
虽然改动的思想很简单，但是这种简化问题的方式很值得学习。不仅是简化了当前的问题，而且由于整体结构的简化，使得后期性能优化的方向更加明确，对未来的工作也是很有利的。








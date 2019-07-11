title: Spark - 利用WeakReference来清理对象
author: Liao Jiayi
tags:
  - JVM
  - Spark
articleId: spark-weakreference
categories:
  - Apache Spark
keywords:
  - Spark
  - ContextCleaner
  - WeakReference
  - Spark GC
description: 本文描述了在Spark ContextCleaner中利用WeakReference和referenceQueue来清理无效对象的机制和原理
date: 2019-02-12 14:53:19
---
> 最近在[stackoverflow](https://stackoverflow.com)上看到有人好奇Spark是在什么时机对Accumulator或者Broadcast这样的变量进行回收的。自己在看源码的时候发现了这个有趣的地方。
  
***
  
  
### Spark ContextCleaner
我们在Spark闲置（没有任务执行）时，容易看到下面的日志：

```
19/02/12 05:19:51 INFO Spark Context Cleaner org.apache.spark.internal.Logging$class.logInfo(Logging.scala:54): Cleaned accumulator 108284023
19/02/12 05:19:51 INFO Spark Context Cleaner org.apache.spark.internal.Logging$class.logInfo(Logging.scala:54): Cleaned accumulator 108283658
```

追溯到源码中，可以得知SparkContext在启动时，初始化了ContextCleaner，并以daemon方式启动了一个cleaningThread线程，这个线程的作用就是不断循环，回收清理RDD、Broadcast变量、Accumulator等无效对象。    
这个时候可以提出一个问题：以Accumulator为例，当某个Accumulator不再使用（没有被任何对象引用）时，ContextCleaner是如何知道这个信息的？   
  
先看一下整个清理过程：

```
val reference = Option(referenceQueue.remove(ContextCleaner.REF_QUEUE_POLL_TIMEOUT))
  .map(_.asInstanceOf[CleanupTaskWeakReference])
// Synchronize here to avoid being interrupted on stop()
synchronized {
  reference.foreach { ref =>
    logDebug("Got cleaning task " + ref.task)
    referenceBuffer.remove(ref)
    ref.task match {
      case CleanRDD(rddId) =>
        doCleanupRDD(rddId, blocking = blockOnCleanupTasks)
      case CleanShuffle(shuffleId) =>
        doCleanupShuffle(shuffleId, blocking = blockOnShuffleCleanupTasks)
      case CleanBroadcast(broadcastId) =>
        doCleanupBroadcast(broadcastId, blocking = blockOnCleanupTasks)
      case CleanAccum(accId) =>
        doCleanupAccum(accId, blocking = blockOnCleanupTasks)
      case CleanCheckpoint(rddId) =>
        doCleanCheckpoint(rddId)
    }
  }
}
```

可以看到，ContextCleaner是通过一个referenceQueue找到了需要回收的对象(CleanAccum)。接下来，从referenceQueue入手，看看JVM中的WeakReference是什么样的存在。

***

### Java WeakReference

Java中对Reference有几种不同的分类：

* StrongReference: 通常我们定义的对象就属于这种，较难被GC。
* WeakReference: 如Spark中封装的**CleanupTaskWeakReference(task, objectForCleanup, referenceQueue)** ，如果引用的对象(task)只和当前的WeakReference对象联结，那么在GC中会被回收，并放入referenceQueue中。
* SoftReference: 相对WeakReference较强的引用，可以回收，但不一定是在下次GC中。

所以在ContextCleaner中，Spark采用了WeakReference + referenceQueue的方式来实现对象的回收。当我们注册一个Accumulator时，会同时调用registerForCleanup：

```
/** Register an object for cleanup. */
private def registerForCleanup(objectForCleanup: AnyRef, task: CleanupTask): Unit = {
  referenceBuffer.add(new CleanupTaskWeakReference(task, objectForCleanup, referenceQueue))
}
```

referenceBuffer的作用是保证WeakReference在处理前不被GC。  

Spark将注册的Accumulator封装到CleanupTask，并基于task初始化了一个WeakReference。当Accumulator不再被引用时，task会被放入referenceQueue中，而此时cleaningThread从referenceQueue中提取即将要GC的对象做处理（见上面的清理过程代码）。



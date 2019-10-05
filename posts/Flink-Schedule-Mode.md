title: Flink Schedule Mode
author: Liao Jiayi
date: 2019-03-18 16:49:08
tags:
  - Flink
articleId: flink-schedule-mode
categories: Apache Flink
keywords:
  - Apache Flink
---

Apache Flink中对流式数据和批数据的资源调度模式是不一样的。这周的周更博客，由于有事情耽搁，想的一些东西并没有时间做足够的整理，所以写的话题和内容有些简单，仅做了解。

### EAGER AND LAZY_FROM_RESOURCES
Apache Flink内部提供了两种调度模式，分别为：

```
/** Schedule tasks lazy from the sources. Downstream tasks start once their input data are ready */
LAZY_FROM_SOURCES,

/** Schedules all tasks immediately. */
EAGER;
```

**LAZY_FROM_SOURCES**的原理我们可以进入到**scheduleLazy**的方法里看一下:

```
private CompletableFuture<Void> scheduleLazy(SlotProvider slotProvider) {

	final ArrayList<CompletableFuture<Void>> schedulingFutures = new ArrayList<>(numVerticesTotal);

	// take the vertices without inputs.
	for (ExecutionJobVertex ejv : verticesInCreationOrder) {
		if (ejv.getJobVertex().isInputVertex()) {
			final CompletableFuture<Void> schedulingJobVertexFuture = ejv.scheduleAll(
				slotProvider,
				allowQueuedScheduling,
				LocationPreferenceConstraint.ALL); // since it is an input vertex, the input based location preferences should be empty

			schedulingFutures.add(schedulingJobVertexFuture);
		}
	}

	return FutureUtils.waitForAll(schedulingFutures);
}
```

**ExecutionJobVertex**代表某个operation，如map。在这里只调度 Source 相关的 ExecutionJobVertex。


**EAGER**的方式：

```
private CompletableFuture<Void> scheduleEager(SlotProvider slotProvider, final Time timeout) {
	checkState(state == JobStatus.RUNNING, "job is not running currently");

	// Important: reserve all the space we need up front.
	// that way we do not have any operation that can fail between allocating the slots
	// and adding them to the list. If we had a failure in between there, that would
	// cause the slots to get lost
	final boolean queued = allowQueuedScheduling;

	// collecting all the slots may resize and fail in that operation without slots getting lost
	final ArrayList<CompletableFuture<Execution>> allAllocationFutures = new ArrayList<>(getNumberOfExecutionJobVertices());

	// allocate the slots (obtain all their futures
	for (ExecutionJobVertex ejv : getVerticesTopologically()) {
		// these calls are not blocking, they only return futures
		Collection<CompletableFuture<Execution>> allocationFutures = ejv.allocateResourcesForAll(
			slotProvider,
			queued,
			LocationPreferenceConstraint.ALL,
			allocationTimeout);

		allAllocationFutures.addAll(allocationFutures);
	}

	// this future is complete once all slot futures are complete.
	// the future fails once one slot future fails.
	final ConjunctFuture<Collection<Execution>> allAllocationsFuture = FutureUtils.combineAll(allAllocationFutures);

	final CompletableFuture<Void> currentSchedulingFuture = allAllocationsFuture
		.thenAccept(
			(Collection<Execution> executionsToDeploy) -> {
				for (Execution execution : executionsToDeploy) {
					try {
						execution.deploy();
					} catch (Throwable t) {
						throw new CompletionException(
							new FlinkException(
								String.format("Could not deploy execution %s.", execution),
								t));
					}
				}
			})
		// Generate a more specific failure message for the eager scheduling
		.exceptionally(
			(Throwable throwable) -> {
				final Throwable strippedThrowable = ExceptionUtils.stripCompletionException(throwable);
				final Throwable resultThrowable;

				if (strippedThrowable instanceof TimeoutException) {
					int numTotal = allAllocationsFuture.getNumFuturesTotal();
					int numComplete = allAllocationsFuture.getNumFuturesCompleted();
					String message = "Could not allocate all requires slots within timeout of " +
						timeout + ". Slots required: " + numTotal + ", slots allocated: " + numComplete;

					resultThrowable = new NoResourceAvailableException(message);
				} else {
					resultThrowable = strippedThrowable;
				}

				throw new CompletionException(resultThrowable);
			});

	return currentSchedulingFuture;
}
```

如果采用EAGER方式的话，是先调用**allocateResourcesForAll**来分配资源，然后才是把所有的task部署到对应的slot上。

### 不同点

这里可以把**LAZY_FROM_SOURCES**理解为，一个一个operator逐个完成，比较适合批处理模式，这种模式使得每一种operator都能最大限度的利用集群资源。而**EAGER**模式比较适用于流式数据处理，因为task正常情况下不存在退出结束的行为。    

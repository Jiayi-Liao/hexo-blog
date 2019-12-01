title: Flink StateBackend - 概览
author: Liao Jiayi
tags:
  - Flink
articleId: flink-statebackend
categories:
  - Apache Flink
keywords:
  - Flink
date: 2019-12-01 16:46:00
---

此文讲述如何在 Flink 从 0 构建一个 State Backend。

# StateBackend 接口

```
public interface StateBackend extends java.io.Serializable {

	CompletedCheckpointStorageLocation resolveCheckpoint(String externalPointer) throws IOException;
	
	CheckpointStorage createCheckpointStorage(JobID jobId) throws IOException;
	
	<K> AbstractKeyedStateBackend<K> createKeyedStateBackend（...);
		
	OperatorStateBackend createOperatorStateBackend(...);
}
```

除去 `resolveCheckpoint` （根据 `externalPointer` 解析 Checkpoint 位置）之外，一个 `StateBackend` 需要具有如下能力：

* 初始化 State 相关的 CheckpointStorage
* 构建 Keyed StateBackend 和 Operator StateBackend

# 实现概览
Flink 目前实现提供 4 种 `StateBackend`：  

* DefaultOperatorStateBackend (Operator StateBackend)
* MemoryStateBackend (Keyed StateBackend)
* FsStateBackend (Keyed StateBackend)
* RocksDBStateBackend (Keyed StateBackend)

正在开发中的有：

* [DiskSpillingStateBackend](https://issues.apache.org/jira/browse/FLINK-12692)




## DefaultOperatorStateBackend




# MemoryStateBackend

# FsStateBackend

# RocksDBStateBackend

# 自定义 StateBackend






















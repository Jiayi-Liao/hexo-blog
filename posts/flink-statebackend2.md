title: Flink StateBackend - DefaultOperatorStateBackend
author: Liao Jiayi
tags:
  - Flink
articleId: flink-defaultOperatorStateBackend
categories:
  - Apache Flink
keywords:
  - Flink
date: 2019-12-02 16:46:00
---

由于目前已实现的 `StateBackend` 只对 `KeyedStateBackend` 进行了重写，所有的 Operator State 都会采用 `DefaultOperatorStateBackend` 进行 snapshot。

# 概览

`DefaultOperatorStateBackend` 状态主要分为两类：

* PartitionableListState
* BackendWritableBroadcastState

# 状态读写


# 状态快照


# 状态恢复
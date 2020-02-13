# Flink StateBackend (2) - OperatorStateBackend

> OperatorStateBackend 是 StateBackend 中最基础，也是相对比较简单的组件。

# 简介

OperatorStateBackend 中维护着 Operator 中不带 Key 的状态，常见的 State 有 ListState / UnionState / BroadcastState。

## ListState

ListState 我们可以用来存储 Kafka Offset，使用形式如下：

```
case class KafkaOffset(topicPartition: KafkaTopicPartition, offset: Long)

val descriptor = new ListStateDescriptor("kafka-offset", classOf[KafkaOffset])

override def initializeState(context: FunctionInitializationContext): Unit = {
	if (context.isRestored) {
  		context.getOperatorStateStore.getListState()
	}
}
```


## UnionState

## BroadcastState

# Operations

## Modify

## Recovery
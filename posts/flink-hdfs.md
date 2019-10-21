title: Flink 和 HDFS 的交互
author: Liao Jiayi
tags:
  - Flink
articleId: flink-hdfs
categories:
  - Apache Flink
keywords:
  - Flink
date: 2019-10-21 16:46:00
---

了解 Flink 和 HDFS 之间的交互有助于我们理清 HDFS 可能会给 Flink 带来的问题。


## Job 提交
在 client 提交 Job 的过程中，会将 HDFS 作为 client 和 AM 的文件传输中转站，具体被传输的文件有：

* flink jar: 即 flink 目录下的 conf 和 jar。
* ship files: 用户指定需要传输到集群中的文件。
* flink-conf: 提交过程中会在 configuration 中加入一些新的 kv 然后重新写入一个文件中，上传给 jm 和 tm 读取。
* user jar: 用户代码所在的 jar。
* jobGraph: 这个只有在 per-job 模式下才会将 jobGraph 序列化到磁盘，然后 jm 从 jobGraph 文件中提取 jobGraph 提交。

## Blob Service

Blob Service 主要是用来存储二进制的大对象，例如 jar、日志文件等。其实也就是序列化到 HDFS 上。具体在这些场景下会使用到 Blob Service：

* 使用 restful 形式上传的 job 所依赖的 jar 包，通过 blob service 持久化到 HDFS 上，然后在 Task 端重新获取这些 jar 生成 ClassLoader。
* Web UI 上展示日志，日志会先通过 Blob Service 写入 HDFS，再读出来。

## JobGraphStore

JobGraphStore 是为了 HA 用的，也就是在 JobManager 挂掉之后，可以从一个地方重新获取之前 JobManager 持有的 JobGraph 并重新提交。

* Per-job mode: 这种情况下不会有 JobGraphStore（其实也有，但是不会持久化），因为上面讲到了这种 per-job mode 其实是通过持久化 jobGraph 的方式来传递 jobGraph。
* Session mode: 这种情况下开启了 HA 会使用基于 zk 和 hdfs 的 JobGraphStore，简单来讲就是持久化到 HDFS 上，然后在 zk 中存一个路径（Handle），然后新的 JobManager 可以直接从这个 zk 路径恢复 JobGraph。

## Checkpoint

Flink 的 Checkpoint 和 Savepoint 的界限一直没有清晰地划开，所以会出现很多奇怪的地方。两种情况：

> 开启 Checkpoint

这种情况肯定是需要 HDFS 不用多说。

> 不开启 Checkpoint

在不开启 Checkpoint 的情况下，Flink 依然会初始化 CheckpointCoordinator，并且在 HDFS 上创建对应的 checkpoint 目录，直觉上讲，不开启 Checkpoint 这些 Checkpoint 相关的组件都不应该被初始化，但是为了支持命令行手动触发 savepoint 这些依然还是需要正常初始化。




***

**工作实在太忙，博客写的太糙，如果有不明白的地方可以邮件咨询。**   
**Email: buptliaojiayi@gmail.com**











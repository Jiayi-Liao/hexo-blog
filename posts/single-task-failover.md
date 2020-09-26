title: 解决实时推荐场景下数据断流问题-单点恢复功能介绍
author: Liao Jiayi
tags:
  - Apache Flink
articleId: single-task-failover
categories: Apache Flink
keywords:
  - 单点恢复
date: 2020-09-22 07:08:40
---

本文摘自我在字节跳动技术公众号上发布的文章，[字节跳动 Flink 单点恢复功能实践](https://mp.weixin.qq.com/s?src=11&timestamp=1601129515&ver=2608&signature=8Xpu5wKw1aCSBBNy1JbK2CtFc9XwHobZtsgm1AVdPbEoNctS2NJzVEfZoQnZj-VudQ82Ck5xFYi5A1jf0uzJJMUfMh9EraGKl4nOHR7eNyyn3D0QNV-WFORjHS8*S*7k&new=1)。

在字节跳动的实时推荐场景中，我们使用 Flink 将用户特征与用户行为进行实时拼接，拼接后的实例会更新后端推荐模型，对用户的实时推荐产生影响。拼接服务的时延和稳定性直接影响了线上产品对用户的推荐效果，而 Flink 中的拼接服务在 Flink 中是一个类似双流 Join 的实现，Job 中的任一 Task 或节点出现故障，都会导致整个 Job 发生 Failover，影响该产品内所有用户或文章的推荐效果。

针对这一痛点，我们提出单点恢复的方案，通过对 network 层的增强，使得在机器宕机或者 Task 失败的情况下，以故障 Task 的部分丢失为代价，达成以下目标：

* 作业不发生全局重启，只有故障 Task 发生 Failover
* 非故障 Task 不受影响，正常为下游提供拼接数据

# 解决思路

当初遇到这些问题的时候，我们提出的想法是说能不能在机器故障下线的时候，只让在这台机器上的 Tasks 进行 Failover，而这些 Tasks 的上下游 Tasks 能恰好感知到这些 Failed 的 Tasks，并作出对应的措施：

* 上游：将原本输出到 Failed Tasks 的数据直接丢弃，等待 Failover 完成后再开始发送数据。
* 下游：清空 Failed Tasks 产生的不完整数据，等待 Failover 完成后再重新建立连接并接受数据

根据这些想法我们思考得出几个比较关键点在于：

* 如何让上下游感知 Task Failed ?
* 如何清空下游不完整的数据 ?
* Failover 完成后如何与上下游重新建立连接 ?

# 现有设计

注：我们的实现基于 Flink-1.9，1.11 后的网络模型加入了 Unaligned Checkpoint 的特性，可能会有所变化。

我们先将 Flink 的上下游 Task 通信模型简单抽象一下：


![sgf1](http://www.liaojiayi.com/assets/single-task-failover-1.png)


上下游 Task 感知彼此状态的逻辑，分三种情况考虑：

* Task因为逻辑错误或OOM等原因Fail，Task自身会主动释放 network resources，给上游发送 channel close 信息，给下游发送 Exception。
* TaskManager 进程被 Yarn Kill，TCP 连接会被操作系统正常关闭，上游 Netty Server 和下游 Netty Client 可以感知到连接状态变化。
* 机器断电宕机，这个情况下操作系统不会正确关闭 TCP 连接，所以 Netty 的 Server 和 Client 可能互相感知不到，这个时候我们在 deploy 新的 Task 后会做一些强制更新的处理。

可以看到，在大部分情况下，Task 是可以直接感知到上下游 Task 的状态变化。了解了基础的通信模型之后，我们可以按照之前的解决思路继续深入一下，分别在上游发送端和下游接收端可以做什么样改进来实现单点恢复。

# 上游发送端的优化

我们再细化一下上游发送端的相关细节，


![sgf3](http://www.liaojiayi.com/assets/single-task-failover-3.png)


1. Netty Server 收到 Client 发送的 Partition Request 后，在对应的 Subpartition 注册读取数据的 SubpartitionView 和 Reader。
2. RecordWriter 发送数据到不同的 Subpartitions，每个 Subpartition 内部维护一个 buffer 队列，并将读取数据的 Reader 放入到 Readers Queue 中。（Task 线程）
3. Netty 线程读取 Readers Queue，取出对应的 Reader 并读取对应 Subpartition 中的 buffer 数据，发送给下游。（Netty 线程）

我们的期望是上游发送端在感知到下游 Task Fail 之后，直接将发送到对应 Task 的数据丢弃。那么我们的改动逻辑，在这个示意图中，就是 Subpartition 通过 Netty Server 收到下游 Task Fail 的消息后，将自己设置为 Unavailable，然后 RecordWriter 在选择发送到该 Subpartition 时判断是 Unavailable 则直接将数据丢弃。而当 Task Failover 完成后重新与上游建立连接后，再将该 Subpartition 置为 Available，则数据可以重新被消费。

由于 Flink 内部对 Subpartition 的逻辑做了很好的抽象，并且可以很容易的通过参数来切换 Subpartition 初始化的类型，我们在这里参考 PipelinedSubpartition 的实现，根据上述的逻辑，实现了我们自己的 Subpartition 和对应的 View。

# 下游接收端的优化

同样，我们来细化一下下游接收端的细节：

![sgf4](http://www.liaojiayi.com/assets/single-task-failover-4.png)



仔细来看，其实和上游的线程模型颇有类似之处：

1. InputGate 初始化所有的 Channel 并通过 Netty Client 和上游 Server 建立连接。
2. InputChannel 接收到数据后，缓存到 buffer 队列中并将自己的引用放入到 Channels Queue 里。（Netty 线程）
3. 和 4. InputGate 通过 InputProcessor 的调用，从 Queue 里拉取 Channel 并读取 Channel 中缓存的 buffer 数据，如果 buffer 不完整（比如只有半条 record），那么则会将不完整的 buffer 暂存到 InputProcessor 中。（Task 线程）

这里我们期望下游接收端感知到上游 Task Fail 之后，能将对应 InputChannel 的接收到的不完整的buffer直接清除。那么对应到图中的组件就是将 InputProcessor 中指定 Channel 的 buffer 清除。

我们在这里的改动逻辑是，当 Netty Client 感知到上游 Task Fail 的信息后传递给对应的 InputChannel，InputChannel 在 buffer 队列的末尾插入一个 Unavailable Event，等到 InputProcessor 读取到该 Channel 的 buffer 队列时，如果读取到 Unavailable Event，则清空当前维护的不完整的 buffer。

# JobManager 重启策略的优化

JobManager 重启策略可以参考社区已有的 RestartIndividualStrategy，比较重要的区别是，在 deploy 这个 Failed Task 后，我们需要通过 ExecutionGraph 中的拓扑信息，找到该 Task 的下游 Tasks，并通过 Rpc 调用让下游 Tasks 和这个新的上游 Task 重新建立连接。

这里需要特别提到一点，在字节跳动内部我们实现了预留 TaskManager 的功能，当 Task 出现 Failover 时，能够直接使用 TaskManager 的资源，大大节约了 Failover 过程数据丢失的损耗。

# 实现中的关键点

整体思路其实比较清晰，相信大家也比较容易理解，但我们在实现上也遇到一些比较复杂的地方，比如：

* JobManager 通过 Rpc 调用更新下游 Tasks 的 Channel 信息时，无法保证旧有 Channel 中的 Unavailable Event 已经被 InputProcessor 消费，所以旧 Channel 还不能被关闭。这里我们的解决办法是先将 Partition 信息缓存起来，等到 Channel 数据被全部消费后再关闭这个 Channel，根据缓存的 Partition 信息初始化新的 Channel。
* 网络层作为 Flink 内线程模型最复杂的一个模块，我们为了减少改动的复杂度和改动的风险，在设计上没有新增或修改 Netty 线程和 Task 线程之间通信的模型，而是借助于已有的线程模型来实现单点恢复的功能。但在实现过程中因为给 Subpartition 和 Channel 增加了类似 isAvailable 的状态位，所以在这些状态的修改上需要特别注意线程可见性的处理，避免多线程读取状态不一致的情况发生。

最后打一个小广告 ^_^，字节跳动流式计算引擎团队持续招人ing，除了我们在网络层的优化，在 SQL、调度、Checkpoint、批流一体等方向都针对我们的场景做了不同程度的创新和改进，欢迎一起来玩~

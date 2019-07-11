title: Database(1) - 谈谈HBase的Transaction
author: Liao Jiayi
date: 2019-04-02 01:42:56
tags:
  - Database
  - Transaction
  - HBase
articleId: hbase-tx
categories:
  - Database
keywords:
  - HBase
  - Transaction

---
起初是因为看了PingCAP的几篇博客，然后知道了所谓的NewSQL。后来发现自己对于OLTP中的一些技术点并不是特别了解，就决定从自己稍微熟悉一点的技术栈开始做一些探究。所以，这是数据库系列中的第一篇 :)。

## ACID
评价一个数据库的事务性往往会从ACID四个方面来考虑，我们先简单看看ACID具体代表着什么含义：

* A -> Atomicity: 原子性。一个事务往往会包括多个操作，那么这些操作只能同时成功或者同时失败。  
* C -> Consistency: 一致性。一致性保证了数据库一直处于一个有效状态，如果出现了非法事务，可以及时回滚，保持一致性。
* I -> Isolation: 隔离性。在实际业务中，容易出现读写同时发生的情况，这时候，读写应该如何隔离。
* D -> Durability: 持久化。事务成功后，不会因为数据库宕掉而丢失此事务。

***

## HBase + ACID

知道了ACID的概念之后，就很容易地去阐述HBase的事务性。

* Atomicity: 只在同一个Region下具有原子性，无法实现跨Region/Table。
* Consistency: 不存在回滚策略，也就是无法实现一致性。
* Isolation: 由于HBase采用LSM结构，更新数据通过Compaction来实现，所以一定程度上，不存在对已有数据同时读写的情况。
* Durability: 满足持久化的概念。

***

## If HBase + ACID

HBase性能高，适合OLAP查询/计算。传统数据库MySQL支持事务性，但是无法方便地支撑海量数据的存储和查询。如果HBase能够完全地支持ACID的话，并且稳定性有所保障的 情况下，相信有不少人会选择弃用RDBMS吧。那么我们可以看看，单纯以ACID来讲，HBase还需要做什么才能弥补完整事务性的空缺。  

#### Atomicity
如果要实现跨表、跨节点的事务保证，必须要想一个机制来保证，所有节点的事务同时成功或者同时失败。比较经典的是2PC（2-Phase-Commit）机制，这个我在之前[Flink的博客](http://www.liaojiayi.com/flink-exactly-once/)中提到过，将不同节点的提交分为两步骤，第一步为Pre-Commit，待所有节点完成Pre-Commit之后，再真正的触发事务。  
来实现这个流程，首先需要有一个Manager和所有节点保持通信，这样才能保证大家的commit流程处于一致的状态。当然，这个机制也不是万能的，如果在真正触发事务时gg了，那也没辙了。目前没有看到更好的算法或机制，也可能是我见识太少？

#### Consistency
重点是在不一致时实现回滚。这意味着在写之前，必须要先读取数据。其实在我看了一两篇数据库论文之后，发现大部分数据库都是这样做的...。于是一个写事务的时间线就变成了这样：

![HBase Consistency](http://www.liaojiayi.com/assets/hbase-tx1.png)


#### Isolation
#### Durability
至于这两部分，HBase目前倒也可以达到标准。




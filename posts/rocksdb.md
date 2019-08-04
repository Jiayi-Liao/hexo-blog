---
title: Database(2) - RocksDB
date: 2019-07-23 03:24:13
keywords: RocksDB
categories: Database
---

在轻量级数据库中，我们不得不提到 RocksDB。这是 Database 系列的第二篇，由于工作原因，距离第一篇已经比较遥远，RocksDB 在我的周围经常可以听到，比如作为 Flink 的状态存储介质，TiDB 基于 RocksDB 做了 Google Spanner 的分布式实现等。

## Quick View

RocksDB 在性能上的目标：

* 点查和范围查找都有不错的性能。
* 快速的随机读。
* 快速的更新性能。
* 能够通过调整参数来适应不同的硬件。

基本数据结构：

* memtable: 内存中的存储结构，新写入的数据在完成 WAL 后会插入 memtable。
* sstfile: 磁盘上的存储文件，memtable 中的数据会 flush 到磁盘上。
* logfile: 当 memtable 数据丢失时可以通过 logfile 恢复数据。

当新数据写入时，数据会先进入 logfile，然后同步写入到 memtable 中，等待一定条件触发后（如 memtable 达到容量限制），持久化到磁盘上。在不同的 sstfiles 之间，会定期出现 compaction 来减少 sstfile 文件的个数以及合并对同一 key 的操作。如果你了解 HBase 中的 Memstore, HFile 和 WAL 机制，那么这个机制对你来说应该很熟悉。他们都是利用了 LSM-Tree 的思想。

## Compaction

RocksDB 提供了三种 Compaction：

* Level Style Compaction(default): 将不同的 sstfile 分级，越老的文件层级越高，定期将小文件向上一个层级的文件合并。这样，会有更好的查询性能，减少了读放大，提供了多线程的实现。
* Universal Style Compaction: 合并同一大小的文件，减少了写放大。
* FIFO Style Compaction: 这种 Compaction 实现的比较粗糙，会出现 evict 数据的情况。

Compaction 部分对于有实时场景的数据存储来说，并不是新鲜事儿。不管是在 Cassandra 还是 HBase 我们都能看到相似的理论。

## Index Sstfile

当 RocksDB 使用默认的 Level Style Compaction 时，由于是多层有序数组的结构，索引 sstfile 文件的过程有些巧妙。假设 RocksDB 需要在 Level=N 的 sstfile 中做一个 key 的点查，如何快速找到对应的 sstfile 文件？

> Fractional Cascading

这里使用了 Fractional Cascading 算法。本质上它还是使用了二分查找的方法，但是在一层一层往下做二分查找时缩小了二分查找的范围。

举例说明：

```
L1 = [0 - 0], [1 - 5], [6 - 10], [11 - 15]
L2 = [0 - 1], [2 - 3], [4 - 12], [13 - 18]
L3 = [0 - 7], [8 - 14], [15 - 19], [20 - 30]
```  

如图所示，每个 sstfile 都有其自己的范围，我们不太可能直接在每个 Level 去进行二分查找，这样效率太低。 Fractional Cascading 通过在每一层的每个 sstfile 在下一层的 index 来不断减少二分查找的范围。加上 index 后，数据变成这样：

```
L1 = [[0 - 0], 0], [[1 - 5], 2], [[6 - 10], 2], [[11 - 15], 3]
L2 = [[0 - 1], 0], [[2 - 3], 0], [[4 - 12], 1], [[13 - 18], 3]
L3 = [[0 - 7], 0], [[8 - 14], 0], [[15 - 19], 0], [[20 - 30], 0]
```

假设我们要对 key='8' 的数据做点查。从 L1 开始，我们找到 [6 - 10] 的 sstfile 是我们在 L1 需要查找的 sstfile，[6 - 10] 对应在 L2 的 index=2，所以我们再 L2 找文件时，可以直接选择在 index ~ [0, 2] 的区间内做二分查找，而不是对整个 L2 数据集做查找。

## Transaction

在 RocksDB 中，它将事务分为3个阶段，依次为： Put，Prepare 和 Commit。如果每次等待事务操作全部 Prepare 后，在 Commit 再持久化到磁盘，这样如果多个大型事务同时出现，势必会降低吞吐速率。

对于事务，有两个改进的方案：

* WritePrepared: 在 Prepare 阶段就持久化到磁盘。
* WriteUnprepared: 在 Put 阶段就持久化到磁盘。

> WritePrepared

RocksDB 在每条记录上加了一个 ```prepare_seq```，在事务被提交后，在 CommitCache 中会存储一个 ```prepare_seq``` 和 ```commit_seq``` 之间的 mapping。CommitCache 会根据最大大小来 evict 数据，```max_evict_seq``` 是用来表示最近 evict 的 ```prepare_seq```。 

在查询中，找到对应记录后，你可以找到对应的 ```prepare_seq```，如果

* ```prepare_seq``` > ```max_evict_seq``` 并且不在 CommitCache 中：表示记录还在 prepare 阶段，没有 commit，不可读取。
* ```prepare_seq``` <= ```max_evict_seq``` 并且 ```prepare_seq``` 不在 CommitCache 中：记录已经被持久化，直接读取即可。
* ```prepare_seq``` in CommitCache or ```prepare_seq``` < ```max_evict_seq```: 记录已经被 committed，可以直接读取。

当然，这样的操作存在一些特殊情况，如果一个事务持续时间过长（Prepare 到 Commit），```max_evict_seq``` 超过了事务中记录的 ```prepare_seq```，那么```prepare_seq```会被放入```delayed_prepared_```的集合里，RocksDB 每次查询会检查这个集合来判断记录是否 commit。


> WriteUnprepared

这一部分，单纯的从文档上看，并没有很好的理解其中的原理，并且这个功能还没有在生产上使用...

在阅读完 RocksDB 相关的文档之后，我相信没有太多的开发者愿意依赖 RocksDB 的事务，首先这个事务的算法机制本身有些复杂，难以理解，一旦出现问题，线上排查问题的过程必定会相当复杂；其次 RocksDB 对于这种事务机制，并不能接受一些极端情况，如长事务和阅读过于久远的历史 snapshot 等。虽然它对 Put -> Prepare -> Commit 的流程做了很大的优化，提升了吞吐，但是这样的确对使用 RocksDB 的业务，有很大的限制。


## Summary

这里是我 Database 系列的第2篇笔记，写 RocksDB 的原因是不少企业已经有了很多成功的案例，并且在我司也曾经有过对 RocksDB 的选型考虑（不过还是因为吞吐并没有我们想象的那么好）。文中的信息大部分是通过 [RocksDB Wiki](https://github.com/facebook/rocksdb/wiki/Rocksdb-Architecture-Guide) 得到，从架构设计上并没有太多惊艳的地方，事务处理也有些不尽人意。但是在使用上看，RocksDB 确实足够轻量，不需要额外的部署，一个 jar 包就可以拥有一个功能完备的数据库，api 的使用体验也不错，并且能灵活对接 HDFS。  

关于 RocksDB 写放大读放大的问题，学术界也提出过相关的理论，我也简单研读过，的确是一个不一样的视角，但是不知是否有成功的实践呢？

* [WiscKey: Separating Keys from Values
in SSD-conscious Storage](https://www.usenix.org/system/files/conference/fast16/fast16-papers-lu.pdf)
* [HashKV: Enabling Efficient Updates in KV Storage via Hashing](https://www.usenix.org/system/files/conference/atc18/atc18-chan.pdf)
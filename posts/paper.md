---
title: Paper Notebook
date: 2018-05-08 22:29:10
tags: Data
keywords: data
categories: Notes
---
记录一下自己读的Paper。

* [Apache Calcite: A Foundational Framework for Optimized Query Processing Over Heterogeneous Data Sources](https://arxiv.org/abs/1802.10233)：资料比较少，写了一篇[博客](http://www.liaojiayi.com/calcite-paper/)。

***

* [taking-advantage-of-a-disaggregated-storage-and-compute-architecture](https://databricks.com/session/taking-advantage-of-a-disaggregated-storage-and-compute-architecture): Facebook关于存储和计算分离的实践，将HDFS/S3/LocalFs抽象成了GenericFile，统一放在存储端，通过配置不同的机型来实现成本的最优化，改进了Spark中对于存储分离不友好的一些地方，比如External Service需要拉两次数据等问题。

***

* [WiscKey: Separating Keys from Values
in SSD-conscious Storage](https://www.usenix.org/system/files/conference/fast16/fast16-papers-lu.pdf): 基于SSD和小key大value的事实：

	* LSM file内部不再排序，更好的利用SSD的随机读的性能，减少了排序的代价。  
	* 引入Vlog的结构，减少写放大，定时检查vlog中数据的有效性。

***

* [HashKV: Enabling Efficient Updates in KV Storage via Hashing](https://www.usenix.org/system/files/conference/atc18/atc18-chan.pdf): 基于 WiscKey 的结构做了一些优化：

	* 通过对数据进行分区，将数据分为了热区和冷区，这样因为热区有频繁的update，可以及时的触发热区的gc。
	* 小value的数据可以直接写入到LSM file中。

	
***

* [SOS: Optimizing Shuffle I/O](https://vimeo.com/274418771): 基于大规模shuffle做了一些优化，主要是针对map多，数据小而碎，在 map 和 reduce 的中间加入了一些组件和 failover 的一些操作。

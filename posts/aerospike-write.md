title: Aerospike(2) - 写机制
author: Liao Jiayi
tags:
  - Aerospike
articleId: aerospike2
categories: Aerospike
keywords:
  - Aerospike
description: 本文描述了Aerospike的写机制以及其中存在的问题
date: 2018-06-03 15:21:29
---
最近使用Aerospike遇到了不少的问题，在不断地看日志，读源码，阅读[Aerospike社区](https://discuss.aerospike.com/t/device-overload-when-map-size-is-too-big/5206)的各种文章之后，也算是对Aerospike有了一些更深的了解。

#### Storage Layout
![Storage Layout][1]
SSD namespace的写流程基本如上图所示，现在，让我们假设有一个写操作***MapOperation.PUT***正在进行，它的路径将会是这样：  
1. 根据**MapOperation.PUT**的各种参数和策略，来校验Metadata，例如namespace、set是否存在，然后写入到最小写单元block5中。  
2. block的默认大小为1024bytes，只有当block为full或者没有数据继续写入时才会触发block添加到写队列Write Queue。  
3. 独立的worker线程会将Write Queue中的数据持久化到SSD中。  
4. 数据写入后，如果memory或者storage存储到达了hwm(high-watermark-memory)，将会触发evict操作，即为了清理空间，把一些未来将要过期的数据提前过期，具体原理在[ttl及eviction机制](https://discuss.aerospike.com/t/records-ttl-and-evictions-for-aerospike-server-version-prior-to-3-8/737)。  
5. 在block中的部分数据被删除后，block的usage level将会从100%下降到低于defrag-lwm-pct（默认是50%），此时会触发defrag，将会有block放入write queue中被重写。  

***
#### Potential Risk
在这样的写机制下，不难发现在一些细节上，会有潜在的问题。具体的调优方式可以参照[Aerospike参数列表](https://www.aerospike.com/docs/reference/configuration#write-block-size)。
* Record被写入block时，会出现record size >  write-block-size的情况，此时异常退出，可以通过write-block-size在namespace级别做调整，write-block-size过大，容易出现usage-level过低频繁defrag，过小会增加和SSD的flush次数。
* Block在写入到write-queue中时，可能会出现queue大小超过最大限制的情况，异常为 "write fail: queue too deep: exceeds max %i"，queue长度可以通过max-write-cache调节， queue length = max-write-cache / write-block-size。
* 为了能够高效读取数据，Record中的数据都是必须是在连续的内存空间中被写入的，这意味着UPDATE/DELETE/PUT等操作，都要将整条Record重新写入，所以不建议存储需要频繁更新的big record，否则对性能会产生很大的影响，且容易触发queue too deep的限制。
* 频繁地UPDATE/DELETE/PUT操作会导致block usage level下降，从而产生defrag，而defrag会影响正常数据写入的效率，可以通过降低defrag的low-water-mark来减少defrag的次数，参数为defrag-lwm-pct。
* 刚刚提到evict操作会将数据提前过期，这个可以通过high-water-memory-pct和high-water-dist-pct来调整evict的策略。

***
#### Log Inspection
Log是最容易看出问题的方式，但是as的Log有些表达显得略有晦涩，采取了不少缩写的表达，目前来看，log level调整为 info 已经能够帮助定位大部分问题，这里挑取一些关键信息做一下记录。
```
{test} /dev/xvdc: used-bytes 3695468032 free-wblocks 34690 write-q 0 write (445674,0.0) defrag-q 0 defrag-read (39134,0.0) defrag-write (5427,0.0)
```
这是as定时output出的某个节点的基本情况，针对namespace test，在/dev/xvdc的SSD上，已经使用了3695468032 bytes的磁盘空间，当前可以使用的free-wblocks有34690个，write-queue长度为0，写入了445674个(包括defrag)blocks，当前写入速率为0.0，defrag-queue长度为0，加入到defrag队列中的有 39134个blocks，当前速率为0.0，真正产生defrag的block数为5427，当前速率为0.0。
```
{test} breached eviction hwm (memory), memory sz:1792174976 (1792174976 + 0) hwm:1288490188, disk sz:3695922432 hwm:20128464896
no records below eviction void-time 266233878 - threshold bucket 4678, width 113 sec, count 298 > target 11 (0.5 pct)
```
这条log和[as的evict机制](https://discuss.aerospike.com/t/records-ttl-and-evictions-for-aerospike-server-version-prior-to-3-8/737)有关，这里是表示当前size已经超过了hwm，触发了eviction，但是由于count 298 > target 11（bucket是最小的evict单位，此时找到了最大可以evict的个数为11个，但是最近的bucket中有298个，所以无法触发）。

















![加一Blog][2]

  [2]: http://www.liaojiayi.com/assets/jiayi_end_qr.png
















[1]: http://liaojiayi.com/assets/aerospike0.png

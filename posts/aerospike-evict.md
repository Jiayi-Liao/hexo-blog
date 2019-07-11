title: Aerospike(3) - Evict机制
author: Liao Jiayi
date: 2019-03-03 16:09:21
tags:
  - Aerospike
articleId: aerospike-evict
categories: Aerospike
keywords:
  - Aerospike
  - aerospike
  - evict
---

在实时的场景中，我们往往会对Aerospike/Redis等设置evict机制，来防止流量暴增带来的存储系统崩溃。


### 原理
![aerospike-evict机制][1]  

原理如上图所示，在Aerospike中，有TTL的数据根据TTL的大小被等分在这个横轴上，每个bucket的大小由最大的TTL和设置的**evict-hist-buckets**来决定。其中：

> bucket_width = max_ttl / evict-hist-buckets

**evict-hist-buckets**可以基于namespace去设置，并且可以动态修改，无需启动集群。我们会设置**high-water-memory-pct**或者**high-water-disk-pct**来决定开始evict数据的时机，当满足条件后，剩下就是等nsup线程启动，从柱状图中的第一个bucket开始驱逐。

### 限制
当然，实际情况不会永远这么简单。Evict机制本身就是获取与丢弃之间的博弈的产物，所以也许根本就找不到一个跟实际业务情况完全匹配的现成方案。Aerospike的evict机制并不完美，有时候存储超过了你所设置的HWM，但是并没有数据被驱逐。Aerospike3.8之后的evict机制中有两个特点：

* **evict-hist-buckets**可以动态配置，也就是用户可以自定义柱状图的粒度和evict数据的粒度。
* Evict的单位是bucket，不能将bucket中的部分数据弹出。

下面引入evict机制中的另一个参数： **evict-tenths-pct**。

这个参数决定了每次evict的数量。举个极端例子，假设柱状图中的元素不够均匀，全部被分配到了第1个bucket上，那么不可能将第1个bucket的数据全部弹出吧？所以这就是**evict-tenths-pct**的作用。类似于这种情况，可以动态调整**evict-hist-buckets**，降低柱状图中的粒度，使得第1个bucket中的数量少于**evict-tenths-pct**所限制的数量，从而达到evict的目的。不过同时注意，bucket的对象也有一定的内存占用，具体可以在下面链接中查看。  

所以说，这种Evict的机制也带来了一些风险，虽然比Redis的evict策略控制的更加精细化，但是在一些极端场景中，很容易出现需要手工调整参数，或者根本就无法evict的情况（几天前因为业务流量上涨刚手工调整过）。  

### 调优
Aerospike的evict机制主要依赖于上述两个参数，如果线上出现故障，可以根据日志来调整自己的策略。在此截取部分官方的Log来加以阐释：

> Apr 07 2016 13:42:17 GMT: WARNING (nsup): (thr_nsup.c:1068)
{test} no records below eviction void-time 200346037 - insufficient histogram resolution?

void-time是由**evict-tenths-pct**决定的threshold bucket的时间戳，这个时间戳是从2010年1月1日算起，可以理解为是Aerospike自己的时间戳。可以看出此时的threshold bucket是第1个bucket，和之前的解决方案类似，调整**evict-hist-buckets**即可。

> Jan 30 2017 02:36:21 GMT: WARNING (nsup): (thr_nsup.c:1043) {test} no records below eviction void-time 222541923 - threshold bucket 361, width 259 sec, count 686375 > target 530312 (0.5 pct)

此时threshold bucket是361，每个bucket时间宽度为259秒，但此时在第一个Bucket中的元素为686375，超过了**evict-tenths-pct**设置的0.5pct的数量，所以无法evict。




### 参考资料
* [https://discuss.aerospike.com/t/records-ttl-and-evictions-for-aerospike-server-version-prior-to-3-8/737](https://discuss.aerospike.com/t/records-ttl-and-evictions-for-aerospike-server-version-prior-to-3-8/737)
* [https://discuss.aerospike.com/t/eviction-mechanisms-in-aerospike/2854](https://discuss.aerospike.com/t/eviction-mechanisms-in-aerospike/2854)





  [1]: http://www.liaojiayi.com/assets/as-evict.png

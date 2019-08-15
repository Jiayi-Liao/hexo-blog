title: 'java.lang.OutOfMemoryError: Map failed'
author: Liao Jiayi
date: 2018-10-11 09:19:07
tags:
  - JVM
articleId: mapfailed
categories:
  - JVM
keywords:
  - Map Failed
  - java
  - OOM
description: 本文记录了一次Map Failed导致的一次JVM OOM故障，给出了原因以及解决办法。
---

最近遇到这个Exception，发现不少开源框架在实现快速读写文件时，采用的都是FileChannel的map方法，示例如下：
```
at sun.nio.ch.FileChannelImpl.map0(Native Method) ~[?:1.8.0_40]
at sun.nio.ch.FileChannelImpl.map(FileChannelImpl.java:904) ~[?:1.8.0_40]
```
这个方法的作用是将文件映射到堆外内存中，然后通过读写内存来实现对文件的快速读写。从[知乎](https://zhuanlan.zhihu.com/p/27698585)摘了一张图。
![mmap display][1]
***
#### 问题 & 解决
目前来看，我在使用MapDB和Phoenix时都曾经出现过这个Exception，MapDB直接将DB文件映射到堆外内存，来达到高效的读写；Phoenix在结果集过大时，需要落地成临时文件，而这个临时文件是采用mmap来操作的。  

**Map Failed** 出现的原因有很多:


1. 对于32-bit JVM，由于地址空间是32 bit，2^32=4GB，所以我们能映射的文件大小只有4GB，但实际上因为其他对象同样需要占用地址空间，所以正常情况下，只能映射1GB左右。   
2. Java程序有默认的maxDirectMemory，即JVM可使用的最大堆外内存，稍不注意，就有可能超过并且抛出异常（如在Phoenix数据查询中结果集过大）。
3. mmap句柄超过了系统默认最大值。系统默认最大值可使用```cat /proc/sys/vm/max_map_count```查看，进程使用句柄数可使用```cat /proc/$PID/maps | wc -l```查看。每一块申请的ByteBuffer都对应一个mmap句柄，也就是说，如果生成了大量的碎ByteBuffer，那么句柄数也会急剧增长。而这些句柄的回收是伴随着ByteBuffer回收的，堆外内存的GC需要显示调用System.gc来进行。  


 
解决方式：

1. 若为32-bit JVM，可升级到64-bit，获得更大的地址空间。
2. 若为64-bit JVM，当超出堆外内存不多且使用总内存小于32GB时，使用-XX:useCompressedOops来压缩对象的空间大小。
3. 调整-XX:maxDirectMemorySize来获得更多的堆外内存。
4. 调整/proc/sys/vm/max_map_count。















  [1]: http://www.liaojiayi.com/assets/mmap1.jpg

---
title: Paper Notebook
date: 2018-05-08 22:29:10
tags: Data
keywords: data
categories: Notes
---


Notes for my paper reading.


* [Apache Calcite: A Foundational Framework for Optimized Query Processing Over Heterogeneous Data Sources](https://arxiv.org/abs/1802.10233)：I can't find much information about Calcite, so I've written a [blog](http://www.liaojiayi.com/calcite-paper/) about it.

***

* [taking-advantage-of-a-disaggregated-storage-and-compute-architecture](https://databricks.com/session/taking-advantage-of-a-disaggregated-storage-and-compute-architecture): Facebook's application on disaggregation of storage and compute, introduce by Brian Cho, Software Engineer, Facebook. By abstracting the GenericFile layer instead of the HDFS layer, Spark can operate on different files sytems like S3、HDFS、LocalFs. And they optimize the external file service to reduce the network I/O.

***

* [WiscKey: Separating Keys from Values
in SSD-conscious Storage](https://www.usenix.org/system/files/conference/fast16/fast16-papers-lu.pdf): Two points base on SSD and Key-Value pair(small size key, big size value):

	* LSM file without sorting: based on the efficiency of random read on SSD, cost on sorting is more.
	* Introduce Vlog structure to reduce the writing amplification and periodically check the availability of the data in Vlog.

***

* [HashKV: Enabling Efficient Updates in KV Storage via Hashing](https://www.usenix.org/system/files/conference/atc18/atc18-chan.pdf): Based on WiscKey, but with some improvements.

	* Seperating hot data and cold data by partitioning data and find the hottest/coldest partition(to decide the frequency of gc).
	* KV pair with small value will be directly stored in LSM file.

***

* [SOS: Optimizing Shuffle I/O](https://vimeo.com/274418771): Optimization on large-scale shuffle scenarios. 

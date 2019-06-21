---
title: Paper Notebook
date: 2018-05-08 22:29:10
tags: Data
keywords: data
description: Paper Notebook
categories: Big Data Computation Engine
---
记录一下自己读的Paper。

* [Apache Calcite: A Foundational Framework for Optimized Query Processing Over Heterogeneous Data Sources](https://arxiv.org/abs/1802.10233)：资料比较少，写了一篇[博客](http://www.liaojiayi.com/calcite-paper/)。
* [taking-advantage-of-a-disaggregated-storage-and-compute-architecture](https://databricks.com/session/taking-advantage-of-a-disaggregated-storage-and-compute-architecture): Facebook关于存储和计算分离的实践，将HDFS/S3/LocalFs抽象成了GenericFile，统一放在存储端，通过配置不同的机型来实现成本的最优化，改进了Spark中对于存储分离不友好的一些地方，比如External Service需要拉两次数据等问题。

---
title: Flink CEP
date: 2019-08-04 23:23:13
keywords: Flink
categories: Apache Flink CEP
---

关于 Flink CEP 的文章，我在[之前](http://www.liaojiayi.com/categories/Apache-Flink-CEP/)分成多个部分讲解过，后来发现有些表述和图例还是有些过于粗糙，正好最近也要在社区线上分享 CEP 源码的课程，那么我顺便就从源码的角度，把我对 CEP 的一些理解写在这里。


## 概要

随着数据分析精细化程度的提升，在企业级应用上，对事件的分析不再仅仅局限于普通的离线计算或者是简单的数字统计，而是转向更实时、更精准、更复杂的数据分析。复杂事件处理的复杂在于事件之间具有关联性，且这种关联在时间上是多种多样的。

我在学习 Flink CEP 模块时，将这个模块内容分为了 3 个部分：

* 规则解析
* 规则匹配
* 数据提取

接下来我们从这 3 个部分详细看看 CEP 模块是怎么工作的。

## 规则解析

Apache Flink 在实现 CEP 时借鉴了 [Efficient Pattern Matching over Event Streams](https://people.cs.umass.edu/~yanlei/publications/sase-sigmod08.pdf) 中 NFA 的模型，所谓的 NFA(Non-Determined Finite Automation)，即不确定的有限状态机，不确定指的是每个状态的下一状态是不确定的。





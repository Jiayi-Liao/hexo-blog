---
title: Flink CEP
date: 2019-08-04 23:23:13
keywords: Flink
categories: Apache Flink CEP
---

关于 Flink CEP 的文章，我在[之前的博客](http://www.liaojiayi.com/categories/Apache-Flink-CEP/)分成多个部分讲解过，后来发现有些表述和图例还是有些过于粗糙，正好最近也要在社区线上分享 CEP 源码的课程，那么我顺便就从源码的角度，把我对 CEP 的一些理解写在这里。


## OnBoarding

随着数据分析精细化程度的提升，在企业级应用上，对事件的分析不再仅仅局限于普通的离线计算或者是简单的数字统计，而是转向更实时、更精准、更复杂的数据分析。复杂事件处理的复杂在于事件之间具有关联性，且这种关联在时间上是多种多样的。

我们可以先从 CEPITCase.java 中找一个 test case 来看看，我这里选取了 testSimplePatternCEP() ，做了一些简化：

```
Pattern<Event> pattern = Pattern.<Event>begin("start").where(new SimpleCondition<Event>() {

	@Override
	public boolean filter(Event value) throws Exception {
		return value.getName().equals("start");
	}
})
.followedByAny("middle").where(
		new SimpleCondition<Event>() {

			@Override
			public boolean filter(Event value) throws Exception {
				return value.getName().equals("middle");
			}
		}
	)
.followedByAny("end").where(new SimpleCondition<Event>() {

	@Override
	public boolean filter(Event value) throws Exception {
		return value.getName().equals("end");
	}
});

DataStream<String> result = CEP.pattern(input, pattern).flatSelect((p, o) -> {
	StringBuilder builder = new StringBuilder();

	builder.append(p.get("start").get(0).getId()).append(",")
		.append(p.get("middle").get(0).getId()).append(",")
		.append(p.get("end").get(0).getId());

	o.collect(builder.toString());
}, Types.STRING);
```

观察这个 Pattern，仅从字面意思上理解，我们可以大致得出这个 Pattern 的意思是需要依次找到 name 等于 start、middle、end 的组合。那么，我们先不看 Flink 是如何实现的，我们先把这个事件之间的关系给画出来。









我们可以看到首先需要定义一个 Pattern，然后通过 ```CEP.pattern(input, pattern)``` 将 DataStream 和 Pattern 结合到一起，然后再通过 flatSelect 函数将匹配后的结果输出。  

通俗一点，可以理解为，CEP 等于数据和规则的匹配，针对这一理解，我们可以提出三个问题：

* 匹配规则 Pattern 是什么？它会被如何解析？
* 如何实现数据和规则的匹配？
* 数据匹配后，如何输出？

所以我之前在学习 Flink CEP 模块时，也对应地将这个模块内容分为了 3 个部分：

* 规则解析
* 规则匹配
* 数据提取

接下来我们从这 3 个部分详细看看 CEP 模块是怎么工作的。

## 规则解析

先提一下 flink-cep 模块中的理论支持。Apache Flink 在实现 CEP 时借鉴了 [Efficient Pattern Matching over Event Streams](https://people.cs.umass.edu/~yanlei/publications/sase-sigmod08.pdf) 中 NFA 的模型，所谓的 NFA(Non-Determined Finite Automation)，即不确定的有限状态机，不确定指的是每个状态的下一状态是不确定的。  





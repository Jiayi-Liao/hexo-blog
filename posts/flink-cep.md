---
title: Flink CEP
date: 2019-08-04 23:23:13
keywords: Flink
categories: Apache Flink CEP
---

关于我之前写的 CEP 博客，可以点击[这里](http://www.liaojiayi.com/categories/Apache-Flink-CEP/)。   

由于之前写的相对来说比较粗糙一些，正好最近也要在线上分享 CEP 源码的课程，那么我顺便就从源码的角度，把我对 CEP 的一些理解写在这里。


## OnBoarding

随着数据分析精细化程度的提升，在企业级应用上，对事件的分析不再仅仅局限于普通的离线计算或者是简单的数字统计，而是转向更实时、更精准、更复杂的数据分析。复杂事件处理的复杂在于事件之间具有关联性，且这种关联在时间上是多种多样的。

我们可以先从 CEPITCase.java 中找一个 test case 来看看，我这里选取了 testSimplePatternCEP() ，做了一些简化：

```
@Test
public void testSimplePatternCEP() throws Exception {
	StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

	DataStream<Event> input = env.fromElements(
		new Event(1, "barfoo", 1.0),
		new Event(2, "start", 2.0),
		new Event(3, "foobar", 3.0),
		new SubEvent(4, "foo", 4.0, 1.0),
		new Event(5, "middle", 5.0),
		new SubEvent(6, "middle", 6.0, 2.0),
		new SubEvent(7, "bar", 3.0, 3.0),
		new Event(42, "42", 42.0),
		new Event(8, "end", 1.0)
	);

	Pattern<Event, ?> pattern = Pattern.<Event>begin("start").where(new SimpleCondition<Event>() {

		@Override
		public boolean filter(Event value) throws Exception {
			return value.getName().equals("start");
		}
	}).followedBy("middle").subtype(SubEvent.class).where(
			new SimpleCondition<SubEvent>() {

				@Override
				public boolean filter(SubEvent value) throws Exception {
					return value.getName().equals("middle");
				}
			}
		)
	.followedBy("end").where(new SimpleCondition<Event>() {

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

	List<String> resultList = new ArrayList<>();

	DataStreamUtils.collect(result).forEachRemaining(resultList::add);

	assertEquals(Arrays.asList("2,6,8"), resultList);
}
```

观察这个 Pattern，仅从字面意思上不难理解，我们可以大致得出这个 Pattern 的意思是需要依次找到 name 等于 start、middle、end 的组合。了解了 CEP 的简单用法之后，我们尝试一步步拆解 CEP 的相关内容。




## 规则解析

接着上一个例子，我们先不看 CEP 本身在 Flink 内部如何实现，根据这个特定的 Pattern，我们可以很容易地画出不同事件之间的关系。可以想到，数据在这个 Pattern 中存在 4 种状态，分别是：

* 还未满足 start 条件
* 已满足 start 条件，还未满足 middle 条件
* 已满足 start、middle 条件，还未满足 end 条件
* 已满足 start、middle、end 条件

我们对这 4 种状态进行命名，分别命名为： start、middle、end、Final State，这四种状态之间关系如下图所示。

![cep-rule1](http://www.liaojiayi.com/assets/flink-cep-slide.png)

看到这里，对 CEP 规则的理解是不是更加清晰了一些？在这里我们引出 flink-cep 模块中的理论支持，即 [Efficient Pattern Matching over Event Streams](https://people.cs.umass.edu/~yanlei/publications/sase-sigmod08.pdf) 中的 NFA 模型（Non-Determined Finite Automation)，即不确定的有限状态机，不确定指的是每个状态对应的下一状态是不确定的。Flink 基于论文中的理论实现了大部分核心内容，剩下的如多规则匹配等，还没有实现。下面，我们从源码层面看看 Flink 内部是如何阐释 NFA 的。

![cep-nfa-uml](http://www.liaojiayi.com/assets/flink-nfa-uml.png)

可以看到，Flink 中使用 NFA.class 来表示 NFA 模型，在NFA中使用了 State.class 来表示 start/middle/end 等状态，在 State 中使用了 StateTransition.class 来表示不同 State 之间的关系。结合上面的状态图看，我们发现 StateTransition 其实就是图中的边(Edge)，sourceState 和 targetState 表示起始状态和转换后的状态，condition 表示完成这个转换的条件。StateTransition 在转换时会有三种操作：

```
public enum StateTransitionAction {
	TAKE, // 获取当前满足条件的事件
	IGNORE, // 忽略当前满足条件的事件
	PROCEED // 自然转换
}
```

PROCEED 这个可能不太好理解，我待会儿会举一个 optional 的例子来解释一下。

看到这里，我们对 NFA 以及在 Flink 内部如何表示 NFA 已经大致有了基本的了解。从 State 的 UML 图中可以看到 State.class 本身已经包含了 StateTransition，所以我们先看看这个包含转换关系的 State 是如何构建的。源码里对很多规则做了 If Else 的特殊情况处理，我们在这儿先针对 Onboarding 中的代码示例看看是如何构建 State 的。

首先很容易可以看出，在代码示例中，Pattern 这个对象是一层一层嵌套的，最外层的 Pattern 对应的是最后一个状态，所以一层层拆解过程中，我们构建 NFA 的顺序是从后往前的。

```
/**
 * Creates all the states between Start and Final state.
 *
 * @param sinkState the state that last state should point to (always the Final state)
 * @return the next state after Start in the resulting graph
 */
private State<T> createMiddleStates(final State<T> sinkState) {
	State<T> lastSink = sinkState;
	while (currentPattern.getPrevious() != null) {

		if (currentPattern.getQuantifier().getConsumingStrategy() == Quantifier.ConsumingStrategy.NOT_FOLLOW) {
			//skip notFollow patterns, they are converted into edge conditions
		} else if (currentPattern.getQuantifier().getConsumingStrategy() == Quantifier.ConsumingStrategy.NOT_NEXT) {
			省略 ................
		} else {
			lastSink = convertPattern(lastSink);
		}

		// we traverse the pattern graph backwards
		followingPattern = currentPattern;
		currentPattern = currentPattern.getPrevious();

		省略 ...........
	}
	return lastSink;
}

```

果不其然，这里采用递归的方式将 Pattern 一层层拆开，然后调用 convertPattern 函数来解析 Pattern（先忽略 NOT\_FOLLOW 和 NOT\_NEXT 的特殊情况）。在 convertPattern 中会调用如下函数：

```
private State<T> createSingletonState(final State<T> sinkState,
			final State<T> proceedState,
			final IterativeCondition<T> takeCondition,
			final IterativeCondition<T> ignoreCondition,
			final boolean isOptional)
```

在这里，先根据 currentPattern 的信息（如 where 条件、ConsumingStrategy 等），组成了下一步可能出现的状态和对应的 Condition，然后调用 createSingletonState 生成新的 State。所以，代码示例对应的 NFA 示意图如下：

![flink-nfa-1](http://www.liaojiayi.com/assets/flink-nfa-1.png)

接下来我们可以描述一些复杂的情况，比如 optional 和 times 的场景。

// TODO


## 规则匹配

// TODO



## 数据输出

// TODO

## 使用 CEP 需要注意的一些地方

// TODO
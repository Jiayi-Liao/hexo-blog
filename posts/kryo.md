title: Kryo (Class cannot be created (missing no-arg constructor))
author: Liao Jiayi
tags:
  - kryo
articleId: bitmap
categories:
  - 未分类技术文章
keywords:
  - kryo
date: 2018-07-06 16:46:00
---


Kryo 可以通过各种方式序列化没有继承 Serializable 的 Java 类，但是当反序列化有些对象时，如不支持无参构造函数的对象，会出现这样的错误：


```
com.esotericsoftware.kryo.KryoException: Class cannot be created (missing no-arg constructor): org.apache.flink.cep.pattern.Pattern

    at com.esotericsoftware.kryo.Kryo$DefaultInstantiatorStrategy.newInstantiatorOf(Kryo.java:1228)
    at com.esotericsoftware.kryo.Kryo.newInstantiator(Kryo.java:1049)
    at com.esotericsoftware.kryo.Kryo.newInstance(Kryo.java:1058)
    at com.esotericsoftware.kryo.serializers.FieldSerializer.create(FieldSerializer.java:547)
    at com.esotericsoftware.kryo.serializers.FieldSerializer.read(FieldSerializer.java:523)
    at com.esotericsoftware.kryo.Kryo.readObject(Kryo.java:657)

```

这个时候，可以在 Kryo 中使用构造函数策略 org.objenesis.strategy.StdInstantiatorStrategy 解决。
---
title: Rpc In Flink
date: 2019-09-09 16:23:13
keywords: Flink
categories: Apache Flink CEP
---

Apache Flink 在 Dispatcher、JobMaster、ResourceManager、TaskExecutor 几大组件之间采用 akka 进行通信。

***

Dispatcher、JobMaster、ResourceManager、TaskExecutor 这几个组件都同时继承了 RpcEndpoint 抽象类。我们来看一下 RpcEndpoint 的构造函数。

```
/**
 * Initializes the RPC endpoint.
 *
 * @param rpcService The RPC server that dispatches calls to this RPC endpoint.
 * @param endpointId Unique identifier for this endpoint
 */
protected RpcEndpoint(final RpcService rpcService, final String endpointId) {
	this.rpcService = checkNotNull(rpcService, "rpcService");
	this.endpointId = checkNotNull(endpointId, "endpointId");

	this.rpcServer = rpcService.startServer(this);

	this.mainThreadExecutor = new MainThreadExecutor(rpcServer, this::validateRunsInMainThread);
}
```

入参有一个 RpcService 实例，rpcService 实例是用来启动或者连接 RpcEndpoint。比如，TaskExecutor 使用 rpcService 实例启动了自己的 TaskExecutor 对应的 Actor，而对 JobMaster 的连接则是调用 rpcService 的 connect 方法获取 JobMaster 对应的 jobMasterGateway，从而可以通过 gateway 远程调用 JobMaster 的方法。  


而构造函数中初始化的 RpcServer 对应的就是 Actor 的一个封装了，里面包含了 address、host 等属性。  


> 如何通过 gateway 远程调用 JobMaster 的方法？

我们先看看 gateway 本身是如何生成的。从 connect 方法进去，找到 connectInternal 的末尾：

```
private <C extends RpcGateway> CompletableFuture<C> connectInternal(
		final String address,
		final Class<C> clazz,
		Function<ActorRef, InvocationHandler> invocationHandlerFactory) {
	checkState(!stopped, "RpcService is stopped");

	........

	return actorRefFuture.thenCombineAsync(
		handshakeFuture,
		(ActorRef actorRef, HandshakeSuccessMessage ignored) -> {
			InvocationHandler invocationHandler = invocationHandlerFactory.apply(actorRef);

			// Rather than using the System ClassLoader directly, we derive the ClassLoader
			// from this class . That works better in cases where Flink runs embedded and all Flink
			// code is loaded dynamically (for example from an OSGI bundle) through a custom ClassLoader
			ClassLoader classLoader = getClass().getClassLoader();

			@SuppressWarnings("unchecked")
			C proxy = (C) Proxy.newProxyInstance(
				classLoader,
				new Class<?>[]{clazz},
				invocationHandler);

			return proxy;
		},
		actorSystem.dispatcher());
}
```

发现这里使用了代理模式，而代理的类是 AkkaInvocationHandler，观察其中的 invokeRpc 方法，它将调用的方法以及参数封装成了 RpcInvocation（即 Message），通过 Akka 自身的机制传递给了 JobMaster 对应的 Actor。而 JobMaster 的 Actor 接收到对应的消息之后，通过反射机制调用了相对应的方法。





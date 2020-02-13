# Delta Lake

所以 Delta Lake 的目的是解决下面的问题：

1. Lambda-Architecture，让以后的数据流都变成纯流式，再通过 Delta Lake 去实现实时的数据应用。
2. Updates 的问题，例如 GDPR 应用场景。
3. Time Travel，可以回溯到之前的数据。

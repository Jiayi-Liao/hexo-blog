title: Table In Flink
author: Liao Jiayi
tags:
  - Flink
articleId: flink-table
categories:
  - Apache Flink
date: 2018-07-06 16:46:00
---

之前没有使用过 Table 相关的 API，在这稍微做下记录。

## Structure of Program

一个使用 Table API 的程序结构大致如下所示：

```
// create a TableEnvironment for specific planner batch or streaming
TableEnvironment tableEnv = ...; // see "Create a TableEnvironment" section

// register a Table
tableEnv.registerTable("table1", ...)            // or
tableEnv.registerTableSource("table2", ...);     // or
// register an output Table
tableEnv.registerTableSink("outputTable", ...);

// create a Table from a Table API query
Table tapiResult = tableEnv.scan("table1").select(...);
// create a Table from a SQL query
Table sqlResult  = tableEnv.sqlQuery("SELECT ... FROM table2 ... ");

// emit a Table API result Table to a TableSink, same for SQL result
tapiResult.insertInto("outputTable");

// execute
tableEnv.execute("java_job");
```

TableEnvironment 分为 Batch 和 Stream 两种，分别在 bridge 模块中可以实现与 DataSet / DataStream 之间的转换。  


注册 Table 的方式有三种：

* registerTable // register with Table
* registerTableSource // register with TableSource
* registerTableSink // register with TableSink

注册后便会在 Catalog 下注册对应的表，目前支持 Hive 和 InMemory 两种模式。





























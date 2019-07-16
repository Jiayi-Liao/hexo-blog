
# Database(2) - RocksDB

When it comes to the light and fast storage, we have to talk about RocksDB.


## Quick View

RocksDB Goals on performance:

* Efficient point looups as well as range scans.
* High random-read workloads.
* High update workloads.
* Easy to tune the tradeoff according to the hardware.

Basic structures:

* memtable: In-Memory structure, new writes are inserted into it after logfile(optional).
* sstfile: data file on disk. memtable flushes data into sstfile after memtable is full.
* logfile: used for recover data if memtable is lost.

When a key-value pair is written, it will go to logfile and memtable at first, then be flushed to disk after the memtable is full. And there are compactions between sstfiles periodically to reduce the rows with the same key. It's easy to understand if you know the Memstore, HFile and WAL in HBase. And they're both leveraging the theory of the LSM-Tree(Log Structured Merge Tree).

## Compaction

RocksDB provides three compaction styles:

* Level Style Compaction(default): merge small files(Level n) into larger files(Level n+1). Better read amplifycation.
* Universal Style Compaction: merge same size files. Better write amplifycation.
* FIFO Style Compaction: this works like LRU cache. I don't think it's a qualified compaction style at all...

The compaction part is not fresh for anyone who has been working on big data for several years. We can see that it learns from Cassandra and HBase including the theory and tuning method.

## Index Sstfile

This part is a bit interesting when RocksDB is using the Level Style Compaction. Assuming that there're N levels and each one is a sorted set. It's impossible that RocksDB does binary search by N on all levels. So how RocksDB figure it out?  

> Fractional Cascading

The secret is fractional cascading. Basically it's still leveraging the ideas of binary search but decrease the range of searching process in multiple sorted set scenario.  

Let me take an example to explain this shortly.  

```
L1 = [0 - 0], [1 - 5], [6 - 10], [11 - 15]
L2 = [0 - 1], [2 - 3], [4 - 12], [13 - 18]
L3 = [0 - 7], [8 - 14], [15 - 19], [20 - 30]
```  

Every sst file on every level has its own range, and obviously it will be much more efficient if we can record the position on the next level for the sstfile on the current level. By doing this, the data becomes this:

```
L1 = [[0 - 0], 0], [[1 - 5], 2], [[6 - 10], 2], [[11 - 15], 3]
L2 = [[0 - 1], 0], [[2 - 3], 0], [[4 - 12], 1], [[13 - 18], 3]
L3 = [[0 - 7], 0], [[8 - 14], 0], [[15 - 19], 0], [[20 - 30], 0]
```

Let's say we are looking for the sstfile for number "8". From L1 we find that the [6 - 10] is what we want and its index on the next level is two. So we continue searching on L2 from index 0 to index 2 instead of doing binary search on the whole sorted set. And it's the same way from L2 down the LSM tree.  

## Snapshot

## Transaction

Transaction is always a topic for database.








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
* FIFO Compaction Style:




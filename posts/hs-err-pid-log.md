title: hs_err_pid.log - 详解
author: Liao Jiayi
tags:
  - Memory
  - Linux
articleId: linux-hs_err_pid
categories: JVM
date: 2018-04-11 20:28:03
---
{% codeblock %}
# There is insufficient memory for the Java Runtime Environment to continue.
# Native memory allocation (mmap) failed to map 12288 bytes for committing reserved memory.
# Possible reasons:
#   The system is out of physical RAM or swap space
#   In 32 bit mode, the process size limit was hit
# Possible solutions:
#   Reduce memory load on the system
#   Increase physical memory or swap space
#   Check if swap backing store is full
#   Use 64 bit Java on a 64 bit OS
#   Decrease Java heap size (-Xmx/-Xms)
#   Decrease number of Java threads
#   Decrease Java thread stack sizes (-Xss)
#   Set larger code cache with -XX:ReservedCodeCacheSize=
# This output file may be truncated or incomplete.
#
#  Out of Memory Error (os_linux.cpp:2673), pid=13016, tid=140682742126336
#
# JRE version: Java(TM) SE Runtime Environment (8.0_40-b25) (build 1.8.0_40-b25)
# Java VM: Java HotSpot(TM) 64-Bit Server VM (25.40-b25 mixed mode linux-amd64 compressed oops)
# Failed to write core dump. Core dumps have been disabled. To enable core dumping, try "ulimit -c unlimited" before starting Java again
{% endcodeblock %}


第一部分主要是程序crash的原因以及相关的solution。
{% codeblock %}
Current thread (0x00007ff2d8001000):  JavaThread "flink-akka.remote.default-remote-dispatcher-15" daemon [_thread_new, id=31925, stack(0x00007ff340ced000,0x00007ff340dee000)]

Stack: [0x00007ff340ced000,0x00007ff340dee000],  sp=0x00007ff340dec9a0,  free space=1022k
Native frames: (J=compiled Java code, j=interpreted, Vv=VM code, C=native code)
V  [libjvm.so+0xaaca9a]  VMError::report_and_die()+0x2ba
V  [libjvm.so+0x4f333b]  report_vm_out_of_memory(char const*, int, unsigned long, VMErrorType, char const*)+0x8b
V  [libjvm.so+0x90e8c3]  os::Linux::commit_memory_impl(char*, unsigned long, bool)+0x103
V  [libjvm.so+0x90e98c]  os::pd_commit_memory(char*, unsigned long, bool)+0xc
V  [libjvm.so+0x90772a]  os::commit_memory(char*, unsigned long, bool)+0x2a
V  [libjvm.so+0x90c97f]  os::pd_create_stack_guard_pages(char*, unsigned long)+0x7f
V  [libjvm.so+0xa52b4e]  JavaThread::create_stack_guard_pages()+0x5e
V  [libjvm.so+0xa5c9b4]  JavaThread::run()+0x34
V  [libjvm.so+0x910ee8]  java_start(Thread*)+0x108
C  [libpthread.so.0+0x7dc5]  start_thread+0xc5
{% endcodeblock %}
Current Thread表示crash时程序所处的线程。
**线程类别**: JavaThread，共有以下几种
* JavaThread
* VMThread（负责VM内的一些操作，包括GC）
* CompilerThread
* GCTaskThread
* WatcherThread
* ConcurrentMarkSweepThread

**线程状态**：_thread_new

线程状态 | 描述
- | -
 _thread_uninitialized | 线程未被创建
 _thread_new | 线程创建但并未执行
 _thread_in_native | 线程正在运行native code
 _thread_in_vm | 执行VM的code
 _thread_in_java | 执行java的code
 _thread_blocked | 被block住的线程

**原生堆栈信息（Native frames）**: 主要是一些jvm动态库的对战信息，是分析crash中比较重要的一个部分。
{% codeblock %}
Java Threads: ( => current thread )
=>0x00007ff2d8001000 JavaThread "flink-akka.remote.default-remote-dispatcher-15" daemon [_thread_new, id=31925, stack(0x00007ff340ced000,0x00007ff340dee000)]
  0x00007ff2ec053800 JavaThread "Hashed wheel timer #1" daemon [_thread_blocked, id=14219, stack(0x00007ff33bdfe000,0x00007ff33beff000)]
  0x00007ff2dc130800 JavaThread "New I/O server boss #6" daemon [_thread_in_native, id=14218, stack(0x00007ff33beff000,0x00007ff33c000000)]
  0x00007ff2dc119800 JavaThread "New I/O worker #5" daemon [_thread_in_native, id=14217, stack(0x00007ff3400e3000,0x00007ff3401e4000)]
  0x00007ff2dc0b6000 JavaThread "New I/O worker #4" daemon [_thread_in_native, id=14216, stack(0x00007ff3401e4000,0x00007ff3402e5000)]
  0x00007ff2dc0bb800 JavaThread "New I/O boss #3" daemon [_thread_in_native, id=14215, stack(0x00007ff3402e5000,0x00007ff3403e6000)]
  0x00007ff2dc05c000 JavaThread "New I/O worker #2" daemon [_thread_in_native, id=14214, stack(0x00007ff3403e6000,0x00007ff3404e7000)]
  0x00007ff2dc052000 JavaThread "New I/O worker #1" daemon [_thread_in_native, id=14213, stack(0x00007ff3404e7000,0x00007ff3405e8000)]
  0x00007ff2c8009800 JavaThread "flink-akka.remote.default-remote-dispatcher-7" daemon [_thread_in_vm, id=14206, stack(0x00007ff3407e8000,0x00007ff3408e9000)]
  0x00007ff2c800c000 JavaThread "flink-akka.remote.default-remote-dispatcher-6" daemon [_thread_in_native, id=14202, stack(0x00007ff3408e9000,0x00007ff3409ea000)]
  0x00007ff2cc020000 JavaThread "flink-akka.actor.default-dispatcher-5" daemon [_thread_blocked, id=14147, stack(0x00007ff3409ea000,0x00007ff340aeb000)]
  0x00007ff36222a800 JavaThread "flink-akka.actor.default-dispatcher-4" daemon [_thread_blocked, id=14136, stack(0x00007ff340aeb000,0x00007ff340bec000)]
  0x00007ff362229000 JavaThread "flink-akka.actor.default-dispatcher-3" daemon [_thread_blocked, id=14135, stack(0x00007ff340bec000,0x00007ff340ced000)]
  0x00007ff362183000 JavaThread "flink-scheduler-1" daemon [_thread_blocked, id=14044, stack(0x00007ff340fee000,0x00007ff3410ef000)]
  0x00007ff3614b4000 JavaThread "Timer for 'phoenix' metrics system" daemon [_thread_blocked, id=14032, stack(0x00007ff342dfa000,0x00007ff342efb000)]
  0x00007ff360fc1000 JavaThread "main-EventThread" daemon [_thread_blocked, id=14031, stack(0x00007ff3431fc000,0x00007ff3432fd000)]
  0x00007ff360faf000 JavaThread "main-SendThread(cnzk2:2181)" daemon [_thread_in_native, id=14030, stack(0x00007ff3432fd000,0x00007ff3433fe000)]
  0x00007ff360471000 JavaThread "Thread-80" daemon [_thread_blocked, id=14029, stack(0x00007ff3430fb000,0x00007ff3431fc000)]
  0x00007ff3608a7000 JavaThread "IPC Parameter Sending Thread #0" daemon [_thread_blocked, id=13178, stack(0x00007ff3437fe000,0x00007ff3438ff000)]
  0x00007ff3608a4000 JavaThread "IPC Client (1508059488) connection to cnhm0/10.0.1.222:8032 from apps" daemon [_thread_blocked, id=13177, stack(0x00007ff348923000,0x00007ff348a24000)]
  0x00007ff3600df800 JavaThread "Service Thread" daemon [_thread_blocked, id=13172, stack(0x00007ff3498c5000,0x00007ff3499c6000)]
  0x00007ff3600d2000 JavaThread "C1 CompilerThread2" daemon [_thread_in_native, id=13171, stack(0x00007ff3499c6000,0x00007ff349ac7000)]
  0x00007ff3600d0000 JavaThread "C2 CompilerThread1" daemon [_thread_blocked, id=13170, stack(0x00007ff349ac7000,0x00007ff349bc8000)]
  0x00007ff3600cd000 JavaThread "C2 CompilerThread0" daemon [_thread_blocked, id=13169, stack(0x00007ff349bc8000,0x00007ff349cc9000)]
  0x00007ff3600cb000 JavaThread "JDWP Event Helper Thread" daemon [_thread_blocked, id=13168, stack(0x00007ff349cc9000,0x00007ff349dca000)]
  0x00007ff3600c7000 JavaThread "JDWP Transport Listener: dt_socket" daemon [_thread_in_native, id=13167, stack(0x00007ff349dca000,0x00007ff349ecb000)]
  0x00007ff3600b8000 JavaThread "Signal Dispatcher" daemon [_thread_blocked, id=13166, stack(0x00007ff34a0cf000,0x00007ff34a1d0000)]
  0x00007ff36008c000 JavaThread "Finalizer" daemon [_thread_blocked, id=13165, stack(0x00007ff34a1d0000,0x00007ff34a2d1000)]
  0x00007ff36008a000 JavaThread "Reference Handler" daemon [_thread_blocked, id=13164, stack(0x00007ff34a2d1000,0x00007ff34a3d2000)]
  0x00007ff360017000 JavaThread "main" [_thread_blocked, id=13158, stack(0x00007ff369c7a000,0x00007ff369d7b000)]

Other Threads:
  0x00007ff360085000 VMThread [stack: 0x00007ff34a3d2000,0x00007ff34a4d3000] [id=13163]
  0x00007ff3600e2000 WatcherThread [stack: 0x00007ff3497c4000,0x00007ff3498c5000] [id=13173]
{% endcodeblock %}
这一部分是crash时Java代码中所有线程的状况。分析类似上一部分。
{% codeblock %}
VM state:not at safepoint (normal execution)
VM Mutex/Monitor currently owned by a thread: None
{% endcodeblock %}
**VM状态**：

状态 | 描述
- | :-: |
not at a safepoint | 正常执行
at safepoint | 所有VM内的线程被block住，在等待某一个VM操作完成
synchronizing | 一个特殊VM操作需要执行，VM在等待所有线程block

{% codeblock %}
Heap:
 PSYoungGen  total 39424K, used 31166K [0x0000000771a00000, 0x0000000774780000, 0x00000007c0000000)
  eden space 38912K, 79% used [0x0000000771a00000,0x000000077384faf0,0x0000000774000000)
  from space 512K, 25% used [0x0000000774680000,0x00000007746a0000,0x0000000774700000)
  to   space 512K, 0% used [0x0000000774700000,0x0000000774700000,0x0000000774780000)
 ParOldGen   total 124928K, used 67043K [0x00000006d4e00000, 0x00000006dc800000, 0x0000000771a00000)
  object space 124928K, 53% used [0x00000006d4e00000,0x00000006d8f78d18,0x00000006dc800000)
 Metaspace   used 54122K, capacity 54748K, committed 54912K, reserved 1097728K
  class spaceused 6562K, capacity 6716K, committed 6784K, reserved 1048576K

Card table byte_map: [0x00007ff3664db000,0x00007ff366c35000] byte_map_base: 0x00007ff362e34000

Marking Bits: (ParMarkBitMap*) 0x00007ff3691426c0
 Begin Bits: [0x00007ff324a70000, 0x00007ff328538000)
 End Bits:   [0x00007ff328538000, 0x00007ff32c000000)

Polling page: 0x00007ff369d84000

CodeCache: size=245760Kb used=17958Kb max_used=18385Kb free=227801Kb
 bounds [0x00007ff34aad9000, 0x00007ff34bd29000, 0x00007ff359ad9000]
 total_blobs=6019 nmethods=5425 adapters=516
 compilation: enabled
{% endcodeblock %}
* Card Table是jvm维护的一种数据结构，用于记录更改对象时的引用，方便GC。
* CodeCache是用来保存本地代码的，不属于PermGen。

{% codeblock %}
Compilation events (10 events):
GC Heap History (10 events):
Deoptimization events (10 events):
Internal exceptions (10 events):
Events (10 events):
Dynamic libraries:
{% endcodeblock %}

这些都是表示crash时jvm最近的一些操作。举个例子说明：
{% codeblock %}
Events (10 events):
Event: 2603309.010 Thread 0x00007ff2c800c000 DEOPT UNPACKING pc=0x00007ff34aaddf69 sp=0x00007ff3409e88a8 mode 2
Event: 2603310.108 Thread 0x00007ff362229000 DEOPT PACKING pc=0x00007ff34b25ce6c sp=0x00007ff340ceb660
Event: 2603310.122 Thread 0x00007ff2c8009800 Uncommon trap: trap_request=0xffffff65 fr.pc=0x00007ff34b890e40
Event: 2603310.124 Thread 0x00007ff2c8009800 DEOPT PACKING pc=0x00007ff34b890e40 sp=0x00007ff3408e7790
Event: 2603310.124 Thread 0x00007ff2c8009800 DEOPT UNPACKING pc=0x00007ff34aaddf69 sp=0x00007ff3408e7680 mode 2
Event: 2603310.125 Thread 0x00007ff2c8009800 Uncommon trap: trap_request=0xffffff65 fr.pc=0x00007ff34b850fe4
Event: 2603310.125 Thread 0x00007ff2c8009800 DEOPT PACKING pc=0x00007ff34b850fe4 sp=0x00007ff3408e7560
Event: 2603310.125 Thread 0x00007ff2c8009800 DEOPT UNPACKING pc=0x00007ff34aaddf69 sp=0x00007ff3408e72d8 mode 2
Event: 2603310.126 Thread 0x00007ff362229000 DEOPT UNPACKING pc=0x00007ff34aaddf69 sp=0x00007ff340ceb628 mode 2
Event: 2603310.935 Thread 0x00007ff2d8001000 Thread added: 0x00007ff2d8001000
{% endcodeblock %}

上述是最近10个runtime VM的事件，拿第一条举例，2603309.010是从VM启动后的时长，单位是秒，pc是program counter，sp是stack pointer。关于 DEOPT、Uncommon trap等的解释可以看这个[issue](https://stackoverflow.com/questions/49716694/what-are-events-in-hs-err-pid-log/49716888#49716888)，大概就是编译的时候，编译器做了一些优化，但是在runtime时发现这个优化没有用，所以叫去优化（deoptimization）。
{% codeblock %}
---------------  S Y S T E M  ---------------

OS:Amazon Linux AMI release 2016.03

uname:Linux 4.4.11-23.53.amzn1.x86_64 #1 SMP Wed Jun 1 22:22:50 UTC 2016 x86_64
libc:glibc 2.17 NPTL 2.17
rlimit: STACK 8192k, CORE 0k, NPROC 65536, NOFILE 65536, AS infinity
load average:10.84 2.76 1.17

/proc/meminfo:
MemTotal:   15403948 kB
MemFree: 2637700 kB
MemAvailable:2571132 kB
Buffers: 304 kB
Cached:13784 kB
SwapCached:0 kB
Active: 12625320 kB
Inactive:   7684 kB
Active(anon):   12619252 kB
Inactive(anon):  336 kB
Active(file):   6068 kB
Inactive(file): 7348 kB
Unevictable:   0 kB
Mlocked:   0 kB
SwapTotal: 0 kB
SwapFree:  0 kB
Dirty:16 kB
Writeback:56 kB
AnonPages:  12606968 kB
Mapped:10896 kB
Shmem:   356 kB
Slab:  46004 kB
SReclaimable:  22384 kB
SUnreclaim:23620 kB
KernelStack:9856 kB
PageTables:38084 kB
NFS_Unstable:  0 kB
Bounce:0 kB
WritebackTmp:  0 kB
CommitLimit: 7701972 kB
Committed_AS:   18337652 kB
VmallocTotal:   34359738367 kB
VmallocUsed:   0 kB
VmallocChunk:  0 kB
AnonHugePages: 0 kB
HugePages_Total:   0
HugePages_Free:0
HugePages_Rsvd:0
HugePages_Surp:0
Hugepagesize:   2048 kB
DirectMap4k:   12288 kB
DirectMap2M:15716352 kB
{% endcodeblock %}
系统内存情况：

名词 | 描述 | 名词 | 描述 | 名词 | 描述
- | :-: | :-: | :-: | :-: | :-
MemToal | 总内存 | MemFree | 未使用内存 | MemAvailable | 可用内存
Buffers | 文件读写Buffer | Cached | 缓存 | SwapCached | 缓存的交换空间
Active | 最近被申请过的空间 | Inactive | 最近未被申请过的空间 | Active(anon) | ..
Inactive(anon) | .. | Active(file) | .. | Inactive(file) | ..
Unevictable | .. | Unevictable | .. | Mlocked | ..
SwapTotal | 可用交换空间 | SwapFree | 可用交换空间 | Dirty | 等待写入磁盘的空间
Writeback | 正在被写入磁盘的空间 | AnonPages | .. | Mapped | ..
Shmem | .. | Slab | kernel使用 | Sreclaimable | ..
SUnreclaim | .. | KernelStack | .. | PageTables | 内存页映射表空间
NFS_Unstable | .. | Bounce | .. | WritebackTmp | ..
CommitLimit | .. | Committed_AS | 完成workload最坏情况的内存使用情况 | VmallocTotal | ..
VmallocUsed | 虚拟空间可映射的大小 | VmallocUsed | 已使用的虚拟空间映射大小 | VmallocChunk | 虚拟空间最大的虚拟空间块
AnonHugePages | .. | HugePages_Total | .. | HugePages_Free | ..
HugePages_Rsvd | .. | HugePages_Surp | .. | Hugepagesize | ..
DirectMap4k | .. | DirectMap2M | ..




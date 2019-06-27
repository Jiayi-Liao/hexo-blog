# Disaggregation of Storage and Computation 

I've read some tech designs about disaggregation on Spark and I'm going to list them first.

## References

I have to start with what I read and what I learn recently, which may be really useful if you're interested in the related projects.

* [Use remote storage for persisting shuffle data](https://issues.apache.org/jira/browse/SPARK-25299): This is a Spark JIRA feature that I've anticipated for a while.
* [Taking Advantage of a Disaggregated Storage and Compute Architecture](https://databricks.com/session/taking-advantage-of-a-disaggregated-storage-and-compute-architecture): A Spark+AI Summit talk shared by Brian Cho from Facebook.
* [SOS: Optimizing Shuffle I/O](https://databricks.com/session/sos-optimizing-shuffle-i-o): A Spark+AI Summit talk shared by the same software engineer from Facebook.
* [Improving Spark Shuffle Reliability](https://docs.google.com/document/d/1uCkzGGVG17oGC6BJ75TpzLAZNorvrAU3FRd2X-rVHSM/edit#heading=h.btqugnmt2h40)

I noticed that more and more developers and business start focusing on the remote storage like OSS instead of local disk and that's why I am writing now.


## Why Disaggregation

* Network is not bottleneck anymore, at least for most business. And time spent on cpu is much more than on  network and that's why we can use remote storage with just a little more cost. This is kind of cliche because Spark already made a big change(Spark Tungsten) several years ago.
* Cloud service providers provide OSS like S3, which is much cheaper than the expenses of HDFS and local disks. Although there are probably some throughput issues, it's still a good choice for most analysists. And we all know that data is where value comes from and that's why companies trying to collect all the data no mather whether they are useful or not...So the budget is also growing, which means corporations have to find cheaper storage to store cold data(less value density).
* Budget again. Assume that your business is growing and you need to increase the computation ability on YARN, what are you going to do? I think you're going to add new servers into the cluster with the same cpu、memory and disk, but the expenses on disk are not what you want, right? By disaggregating the storage and computation you can only enhance the storage or computation individually.


## Disaggregation on Spark

Basically Spark is an processing engine, which means that it's only responsible for computation and writing/reading from S3 is already supported. However, there're still resources taken up by local disk like cache/shuffle. For cache it's like 


## Thoughts In My Mind

In the end of last century, a company bought PC desktop applications for human resources management. In the early days of the 21st century, this company registered an account on online system which is dedicated to the human resources management and paid for the service annually. Nowadays, the company is willing pay for the mobile application of human resources management due to the popularity of the smart phones. Obviously, the To-Business service evolved with the development of the architecture of technology, so does the data processing engine.  


Spark on Tungsten is a typical example for this. The background was the exchange of the network I/O and CPU I/O, which makes CPU become the new bottleneck of the large scale data processing. These days, the cloud service becomes a must-to-do thing for almost every corporation and after I watched some talks, read some papers and then, I find that the disaggregation of storage and computation is the future of data processing based on cloud service.   

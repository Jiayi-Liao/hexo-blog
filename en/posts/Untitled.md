# Disaggregation of Storage and Computation on Spark

In the end of last century, a company bought PC desktop applications for human resources management. In the early days of the 21st century, this company registered an account on online system which is dedicated to the human resources management and paid for the service annually. Nowadays, the company is willing pay for the mobile application of human resources management due to the popularity of the smart phones. Obviously, the To-Business service evolved with the development of the architecture of technology, so does the data processing engine.  


Spark on Tungsten is a typical example for this. The background was the exchange of the network I/O and CPU I/O, which makes CPU become the new bottleneck of the large scale data processing. These days, the cloud service becomes a must-to-do thing for almost every corporation and after I watched some talks, read some papers and then, I find that the disaggregation of storage and computation is the future of data processing based on cloud service.   


## References

I have to start with what I read and what I learn recently, which may be really useful if you're interested in the related projects.

* [Use remote storage for persisting shuffle data](https://issues.apache.org/jira/browse/SPARK-25299): This is a Spark JIRA feature that I've anticipated for a while.
* [Taking Advantage of a Disaggregated Storage and Compute Architecture](https://databricks.com/session/taking-advantage-of-a-disaggregated-storage-and-compute-architecture): A Spark+AI Summit talk shared by Brian Cho from Facebook.
* [SOS: Optimizing Shuffle I/O](https://databricks.com/session/sos-optimizing-shuffle-i-o): A Spark+AI Summit talk shared by the same software engineer from Facebook.
* [Improving Spark Shuffle Reliability](https://docs.google.com/document/d/1uCkzGGVG17oGC6BJ75TpzLAZNorvrAU3FRd2X-rVHSM/edit#heading=h.btqugnmt2h40)

## Why Cloud Service

Obviously, it's much easier and more efficient for corporations to build their own business with cloud service. And let's take a look at how we benefit from 

## Aggregation vs Disaggregation

## How to Implement


## Thoughts In My Mind
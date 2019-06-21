---
title: 排序算法
date: 2016-09-23 09:02:23
tags: Algorithm
keywords: Algorithm
description: 
categories: Programming
---

排序很基础，但是不同的排序算法所使用的思想不一样，还是很值得借鉴学习的。为了给自己巩固一下，手码一遍所有简单排序的代码。

## 快速排序
给出一个数组：  

1. 选取一个基准点，然后把小于基准点的数据放在左边，大于基准点的数据放在右边。  
2. 在基准点左边和右边的数组里重复1。  



```
def quickSort(arr: Array[Int], begin: Int, end: Int): Unit = {
  if (end > begin) {
    var (i, j) = (begin, end)
    val pivot = arr(i)

    while (i < j) {
      while (j > i && arr(j) > pivot) {
        j -= 1
      }

      if (j > i) {
        swap(arr, i, j)
      }

      while (i < j && arr(i) < pivot) {
        i += 1
      }

      if (i < j) {
        swap(arr, i, j)
      }
    }

    quickSort(arr, begin, i-1)
    quickSort(arr, i+1, end)
  }
}
```

## 插入排序：

新建一个数组，逐一插入。。。逻辑太简单了，不写...

## 冒泡排序

遍历所有元素，不停地将元素做交换。 n * n，很傻的算法。

```
def bubbleSort(arr: Array[Int]): Unit = {
  arr.indices.foreach(i => {
    (0 until arr.length - 1).foreach(j => {
      if (arr(j) > arr(j+1)) {
        swap(arr, j, j+1)
      }
    })
  })
}
```

## 选择排序
太傻的排序算法，不写。。。

## 归并排序
归并两个有序数组的思想，有序数组 = 归并（有序数组(0 -> mid), 有序数组(mid+1 -> N)），形成递归。

```
def mergeSort(arr: Array[Int], begin: Int, end: Int): Array[Int] = {
  if (begin == end) Array(arr(begin))
  else {
    val mid = (begin + end) / 2
    merge(mergeSort(arr, begin, mid), mergeSort(arr, mid+1, end))
  }
}

def merge(arr1: Array[Int], arr2: Array[Int]): Array[Int] = {
  var (i, j) = (0, 0)
  val newArr = mutable.ArrayBuffer[Int]()
  while (i < arr1.length || j < arr2.length) {
    if (i >= arr1.length) {
      newArr.append(arr2(j))
      j +=1
    } else if (j >= arr2.length) {
      newArr.append(arr1(i))
      i += 1
    } else if (arr1(i) <= arr2(j)) {
      newArr.append(arr1(i))
      i += 1
    } else if (arr1(i) > arr2(j)) {
      newArr.append(arr2(j))
      j += 1
    }
  }
  newArr.toArray
}
```


## 堆排序

1. 将数组构造成一个大顶堆，特性是父节点大于子节点的值。
2. 将大顶堆的第一个值移到最后，剩下的数字重新构造大顶堆，并重复这一流程。

```
def heapsort(arr: Array[Int]): Unit = {
  // 构建大顶堆
  (0 to arr.length / 2).foreach(i => {
    adjustHeap(arr, i, arr.length)
  })

  // remove first
  (arr.length to 1 by -1).foreach(i => {
    swap(arr, 0, i-1)
    adjustHeap(arr, 0, i-1)
  })
}

def adjustHeap(arr: Array[Int], idx: Int, length: Int): Unit = {

  (0 to length / 2).foreach(i => {
    var maxIdx = i
    if (i * 2+1 < length && arr(i*2+1) > arr(i)) {
      maxIdx = i * 2+1
    }

    if (i * 2 + 2 < length && arr(i*2+2) > arr(maxIdx)) {
      maxIdx = i * 2 + 2
    }

    swap(arr, i, maxIdx)
  })
}
```

## 计数排序
空间换时间，利用有限的数集大小，来直接将元素放入对应的位置。


## 桶排序
通过一个partition函数将数据集放入不同的桶中，再针对桶中数据做排序。






























# weibo-repost-get

## 简介

结课作业需要做一些微博爬虫任务，为了方便和爬取更多信息，结合网络上的教程，自己重新写了一个微博转发爬虫。

## 准备

### 0.下载

windows平台在cmd中运行：

```powershell
git clone git@github.com:AquariniqueMu/weibo-repost-get.git
```

### 1.获取uid和cookie

在m.weibo.cn搜索要爬取的微博，获取链接中的uid，以及账号的cookie，在`main.py`中设置

```python
if __name__ == '__main__':
    
    # 设置目标微博的uid
    uid = 4892360577649109
    
    # m.weibo.cn的cookie
    Cookie = ''
    
    # 调用转发微博爬虫工具，需要爬取转发微博的文本、转发时间、被转发数、评论数、点赞数时使用
    repo_main(uid, Cookie)
    
    # 调用添加用户信息工具，需要添加粉丝数、关注数、微博数、个人简介等信息时使用
    append_user_info(uid, Cookie)
```

### 2.安装依赖

在cmd中进入weibo-repost-get文件夹：

```powershell
cd weibo-repost-get
```

安装需要的package：

```powershell
pip install -r requiremes.txt
```

## 使用方法

设置好`main.py`的信息后，直接运行即可。

如果只需要转发微博的数据，可以只运行

```python
repo_main(uid, Cookie)
```

如果需要转发微博的用户信息，则需要后续运行

```python
append_user_info(uid, Cookie)
```

（用户信息爬取时很容易被锁cookie，除了cookie池外暂未找到合适的解决办法orz）
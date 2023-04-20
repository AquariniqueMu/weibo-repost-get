'''
Description: 简单调用转发微博爬虫工具
Author: Junwen Yang
Date: 2023-04-19 02:44:59
LastEditTime: 2023-04-20 11:06:04
LastEditors: Junwen Yang
'''
# 调用转发微博爬虫工具
from repost import repo_main
# 调用添加用户信息工具
from append_user_info import append_user_info


if __name__ == '__main__':
    
    # 设置目标微博的uid
    uid = 4892360577649109
    
    # m.weibo.cn的cookie
    Cookie = ''
    
    # 调用转发微博爬虫工具，需要爬取转发微博的文本、转发时间、被转发数、评论数、点赞数时使用
    repo_main(uid, Cookie)
    
    # 调用添加用户信息工具，需要添加粉丝数、关注数、微博数、个人简介等信息时使用
    append_user_info(uid, Cookie)
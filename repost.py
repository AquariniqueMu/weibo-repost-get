'''
Description: 获取特定微博的转发信息
Author: Junwen Yang
Date: 2023-04-19 02:44:59
LastEditTime: 2023-04-20 10:02:26
LastEditors: Junwen Yang
'''
import json
import requests
import time
from lxml import etree
import os
from urllib.parse import parse_qs
import fake_useragent
import random
import datetime
import pandas as pd
import openpyxl
from openpyxl import Workbook
import re


# 从微博的IP信息中解析出地址
def extract_location(string):
    if string == None:
        return ''
    elif '发布于 ' in string:
        return string.split('发布于 ')[-1].strip()
    else:
        return string

# 将字典按照DataFrame列顺序添加到DataFrame中
def append_dict_to_dataframe(info_dict:dict, repo_col:list) -> pd.DataFrame:
    """
    将字典按照DataFrame列顺序添加到DataFrame中
    """
    # 将字典按照DataFrame列顺序重排
    df_info = pd.DataFrame(columns=repo_col)
    info_dict_sorted = {col: info_dict[col] for col in df_info.columns}
    
    # 将d_sorted的值添加到DataFrame中
    df_info = df_info.append(info_dict_sorted, ignore_index=True)
    
    return df_info

# 从发布终端数据中提取出终端信息
def extract_device(text):
    # 使用正则表达式匹配所需的文本部分
    if text == None:
        return ''
    else:
        pattern = r'<a.*?>(.*?)<\/a>'
        result = re.search(pattern, text)
        
        if result:
            return result.group(1)
        else:
            return text


# 将微薄的时间信息转化为更易读的格式
def format_datetime(datetime_str):
    
    # 解析字符串为日期时间对象
    dt = datetime.datetime.strptime(datetime_str, '%a %b %d %H:%M:%S %z %Y')
    
    # 格式化日期时间对象为指定的字符串格式
    return '{0:%Y}-{0.month}-{0.day} {0:%H:%M:%S} {0:%a}'.format(dt)

# 微博的数字往往有亿和万的单位，需要转换为纯数字
def Number_unit_conversion(number: str) -> str:
    """
    数字单位转换
    """
    if type(number) == int:
        return str(number)
    elif number[-1] == '万':
        number = str(int(float(number[:-1])*10000))
    elif number[-1] == '亿':
        number = str(int(float(number[:-1])*100000000))
    else:
        return number

# 根据微博的id获取用户的各项资料和数据
def Get_User_Info(user_id: str, headers:dict) -> dict:
    """
    获取用户信息
    -------------
    userInfo中的keys:
    'id', 'screen_name', 'profile_image_url', 'profile_url', 'statuses_count', 'verified', 'verified_type', 'close_blue_v', 'description', 'gender', 'mbtype', 'svip', 'urank', 'mbrank', 'follow_me', 'following', 'follow_count', 'followers_count', 'followers_count_str', 'cover_image_phone', 'avatar_hd', 'like', 'like_me', 'toolbar_menus'
    """
    # print(user_id)
    url = "https://m.weibo.cn/api/container/getIndex?type=uid&value="+str(user_id)
    user_info = requests.get(url, headers=headers).json()
    with open('user_info.json', 'w', encoding='utf-8') as f:
        json.dump(user_info, f, ensure_ascii=False, indent=4)
    user_info = user_info['data']['userInfo']
    
    user_info_dict = {
        '用户id': user_info['id'],
        '昵称': user_info['screen_name'],
        '微博数量': user_info['statuses_count'],
        '关注数': Number_unit_conversion(user_info.get('follow_count')),
        '粉丝数': Number_unit_conversion(user_info.get('followers_count')),
        '个人简介': user_info.get('description'),
        '性别': user_info.get('gender'),
        '认证原因': user_info.get('verified_reason'),
        '是否会员': '是' if user_info['mbtype'] > 2 else '否',
        '会员等级': user_info['mbrank'],
        '微博等级': user_info.get('urank')
    }
    
    return user_info_dict

# 根据微博的id，当前的page数和headers获取指定页数的转发微博数据
def Get_Reposts(weibo_id: str, page:int, Cookie:str) -> dict:
    """
    获取指定id和页数的转发微博
    -------------
    data可用keys:
    'visible', 'created_at', 'id', 'idstr', 'mid', 'mblogid', 'user', 'can_edit', 'text_raw', 'text', 'annotations', 'source', 'favorited', 'cardid', 'pic_ids', 'geo', 'pic_num', 'is_paid', 'pic_bg_new', 'mblog_vip_type', 'number_display_strategy', 'reposts_count', 'comments_count', 'attitudes_count', 'attitudes_status', 'isLongText', 'mlevel', 'content_auth', 'is_show_bulletin', 'comment_manage_info', 'repost_type', 'share_repost_type', 'mblogtype', 'showFeedRepost', 'showFeedComment', 'pictureViewerSign', 'showPictureViewer', 'rcList', 'region_name', 'customIcons', 'retweeted_status'
    
    """
    
    # 设置代理信息
    headers = {
        
    # 随机生成的User-Agent，确保每次爬取的都是不同的User-Agent
    'User-Agent': random.choice(fake_useragent.UserAgent().data_browsers['chrome']),
    
    # 这里输入使用的cookie
    'Cookie': Cookie,
    
    }
    
    
    url = 'https://weibo.com/ajax/statuses/repostTimeline?moduleID=feed&id={}&page={}'.format(weibo_id, page)
    repost_info = requests.get(url, headers=headers).json()
    
    return repost_info

# 根据获取的json数据解析转发微博的各种数据
def Get_Weibo_Info(weibo_info:dict) -> dict:
    """
    获取微博的相关信息
    ----------------
    可用keys:
    'visible', 'created_at', 'id', 'idstr', 'mid', 'mblogid', 'user', 'can_edit', 'text_raw', 'text', 'annotations', 'source', 'favorited', 'cardid', 'pic_ids', 'geo', 'pic_num', 'is_paid', 'pic_bg_new', 'mblog_vip_type', 'number_display_strategy', 'reposts_count', 'comments_count', 'attitudes_count', 'attitudes_status', 'isLongText', 'mlevel', 'content_auth', 'is_show_bulletin', 'comment_manage_info', 'repost_type', 'share_repost_type', 'mblogtype', 'showFeedRepost', 'showFeedComment', 'pictureViewerSign', 'showPictureViewer', 'rcList', 'region_name', 'customIcons', 'retweeted_status'
    ----------------
    root微博可用keys:
    'visible', 'created_at', 'id', 'idstr', 'mid', 'mblogid', 'user', 'can_edit', 'text_raw', 'text', 'textLength', 'annotations', 'source', 'favorited', 'buttons', 'cardid', 'pic_ids', 'pic_focus_point', 'geo', 'pic_num', 'pic_infos', 'is_paid', 'mblog_vip_type', 'number_display_strategy', 'reposts_count', 'comments_count', 'attitudes_count', 'attitudes_status', 'isLongText', 'mlevel', 'content_auth', 'is_show_bulletin', 'comment_manage_info', 'mblogtype', 'showFeedRepost', 'showFeedComment', 'pictureViewerSign', 'showPictureViewer', 'rcList', 'region_name', 'customIcons'
    """
    
    info_dict = {
        '发布时间': format_datetime(weibo_info['created_at']),
        '微博ID': weibo_info['id'],
        '文本内容': weibo_info['text_raw'],
        '发布终端': extract_device(weibo_info['source']),
        '转发数': weibo_info['reposts_count'],
        '评论数': weibo_info['comments_count'],
        '点赞数': weibo_info['attitudes_count'],
        '用户ID': weibo_info['user']['id'],
        '昵称': weibo_info['user']['screen_name'], 
        '发布IP': extract_location(weibo_info.get('region_name'))
    }
        
    return info_dict

def merge_dataframes_remove_duplicate_rows(dfA, dfB):
    # 找出 dfB 中与 dfA 重复的行
    duplicated_rows = dfB['微博ID'].isin(dfA['微博ID'])

    # 通过布尔索引删除 dfB 中的重复行
    dfB = dfB[~duplicated_rows]

    # 纵向合并 dfA 和 dfB
    merged_df = pd.concat([dfA, dfB], axis=0).reset_index(drop=True)

    return merged_df


# 转发微博获取和解析的主函数
def start_crawl(uid:int, Cookie:str):
    """根据微博uid获取所有转发微博数据的主函数

    Args:
        uid (int): 核心微博的uid, 在微博链接的url中可以找到
        headers (dict): 请求header, 设置User-Agent, Cookie等信息
    """
    
    # 含个人用户信息的列名，可能导致get次数过多，用户数据另外获取
    # repo_columns=['发布时间', '微博ID', '文本内容', '发布终端', '转发数', '评论数', '点赞数', '用户ID', '昵称', '微博数量', '关注数', '粉丝数', '个人简介', '性别', '认证原因', '是否会员', '会员等级', '微博等级','发布IP', '转发微博ID', '转发微博文本', '转发微博作者ID', '转发微博作者昵称']
    
    # 微博信息与含用户ID与名称的列名，可用于之后获取用户数据
    repo_columns=['发布时间', '微博ID', '文本内容', '发布终端', '转发数', '评论数', '点赞数', '用户ID', '昵称', '发布IP']
    
    # 参数设置
    weibo_id = uid
    filename_df = 'repo_'+str(weibo_id)+'.xlsx'
    sheet_name = '转发信息'
    # filename_json = 'repo_'+str(weibo_id)+'.json'
    page = 0
    repost_count = 0
    df = pd.DataFrame(columns=repo_columns)
    df.to_excel(filename_df, index=False, encoding='utf-8-sig', engine='openpyxl')
    
    
    # 删除之前的表格
    # if os.path.exists(filename_df):
    #     os.remove(filename_df)
    # if os.path.exists(filename_json):
    #     os.remove(filename_json)
        
    # csv格式不好用，建议在最后保存xlsx格式
    # df.to_csv(filename_df, encoding='utf-8-sig', index=False)
       
    # json格式会导致数十个G的文件，不建议使用
    # js = []
    # with open(filename_json, 'w', encoding='utf-8') as f:
    #     json.dump(js, f, ensure_ascii=False, indent=4)
    
    # 开始抓取并记录数据
    while True:
        #  获取转发信息
        repost_info = Get_Reposts(weibo_id, page, Cookie)
        reposts = repost_info.get('data')
        
        #  若成功获取信息，则开始解析
        if reposts == None or len(reposts) == 0:
            break
        else:
            # js.extend(reposts)
            for repost in reposts:
                
                # 获取转发微博信息
                weibo_info = Get_Weibo_Info(repost)
                
                # 获取转发用户信息，由于可能导致get次数过多，用户数据另外获取
                # user_info = Get_User_Info(repost['user']['id'], headers)
                
                # 合并微博信息与用户信息
                # combined_dict = {**weibo_info, **user_info}
                combined_dict = weibo_info
                
                # 将解析的dict格式的信息记录进dataframe
                df_repo_all_info = append_dict_to_dataframe(combined_dict, repo_columns)
                
                # 追加到总dataframe中
                # df = df.append(df_repo_all_info, ignore_index=True)
                df = merge_dataframes_remove_duplicate_rows(df, df_repo_all_info)
                
                repost_count += 1
                
                # 没必要在这里sleep
                # time.sleep(random.uniform(0, 0.1))
        
        # csv数据占用空间较大，且存储次数过多影响性能，不建议使用
        # df.to_csv(filename_df, index=False, encoding='utf-8-sig',mode='a', header=False)
        
        # 会产生大于50个G的数据，不建议使用
        # with open(filename_json, 'a') as f:
        #     json.dump(js, f)
        
        # 标记进度
        page += 1
        print('Done with {} pages and {} reposts...'.format(page, len(df)))
        
        # sleep的时间一定要随机，否则容易被识别导致被锁IP或Cookie
        time.sleep(random.uniform(0.2, 0.6))
    
    # 爬取结束后保存数据
    df = df.astype(str)
    with pd.ExcelWriter(filename_df,mode='a',engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

def repo_main(uid, Cookie):
    
    
    
    # 这里输入要爬取的微博ID 
    # uid = 4890498505115219
    
    # 没什么用的格式输出
    print("=============================================================")
    print('========Crawling reposts of weibo id: {}======='.format(uid))
    print("=============================================================")
    
    # 开始爬取
    start_crawl(uid, Cookie)


'''
Description: 向已经获取的转发微博数据中添加用户信息
Author: Junwen Yang
Date: 2023-04-20 05:20:36
LastEditTime: 2023-04-20 10:46:17
LastEditors: Junwen Yang
'''
import pandas as pd
import json
import os
import time
import random
import requests
import re
import fake_useragent
import numpy as np
from bs4 import BeautifulSoup
from alive_progress import alive_bar

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

# 从html中提取用户信息
def extract_html_user_info(user_id:int, Cookie:str):
    
    # weibo.cn的个人主页url
    url = 'https://weibo.cn/'+str(user_id)
    
    # 设置代理信息, 建议每次循环更新代理, 防止被封
    headers = {
        
    # 随机生成的User-Agent，确保每次爬取的都是不同的User-Agent
    'User-Agent': random.choice(fake_useragent.UserAgent().data_browsers['chrome']),
    
    # 这里输入使用的cookie
    'Cookie': Cookie,
    
    }
    
    response = requests.get(url, headers=headers)
    html = response.text
    
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    
    weibo_num = re.findall(r'微博\[(\d+)\]', text)[0]
    follow = re.findall(r'关注\[(\d+)\]', text)[0]
    followers = re.findall(r'粉丝\[(.*?)]', text)[0]
    description = re.findall(r'<span class="ctt" style="word-break:break-all; width:50px;">(.*?)<\/span>', html)[0]
    gender_and_loc = re.findall(r'</a>&nbsp;(.*?) &nbsp;', html)
    # gender_and_loc = gender_and_loc.split('/')
    verified_reason = re.findall(r'<span class="ctt">认证：(.*?)<\/span>', html)
    
    info_dict = {
        '微博数量': weibo_num,
        '关注数': Number_unit_conversion(follow),
        '粉丝数': Number_unit_conversion(followers),
        '个人简介': description,
        '认证原因': verified_reason,
        '性别': gender_and_loc[0].split('/')[0] if gender_and_loc != [] else '',
        '地区': gender_and_loc[0].split('/')[1] if gender_and_loc != [] else ''
    }
    
    return info_dict

# 根据微博的id获取用户的各项资料和数据
def Get_User_Info(user_id: str, cookie) -> dict:
    """
    获取用户信息
    -------------
    userInfo中的keys:
    'id', 'screen_name', 'profile_image_url', 'profile_url', 'statuses_count', 'verified', 'verified_type', 'close_blue_v', 'description', 'gender', 'mbtype', 'svip', 'urank', 'mbrank', 'follow_me', 'following', 'follow_count', 'followers_count', 'followers_count_str', 'cover_image_phone', 'avatar_hd', 'like', 'like_me', 'toolbar_menus'
    """
    # print(user_id)
    
    # 设置代理信息, 建议每次循环更新代理, 防止被封
    headers = {
        
    # 随机生成的User-Agent，确保每次爬取的都是不同的User-Agent
    'User-Agent': random.choice(fake_useragent.UserAgent().data_browsers['chrome']),
    
    # 这里输入使用的cookie
    'Cookie': cookie,
    
    }
    
    
    url = 'https://m.weibo.cn/api/container/getIndex?uid={uid}&luicode=10000011&lfid=230413{uid}_-_WEIBO_SECOND_PROFILE_WEIBO&type=uid&value={uid}&containerid=100505{uid}'.format(uid=user_id)
    
    
    
    user_info = requests.get(url, headers=headers).json()
    with open('user_info.json', 'w', encoding='utf-8') as f:
        json.dump(user_info, f, ensure_ascii=False, indent=4)
    # print(user_info)
    user_info = user_info['data']['userInfo']
    
    user_info_dict = {
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

# 获取用户信息的主函数
def get_user_info(data:pd.DataFrame, Cookie:str) -> pd.DataFrame:
    # 设置表格列名
    df_user_info = pd.DataFrame(columns=['昵称','微博数量', '关注数', '粉丝数', '个人简介','认证原因', '性别','是否会员','会员等级','微博等级'] )
    
    u_cnt = 0
    
    # 开始获取用户信息
    print('\nStart Searching Users Info... \n')
    with alive_bar(len(data['用户ID']),bar='blocks',title='Searching Users Info ---> ') as bar:
        for uid in data['用户ID']:
            
            # m.weibo.cn的api接口容易被封, 注释掉
            user_info = Get_User_Info(uid,cookie=Cookie)
            
            # 这里采用weibo.cn的网页接口
            # user_info = extract_html_user_info(uid, Cookie)
            
            # 将获取到的用户信息添加到DataFrame中
            df_user_info = df_user_info.append(user_info, ignore_index=True)
            u_cnt += 1
            
            # 随机休眠一段时间，防止被封
            time.sleep(random.uniform(0.1,0.4))
            if u_cnt % 20 == 0:
                time.sleep(random.uniform(10,15))
            # 更新进度条
            bar()
            
    return df_user_info

# 重新排列表格的列顺序
def reorder_columns(df, new_order):
    return df.reindex(columns=new_order)

# 合并两个 DataFrame 并删除重复列
def merge_dataframes_remove_duplicate_columns(dfA, dfB):
    
    # 横向合并两个 DataFrame
    merged_df = pd.concat([dfA, dfB], axis=1)
    
    # 删除重复列
    _, idx = np.unique(merged_df.columns, return_index=True)
    result_df = merged_df.iloc[:, idx]

    return result_df

# 保存数据到 Excel 文件
def append_user_info(uid:int, Cookie:str):
    
    # 读取转发信息
    filename = 'repo_' + str(uid) + '.xlsx'
    sheet_name = '转发信息'
    data_repo = pd.read_excel(filename, sheet_name=sheet_name,engine='openpyxl')
    
    # 爬取用户信息
    data_users = get_user_info(data_repo, Cookie)
    
    # 合并两个 DataFrame 并删除重复列
    merge_data = merge_dataframes_remove_duplicate_columns(data_repo, data_users)
    
    # 重新排序列
    new_cols_order = ['发布时间', '微博ID', '文本内容', '发布终端', '转发数', '评论数', '点赞数', '用户ID', '昵称', '微博数量', '关注数', '粉丝数', '个人简介','发布IP', '性别', '认证原因','是否会员','会员等级','微博等级']
    
    # 按照新的列顺序重新排序数据表格 
    data_new_order = reorder_columns(merge_data, new_cols_order)
    
    # 保存数据
    save_filename = 'repo_' + str(uid) + '_all_info.xlsx'
    data_new_order.to_excel(save_filename, index=False, encoding='utf-8', sheet_name=sheet_name, engine='openpyxl')
    

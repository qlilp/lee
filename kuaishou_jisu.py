#!/usr/bin/python
# coding=utf-8
import sys
import os
import traceback
import requests
import json

import hashlib

SIGN_LOG = 'logs/kuaishou_sign.log'

work_path = os.path.dirname(os.path.abspath(__file__))
SIGN_LOG_FILE = os.path.join(work_path, SIGN_LOG)


def get_baoxiang(token, __NS_sig3):
    print('💎💎💎💎开始领取宝箱💎💎💎💎')
    access_token = ''
    try:
        url = "https://nebula.kuaishou.com/rest/wd/encourage/unionTask/treasureBox/report?__NS_sig3=" + __NS_sig3 + "&sigCatVer=1"

        # 定义请求头
        headers = {
            "Host": "nebula.kuaishou.com",
            "Connection": "keep-alive",
            "Content-Length": "2",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 23113RKC6C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.226 KsWebView/1.8.90.675 (rel) Mobile Safari/537.36 Yoda/3.1.7-alpha33-intercept1 ksNebula/12.5.20.8014 OS_PRO_BIT/64 MAX_PHY_MEM/15199 AZPREFIX/az4 ICFO/0 StatusHT/34 TitleHT/43 NetType/WIFI ISLP/0 ISDM/0 ISLB/0 locale/zh-cn DPS/19.822 DPP/99 CT/0 ISLM/0",
            "content-type": "application/json",
            "Accept": "*/*",
            "Origin": "https://nebula.kuaishou.com",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://nebula.kuaishou.com/nebula/task/earning?source=timer&layoutType=4&hyId=nebula_earning",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": token
        }

        # 发送 POST 请求
        resp = requests.post(url, headers=headers, data=json.dumps({}))
        resp_json = resp.json()
        if resp_json['result'] == 1:
            title_reward_count = resp_json['data']['title']['rewardCount']
            print(f"得到金币：{title_reward_count}")
        else:
            print(resp_json['error_msg'])
    except:
        print(f"获取异常:{traceback.format_exc()}")
        

    return access_token

def get_fanbu(token, __NS_sig4):
    print("🍱🍱🍱🍱开始领取饭补🍱🍱🍱🍱")
    try:
        url = "https://encourage.kuaishou.com/rest/wd/encourage/unionTask/dish/report?__NS_sig4=" + __NS_sig4 + "&sigCatVer=1"

        # 定义请求头
        headers = {
            "Host": "encourage.kuaishou.com",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 23113RKC6C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.226 KsWebView/1.8.90.675 (rel) Mobile Safari/537.36 Yoda/3.1.7-alpha33-intercept1 ksNebula/12.5.20.8014 OS_PRO_BIT/64 MAX_PHY_MEM/15199 AZPREFIX/az4 ICFO/0 StatusHT/34 TitleHT/43 NetType/WIFI ISLP/0 ISDM/0 ISLB/0 locale/zh-cn DPS/19.822 DPP/99 CT/0 ISLM/0",
            "content-type": "application/json",
            "Accept": "*/*",
            "Origin": "https://encourage.kuaishou.com",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://encourage.kuaishou.com/activity/dish?layoutType=4&encourageEventTracking=W3siZW5jb3VyYWdlX3Rhc2tfaWQiOjIwMDA4LCJlbmNvdXJhZ2VfcmVzb3VyY2VfaWQiOiJlYXJuUGFnZV90YXNrTGlzdF8xNyIsImV2ZW50VHJhY2tpbmdMb2dJbmZvIjpbeyJldmVudFRyYWNraW5nVGFza0lkIjoyMDAwOCwicmVzb3VyY2VJZCI6ImVhcm5QYWdlX3Rhc2tMaXN0XzE3IiwiZXh0UGFyYW1zIjp7fX1dfV0",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": token
        }

        # 发送 POST 请求
        resp = requests.post(url, headers=headers, data=json.dumps({}))
        
        resp_json = resp.json()
        if resp_json['result'] == 1:
            title = resp_json['data']['title']
            dsd = resp_json['data']['amount']
            print(f"{title} 共计: {dsd}")
        else:
            print(resp_json['error_msg'])

    except:
        print(f"获取异常:{traceback.format_exc()}")

def get_money(token):
    print('🥰🥰🥰🥰🥰开始获取当前的现金💰️💰️💰️💰️💰️')
    money = ''
    try:
        url = "https://nebula.kuaishou.com/rest/n/nebula/activity/earn/overview/basicInfo"

        # 定义请求头
        headers = {
            "Host": "nebula.kuaishou.com",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 23113RKC6C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.226 KsWebView/1.8.90.675 (rel) Mobile Safari/537.36 Yoda/3.1.7-alpha33-intercept1 ksNebula/12.5.20.8014 OS_PRO_BIT/64 MAX_PHY_MEM/15199 AZPREFIX/az4 ICFO/0 StatusHT/34 TitleHT/43 NetType/WIFI ISLP/0 ISDM/0 ISLB/0 locale/zh-cn DPS/19.822 DPP/99 CT/0 ISLM/0",
            "content-type": "application/json",
            "Accept": "*/*",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://nebula.kuaishou.com/nebula/task/earning?source=timer&layoutType=4&hyId=nebula_earning",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": token
        }

        # 发送 POST 请求
        resp = requests.get(url, headers=headers)
        
        resp_json = resp.json()
        money = resp_json['data']['allCash']
        print(f"现在的钱总共：{money}")
    except:
        print(f"获取异常:{traceback.format_exc()}")

    return money


def get_qiandao(token, __NS_sig3):
    print('❤❤❤❤❤开始执行签到❤❤❤❤❤')
    try:
        url = "https://nebula.kuaishou.com/rest/wd/encourage/unionTask/signIn/report?__NS_sig3=" + __NS_sig3 + "&sigCatVer=1"

        # 定义请求头
        headers = {
            "Host": "nebula.kuaishou.com",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 23113RKC6C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.226 KsWebView/1.8.90.675 (rel) Mobile Safari/537.36 Yoda/3.1.7-alpha33-intercept1 ksNebula/12.5.20.8014 OS_PRO_BIT/64 MAX_PHY_MEM/15199 AZPREFIX/az4 ICFO/0 StatusHT/34 TitleHT/43 NetType/WIFI ISLP/0 ISDM/0 ISLB/0 locale/zh-cn DPS/19.822 DPP/99 CT/0 ISLM/0",
            "content-type": "application/json",
            "Accept": "*/*",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://nebula.kuaishou.com/nebula/task/earning?source=timer&layoutType=4&hyId=nebula_earning",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": token
        }

        # 发送 POST 请求
        resp = requests.get(url, headers=headers)
        resp_json = resp.json()

        #print(resp.text)

        if resp_json['result'] == 1:
            if 'reportRewardResult' in resp_json['data']:
                title = resp_json['data']['reportRewardResult']['awardToast']['title']
                print(f"{title}")
                bsd1 = resp_json['data']['reportRewardResult']['awardToast']['basicSignInAwardResultShow']['bottomText']
                bsd2 = resp_json['data']['reportRewardResult']['awardToast']['basicSignInAwardResultShow']['bottomText']
                print(f"正常：{bsd1}  额外：{bsd2}")
            elif 'signInUnionSpecialAreaData' in resp_json['data']:
                subtitle = resp_json['data']['signInUnionSpecialAreaData']['subtitle']
                todaySignInAmount = resp_json['data']['signInUnionSpecialAreaData']['todaySignInAmount']
                print(f"{subtitle}")
                print(f"今日签到得到：{todaySignInAmount}元")
        else:
            print(resp_json['error_msg'])
    except:
        print(f"获取异常:{traceback.format_exc()}")

# 获取环境变量
_cookie = os.getenv('KSJSB_COOKIE')

# 检查变量是否存在
if _cookie == '':
    print("请先在环境变量里添加 \"KS_COOKIE\" 填写对应快手的 cookie 值")
    exit(0)

def gen_tokensig(sig,salt=""):
    v = sig + salt
    return hashlib.sha256(v.encode('utf-8')).hexdigest()

def gen_sig(params,data):
    dd = dict(params,**data)
    dict_sort_res = dict(sorted(dd.items(),key=lambda x:x[0]))
    ss = ""
    for key,value in dict_sort_res.items():
        if key not in ["sig","__NS_sig3","sig2"]:
            ss += f"{key}={value}"
    ss += "ca8e86efb32e"
    return hashlib.md5(ss.encode()).hexdigest()



def main():
    get_baoxiang(_cookie, "273770408664a7a2ea7b10787f7e62718c6a7e50b5b0f4654b2568686e6e6d6c5373")
    get_fanbu(_cookie, "HUDR_sFnX-HFuAE5VsdPNKlLOPr4ntwVLcugxjxZz8_z61EHYFY07AGiHwMelb_ny_pMHxR_0BjgEKKQba1Uc3eSWmMYZtd0w8l4XDj-3MCjD__Ta_XvZSJ4TCB8KqqVKMgRgdptyHjC4q5WxhjlivWeuiUH73Q5s2-4u88UkwHrtgNYFpaoTLyzpjhJN-kWm8EpIT1cd-4gSarv9lyc5eoynpqIeL1p8oDC_aNVs06Eqr9eEDO9WQN6bPOljEgPJOUyOx2TUE6Zol22dloUXNTFoJdgLPRKfw_RHixi41S59Nig74-a-EOa96K3w3f2SK367nfaMVvB8TYO9Zh3FHGMRsgPwfpaekre0Ra5-ZMIxO_S1Jpimvzg8hzW00xtV2EkEfYDNFvw68MgnbnxspI6ndwP4goeqm_Gr_PeS3rmTNMpgPIhHOlYIzTyVqRydZeTwh5ckgKW0moc1WndwyJqoqIh222uMxhDr_q2L_eyoTl7L7Moo_r17aDmbuEH0je0LPc3uCfeFHFlC$HE_4b541fe2ab6646f3d69101f15f438f046f01070200376b00000041da22b49a5cf4d691019b563eda7b563e1200")
    get_qiandao(_cookie, "0b1b5c6c1243e48ec657335453525d3e5ff0b056f69cd8490b5e4444424241407f5f")
    get_money(_cookie)
    
if __name__ == '__main__':
    main()


#!/usr/bin/python
# coding=utf-8
import sys
import os
import traceback
import requests
import json

SIGN_LOG = 'logs/kuaishou.log'

work_path = os.path.dirname(os.path.abspath(__file__))
SIGN_LOG_FILE = os.path.join(work_path, SIGN_LOG)

_cookie = os.getenv('KS_COOKIE1')
# 检查变量是否存在
if _cookie == '':
    print("请先在环境变量里添加 \"KS_COOKIE\" 填写对应快手的 cookie 值")
    exit(0)


def get_baoxiang(token):
    print('开始领取宝箱 💎💎')
    access_token = ''
    try:
        url = "https://encourage.kuaishou.com/rest/wd/encourage/unionTask/treasureBox/report?__NS_sig3=bfafe8d8fdd76d6d73e393e0e7e6828ddee27d58767f6dfdf1def0f0f6f6f5f4cbeb&sigCatVer=1"

        # 定义请求头
        headers = {
            "Host": "encourage.kuaishou.com",
            "Connection": "keep-alive",
            "Content-Length": "2",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 23113RKC6C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.226 KsWebView/1.8.90.675 (rel) Mobile Safari/537.36 Yoda/3.1.7-alpha33-intercept1 ksNebula/12.5.20.8014 OS_PRO_BIT/64 MAX_PHY_MEM/15199 AZPREFIX/az4 ICFO/0 StatusHT/34 TitleHT/43 NetType/WIFI ISLP/0 ISDM/0 ISLB/0 locale/zh-cn DPS/19.822 DPP/99 CT/0 ISLM/0",
            "content-type": "application/json",
            "Accept": "*/*",
            "Origin": "https://encourage.kuaishou.com",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://encourage.kuaishou.com/kwai/task?layoutType=4&source=pendant&hyId=encourage_earning",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": token
        }

        # 发送 POST 请求
        resp = requests.post(url, headers=headers, data=json.dumps({}))
        resp_json = resp.json()
        title_reward_count = resp_json['data']['title']['rewardCount']
        print(f"得到金币：{title_reward_count}")
    except:
        print(f"获取异常:{traceback.format_exc()}")

    return access_token


def get_fanbu(token):
    print("开始领取饭补 🍱")
    try:
        # 获取当前的是否领取过饭补
        url = "https://encourage.kuaishou.com/rest/wd/encourage/unionTask/dish/detail?__NS_sig4=HUDR_sFnX-HFuAE5VsdPNKlLOPr4ntwVLcugxjxZz8_z61EHYFY07AGiHwMelb_ny_pMHxR_0BjgEKKQba1Uc3eSWmMYZtd0w8l4XDj-3MCjD__Ta_XvZSJ4TCB8KqqVKMgRgdptyHjC4q5WxkzlivWeuOUH73Q5s2-4u88UkwHrtgNYFpaoTLyzpjhJN-kWm8EpIT1cd-4gSarv9lyc5NYynpqIeL1p8oDC_aNVs06Eqr9eEDO9WQN6bPOljEgPJOUyOx2TUE6Zol22dloUXNTFoJdgLPRKfw_RHi0y41S59Nig74-a-EOa976Kn3PySfizrwKPeBfIvE4O9ZR3FHGMRsQPwfpaekre0Ra5-vsMxO_S1KZimvzg8hzW00xtV2EkEeYPLRaBq8MgnbnxspIGrdAT7goeqm_Gr_PeS3rmTNMpgPIhHOlYIzTyVqRydZeTwh5ckgKW0moc1WndwyJqoqIh222uMxhDr_q2L_eyoTgrL6MkureEraDmbuEH0je0NPMrtCfeKHFlC$HE_4b541fe2ab24d38e819001d42e68655f9401070200376400000011de71b732d48e8190019b563eda7b563ee200&sigCatVer=1"
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
        resp = requests.get(url, headers=headers)
        resp_json = resp.json()
        #print(resp.text)
        if resp_json['result'] == 1:
            if resp_json['data']['mainButtonInfo']['buttonStatus'] == 'TO_COMPLETE':

                url = "https://encourage.kuaishou.com/rest/wd/encourage/unionTask/dish/report?__NS_sig4=HUDR_sFnX-HFuAE5VsdPNKlLOPr4ntwVLcugxjxZz8_z61EHYFY07AGiHwMelb_ny_pMHxR_0BjgEKKQba1Uc3eSWmMYZtd0w8l4XDj-3MCjD__Ta_XvZSJ4TCB8KqqVKMgRgdptyHjC4q5WxkzlivWeuJ0H73Q5s2-4u88UkwHrtgNYFpaoTLyzpjhJN-kWm8EpIT1cd-4gSarv9lyc5NYynpqIeL1p8oDC_aNVs06Eqr9eEDO9WQN6bPOljEgPJOUyOx2TUE6Zol22dloUXNTFoJdgLPRKfw_RHi0y41S59Nig74-a-EOa976Kn3PySfizrwKPeBfIvE4O9ZB3FHGMRsAPwfpaekre0Ra5-ycExO_S1JZimvzg8hzW00xtV2EkEeYPLRaBq8MgnbnxspIGrdAT7goeqm_Gr_PeS3rmTNMpgPIhHOlYIzTyVqRydZeTwh5ckgKW0moc1WndwyJqoqIh222uMxhDr_q2L_eyoTgrL6MkureEraDmbuEH0je0NPMrtCfeGHFlC$HE_4b541fe2abe1d0e080900153dec924ff8e0107020037680000001bdd71b4d02fe18090019b563eda7b563e9900&sigCatVer=1"

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
            else:
                buttonText = resp_json['data']['mainButtonInfo']['buttonText']
                print(f'还不到饭补时间         {buttonText}')
        else:
            print(resp_json['error_msg'])

    except:
        print(f"获取异常:{traceback.format_exc()}")


def get_money(token):
    print('🥰开始获取当前的现金  💰️💰️💰️💰️💰️💰️💰️')
    money = ''
    try:
        url = "https://encourage.kuaishou.com/rest/wd/encourage/home"

        # 定义请求头
        headers = {
            "Host": "encourage.kuaishou.com",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 23113RKC6C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.226 KsWebView/1.8.90.675 (rel) Mobile Safari/537.36 Yoda/3.1.7-alpha33-intercept1 ksNebula/12.5.20.8014 OS_PRO_BIT/64 MAX_PHY_MEM/15199 AZPREFIX/az4 ICFO/0 StatusHT/34 TitleHT/43 NetType/WIFI ISLP/0 ISDM/0 ISLB/0 locale/zh-cn DPS/19.822 DPP/99 CT/0 ISLM/0",
            "content-type": "application/json",
            "Accept": "*/*",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://encourage.kuaishou.com/kwai/task?layoutType=4&source=pendant&hyId=encourage_earning",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": token
        }

        # 发送 POST 请求
        resp = requests.get(url, headers=headers)
        
        resp_json = resp.json()
        cash = resp_json['data']['cash']
        coin = resp_json['data']['coin']
        print(f"现在的钱总共：{cash}元")

        print(f"现在的钱总共：{coin}金币")
    except:
        print(f"获取异常:{traceback.format_exc()}")

    return money



def get_qiandao(token):
    print('❤开始执行签到')
    try:
        url = "https://encourage.kuaishou.com/rest/wd/encourage/unionTask/signIn/report?__NS_sig3=2a3a7d4d6842f8f8e6761f757273493c0c023838eaeaf868ce516565636360615e7e&sigCatVer=1"

        # 定义请求头
        headers = {
            "Host": "encourage.kuaishou.com",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 23113RKC6C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.226 KsWebView/1.8.90.675 (rel) Mobile Safari/537.36 Yoda/3.1.7-alpha33-intercept1 ksNebula/12.5.20.8014 OS_PRO_BIT/64 MAX_PHY_MEM/15199 AZPREFIX/az4 ICFO/0 StatusHT/34 TitleHT/43 NetType/WIFI ISLP/0 ISDM/0 ISLB/0 locale/zh-cn DPS/19.822 DPP/99 CT/0 ISLM/0",
            "content-type": "application/json",
            "Accept": "*/*",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://encourage.kuaishou.com/kwai/task?layoutType=4&source=pendant&hyId=encourage_earning",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": token
        }

        # 发送 POST 请求
        resp = requests.get(url, headers=headers)
        resp_json = resp.json()
        if resp_json['result'] == 1:
            title = resp_json['data']['reportRewardResult']['awardToast']['title']
            print(f"{title}")
            bsd1 = resp_json['data']['reportRewardResult']['awardToast']['basicSignInAwardResultShow']['bottomText']
            bsd2 = resp_json['data']['reportRewardResult']['awardToast']['basicSignInAwardResultShow']['bottomText']
            print(f"正常：{bsd1}  额外：{bsd2}")
        else:
            print(resp_json['error_msg'])
    except:
        print(f"获取异常:{traceback.format_exc()}")


def main():
    get_qiandao(_cookie)
    get_baoxiang(_cookie)
    get_fanbu(_cookie)
    get_money(_cookie)

if __name__ == '__main__':
    main()

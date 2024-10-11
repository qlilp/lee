#   --------------------------------注释区--------------------------------
#   https://openapp.fmy90.com/auth/找token,格式：bearer eyJxxx
#   变量:mnhs ，格式：多号@分割
#   跟飞蚂蚁同一家，token有效期半个月
#   走个头谢谢，下面二选一
#   https://gitee.com/wry-fisher/push-notifications/blob/master/mnhstgm.png
#   https://gitee.com/wry-fisher/push-notifications/blob/master/mnhstgm-2.png
#   corn: 每天跑一次就行 22 6 * * *
#   建议把请求头替换成自己的UA，填进ua里，不改也行挑选随机幸运儿封号
#   by fisher 2024.09.08

cookie =""
import requests
import os
import time
import random

# 初始化 User-Agent
ua = ""

def send(title, con):
    try:
        notify = __import__('notify')
        notify.send(title, con)
    except ImportError:
        print("通知模块加载失败")

class yyf():
    def __init__(self, cookie):
        self.key = ""
        self.token = cookie
        self.headers = {
            'User-Agent': ua or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090b19)XWEB/11253",
            'xweb_xhr': "1",
            'authorization': self.token,
            'content-type': "application/json",
            'sec-fetch-site': "cross-site",
            'sec-fetch-mode': "cors",
            'sec-fetch-dest': "empty",
            'referer': "https://servicewechat.com/wxa587f7c3393d3d2f/3/page-frame.html",
            'accept-language': "zh-CN,zh;q=0.9"
        }

    def signin(self):
        url = "https://openapp.fmy90.com/active/sign-in/do"

        payload = {
        "platformKey": "wxa587f7c3393d3d2f",
        "mini_scene": 1007
        }
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10).json()
            if response["code"] == 200:
                print("签到成功")
                return "签到成功"
            else:
                print("签到失败")
                return f"签到失败: {response}"
        except Exception as e:
            print(f"请求失败: {e}")
            return f"请求失败: {e}"
    
    def info(self):
        url = "https://openapp.fmy90.com/user/paid/base/info"
        params = {
        'platformKey': "wxa587f7c3393d3d2f",
        'mini_scene': "1007"
        }
        response = requests.get(url, params=params, headers=self.headers).json()

        if response["code"] == 200:
            money = response["data"]['unfreeze_balance']
            print(f"余额：{money}")
        else:
            print("查询余额失败")
            print(response)

if __name__ == '__main__':
    cookie = os.getenv("mnhs") or cookie
    if not cookie:
        print("请设置环境变量:mnhs")
        exit()
    cookies = cookie.split("@")
    print(f"一共获取到{len(cookies)}个账号")
    count = 1
    errors = []
    for cookie in cookies:
        print(f"\n--------开始第{count}个账号--------")
        t = random.randint(1, 300)
        print(f"随机等待{t}秒")
        time.sleep(t)
        main = yyf(cookie)
        error_msg = main.signin()
        if error_msg:
            errors.append(f"账号{count}{error_msg}")
        main.info()
        print(f"--------第{count}个账号执行完毕--------")
        count += 1
    
    if errors:
        send("蛮牛回收", "\n".join(errors))
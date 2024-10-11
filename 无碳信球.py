#   --------------------------------注释区--------------------------------
#   https://wt.api.5tan.com/api/找authorization,格式：bearer XXX
#   变量:wtxqck ，格式：多号@分割
#   token有效期不知道
#   corn: 每天跑一次就行 22 7 * * *
#   建议把请求头替换成自己的UA，填进ua里，不改也行挑选随机幸运儿封号
#   活动入口下面二选一
#   https://gitee.com/wry-fisher/push-notifications/blob/master/wtxqtgm-2.png
#   https://gitee.com/wry-fisher/push-notifications/blob/master/wtxqtgm.png
#   by fisher 2024.08.05
cookie =""
ua = ""
money=1 #满多少提现，默认1，最少1
import requests
import json
import os
import time
import random
def send(title,con):
    try:
        notify = __import__('notify')
        notify.send(title,con)
    except ImportError:
        print("通知模块加载失败")

class yyf():
    def __init__(self,cookie):
        self.key = ""
        self.token = cookie
        self.headers = {
        'User-Agent': ua or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090b19)XWEB/11159",
        'Content-Type': "application/json",
        'xweb_xhr': "1",
        'authorization': self.token,
        'sec-fetch-site': "cross-site",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://servicewechat.com/wx54c4768a6050a90e/211/page-frame.html",
        'accept-language': "zh-CN,zh;q=0.9"
        }

    def signin(self):
        url = "https://wt.api.5tan.com/api/signin/addSignIn"
        payload = {
        "platform": 1
        }
        response = requests.post(url, json=payload, headers=self.headers).json()
        if response["code"] == 200:
            print("签到成功")
        else:
            print(response)
            global SendMsg
            SendMsg+=f"账号{count}签到异常"
    
    def getmoney(self):
        url = "https://wt.api.5tan.com/api/user/getMoney"
        response = requests.get(url, headers=self.headers).json()
        if response["code"] == 200:
            print("余额：",response["data"]["money"])
            if response["data"]["money"]>=money:
                time.sleep(random.randint(1, 3))
                self.cash(money)
        else:
            print(response)
    
    def cash(self,money=1):
        url = "https://wt.api.5tan.com/api/logmoney/cash"
        payload = {
        "money": str(money),
        "platform": 1
        }
        headers = self.headers
        response = requests.post(url, json=payload, headers=headers).text
        print(response)
        global SendMsg
        SendMsg+=f"账号{count}提现{money}:{response}"
    
    def task(self):
        self.signin()
        time.sleep(random.randint(1, 3))
        self.getmoney()

if __name__ == '__main__':
    
    if not cookie:
        cookie = os.getenv("wtxqck")
        if not cookie:
            print("请设置环境变量:wtxqck")
            exit()
    cookies = cookie.split("@")
    print(f"一共获取到{len(cookies)}个账号")
    count = 1
    SendMsg = ""
    for cookie in cookies:
        print(f"\n--------开始第{count}个账号--------")
        t = random.randint(1, 300)
        print(f"随机等待{t}秒")
        time.sleep(t)
        main = yyf(cookie)
        main.task()
        print(f"--------第{count}个账号执行完毕--------")
        count += 1
    if SendMsg!="":
        send("wtxq",SendMsg)

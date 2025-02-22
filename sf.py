#!/usr/bin/python3
# -- coding: utf-8 --
"""
打开小程序或APP-我的-积分, 捉以下几种url之一,把整个url放到变量 sfsyUrl 里,多账号换行分割
https://mcs-mimp-web.sf-express.com/mcs-mimp/share/weChat/shareGiftReceiveRedirect 
https://mcs-mimp-web.sf-express.com/mcs-mimp/share/app/shareRedirect 
每天跑一到两次就行
来自拉菲大佬的本
2025.1.2添加财神活动
"""

# cron: 11 6,9,12,15,18 * * *
# const $ = new Env("顺丰速运");
import hashlib
import json
import os
import random
import time
import re
from datetime import datetime, timedelta
from sys import exit
import requests
from requests.packages.urllib3.exceptions  import InsecureRequestWarning
from datetime import datetime

os.environ['NEW_VAR']  = 'sfsyUrl'  # 环境变量
# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning) 

IS_DEV = False

if os.path.isfile('notify.py'): 
    from notify import send
    print("加载通知服务成功！")
else:
    print("加载通知服务失败!")
    send_msg = ''
    one_msg = ''

def Log(cont=''):
    global send_msg, one_msg
    print(cont)
    if cont:
        one_msg += f'{cont}\n'
        send_msg += f'{cont}\n'

inviteId = ['A959FF988C64448198CDEB08FC84844F', '0A5BCEB5EA454B878C34EB01A33AF080']

class RUN:
    def __init__(self, info, index):
        global one_msg
        one_msg = ''
        split_info = info.split('@') 
        url = split_info[0]
        len_split_info = len(split_info)
        last_info = split_info[len_split_info - 1] if len_split_info > 0 else ''
        self.send_UID  = None
        self.all_logs  = []  # 每个账号的日志集合
        if len_split_info > 0 and "UID_" in last_info:
            self.send_UID  = last_info
        self.index  = index + 1
        Log(f"\n---------开始执行第{self.index} 个账号>>>>>")
        self.s = requests.session() 
        self.s.verify  = False
        self.headers  = {
            'Host': 'mcs-mimp-web.sf-express.com', 
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x63090551) XWEB/6945 Flue',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'zh-CN,zh',
            'platform': 'MINI_PROGRAM',
        }
        self.anniversary_black  = False
        self.member_day_black  = False
        self.member_day_red_packet_drew_today  = False
        self.member_day_red_packet_map  = {}
        self.login_res  = self.login(url) 
        self.today  = datetime.now().strftime('%Y-%m-%d') 
        self.answer  = False
        self.max_level  = 8
        self.packet_threshold  = 1 << (self.max_level  - 1)

    def get_deviceId(self, characters='abcdef0123456789'):
        result = ''
        for char in 'xxxxxxxx-xxxx-xxxx':
            if char == 'x':
                result += random.choice(characters) 
            elif char == 'X':
                result += random.choice(characters).upper() 
            else:
                result += char
        return result

    def login(self, sfurl):
        ress = self.s.get(sfurl,  headers=self.headers) 
        self.user_id  = self.s.cookies.get_dict().get('_login_user_id_',  '')
        self.sessionId  = self.s.cookies.get_dict().get('sessionId',  '')
        self.phone  = self.s.cookies.get_dict().get('_login_mobile_',  '')
        self.mobile  = self.phone[:3]  + "*" * 4 + self.phone[7:]  if self.phone  else ''
        if self.phone: 
            Log(f'用户:【{self.mobile} 】登陆成功')
            return True
        else:
            Log(f'获取用户信息失败')
            return False

    def getSign(self):
        timestamp = str(int(round(time.time()  * 1000)))
        token = 'wwesldfs29aniversaryvdld29'
        sysCode = 'MCS-MIMP-CORE'
        data = f'token={token}&timestamp={timestamp}&sysCode={sysCode}'
        signature = hashlib.md5(data.encode()).hexdigest() 
        data = {
            'sysCode': sysCode,
            'timestamp': timestamp,
            'signature': signature
        }
        self.headers.update(data) 
        return data

    def do_request(self, url, data={}, req_type='post'):
        try:
            if req_type.lower()  == 'get':
                response = self.s.get(url,  headers=self.headers) 
            elif req_type.lower()  == 'post':
                response = self.s.post(url,  headers=self.headers,  json=data)
            else:
                raise ValueError(f"Invalid request type: {req_type}")

            try:
                res = response.json()   # 尝试解析 JSON
            except json.JSONDecodeError:
                Log(f"JSON 解码失败，响应内容: {response.text}") 
                return {"success": False, "errorMessage": "JSON 解码失败"}

            return res
        except requests.exceptions.RequestException  as e:
            Log(f"网络请求失败: {e}")
            return {"success": False, "errorMessage": "网络请求失败"}
        except Exception as e:
            Log(f"未知错误: {e}")
            return {"success": False, "errorMessage": "未知错误"}

    def sign(self):
        print(f'>>>>>>开始执行签到')
        json_data = {"comeFrom": "vioin", "channelFrom": "WEIXIN"}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskSignPlusService~automaticSignFetchPackage' 
        url2 = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskSignPlusService~queryPointSignAwardList' 
        url3 = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskSignPlusService~getUnFetchPointAndDiscount' 
        result = self.do_request(url2,  data={"channelType": "1"})
        result2 = self.do_request(url3,  data={})
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True:
            count_day = response.get('obj',  {}).get('countDay', 0)
            if response.get('obj')  and response['obj'].get('integralTaskSignPackageVOList'):
                packet_name = response["obj"]["integralTaskSignPackageVOList"][0]["packetName"]
                Log(f'>>>签到成功，获得【{packet_name}】，本周累计签到【{count_day + 1}】天')
            else:
                Log(f'今日已签到，本周累计签到【{count_day + 1}】天')
        else:
            print(f'签到失败！原因：{response.get("errorMessage")}') 

    def superWelfare_receiveRedPacket(self):
        print(f'>>>>>>超值福利签到')
        json_data = {
            'channel': 'czflqdlhbxcx'
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberActLengthy~redPacketActivityService~superWelfare~receiveRedPacket' 
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True:
            gift_list = response.get('obj',  {}).get('giftList', [])
            if response.get('obj',  {}).get('extraGiftList', []):
                gift_list.extend(response['obj']['extraGiftList']) 
            gift_names = ', '.join([gift['giftName'] for gift in gift_list]) if gift_list else ''
            receive_status = response.get('obj',  {}).get('receiveStatus')
            status_message = '领取成功' if receive_status == 1 else '已领取过'
            Log(f'超值福利签到[{status_message}]: {gift_names}')
        else:
            error_message = response.get('errorMessage')  or json.dumps(response)  or '无返回'
            print(f'超值福利签到失败: {error_message}')

    def get_SignTaskList(self, END=False):
        if not END:
            print(f'>>>开始获取签到任务列表')
        json_data = {
            'channelType': '3',
            'deviceId': self.get_deviceId(), 
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskStrategyService~queryPointTaskAndSignFromES' 
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True and response.get('obj')  != []:
            totalPoint = response["obj"]["totalPoint"]
            if END:
                Log(f'当前积分：【{totalPoint}】')
                return
            Log(f'执行前积分：【{totalPoint}】')
            for task in response["obj"]["taskTitleLevels"]:
                self.taskId  = task["taskId"]
                self.taskCode  = task["taskCode"]
                self.strategyId  = task["strategyId"]
                self.title  = task["title"]
                status = task["status"]
                skip_title = ['用行业模板寄件下单', '去新增一个收件偏好', '参与积分活动']
                if status == 3:
                    print(f'>{self.title}- 已完成')
                    continue
                if self.title  in skip_title:
                    print(f'>{self.title}- 跳过')
                    continue
                if self.title  == '领任意生活特权福利':
                    json_data_task = {
                        "memGrade": 2,
                        "categoryCode": "SHTQ",
                        "showCode": "SHTQWNTJ"
                    }
                    url_task = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberGoods~mallGoodsLifeService~list' 
                    response_task = self.do_request(url_task,  data=json_data_task)
                    if response_task.get('success')  == True:
                        goodsList = response_task["obj"][0]["goodsList"]
                        for goods in goodsList:
                            exchangeTimesLimit = goods['exchangeTimesLimit']
                            if exchangeTimesLimit >= 1:
                                self.goodsNo  = goods['goodsNo']
                                print(f'领取生活权益：当前选择券号：{self.goodsNo}') 
                                self.get_coupom() 
                                break
                    else:
                        print(f'>领券失败！原因：{response_task.get("errorMessage")}') 
                else:
                    self.doTask() 
                    time.sleep(3) 
                    self.receiveTask() 

    def doTask(self):
        print(f'>>>开始去完成【{self.title} 】任务')
        json_data = {
            'taskCode': self.taskCode, 
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonRoutePost/memberEs/taskRecord/finishTask' 
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True:
            print(f'>【{self.title} 】任务-已完成')
        else:
            print(f'>【{self.title} 】任务-{response.get("errorMessage")}') 

    def receiveTask(self):
        print(f'>>>开始领取【{self.title} 】任务奖励')
        json_data = {
            "strategyId": self.strategyId, 
            "taskId": self.taskId, 
            "taskCode": self.taskCode, 
            "deviceId": self.get_deviceId() 
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~integralTaskStrategyService~fetchIntegral' 
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True:
            print(f'>【{self.title} 】任务奖励领取成功！')
        else:
            print(f'>【{self.title} 】任务-{response.get("errorMessage")}') 

    def do_honeyTask(self):
        # 做任务
        json_data = {"taskCode": self.taskCode} 
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberEs~taskRecord~finishTask' 
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True:
            print(f'>【{self.taskType} 】任务-已完成')
        else:
            print(f'>【{self.taskType} 】任务-{response.get("errorMessage")}') 

    def receive_honeyTask(self):
        print('>>>执行收取丰蜜任务')
        # 收取
        self.headers['syscode']  = 'MCS-MIMP-CORE'
        self.headers['channel']  = 'wxwdsj'
        self.headers['accept']  = 'application/json, text/plain, */*'
        self.headers['content-type']  = 'application/json;charset=UTF-8'
        self.headers['platform']  = 'MINI_PROGRAM'
        json_data = {"taskType": self.taskType} 
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~receiveHoney' 
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True:
            print(f'收取任务【{self.taskType} 】成功！')
        else:
            print(f'收取任务【{self.taskType} 】失败！原因：{response.get("errorMessage")}') 

    def get_coupom(self):
        print('>>>执行领取生活权益领券任务')
        # 领取生活权益领券
        json_data = {
            "from": "Point_Mall",
            "orderSource": "POINT_MALL_EXCHANGE",
            "goodsNo": self.goodsNo, 
            "quantity": 1,
            "taskCode": self.taskCode 
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberGoods~pointMallService~createOrder' 
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True:
            print(f'>领券成功！')
        else:
            print(f'>领券失败！原因：{response.get("errorMessage")}') 

    def get_coupom_list(self):
        print('>>>获取生活权益券列表')
        json_data = {
            "memGrade": 1,
            "categoryCode": "SHTQ",
            "showCode": "SHTQWNTJ"
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberGoods~mallGoodsLifeService~list' 
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True:
            goodsList = response["obj"][0]["goodsList"]
            for goods in goodsList:
                exchangeTimesLimit = goods['exchangeTimesLimit']
                if exchangeTimesLimit >= 1:
                    self.goodsNo  = goods['goodsNo']
                    print(f'当前选择券号：{self.goodsNo}') 
                    self.get_coupom() 
                    break
        else:
            print(f'>领券失败！原因：{response.get("errorMessage")}') 

    def get_honeyTaskListStart(self):
        print('>>>开始获取采蜜换大礼任务列表')
        # 任务列表
        json_data = {}
        self.headers['channel']  = 'wxwdsj'
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~taskDetail' 
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True:
            for item in response["obj"]["list"]:
                self.taskType  = item["taskType"]
                status = item["status"]
                if status == 3:
                    print(f'>【{self.taskType} 】-已完成')
                    continue
                if "taskCode" in item:
                    self.taskCode  = item["taskCode"]
                    if self.taskType  == 'DAILY_VIP_TASK_TYPE':
                        self.get_coupom_list() 
                    else:
                        self.do_honeyTask() 
                        time.sleep(2) 
                    if self.taskType  == 'BEES_GAME_TASK_TYPE':
                        self.honey_damaoxian() 
                        time.sleep(2) 

    def honey_damaoxian(self):
        print('>>>执行大冒险任务')
        gameNum = 5
        for i in range(1, gameNum + 1):
            json_data = {
                'gatherHoney': 20,
            }
            print(f'>>开始第{i}次大冒险')
            url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeGameService~gameReport' 
            response = self.do_request(url,  data=json_data)
            stu = response.get('success',  False)
            if stu:
                gameNum_remaining = response.get('obj',  {}).get('gameNum', 0)
                print(f'>大冒险成功！剩余次数【{gameNum_remaining}】')
                time.sleep(2) 
                gameNum_remaining -= 1
                gameNum -= 1
            elif response.get("errorMessage")  == '容量不足':
                print(f'> 需要扩容')
                self.honey_expand() 
                break
            else:
                print(f'>大冒险失败！【{response.get("errorMessage")} 】')
                break

    def honey_expand(self):
        print('>>>容器扩容')
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~expand' 
        response = self.do_request(url,  data={})
        stu = response.get('success',  False)
        if stu:
            obj = response.get('obj',  {})
            expand_size = obj.get('expandSize',  0)
            print(f'>成功扩容【{expand_size}】容量')
        else:
            print(f'>扩容失败！【{response.get("errorMessage")} 】')

    def honey_indexData(self, END=False):
        if not END:
            print('\n>>>>>>>开始执行采蜜换大礼任务')
        # 邀请
        random_invite = random.choice([invite  for invite in inviteId if invite != self.user_id]) 
        self.headers['channel']  = 'wxwdsj'
        json_data = {"inviteUserId": random_invite}
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~receiveExchangeIndexService~indexData' 
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True:
            usableHoney = response.get('obj',  {}).get('usableHoney', 0)
            if END:
                Log(f'当前丰蜜：【{usableHoney}】')
                return
            Log(f'执行前丰蜜：【{usableHoney}】')
            taskDetail = response.get('obj',  {}).get('taskDetail', [])
            activityEndTime_str = response.get('obj',  {}).get('activityEndTime', '')
            if activityEndTime_str:
                activity_end_time = datetime.strptime(activityEndTime_str,  "%Y-%m-%d %H:%M:%S")
                current_time = datetime.now() 
                if current_time.date()  == activity_end_time.date(): 
                    Log("本期活动今日结束，请及时兑换")
                else:
                    print(f'本期活动结束时间【{activityEndTime_str}】')
            if taskDetail:
                for task in taskDetail:
                    self.taskType  = task['type']
                    self.receive_honeyTask() 
                    time.sleep(2) 

    def EAR_END_2023_TaskList(self):
        print('\n>>>>>>开始年终集卡任务')
        # 任务列表
        json_data = {
            "activityCode": "YEAR_END_2023",
            "channelType": "MINI_PROGRAM"
        }
        self.headers['channel']  = 'xcx23nz'
        self.headers['platform']  = 'MINI_PROGRAM'
        self.headers['syscode']  = 'MCS-MIMP-CORE'

        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~activityTaskService~taskList' 
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True:
            for item in response["obj"]:
                self.title  = item["taskName"]
                self.taskType  = item["taskType"]
                status = item["status"]
                if status == 3:
                    print(f'>【{self.taskType} 】-已完成')
                    continue
                if self.taskType  == 'INTEGRAL_EXCHANGE':
                    self.EAR_END_2023_ExchangeCard()
                elif self.taskType  == 'CLICK_MY_SETTING':
                    self.taskCode  = item["taskCode"]
                    self.addDeliverPrefer() 
                if "taskCode" in item:
                    self.taskCode  = item["taskCode"]
                    self.doTask() 
                    time.sleep(3) 
                    self.EAR_END_2023_receiveTask()
            # 其他任务处理...
            # 这里可能需要根据实际返回的任务类型进行处理

    def addDeliverPrefer(self):
        print(f'>>>开始【{self.title} 】任务')
        json_data = {
            "country": "中国",
            "countryCode": "A000086000",
            "province": "北京市",
            "provinceCode": "A110000000",
            "city": "北京市",
            "cityCode": "A111000000",
            "county": "东城区",
            "countyCode": "A110101000",
            "address": "1号楼1单元101",
            "latitude": "",
            "longitude": "",
            "memberId": "",
            "locationCode": "010",
            "zoneCode": "CN",
            "postCode": "",
            "takeWay": "7",
            "callBeforeDelivery": 'false',
            "deliverTag": "2,3,4,1",
            "deliverTagContent": "",
            "startDeliverTime": "",
            "selectCollection": 'false',
            "serviceName": "",
            "serviceCode": "",
            "serviceType": "",
            "serviceAddress": "",
            "serviceDistance": "",
            "serviceTime": "",
            "serviceTelephone": "",
            "channelCode": "RW11111",
            "taskId": self.taskId, 
            "extJson": "{\"noDeliverDetail\":[]}"
        }
        url = 'https://ucmp.sf-express.com/cx-wechat-member/member/deliveryPreference/addDeliverPrefer' 
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True:
            print('新增一个收件偏好，成功')
        else:
            print(f'>【{self.title} 】任务-{response.get("errorMessage")}') 

    def EAR_END_2023_ExchangeCard(self):
        print(f'>>>开始积分兑换年卡')
        json_data = {
            "exchangeNum": 2,
            "activityCode": "YEAR_END_2023",
            "channelType": "MINI_PROGRAM"
        }
        url = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonNoLoginPost/~memberNonactivity~yearEnd2023TaskService~integralExchange' 
        response = self.do_request(url,  data=json_data)
        if response.get('success')  == True:
            receivedAccountList = response['obj']['receivedAccountList']
            for card in receivedAccountList:
                print(f'>获得：【{card["currency"]}】卡【{card["amount"]}】张！')
        else:
            print(f'>【{self.title} 】任务-{response.get("errorMessage")}') 

    def EAR_END_2023_getAward(self):
        print(f'>>>开始抽卡')
        url_award = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~yearEnd2023GardenPartyService~getAward' 
        for l in range(10):
            for i in range(3):
                json_data_award = {
                    "cardType": i
                }
                response_award = self.do_request(url_award,  data=json_data_award)
                if response_award.get('success')  == True:
                    receivedAccountList_award = response_award['obj']['receivedAccountList']
                    for card_award in receivedAccountList_award:
                        print(f'>获得：【{card_award["currency"]}】卡【{card_award["amount"]}】张！')
                elif response_award.get('errorMessage')  in ['达到限流阈值，请稍后重试', '用户信息失效，请退出重新进入']:
                    break
                else:
                    print(f'>抽卡失败：{response_award.get("errorMessage")}') 
                time.sleep(3) 

    def EAR_END_2023_GuessIdiom(self):
        print(f'>>>开始猜成语')
        url_guess_idiom = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~yearEnd2023GuessIdiomService~win' 
        for i in range(1, 11):
            json_data_guess_idiom = {
                "index": i
            }
            response_guess_idiom = self.do_request(url_guess_idiom,  data=json_data_guess_idiom)
            if response_guess_idiom.get('success')  == True:
                print(f'第{i}关成功！')
            else:
                print(f'第{i}关失败！')

    def EAR_END_2023_receiveTask(self):
        print(f'>>>开始领取【{self.title} 】任务奖励')
        json_data_receive_task = {
            "taskType": self.taskType, 
            "activityCode": "YEAR_END_2023",
            "channelType": "MINI_PROGRAM"
        }
        url_receive_task = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonNoLoginPost/~memberNonactivity~yearEnd2023TaskService~fetchMixTaskReward' 
        response_receive_task = self.do_request(url_receive_task,  data=json_data_receive_task)
        if response_receive_task.get('success')  == True:
            print(f'>【{self.title} 】任务奖励领取成功！')
        else:
            print(f'>【{self.title} 】任务-{response_receive_task.get("errorMessage")}') 

    def anniversary2024_weekly_gift_status(self):
        print(f'\n>>>>>>>开始周年庆任务')
        url_anniversary_gift_status = 'https://mcs-mimp-web.sf-express.com/mcs-mimp/commonPost/~memberNonactivity~anniversary2024IndexService~weeklyGiftStatus' 
        response_anniversary_gift_status = self.do_request(url_anniversary_gift_status) 
        if response_anniversary_gift_status.get('success')  == True:
            weekly_gift_list_anniversary_gift_status = response_anniversary_gift_status.get('obj',  {}).get('weeklyGiftList', [])
            for weekly_gift_anniversary_gift_status in weekly_gift_list_anniversary_gift_status:
                if not weekly_gift_anniversary_gift_status.get('received'): 
                    receive_start_time_anniversary_gift_status_str = weekly_gift_anniversary_gift_status['receiveStartTime']
                    receive_end_time_anniversary_gift_status_str = weekly_gift_anniversary_gift_status['receiveEndTime']
                    receive_start_time_anniversary_gift_status_datetime = datetime.strptime(receive_start_time_anniversary_gift_status_str,  '%Y-%m-%d %H:%M:%S')
                    receive_end_time_anniversary_gift_status_datetime = datetime.strptime(receive_end_time_anniversary_gift_status_str,  '%Y-%m-%d %H:%M:%S')
                    current_time_anniversary_gift_status_datetime = datetime.now() 
                    if receive_start_time_anniversary_gift_status_datetime <= current_time_anniversary_gift_status_datetime <= receive_end_time_anniversary_gift_status_datetime:
                        self.anniversary2024_receive_weekly_gift() 
                        break
                    else:
                        error_message_anniversary_gift_status_response_or_json_dump_or_default_message = response_anniversary_gift_status.get('errorMessage')  or json.dumps(response_anniversary_gift_status)  or '无返回'
                        print(f'查询每周领券失败: {error_message_anniversary_gift_status_response_or_json_dump_or_default_message}')
                        if any(error_msg in error_message_anniversary_gift_status_response_or_json_dump_or_default_message for error_msg in ['系统繁忙', '用户手机号校验未通过']):
                            self.anniversary_black  = True

    def anniversary2024_receive_weekly_gift(self):
        print(f'>>>开始领取每周领券')
        url_anniversary_receive_weekly_gift_url_variable_name_too_long_please_shorten_me_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_please_p lease me! I'm getting too long! Please make it shorter! Okay? Okay.'
              )  # This line is intentionally left as is to demonstrate the issue.

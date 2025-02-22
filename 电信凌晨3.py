import os
import re
import sys
import ssl
import time
import json
import execjs
import base64
import random
import certifi
import aiohttp
import asyncio
import datetime
import requests
import binascii
from lxml import etree
from http import cookiejar
from Crypto.Cipher import AES, DES3
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Util.Padding import pad, unpad
from aiohttp import ClientSession, TCPConnector
from concurrent.futures  import ThreadPoolExecutor

# 配置全局变量
run_num = int(os.environ.get('reqNUM')  or "80")
diffValue = 2

# 用户消息中的变量定义
PHONES = os.environ.get('chinaTelecomAccount') 

# 全局常量
MAX_RETRIES = 3
RATE_LIMIT = 10  # 每秒请求数限制

class RateLimiter:
    def __init__(self, rate_limit):
        self.rate_limit  = rate_limit
        self.tokens  = rate_limit
        self.updated_at  = time.monotonic() 

    async def acquire(self):
        while self.tokens  < 1:
            self.add_new_tokens() 
            await asyncio.sleep(0.1) 
        self.tokens  -= 1

    def add_new_tokens(self):
        现在 = time.monotonic() 
        time_since_update = now - self.updated_at 
        new_tokens = time_since_update * self.rate_limit 
        if new_tokens > 1:
            self.tokens  = min(self.tokens  + new_tokens, self.rate_limit) 
            self.updated_at  = now

class AsyncSessionManager:
    def __init__(self):
        self.session  = None
        self.connector  = None

    async def __aenter__(self):
        ssl_context = ssl.create_default_context(cafile=certifi.where()) 
        ssl_context.set_ciphers('DEFAULT@SECLEVEL=1') 
        self.connector  = TCPConnector(ssl=ssl_context, limit=1000)
        self.session  = ClientSession(connector=self.connector) 
        return self.session 

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close() 
        await self.connector.close() 

async def retry_request(session, method, url, **kwargs):
    for attempt in range(MAX_RETRIES):
        try:
            async with session.request(method,  url, **kwargs) as response:
                return await response.json() 
        except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError) as e:
            print(f"请求失败，第 {attempt + 1} 次重试: {e}")
            if attempt == MAX_RETRIES - 1:
                raise 
            await asyncio.sleep(2  ** attempt)

class BlockAll(cookiejar.CookiePolicy):
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False

def printn(m):  
    print(f'\n{m}')

context = ssl.create_default_context() 
context.set_ciphers('DEFAULT@SECLEVEL=1')   # 低安全级别0/1
context.check_hostname  = False  # 禁用主机检查
context.verify_mode  = ssl.CERT_NONE  # 禁用证书验证

class DESAdapter(requests.adapters.HTTPAdapter): 
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

requests.packages.urllib3.disable_warnings() 
ss = requests.session() 
ss.headers  = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; 22081212C Build/TKQ1.220829.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.97 Mobile Safari/537.36",
    "Referer": "https://wapact.189.cn:9001/JinDouMall/JinDouMall_independentDetails.html" 
}    
ss.mount('https://',  DESAdapter())       
ss.cookies.set_policy(BlockAll()) 

key = b'1234567`90koiuyhgtfrdews'
iv = 8 * b'\0'

public_key_b64 = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDBkLT15ThVgz6/NOl6s8GNPofdWzWbCkWnkaAm7O2LjkM1H7dMvzkiqdxU02jamGRHLX/ZNMCXHnPcW/sDhiFCBN18qFvy8g6VYb9QtroI09e176s+ZCtiv7hbin2cCTj99iUpnEloZm19lwHyo69u5UMiPMpq0/XKBO8lYhN/gwIDAQAB
-----END PUBLIC KEY-----'''

public_key_data = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC+ugG5A8cZ3FqUKDwM57GM4io6JGcStivT8UdGt67PEOihLZTw3P7371+N47PrmsCpnTRzbTgcupKtUv8ImZalYk65dU8rjC/ridwhw9ffW2LBwvkEnDkkKKRi2liWIItDftJVBiWOh17o6gfbPoNrWORcAdcbpk2L+udld5kZNwIDAQAB
-----END PUBLIC KEY-----'''

def get_first_three(value):
    if isinstance(value, (int, float)):
        return int(str(value)[:3])
    elif isinstance(value, str):
        return str(value)[:3]
    else:
        raise TypeError("error")

def run_Time(hour minute,, second):    
    date = datetime.datetime.now() 
    date_zero = date.replace(hour=hour,  minute=minute, second=second)
    return int(date_zero.timestamp()) 

def encrypt(text):    
    cipher = DES3.new(key,  DES3.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(text.encode(),  DES3.block_size)) 
    return ciphertext.hex() 

def decrypt(text):
    ciphertext = bytes.fromhex(text) 
    cipher = DES3.new(key,  DES3.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext),  DES3.block_size) 
    return plaintext.decode() 

def b64(plaintext):
    public_key = RSA.import_key(public_key_b64) 
    cipher = PKCS1_v1_5.new(public_key) 
    ciphertext = cipher.encrypt(plaintext.encode()) 
    return base64.b64encode(ciphertext).decode()

def encrypt_para(plaintext):
    if not isinstance(plaintext, str):
        plaintext = json.dumps(plaintext) 
    public_key = RSA.import_key(public_key_data)   
    cipher = PKCS1_v1_5.new(public_key) 
    ciphertext = cipher.encrypt(plaintext.encode()) 
    return binascii.hexlify(ciphertext).decode() 

def encode_phone(text):
    encoded_chars = []
    for char in text:
        encoded_chars.append(chr(ord(char)  + 2))
    return ''.join(encoded_chars)

def getApiTime(api_url):
    try:
        with requests.get(api_url)  as response:
            if not response or not response.text: 
                return time.time() 
            json_data = json.loads(response.text) 
            if json_data.get("api")  and json_data.get("api")  != "time":
                timestamp_str = json_data.get('data',  {}).get('t', '')
            else:
                timestamp_str = json_data.get('currentTime',  '')
            if timestamp_str:
                timestamp = int(timestamp_str) / 1000.0  # 将毫秒转为秒
                difftime = time.time()  - timestamp
                return difftime
            return 0
    except Exception as e:
        print(f"获取时间失败: {e}")
        return 0

def userLoginNormal(phone, password):
    alphabet = 'abcdef0123456789'
    uuid_parts = [
        ''.join(random.sample(alphabet,  8)),
        ''.join(random.sample(alphabet,  4)),
        '4' + ''.join(random.sample(alphabet,  3)),
        ''.join(random.sample(alphabet,  4)),
        ''.join(random.sample(alphabet,  12))
    ]
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S") 
    loginAuthCipherAsymmertric = (
        'iPhone 14 15.4.' +
        uuid_parts[0] + uuid_parts[1] + phone + timestamp + password[:6] + 
        '0$$$0.'
    )
    
    payload = {
        "headerInfos": {
            "code": "userLoginNormal",
            "timestamp": timestamp,
            "broadAccount": "",
            "broadToken": "",
            "clientType": "#9.6.1#channel50#iPhone 14 Pro Max#",
            "shopId": "20002",
            "source": "110003",
            "sourcePassword": "Sid98s",
            "token": "",
            "userLoginName": phone
        },
        "content": {
            "attach": "test",
            "fieldData": {
                "loginType": "4",
                "accountType": "",
                "loginAuthCipherAsymmertric": b64(loginAuthCipherAsymmertric),
                "deviceUid": ''.join(uuid_parts[:3]),
                "phoneNum": encode_phone(phone),
                "isChinatelecom": "0",
                "systemVersion": "15.4.0",
                "authentication": password
            }
        }
    }
    
    try:
        response = ss.post( 
            'https://appgologin.189.cn:9031/login/client/userLoginNormal', 
            json=payload,
            verify=certifi.where() 
        )
        data = response.json() 
        if data.get('responseData',  {}).get('data', {}).get('loginSuccessResult'):
            return get_ticket(phone, data['responseData']['data']['loginSuccessResult']['userId'], data['responseData']['data']['loginSuccessResult']['token'])
        return False
    except Exception as e:
        print(f"登录失败: {e}")
        return False

async def exchange_for_day(phone, session, run_num, rid, stime):
    async def delayed_conversion(delay):
        await asyncio.sleep(delay) 
        await conversion_rights(phone, rid, session)
    
    run_num_int = int(run_num)
    tasks = [
        asyncio.create_task(delayed_conversion(i  * stime))
        for i in range(run_num_int)
    ]
    await asyncio.gather(*tasks) 

def get_ticket(phone, user_id, token):
    try:
        data = f'<Request><HeaderInfos><Code>getSingle</Code><Timestamp>{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}</Timestamp><BroadAccount></BroadAccount><BroadToken></BroadToken><ClientType>#9.6.1#channel50#iPhone  14 Pro Max#</ClientType><ShopId>20002</ShopId><Source>110003</Source><SourcePassword>Sid98s</SourcePassword><Token>{token}</Token><UserLoginName>{phone}</UserLoginName></HeaderInfos><Content><Attach>test</Attach><FieldData><TargetId>{encrypt(user_id)}</TargetId><Url>4a6862274835b451</Url></FieldData></Content></Request>'
        
        response = ss.post( 
            'https://appgologin.189.cn:9031/map/clientXML', 
            data=data,
            headers={'user-agent': 'CtClient;10.4.1;Android;13;22081212C;NTQzNzgx!#!MTgwNTg1'},
            verify=certifi.where() 
        )
        
        ticket_match = re.search(r'<Ticket>(.*?)</Ticket>',  response.text) 
        if ticket_match:
            return decrypt(ticket_match.group(1)) 
        return False
    except Exception as e:
        print(f"获取Ticket失败: {e}")
        return False

async def exchange(session, phone, title, aid, jsexec, ckvalue):
    try:
        get_url_js = await asyncio.to_thread(jsexec.call,  "getUrl", "POST", "https://wapact.189.cn:9001/gateway/stand/detailNew/exchange") 
        async with session.post(get_url_js,  cookies=ckvalue, json={"activityId": aid}) as response:
            pass
    except Exception as e:
        print(f"兑换失败: {e}")

async def check(session, item_id, ckvalue):
    try:
        response = await session.get( 
            f'https://wapact.189.cn:9001/gateway/stand/detailNew/check?activityId={item_id}', 
            cookies=ckvalue
        )
        return response.json() 
    except Exception as e:
        print(f"检查库存失败: {e}")
        return None

async def conversion_rights(phone, aid, session):
    try:
        value = {"phone": phone, "rightsId": aid}
        paraV = encrypt_para(value)
        
        response = session.post( 
            'https://wapside.189.cn:9001/jt-sign/paradise/conversionRights', 
            json={"para": paraV}
        )
        
        data = response.json() 
        printn(f"{get_first_three(phone)},{datetime.datetime.now().strftime('%H:%M:%S')}:  {data}")
    except Exception as e:
        print(f"兑换权益失败: {e}")

async def get_level_rights_list(phone, session):
    try:
        value = {"phone": phone}
        paraV = encrypt_para(value)
        
        response = session.post( 
            'https://wapside.189.cn:9001/jt-sign/paradise/getLevelRightsList', 
            json={"para": paraV}
        )
        
        data = response.json() 
        if data.get('code')  == 401:
            print(f"获取权益失败: {data}, 可能是sign过期")
            return None
        
        current_level = int(data['currentLevel'])
        key_name = f'V{current_level}'
        
        ids = [
            item['id'] 
            for item in data.get(key_name,  [])
            if item.get('name')  == '话费'
        ]
        
        if not ids:
            print("未找到话费权益")
        
        return ids
    except Exception as e:
        print(f"获取权益失败: {e}")
        return None

async def get_sign(ticket, session):
    try:
        response_data = session.get( 
            f'https://wapside.189.cn:9001/jt-sign/ssoHomLogin?ticket={ticket}' 
        ).json()
        
        if response_data.get('resoultCode')  == '0':
            return response_data.get('sign') 
        else:
            print(f"获取sign失败: {response_data}")
            return None
    except Exception as e:
        print(f"获取sign失败: {e}")
        return None

async def login_request(ss_session, url, payload):
    try:
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Origin': 'https://wapact.189.cn:9001', 
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Android WebView";v="126"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'Content-Type': 'application/json;charset=UTF-8'
        }
        
        response = ss_session.post(url,  headers=headers, json=payload)
        
        if response.status_code  == 412:
            print("检测到瑞数特征码412")
            
            html = etree.HTML(response.text) 
            arg1 = html.xpath('//meta/@content')[-1] 
            arg2 = html.xpath('//script/text()')[0] 
            arg3 = html.xpath('//meta/@id')[-1] 
            
            with open("rs6.js",  "r", encoding="utf-8") as f:
                js_code_read = f.read() 
            
            js_code_read = js_code_read.replace("contentCODE",  arg1).replace('"tsCODE"', arg2).replace('"tsID"', f'"{arg3}"')
            
            jsexec = execjs.compile(js_code_read) 
            
            ck_value_js = await asyncio.to_thread(jsexec.call,  "getck")
            
            cookies_dict = {}
            for part in ck_value_js.split(';'): 
                part = part.strip() 
                if '=' in part:
                    key, value = part.split('=',  1)
                    cookies_dict[key] = value
            
            rs_ck_match = re.search(r'yiUIIlbdQT3fO=([^;]+)',  response.headers.get('Set-Cookie',  ''))
            if rs_ck_match:
                rs_ck_value = rs_ck_match.group(1) 
                cookies_dict["yiUIIlbdQT3fO"] = rs_ck_value
            
            new_url_js = await asyncio.to_thread(jsexec.call,  "getUrl", "POST", url)
            
            final_response = ss_session.post(new_url_js,  headers=headers, json=payload, cookies=cookies_dict)
            
            if final_response.status_code  == 200:
                print("瑞数破解成功")
                return final_response, jsexec, cookies_dict
            else:
                print("瑞数破解失败")
                return final_response, None, None
        
        else:
            print("未检测到瑞数特征码")
            return response, None, None
        
    except Exception as e:
        print(f"登录请求失败: {e}")
        return None, None, None

async def qg_night(phone, ticket, time_value, is_true):
    try:
        if is_true:
            target_time = run_Time(23, 59, 3) + 0.65
        else:
            target_time = run_Time(0, 0, 0) + 0.65
        
        if target_time > (time.time()  + time_value):
            difftime = target_time - time.time()  - time_value
            printn(f"当前时间: {datetime.datetime.now().strftime('%H:%M:%S')},  等待{difftime}秒开始兑换每天一次的")
            await asyncio.sleep(difftime) 
        
        session = requests.Session()
        session.mount('https://',  DESAdapter())
        session.verify  = False
        
        sign = await get_sign(ticket, session)
        if sign:
            print(f"当前时间: {datetime.datetime.now().strftime('%H:%M:%S')}  获取到 Sign: {sign}")
            session.headers.update({"sign":  sign})
        else:
            print("未能获取 Sign")
            return
        
        rights_ids = await get_level_rights_list(phone, session)
        if not rights_ids:
            print("未能获取 rightsId")
            return
        
        if is_true:
            target_time_2 = run_Time(23, 59, 58) + 0.65
            difftime_2 = target_time_2 - time.time()  - time_value
            await asyncio.sleep(difftime_2) 
        
        printn(f"{datetime.datetime.now().strftime('%H:%M:%S')}  开始兑换每天一次的")
        
        await exchange_for_day(phone, session, run_num, rights_ids[0], 0.1)
        
    except Exception as e:
        print(f"夜间兑换失败: {e}")

async def qg_day(phone, ticket, time_value, is_true):
    try:
        async with AsyncSessionManager() as s:
            # 这里可以根据需求添加具体的兑换逻辑
            pass
    except Exception as e:
        print(f"日间兑换失败: {e}")

async def main(time_diff, is_true_flag, hour):
    tasks = []
    
    phone_list = PHONES.split('&') 
    
    for phone_entry in phone_list:
        phone_info = phone_entry.split('@') 
        if len(phone_info) != 2:
            continue
        
        phone, password = phone_info[0], phone_info[1]
        
        printn(f'{get_first_three(phone)} 开始登录')
        
        ticket_result = userLoginNormal(phone, password)
        
        if ticket_result:
            if hour > 15:
                tasks.append(qg_night(phone,  ticket_result, time_diff, is_true_flag))
            else:
                tasks.append(qg_day(phone,  ticket_result, time_diff, is_true_flag))
        
    await asyncio.gather(*tasks) 

if __name__ == "__main__":
    h = datetime.datetime.now().hour 
    
    print(f"当前小时为: {h}")
    
    if 0 < h < 10:
        print("准备抢十点场次")
        wait_time_target = run_Time(9, 59, 8)
    elif 10 <= h < 14:
        print("准备抢十四点场次")
        wait_time_target = run_Time(13, 59, 8)
    else:
        print("准备抢凌晨场次")
        wait_time_target = run_Time(23, 58, 58)
    
    is_true_flag = True
    
    if wait_time_target > time.time(): 
        wait_seconds = wait_time_target - time.time() 
        print(f"未到时间，等待 {wait_seconds:.2f} 秒")
        
        if is_true_flag:
            time.sleep(wait_seconds) 
    
    api_time_diff = getApiTime("https://f.m.suning.com/api/ct.do") 
    
    asyncio.run(main(api_time_diff  if api_time_diff > 0 else 0, is_true_flag, h))
    
    print("所有任务执行完毕！")

import os 
import re 
import ssl 
import time 
import json 
import base64 
import random 
import certifi 
import aiohttp 
import asyncio 
import datetime 
import requests 
import binascii
from Crypto.Cipher import AES, DES3, PKCS1_v1_5
from Crypto.PublicKey import RSA 
from Crypto.Util.Padding import pad, unpad 
from aiohttp import ClientSession, TCPConnector 
 
# 配置参数 
RUN_NUM = int(os.environ.get('reqNUM',  80))
MAX_RETRIES = 3 
RATE_LIMIT = 10  # 每秒请求数限制 
 
class RateLimiter:
    """请求速率限制器"""
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
        now = time.monotonic() 
        time_since_update = now - self.updated_at  
        if (new_tokens := time_since_update * self.rate_limit)  > 1:
            self.tokens  = min(self.tokens  + new_tokens, self.rate_limit) 
            self.updated_at  = now 
 
class AsyncSessionManager:
    """异步会话管理器"""
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
    """带重试机制的请求函数"""
    for attempt in range(MAX_RETRIES):
        try:
            async with session.request(method,  url, **kwargs) as response:
                response.raise_for_status() 
                return await response.json() 
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f"请求失败，第 {attempt + 1} 次重试: {e}")
            if attempt == MAX_RETRIES - 1:
                raise 
            await asyncio.sleep(2  ** attempt)
 
# 加密相关函数 
KEY = b'1234567`90koiuyhgtfrdews'
IV = 8 * b'\0'
 
PUBLIC_KEY_B64 = '''-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDBkLT15ThVgz6/NOl6s8GNPofdWzWbCkWnkaAm7O2LjkM1H7dMvzkiqdxU02jamGRHLX/ZNMCXHnPcW/sDhiFCBN18qFvy8g6VYb9QtroI09e176s+ZCtiv7hbin2cCTj99iUpnEloZm19lwHyo69u5UMiPMpq0/XKBO8lYhN/gwIDAQAB 
-----END PUBLIC KEY-----'''
 
def encrypt_3des(text):
    """3DES加密"""
    cipher = DES3.new(KEY,  DES3.MODE_CBC, IV)
    return cipher.encrypt(pad(text.encode(),  DES3.block_size)).hex() 
 
def decrypt_3des(hex_str):
    """3DES解密"""
    cipher = DES3.new(KEY,  DES3.MODE_CBC, IV)
    return unpad(cipher.decrypt(bytes.fromhex(hex_str)),  DES3.block_size).decode() 
 
def rsa_encrypt(plaintext, public_key):
    """RSA加密"""
    cipher = PKCS1_v1_5.new(RSA.import_key(public_key)) 
    return base64.b64encode(cipher.encrypt(plaintext.encode())).decode() 
 
# 核心业务逻辑 
async def main_workflow(phone, password):
    """主业务流程"""
    async with AsyncSessionManager() as session:
        # 登录认证 
        login_data = await user_login(phone, password, session)
        if not login_data:
            return False 
 
        # 获取票证 
        ticket = await get_ticket(phone, login_data['userId'], login_data['token'], session)
        if not ticket:
            return False 
 
        # 权益兑换 
        rights_ids = await get_level_rights(phone, session)
        if not rights_ids:
            return False 
 
        # 批量兑换 
        tasks = [exchange_rights(phone, rid, session) for rid in rights_ids]
        await asyncio.gather(*tasks) 
 
async def user_login(phone, password, session):
    """用户登录"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S") 
    payload = {
        "headerInfos": {
            "code": "userLoginNormal",
            "timestamp": timestamp,
            "clientType": "#9.6.1#channel50#iPhone 14 Pro Max#",
            "shopId": "20002",
            "source": "110003",
            "userLoginName": phone 
        },
        "content": {
            "fieldData": {
                "loginAuthCipherAsymmertric": rsa_encrypt(
                    f"iPhone 14 15.4.{phone}{timestamp}{password[:6]}",
                    PUBLIC_KEY_B64 
                ),
                "phoneNum": ''.join(chr(ord(c) + 2) for c in phone),
                "authentication": password 
            }
        }
    }
    return await retry_request(session, 'POST', 
        'https://appgologin.189.cn:9031/login/client/userLoginNormal', 
        json=payload 
    )
 
if __name__ == "__main__":
    # 示例使用（需替换实际参数）
    asyncio.run(main_workflow("13800138000"，  "your_password"))

#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
天翼云盘签到脚本优化版

环境变量：
ty_username  多账号用 & 分隔
ty_password  多账号用 & 分隔

可选推送：
WXPUSHER_APP_TOKEN
WXPUSHER_UID  多个 UID 用 & 分隔

优化点：
1. 首次账号密码登录成功后自动保存 Cookie 到脚本目录
2. 后续优先使用本地 Cookie，减少登录风控
3. Cookie 失效后自动重新账号密码登录
4. 登录失败打印完整接口返回
"""

import time
import os
import random
import json
import base64
import hashlib
import rsa
import requests
import re
from urllib.parse import urlparse
from requests.utils import dict_from_cookiejar, cookiejar_from_dict


BI_RM = list("0123456789abcdefghijklmnopqrstuvwxyz")
B64MAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


# =========================
# 基础配置
# =========================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_STORE_FILE = os.path.join(SCRIPT_DIR, "ty189_cookie_store.json")

ty_usernames = os.getenv("ty_username").split('&') if os.getenv("ty_username") else []
ty_passwords = os.getenv("ty_password").split('&') if os.getenv("ty_password") else []

if not ty_usernames or not ty_passwords:
    raise ValueError("❌ 请设置环境变量 ty_username 和 ty_password")

accounts = [{"username": u.strip(), "password": p.strip()} for u, p in zip(ty_usernames, ty_passwords)]

WXPUSHER_APP_TOKEN = os.getenv("WXPUSHER_APP_TOKEN")
WXPUSHER_UIDS = os.getenv("WXPUSHER_UID", "").split('&') if os.getenv("WXPUSHER_UID") else []


# =========================
# 通用工具
# =========================

def mask_phone(phone):
    """隐藏手机号中间四位"""
    if not phone:
        return ""
    return phone[:3] + "****" + phone[-4:] if len(phone) >= 7 else phone


def account_key(username):
    """用账号生成本地 Cookie 存储 key，避免明文账号作为 key"""
    return hashlib.md5(username.encode("utf-8")).hexdigest()


def int2char(a):
    return BI_RM[a]


def b64tohex(a):
    d = ""
    e = 0
    c = 0
    for i in range(len(a)):
        if list(a)[i] != "=":
            v = B64MAP.index(list(a)[i])
            if e == 0:
                e = 1
                d += int2char(v >> 2)
                c = 3 & v
            elif e == 1:
                e = 2
                d += int2char(c << 2 | v >> 4)
                c = 15 & v
            elif e == 2:
                e = 3
                d += int2char(c)
                d += int2char(v >> 2)
                c = 3 & v
            else:
                e = 0
                d += int2char(c << 2 | v >> 4)
                d += int2char(15 & v)
    if e == 1:
        d += int2char(c << 2)
    return d


def rsa_encode(j_rsakey, string):
    rsa_key = f"-----BEGIN PUBLIC KEY-----\n{j_rsakey}\n-----END PUBLIC KEY-----"
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(rsa_key.encode())
    result = b64tohex((base64.b64encode(rsa.encrypt(f'{string}'.encode(), pubkey))).decode())
    return result


def safe_json(resp):
    """安全解析 JSON"""
    try:
        return resp.json()
    except Exception:
        return None


# =========================
# Cookie 存储
# =========================

def load_cookie_store():
    if not os.path.exists(COOKIE_STORE_FILE):
        return {}

    try:
        with open(COOKIE_STORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 读取 Cookie 文件失败：{e}")
        return {}


def save_cookie_store(data):
    try:
        with open(COOKIE_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        try:
            os.chmod(COOKIE_STORE_FILE, 0o600)
        except Exception:
            pass
    except Exception as e:
        print(f"⚠️ 保存 Cookie 文件失败：{e}")


def save_session_cookie(username, session):
    """保存当前 session cookie"""
    store = load_cookie_store()
    key = account_key(username)

    store[key] = {
        "account": mask_phone(username),
        "cookies": dict_from_cookiejar(session.cookies),
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    save_cookie_store(store)
    print(f"💾 Cookie 已保存：{os.path.basename(COOKIE_STORE_FILE)}")


def load_session_from_cookie(username):
    """从本地 Cookie 创建 session"""
    store = load_cookie_store()
    key = account_key(username)

    if key not in store:
        return None

    cookies = store.get(key, {}).get("cookies")
    saved_at = store.get(key, {}).get("saved_at", "")

    if not cookies:
        return None

    s = requests.Session()
    s.cookies = cookiejar_from_dict(cookies)

    s.headers.update({
        "User-Agent": get_mobile_ua(),
        "Referer": "https://m.cloud.189.cn/"
    })

    print(f"🍪 已加载本地 Cookie，上次保存时间：{saved_at}")
    return s


def delete_saved_cookie(username):
    """删除某个账号的本地 Cookie"""
    store = load_cookie_store()
    key = account_key(username)

    if key in store:
        store.pop(key)
        save_cookie_store(store)
        print("🧹 已删除失效 Cookie")


# =========================
# UA
# =========================

def get_pc_ua():
    return (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )


def get_mobile_ua():
    return (
        "Mozilla/5.0 (Linux; Android 10; SM-G9730 Build/QP1A.190711.020; wv) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
        "Chrome/90.0.4430.91 Mobile Safari/537.36 "
        "Ecloud/8.6.3 Android/29 clientId/355325117317828 "
        "clientModel/SM-G9730 imsi/460071114317824 "
        "clientChannelId/qq proVersion/1.0.6"
    )


# =========================
# 登录逻辑
# =========================

def login_by_password(username, password):
    print("🔄 正在执行账号密码登录流程...")

    s = requests.Session()
    s.headers.update({
        "User-Agent": get_pc_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })

    try:
        url_token = (
            "https://m.cloud.189.cn/udb/udb_login.jsp?"
            "pageId=1&pageKey=default&clientType=wap"
            "&redirectURL=https://m.cloud.189.cn/zhuanti/2021/shakeLottery/index.html"
        )

        r = s.get(url_token, timeout=15)
        match = re.search(r"https?://[^\s'\"]+", r.text)

        if not match:
            print("❌ 错误：未找到动态登录页")
            print(r.text[:500])
            return None

        url = match.group()
        r = s.get(url, timeout=15)

        match = re.search(r'href="([^"]+)"', r.text)
        if not match:
            print("❌ 错误：登录入口获取失败")
            print(r.text[:500])
            return None

        href = match.group(1)
        r = s.get(href, timeout=15)

        html = r.text

        def find_one(pattern, name):
            result = re.findall(pattern, html)
            if not result:
                raise ValueError(f"登录页参数提取失败：{name}")
            return result[0]

        captcha_token = find_one(r"captchaToken' value='(.+?)'", "captchaToken")
        lt = find_one(r'lt = "(.+?)"', "lt")
        return_url = find_one(r"returnUrl= '(.+?)'", "returnUrl")
        param_id = find_one(r'paramId = "(.+?)"', "paramId")
        j_rsakey = find_one(r'j_rsaKey" value="(\S+)"', "j_rsaKey")

        s.headers.update({"lt": lt})

        username_enc = rsa_encode(j_rsakey, username)
        password_enc = rsa_encode(j_rsakey, password)

        data = {
            "appKey": "cloud",
            "accountType": "01",
            "userName": f"{{RSA}}{username_enc}",
            "password": f"{{RSA}}{password_enc}",
            "validateCode": "",
            "captchaToken": captcha_token,
            "returnUrl": return_url,
            "mailSuffix": "@189.cn",
            "paramId": param_id
        }

        headers = {
            "User-Agent": get_pc_ua(),
            "Referer": "https://open.e.189.cn/",
            "Origin": "https://open.e.189.cn",
        }

        r = s.post(
            "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do",
            data=data,
            headers=headers,
            timeout=15
        )

        login_json = safe_json(r)
        if not login_json:
            print("❌ 登录接口返回非 JSON：")
            print(r.text[:800])
            return None

        if login_json.get("result", 1) != 0:
            msg = login_json.get("msg", "未知错误")
            print(f"❌ 登录错误：{msg}")
            print(f"📦 登录接口返回：{json.dumps(login_json, ensure_ascii=False)}")

            msg_str = str(msg)

            if "设备ID不存在" in msg_str or "二次设备校验" in msg_str:
                print("⚠️ 当前账号仍然触发设备二次校验。")
                print("👉 你已经关闭设备锁的话，建议先用浏览器或天翼云盘 App 手动登录一次该账号。")
                print("👉 手动登录成功后，再运行本脚本。")

            if "验证码" in msg_str or "validateCode" in msg_str:
                print("⚠️ 当前账号触发图形验证码，脚本暂不支持自动识别。")
                print("👉 建议网页端登录通过验证码后，等待一段时间再运行。")

            return None

        to_url = login_json.get("toUrl")
        if not to_url:
            print("❌ 登录接口没有返回 toUrl")
            print(json.dumps(login_json, ensure_ascii=False))
            return None

        s.get(to_url, timeout=15)

        print("✅ 账号密码登录成功")
        save_session_cookie(username, s)
        return s

    except Exception as e:
        print(f"⚠️ 登录异常：{str(e)}")
        return None


def get_session(username, password):
    """
    优先使用本地 Cookie。
    没有 Cookie 时，使用账号密码登录。
    """
    session = load_session_from_cookie(username)
    if session:
        return session

    return login_by_password(username, password)


def relogin(username, password):
    """Cookie 失效后的重新登录"""
    print("🔁 尝试重新账号密码登录...")
    delete_saved_cookie(username)
    return login_by_password(username, password)


# =========================
# 签到与抽奖
# =========================

def is_login_invalid_response(resp):
    """
    判断是否 Cookie 失效。
    主要表现：
    1. 返回非 JSON
    2. 返回 HTML 登录页
    3. 返回特定错误码
    """
    if resp is None:
        return True

    if isinstance(resp, dict):
        text = json.dumps(resp, ensure_ascii=False)
        invalid_keywords = [
            "未登录",
            "登录",
            "Session",
            "session",
            "AccessToken",
            "无效",
            "过期"
        ]
        return any(k in text for k in invalid_keywords)

    return False


def do_sign_and_lottery(session):
    """
    返回：
    {
        "ok": True/False,
        "cookie_invalid": True/False,
        "sign": "...",
        "lottery": "..."
    }
    """

    result = {
        "ok": False,
        "cookie_invalid": False,
        "sign": "",
        "lottery": ""
    }

    headers = {
        "User-Agent": get_mobile_ua(),
        "Referer": "https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp?albumBackupOpened=1",
        "Host": "m.cloud.189.cn",
    }

    try:
        # 每日签到
        rand = str(round(time.time() * 1000))
        sign_url = (
            f"https://api.cloud.189.cn/mkt/userSign.action?"
            f"rand={rand}&clientType=TELEANDROID&version=8.6.3&model=SM-G9730"
        )

        resp = session.get(sign_url, headers=headers, timeout=15)

        sign_json = safe_json(resp)
        if not sign_json:
            text = resp.text[:300] if resp is not None else ""
            print(f"⚠️ 签到接口返回非 JSON，可能 Cookie 失效：{text}")
            result["cookie_invalid"] = True
            result["sign"] = "❌ Cookie失效"
            return result

        if is_login_invalid_response(sign_json):
            print(f"⚠️ 签到接口疑似登录失效：{json.dumps(sign_json, ensure_ascii=False)}")
            result["cookie_invalid"] = True
            result["sign"] = "❌ Cookie失效"
            return result

        if sign_json.get("isSign") == "false":
            result["sign"] = f"✅ +{sign_json.get('netdiskBonus', 0)}M"
        else:
            result["sign"] = f"⏳ 已签到+{sign_json.get('netdiskBonus', 0)}M"

        # 单次抽奖
        time.sleep(random.randint(2, 5))

        lottery_url = (
            "https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?"
            "taskId=TASK_SIGNIN&activityId=ACT_SIGNIN"
        )

        resp = session.get(lottery_url, headers=headers, timeout=15)
        lottery_json = safe_json(resp)

        if not lottery_json:
            result["lottery"] = "⚠️ 抽奖返回非JSON"
        elif "errorCode" in lottery_json:
            error_msg = lottery_json.get("errorMsg") or lottery_json.get("errorCode")
            result["lottery"] = f"❌ {error_msg}"
        else:
            prize = lottery_json.get("prizeName") or lottery_json.get("description") or "未中奖"
            result["lottery"] = f"🎁 {prize}"

        result["ok"] = True
        return result

    except Exception as e:
        result["sign"] = "❌ 操作异常"
        result["lottery"] = f"⚠️ {str(e)}"
        return result


# =========================
# 推送
# =========================

def send_wxpusher(msg):
    if not WXPUSHER_APP_TOKEN or not WXPUSHER_UIDS:
        print("⚠️ 未配置WxPusher，跳过消息推送")
        return

    url = "https://wxpusher.zjiecode.com/api/send/message"
    headers = {"Content-Type": "application/json"}

    for uid in WXPUSHER_UIDS:
        if not uid:
            continue

        data = {
            "appToken": WXPUSHER_APP_TOKEN,
            "content": msg,
            "contentType": 3,
            "topicIds": [],
            "uids": [uid],
        }

        try:
            resp = requests.post(url, json=data, headers=headers, timeout=10)
            resp_json = safe_json(resp)

            if resp_json and resp_json.get("code") == 1000:
                print(f"✅ 消息推送成功 -> UID: {uid}")
            else:
                print(f"❌ 消息推送失败：{resp.text}")
        except Exception as e:
            print(f"❌ 推送异常：{str(e)}")


# =========================
# 主程序
# =========================

def main():
    print("\n=============== 天翼云盘签到开始 ===============")

    all_results = []

    for idx, acc in enumerate(accounts):
        username = acc["username"]
        password = acc["password"]
        masked_phone = mask_phone(username)

        account_result = {
            "username": masked_phone,
            "sign": "",
            "lottery": ""
        }

        print(f"\n🔔 处理账号：{masked_phone}")

        session = get_session(username, password)

        if not session:
            account_result["sign"] = "❌ 登录失败"
            account_result["lottery"] = "-"
            all_results.append(account_result)
            continue

        # 第一次尝试：优先 Cookie 或刚登录的 session
        sign_result = do_sign_and_lottery(session)

        # 如果 Cookie 失效，则账号密码重新登录并重试一次
        if sign_result.get("cookie_invalid"):
            session = relogin(username, password)

            if session:
                sign_result = do_sign_and_lottery(session)
            else:
                sign_result = {
                    "sign": "❌ 重新登录失败",
                    "lottery": "-"
                }

        account_result["sign"] = sign_result.get("sign", "")
        account_result["lottery"] = sign_result.get("lottery", "")

        all_results.append(account_result)

        print(f" {account_result['sign']} | {account_result['lottery']}")

    table = "### ⛅ 天翼云盘签到汇总\n\n"
    table += "| 账号 | 签到结果 | 每日抽奖 |\n"
    table += "|:-:|:-:|:-:|\n"

    for res in all_results:
        table += f"| {res['username']} | {res['sign']} | {res['lottery']} |\n"

    send_wxpusher(table)

    print("\n✅ 所有账号处理完成！")


if __name__ == "__main__":
    main()

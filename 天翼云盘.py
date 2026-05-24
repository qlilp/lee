#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
天翼云盘签到脚本优化版

环境变量：
ty_username 多账号用 & 分隔
ty_password 多账号用 & 分隔

可选推送：
WXPUSHER_APP_TOKEN
WXPUSHER_UID 多个 UID 用 & 分隔

调试开关：
TY_DEBUG_LOGIN=1 默认开启
TY_DEBUG_LOGIN=0 关闭登录页调试文件保存
"""

import os
import re
import json
import time
import random
import base64
import hashlib
import requests
import rsa
import hmac
from email.utils import formatdate
from urllib.parse import urljoin, urlparse, quote
from requests.utils import dict_from_cookiejar, cookiejar_from_dict


# =========================
# 基础配置
# =========================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_STORE_FILE = os.path.join(SCRIPT_DIR, "ty189_cookie_store.json")

ty_usernames = os.getenv("ty_username").split("&") if os.getenv("ty_username") else []
ty_passwords = os.getenv("ty_password").split("&") if os.getenv("ty_password") else []

if not ty_usernames or not ty_passwords:
    raise ValueError("❌ 请设置环境变量 ty_username 和 ty_password")

accounts = [
    {
        "username": u.strip(),
        "password": p.strip()
    }
    for u, p in zip(ty_usernames, ty_passwords)
]

WXPUSHER_APP_TOKEN = os.getenv("WXPUSHER_APP_TOKEN")
WXPUSHER_UIDS = os.getenv("WXPUSHER_UID", "").split("&") if os.getenv("WXPUSHER_UID") else []

TY_DEBUG_LOGIN = os.getenv("TY_DEBUG_LOGIN", "1") != "0"


# =========================
# 通用工具
# =========================

def mask_phone(phone):
    if not phone:
        return ""
    return phone[:3] + "****" + phone[-4:] if len(phone) >= 7 else phone


def account_key(username):
    return hashlib.md5(username.encode("utf-8")).hexdigest()


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


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        try:
            return json.loads(resp.text)
        except Exception:
            return None


def print_response_debug(label, resp):
    ct = resp.headers.get("Content-Type", "")
    print(f"DEBUG {label}: status={resp.status_code}, ct={ct}, len={len(resp.content)}, url={resp.url}")


def dump_debug_response(resp, filename_prefix):
    if not TY_DEBUG_LOGIN:
        return

    try:
        ct = resp.headers.get("Content-Type", "")
        ct_lower = ct.lower()
        url = resp.url
        status = resp.status_code
        content_len = len(resp.content or b"")

        meta_path = os.path.join(SCRIPT_DIR, f"{filename_prefix}.meta.txt")
        with open(meta_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(f"status: {status}\n")
            f.write(f"url: {url}\n")
            f.write(f"content-type: {ct}\n")
            f.write(f"content-length: {content_len}\n")
            f.write("\nheaders:\n")
            for k, v in resp.headers.items():
                f.write(f"{k}: {v}\n")

        if "image/" in ct_lower:
            ext = "png"
            if "jpeg" in ct_lower or "jpg" in ct_lower:
                ext = "jpg"
            elif "gif" in ct_lower:
                ext = "gif"
            elif "webp" in ct_lower:
                ext = "webp"

            path = os.path.join(SCRIPT_DIR, f"{filename_prefix}.{ext}")
            with open(path, "wb") as f:
                f.write(resp.content)

            print(f"🧩 已保存图片调试文件：{path}")
            print(f"🧩 已保存响应信息：{meta_path}")
        else:
            path = os.path.join(SCRIPT_DIR, f"{filename_prefix}.html")
            with open(path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(resp.text)

            print(f"🧩 已保存页面调试文件：{path}")
            print(f"🧩 已保存响应信息：{meta_path}")

    except Exception as e:
        print(f"⚠️ 保存调试响应失败：{e}")


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
    store = load_cookie_store()
    key = account_key(username)

    if key in store:
        store.pop(key)
        save_cookie_store(store)
        print("🧹 已删除失效 Cookie")


# =========================
# 登录页辅助函数
# =========================

def is_probably_image_url(url):
    if not url:
        return False

    lower = url.lower().split("?")[0]
    exts = [
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".bmp",
        ".css", ".js", ".woff", ".woff2", ".ttf"
    ]
    return any(lower.endswith(ext) for ext in exts)


def is_html_response(resp):
    ct = resp.headers.get("Content-Type", "").lower()

    if "image/" in ct:
        return False
    if "text/html" in ct:
        return True
    if "application/xhtml" in ct:
        return True

    text_head = resp.text[:500].lower() if resp.text else ""
    if "<html" in text_head or "<!doctype html" in text_head:
        return True

    return False


def fetch_login_page(session, url, label):
    try:
        resp = session.get(url, timeout=15, allow_redirects=True)
        print_response_debug(label, resp)
        dump_debug_response(resp, label)

        if not is_html_response(resp):
            print(f"⚠️ {label} 不是 HTML，跳过")
            return None, resp

        return resp.text, resp
    except Exception as e:
        print(f"⚠️ 请求 {label} 异常：{e}")
        return None, None


def find_first(patterns, html, name="", required=False, default=""):
    for p in patterns:
        m = re.search(p, html, re.I | re.S)
        if m:
            return m.group(1).strip()

    if required:
        raise ValueError(f"未能从登录页提取参数：{name}")

    return default


def extract_input_value(html, field_name):
    if not html:
        return ""

    inputs = re.findall(r"<input\b[^>]*>", html, re.I | re.S)
    for tag in inputs:
        has_name = re.search(
            rf'\bname\s*=\s*["\']{re.escape(field_name)}["\']',
            tag,
            re.I
        )
        has_id = re.search(
            rf'\bid\s*=\s*["\']{re.escape(field_name)}["\']',
            tag,
            re.I
        )

        if not has_name and not has_id:
            continue

        m = re.search(r'\bvalue\s*=\s*["\']([^"\']*)["\']', tag, re.I | re.S)
        if m:
            return m.group(1).strip()

    return ""


def html_has_login_params(html):
    if not html:
        return False

    keys = [
        "loginSubmit.do",
        "paramId",
        "returnUrl",
        "j_rsaKey",
        "captchaToken",
        "encryptConf.do"
    ]

    hit = sum(1 for k in keys if k in html)
    return hit >= 2


def extract_candidate_urls(html, base_url):
    candidates = []

    patterns = [
        r'href=["\']([^"\']+)["\']',
        r'action=["\']([^"\']+)["\']',
        r'src=["\']([^"\']+)["\']',
        r'url\s*:\s*["\']([^"\']+)["\']',
        r'location\.href\s*=\s*["\']([^"\']+)["\']',
        r'window\.location\s*=\s*["\']([^"\']+)["\']',
        r'var\s+\w+\s*=\s*["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        for m in re.findall(pattern, html, re.I | re.S):
            url = m.strip().replace("&amp;", "&")

            if not url:
                continue
            if url.startswith("javascript:"):
                continue
            if url.startswith("#"):
                continue

            full_url = urljoin(base_url, url)

            if is_probably_image_url(full_url):
                continue

            lower_url = full_url.lower()

            bad_words = [
                "favicon", "logo", "img", "image", "pixel", "track",
                "tongji", "analytics", "css", ".js"
            ]

            if any(w in lower_url for w in bad_words):
                continue

            good_words = [
                "open.e.189.cn", "e.189.cn", "udb", "login", "oauth2",
                "authorize", "autoLogin"
            ]

            if any(w.lower() in lower_url for w in good_words):
                if full_url not in candidates:
                    candidates.append(full_url)

    return candidates


# =========================
# RSA / 加密配置
# =========================

def normalize_j_rsakey(pubkey):
    if not pubkey:
        return ""

    pubkey = str(pubkey).strip()
    pubkey = pubkey.replace("-----BEGIN PUBLIC KEY-----", "")
    pubkey = pubkey.replace("-----END PUBLIC KEY-----", "")
    pubkey = pubkey.replace("\r", "")
    pubkey = pubkey.replace("\n", "")
    pubkey = pubkey.replace(" ", "")
    pubkey = pubkey.replace("{RSA}", "")
    pubkey = pubkey.replace("{NRP}", "")
    return pubkey.strip()


def extract_pubkey_from_json(data):
    if not isinstance(data, dict):
        return ""

    possible_keys = [
        "pubKey",
        "publicKey",
        "j_rsaKey",
        "rsaKey",
        "key"
    ]

    for k in possible_keys:
        if data.get(k):
            return normalize_j_rsakey(data.get(k))

    inner = data.get("data")
    if isinstance(inner, dict):
        for k in possible_keys:
            if inner.get(k):
                return normalize_j_rsakey(inner.get(k))

    return ""


def fetch_j_rsakey_from_api(session, referer_url="https://open.e.189.cn/"):
    """
    从 encryptConf.do 获取：
    1. RSA 公钥
    2. 加密前缀，例如 {NRP}
    """
    print("🔎 HTML 中未找到 j_rsaKey，尝试从接口获取 RSA 公钥...")

    api_url = "https://open.e.189.cn/api/logbox/config/encryptConf.do"

    headers = {
        "User-Agent": get_pc_ua(),
        "Referer": referer_url or "https://open.e.189.cn/",
        "Origin": "https://open.e.189.cn",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    }

    attempts = [
        {
            "method": "GET",
            "params": {
                "appId": "cloud",
            },
            "data": None,
        },
        {
            "method": "GET",
            "params": {
                "appId": "cloud",
                "clientType": "20100",
            },
            "data": None,
        },
        {
            "method": "POST",
            "params": None,
            "data": {
                "appId": "cloud",
            },
        },
        {
            "method": "POST",
            "params": None,
            "data": {
                "appId": "cloud",
                "clientType": "20100",
            },
        },
    ]

    for idx, item in enumerate(attempts, 1):
        try:
            if item["method"] == "GET":
                r = session.get(
                    api_url,
                    params=item["params"],
                    headers=headers,
                    timeout=15
                )
            else:
                r = session.post(
                    api_url,
                    data=item["data"],
                    headers=headers,
                    timeout=15
                )

            print_response_debug(f"ty189_encrypt_conf_{idx}", r)
            dump_debug_response(r, f"ty189_encrypt_conf_{idx}")

            data = safe_json(r)
            if not data:
                print(f"⚠️ encryptConf 第 {idx} 次返回非 JSON")
                continue

            print(f"DEBUG encryptConf JSON {idx}：{json.dumps(data, ensure_ascii=False)}")

            enc_data = data.get("data", {}) if isinstance(data, dict) else {}
            rsa_prefix = enc_data.get("pre") or "{RSA}"

            pubkey = extract_pubkey_from_json(data)

            if pubkey:
                pubkey = normalize_j_rsakey(pubkey)

                print(f"✅ 已从 encryptConf 接口获取 RSA 公钥，长度：{len(pubkey)}")
                print(f"✅ 已从 encryptConf 接口获取加密前缀：{rsa_prefix}")

                return pubkey, rsa_prefix

        except Exception as e:
            print(f"⚠️ encryptConf 第 {idx} 次请求异常：{e}")

    print("❌ encryptConf 接口未能获取 RSA 公钥")
    return "", "{RSA}"


def rsa_encode(text, pub_key):
    """
    天翼登录 RSA 加密：
    - 输入 encryptConf 返回的裸 base64 公钥
    - 输出 RSA 加密后的 hex
    """
    if text is None:
        text = ""

    if not pub_key:
        raise ValueError("RSA 公钥为空")

    pub_key = normalize_j_rsakey(pub_key)

    missing_padding = len(pub_key) % 4
    if missing_padding:
        pub_key += "=" * (4 - missing_padding)

    pem = (
        "-----BEGIN PUBLIC KEY-----\n"
        + "\n".join([pub_key[i:i + 64] for i in range(0, len(pub_key), 64)])
        + "\n-----END PUBLIC KEY-----"
    )

    try:
        public_key = rsa.PublicKey.load_pkcs1_openssl_pem(pem.encode())
    except Exception as e:
        print(f"❌ RSA 公钥加载失败：{e}")
        print(f"DEBUG pub_key length: {len(pub_key)}")
        print(f"DEBUG pub_key head: {pub_key[:50]}")
        raise

    encrypted = rsa.encrypt(str(text).encode("utf-8"), public_key)

    return encrypted.hex()


# =========================
# 账号标准化
# =========================

def normalize_account(account):
    account = str(account).strip()

    if re.fullmatch(r"1\d{10}", account):
        return account, "01", ""

    if "@" in account:
        name, suffix = account.split("@", 1)
        return name, "02", "@" + suffix

    return account, "01", ""


# =========================
# 登录逻辑
# =========================

def login_by_password(username, password):
    print("🔄 正在执行账号密码登录流程...")

    print("========== 登录前账号自检 ==========")
    print("username repr:", repr(username))
    print("username len:", len(username) if username is not None else "None")
    print("password len:", len(password) if password is not None else "None")

    if username is not None:
        username_check = str(username).strip()
        print("username strip repr:", repr(username_check))
        print("username strip len:", len(username_check))
        print("is phone:", bool(re.fullmatch(r"1\d{10}", username_check)))
        print("contains *:", "*" in username_check)
        print("contains space:", " " in str(username))
        print("contains newline:", "\n" in str(username) or "\r" in str(username))

    print("===================================")

    s = requests.Session()
    s.headers.update({
        "User-Agent": get_pc_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    })

    try:
        url_token = (
            "https://m.cloud.189.cn/udb/udb_login.jsp?"
            "pageId=1&pageKey=default&clientType=wap"
            "&redirectURL=https://m.cloud.189.cn/zhuanti/2021/shakeLottery/index.html"
        )

        html1, resp1 = fetch_login_page(s, url_token, "ty189_step1_udb_login")

        if not html1 or not resp1:
            print("❌ Step1 未获取到有效 HTML")
            return None

        final_login_html = None
        final_login_url = resp1.url

        if html_has_login_params(html1):
            print("✅ Step1 页面已经包含登录参数")
            final_login_html = html1
            final_login_url = resp1.url
        else:
            candidates = extract_candidate_urls(html1, resp1.url)
            print(f"DEBUG Step1 提取候选登录 URL 数量：{len(candidates)}")

            for i, u in enumerate(candidates[:10], 1):
                print(f"DEBUG candidate1-{i}: {u}")

            if not candidates:
                print("❌ Step1 未找到候选登录 URL")
                return None

            visited = set()

            for idx, candidate_url in enumerate(candidates[:8], 1):
                if candidate_url in visited:
                    continue

                visited.add(candidate_url)

                html2, resp2 = fetch_login_page(
                    s,
                    candidate_url,
                    f"ty189_step2_candidate_{idx}"
                )

                if not html2 or not resp2:
                    continue

                if html_has_login_params(html2):
                    print(f"✅ Step2 找到真正登录页：candidate {idx}")
                    final_login_html = html2
                    final_login_url = resp2.url
                    break

                nested_candidates = extract_candidate_urls(html2, resp2.url)
                print(f"DEBUG candidate {idx} 二级候选数量：{len(nested_candidates)}")

                for j, u in enumerate(nested_candidates[:10], 1):
                    print(f"DEBUG candidate2-{idx}-{j}: {u}")

                for jdx, nested_url in enumerate(nested_candidates[:8], 1):
                    if nested_url in visited:
                        continue

                    visited.add(nested_url)

                    html3, resp3 = fetch_login_page(
                        s,
                        nested_url,
                        f"ty189_step3_candidate_{idx}_{jdx}"
                    )

                    if not html3 or not resp3:
                        continue

                    if html_has_login_params(html3):
                        print(f"✅ Step3 找到真正登录页：candidate {idx}-{jdx}")
                        final_login_html = html3
                        final_login_url = resp3.url
                        break

                if final_login_html:
                    break

        if not final_login_html:
            print("❌ 未能找到包含登录参数的页面")
            print("👉 请查看脚本目录下生成的 ty189_step*.html 和 .meta.txt")
            return None

        html = final_login_html

        if TY_DEBUG_LOGIN:
            try:
                final_path = os.path.join(SCRIPT_DIR, "ty189_final_login_page.html")
                with open(final_path, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(html)

                print(f"🧩 已保存最终登录页：{final_path}")
                print(f"DEBUG 最终登录页 URL：{final_login_url}")
            except Exception as e:
                print(f"⚠️ 保存最终登录页失败：{e}")

        # =========================
        # 参数提取
        # =========================

        rsa_prefix = "{RSA}"

        # 先全部初始化，避免 UnboundLocalError
        captcha_token = ""
        lt = ""
        param_id = ""
        return_url = ""
        j_rsakey = ""

        captcha_token = extract_input_value(html, "captchaToken")
        if not captcha_token:
            captcha_token = find_first([
                r'<input[^>]*(?:name|id)=["\']captchaToken["\'][^>]*value=["\']([^"\']*)["\']',
                r'\bcaptchaToken\b\s*[:=]\s*["\']([^"\']*)["\']',
            ], html, "captchaToken", required=False, default="")

        lt = extract_input_value(html, "lt")
        if not lt:
            lt = find_first([
                r'<input[^>]*(?:name|id)=["\']lt["\'][^>]*value=["\']([^"\']+)["\']',
                r'<input[^>]*value=["\']([^"\']+)["\'][^>]*(?:name|id)=["\']lt["\']',
                r'\blt\b\s*[:=]\s*["\']([^"\']+)["\']',
            ], html, "lt", required=False, default="")

        param_id = extract_input_value(html, "paramId")
        if not param_id:
            param_id = find_first([
                r'<input[^>]*(?:name|id)=["\']paramId["\'][^>]*value=["\']([^"\']+)["\']',
                r'\bparamId\b\s*[:=]\s*["\']([^"\']+)["\']',
            ], html, "paramId", required=True)

        return_url = extract_input_value(html, "returnUrl")
        if not return_url:
            return_url = find_first([
                r'<input[^>]*(?:name|id)=["\']returnUrl["\'][^>]*value=["\']([^"\']+)["\']',
                r'\breturnUrl\b\s*[:=]\s*["\']([^"\']+)["\']',
            ], html, "returnUrl", required=True)

        j_rsakey = extract_input_value(html, "j_rsaKey")
        if not j_rsakey:
            j_rsakey = find_first([
                r'<input[^>]*(?:name|id)=["\']j_rsaKey["\'][^>]*value=["\']([^"\']+)["\']',
                r'\bj_rsaKey\b\s*[:=]\s*["\']([^"\']+)["\']',
                r'\bpubKey\b\s*[:=]\s*["\']([^"\']+)["\']',
                r'\bpublicKey\b\s*[:=]\s*["\']([^"\']+)["\']',
            ], html, "j_rsaKey", required=False, default="")

        j_rsakey = normalize_j_rsakey(j_rsakey)

        # HTML 里没有公钥时，从 encryptConf.do 获取，同时获取 {NRP}
        if not j_rsakey:
            j_rsakey, rsa_prefix = fetch_j_rsakey_from_api(s, final_login_url)

        if not j_rsakey:
            raise ValueError("登录页和 encryptConf 接口均未获取到 j_rsaKey")

        print("✅ 登录页参数提取成功")
        print(f"DEBUG captchaToken repr: {repr(captcha_token)}")
        print(f"DEBUG lt repr: {repr(lt)}")
        print(f"DEBUG paramId repr: {repr(param_id)}")
        print(f"DEBUG returnUrl repr: {repr(return_url[:80])}")
        print(f"DEBUG j_rsaKey length: {len(j_rsakey)}")
        print(f"DEBUG rsa_prefix from config/page: {rsa_prefix}")

        # =========================
        # 账号标准化 + 加密
        # =========================

        login_user, account_type, mail_suffix = normalize_account(username)

        print(
            f"🔎 账号标准化后：accountType={account_type}, "
            f"mailSuffix='{mail_suffix}', userName={login_user[:3]}..."
        )

        username_enc = rsa_encode(login_user, j_rsakey)
        password_enc = rsa_encode(password, j_rsakey)

        print(f"DEBUG rsa_prefix: {rsa_prefix}")
        print(f"DEBUG username_enc length: {len(username_enc)}")
        print(f"DEBUG password_enc length: {len(password_enc)}")
        print(f"DEBUG username_enc head: {username_enc[:20]}")

        # =========================
        # 登录提交
        # =========================

        submit_url = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"

        headers = {
            "User-Agent": get_pc_ua(),
            "Referer": final_login_url,
            "Origin": "https://open.e.189.cn",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }

        data = {
            "appKey": "cloud",
            "accountType": account_type,
            "userName": f"{rsa_prefix}{username_enc}",
            "password": f"{rsa_prefix}{password_enc}",
            "validateCode": "",
            "captchaToken": captcha_token,
            "returnUrl": return_url,
            "mailSuffix": mail_suffix,
            "paramId": param_id,
        }

        if lt:
            data["lt"] = lt

        r = s.post(
            submit_url,
            data=data,
            headers=headers,
            timeout=15,
            allow_redirects=False
        )

        print_response_debug("ty189_login_submit", r)
        dump_debug_response(r, "ty189_login_submit")

        login_json = safe_json(r)

        if not login_json:
            print("❌ 登录接口未返回 JSON")
            print(r.text[:500])
            return None

        print(f"DEBUG 登录接口 JSON：{json.dumps(login_json, ensure_ascii=False)}")

        result = login_json.get("result")
        msg = login_json.get("msg") or login_json.get("message") or ""

        if result not in [0, "0"]:
            print(f"❌ 登录错误：{msg}")
            print(f"📦 登录接口返回：{json.dumps(login_json, ensure_ascii=False)}")

            if "用户名不合法" in msg:
                print("⚠️ 用户名不合法，请检查：")
                print("1. rsa_prefix 是否为 {NRP}")
                print("2. username_enc length 是否为 256")
                print("3. 环境变量账号是否完整手机号")
                print("4. 如仍失败，可尝试把手机号 mailSuffix 改为 @189.cn")

            return None

        print("✅ 登录接口返回成功")

        to_url = (
            login_json.get("toUrl")
            or login_json.get("redirectUrl")
            or login_json.get("url")
            or login_json.get("data", {}).get("toUrl")
            or login_json.get("data", {}).get("redirectUrl")
        )

        if to_url:
            print(f"🔁 登录成功，开始跳转：{to_url[:100]}...")

            try:
                r2 = s.get(
                    to_url,
                    headers={
                        "User-Agent": get_mobile_ua(),
                        "Referer": final_login_url,
                    },
                    timeout=15,
                    allow_redirects=True
                )

                print_response_debug("ty189_login_redirect", r2)
                dump_debug_response(r2, "ty189_login_redirect")
            except Exception as e:
                print(f"⚠️ 登录跳转异常：{e}")
        else:
            print("⚠️ 登录成功但未找到 toUrl，继续尝试使用当前 Cookie")

        s.headers.update({
            "User-Agent": get_mobile_ua(),
            "Referer": "https://m.cloud.189.cn/"
        })

        if check_login_valid(s):
            print("✅ 登录态验证成功")
            save_session_cookie(username, s)
            return s

        print("⚠️ 登录接口成功，但登录态验证失败")
        return s

    except Exception as e:
        print(f"⚠️ 登录异常：{e}")
        print("👉 请查看脚本目录下生成的 ty189_step*.html / .meta.txt / ty189_final_login_page.html")
        return None


# =========================
# 登录态检查
# =========================

def check_login_valid(session):
    urls = [
        "https://m.cloud.189.cn/v2/getUserBriefInfo.action",
        "https://cloud.189.cn/api/portal/getUserBriefInfo.action",
        "https://cloud.189.cn/api/portal/getUserInfo.action",
    ]

    for idx, url in enumerate(urls, 1):
        try:
            r = session.get(
                url,
                headers={
                    "User-Agent": get_mobile_ua(),
                    "Referer": "https://m.cloud.189.cn/",
                    "Accept": "application/json, text/plain, */*",
                },
                timeout=15
            )

            print_response_debug(f"ty189_check_login_{idx}", r)

            text = r.text or ""
            print(f"DEBUG ty189_check_login_{idx} text: {text[:300]}")

            if r.status_code != 200:
                continue

            data = safe_json(r)

            if data:
                s = json.dumps(data, ensure_ascii=False)

                # 明确未登录
                if any(k in s for k in ["未登录", "请登录", "登录超时", "SESSION失效"]):
                    continue

                # 常见登录成功字段
                if any(k in s for k in [
                    "loginName",
                    "userName",
                    "nickName",
                    "userId",
                    "account",
                    "phone",
                    "mobile",
                    "familyId",
                    "cloudCapacityInfo",
                    "usedSize",
                    "totalSize"
                ]):
                    return True

                # 有些接口只返回 result=0 或 code=0
                if data.get("result") in [0, "0"] or data.get("code") in [0, "0", 200, "200"]:
                    return True

            else:
                if any(k in text for k in ["loginName", "userName", "nickName", "userId"]):
                    return True

        except Exception as e:
            print(f"⚠️ 登录态检查异常 {idx}：{e}")

    return False


def get_session(username, password):
    session = load_session_from_cookie(username)

    if session:
        if check_login_valid(session):
            print("✅ 本地 Cookie 有效，跳过账号密码登录")
            return session

        print("⚠️ 本地 Cookie 已失效，准备重新登录")
        delete_saved_cookie(username)

    session = login_by_password(username, password)
    return session


def relogin(username, password):
    delete_saved_cookie(username)
    return login_by_password(username, password)

# =========================
# 天翼云盘 API 签名
# =========================

def get_cookie_value(session, possible_names):
    """
    从 session.cookies 里按多个可能名称查找 cookie。
    """
    jar = session.cookies

    # 先精确匹配
    for name in possible_names:
        v = jar.get(name)
        if v:
            return v

    # 再忽略大小写匹配
    lower_map = {}
    for c in jar:
        lower_map[c.name.lower()] = c.value

    for name in possible_names:
        v = lower_map.get(name.lower())
        if v:
            return v

    return ""


def recursive_find_key(obj, target_names):
    """
    递归从 dict/list 里查找指定字段名。
    """
    if obj is None:
        return ""

    target_lower = [x.lower() for x in target_names]

    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in target_lower and v:
                return str(v)

        for v in obj.values():
            found = recursive_find_key(v, target_names)
            if found:
                return found

    elif isinstance(obj, list):
        for item in obj:
            found = recursive_find_key(item, target_names)
            if found:
                return found

    return ""


def try_fetch_app_session_from_api(session):
    """
    H5 登录后，尝试通过若干接口换取 App API 所需的 SessionKey / SessionSecret。

    注意：
    - 有些账号/地区/登录入口可能不给 SessionSecret；
    - 如果拿不到，就说明必须切 App 登录流程。
    """
    candidates = [
        {
            "name": "getUserBriefInfo",
            "url": "https://m.cloud.189.cn/v2/getUserBriefInfo.action",
            "params": {},
            "referer": "https://m.cloud.189.cn/",
        },
        {
            "name": "userBriefInfo_web",
            "url": "https://cloud.189.cn/api/portal/getUserBriefInfo.action",
            "params": {},
            "referer": "https://cloud.189.cn/",
        },
        {
            "name": "getUserInfo_web",
            "url": "https://cloud.189.cn/api/portal/getUserInfo.action",
            "params": {},
            "referer": "https://cloud.189.cn/",
        },
        {
            "name": "getSessionForPC",
            "url": "https://api.cloud.189.cn/getSessionForPC.action",
            "params": {
                "clientType": "TELEANDROID",
                "version": "8.6.3",
                "model": "SM-G9730",
            },
            "referer": "https://m.cloud.189.cn/",
        },
        {
            "name": "getSessionForPC_m",
            "url": "https://m.cloud.189.cn/v2/getSessionForPC.action",
            "params": {
                "clientType": "TELEANDROID",
                "version": "8.6.3",
                "model": "SM-G9730",
            },
            "referer": "https://m.cloud.189.cn/",
        },
    ]

    headers_base = {
        "User-Agent": get_mobile_ua(),
        "Accept": "application/json, text/plain, */*",
    }

    for item in candidates:
        try:
            headers = dict(headers_base)
            headers["Referer"] = item["referer"]

            r = session.get(
                item["url"],
                params=item["params"],
                headers=headers,
                timeout=15
            )

            print_response_debug(f"ty189_fetch_app_session_{item['name']}", r)

            try:
                print(f"DEBUG {item['name']} text: {r.text[:500]}")
            except Exception:
                pass

            data = safe_json(r)
            if not data:
                continue

            session_key = recursive_find_key(data, [
                "SessionKey",
                "sessionKey",
                "session_key",
                "sessionkey",
            ])

            session_secret = recursive_find_key(data, [
                "SessionSecret",
                "sessionSecret",
                "session_secret",
                "sessionsecret",
            ])

            access_token = recursive_find_key(data, [
                "accessToken",
                "access_token",
                "AccessToken",
                "token",
            ])

            print(
                f"DEBUG {item['name']} 提取结果："
                f"session_key={bool(session_key)}, "
                f"session_secret={bool(session_secret)}, "
                f"access_token={bool(access_token)}"
            )

            if session_key and session_secret:
                print(f"✅ 已通过 {item['name']} 获取 SessionKey/SessionSecret")

                # 写入 cookie，后面 build_cloud189_api_headers 可以直接读取
                session.cookies.set("SessionKey", session_key, domain=".cloud.189.cn", path="/")
                session.cookies.set("SessionSecret", session_secret, domain=".cloud.189.cn", path="/")

                return session_key, session_secret

        except Exception as e:
            print(f"⚠️ 尝试 {item['name']} 获取 App 凭证异常：{e}")

    return "", ""


def extract_session_key_secret(session):
    """
    尝试从 Cookie 或接口中提取 SessionKey / SessionSecret。
    """
    session_key_names = [
        "SessionKey",
        "sessionKey",
        "SESSIONKEY",
        "SESSION_KEY",
        "session_key",
        "cloud189_session_key",
        "CLOUD189_SESSION_KEY",
    ]

    session_secret_names = [
        "SessionSecret",
        "sessionSecret",
        "SESSIONSECRET",
        "SESSION_SECRET",
        "session_secret",
        "cloud189_session_secret",
        "CLOUD189_SESSION_SECRET",
    ]

    session_key = get_cookie_value(session, session_key_names)
    session_secret = get_cookie_value(session, session_secret_names)

    try:
        cookie_names = [c.name for c in session.cookies]
        print(f"DEBUG 当前 Cookie 名称列表：{cookie_names}")
    except Exception:
        pass

    if session_key:
        print(f"✅ 已从 Cookie 找到 SessionKey，长度：{len(session_key)}")
    else:
        print("⚠️ 未在 Cookie 中找到 SessionKey")

    if session_secret:
        print(f"✅ 已从 Cookie 找到 SessionSecret，长度：{len(session_secret)}")
    else:
        print("⚠️ 未在 Cookie 中找到 SessionSecret")

    # Cookie 里没有，就尝试用 H5 登录态换取
    if not session_key or not session_secret:
        print("🔁 尝试通过网页登录态换取 App API SessionKey/SessionSecret...")
        session_key, session_secret = try_fetch_app_session_from_api(session)

    if session_key:
        print(f"✅ 最终 SessionKey 长度：{len(session_key)}")
    else:
        print("❌ 最终仍未获取到 SessionKey")

    if session_secret:
        print(f"✅ 最终 SessionSecret 长度：{len(session_secret)}")
    else:
        print("❌ 最终仍未获取到 SessionSecret")

    return session_key, session_secret


def make_cloud189_signature(method, url, session_key, session_secret, date_str):
    """
    生成天翼云盘 API 签名。

    常见签名原文格式：
    SessionKey={SessionKey}&Operate={METHOD}&RequestURI={PATH}&Date={DATE}
    """
    method = method.upper()
    parsed = urlparse(url)

    request_uri = parsed.path
    if not request_uri.startswith("/"):
        request_uri = "/" + request_uri

    sign_text = (
        f"SessionKey={session_key}"
        f"&Operate={method}"
        f"&RequestURI={request_uri}"
        f"&Date={date_str}"
    )

    digest = hmac.new(
        session_secret.encode("utf-8"),
        sign_text.encode("utf-8"),
        hashlib.sha1
    ).digest()

    signature = base64.b64encode(digest).decode("utf-8")

    print(f"DEBUG signature raw: {sign_text}")
    print(f"DEBUG signature len: {len(signature)}")

    return signature


def build_cloud189_api_headers(session, url, method="GET", referer="https://m.cloud.189.cn/"):
    """
    构造带 Date / SessionKey / Signature 的请求头。
    """
    session_key, session_secret = extract_session_key_secret(session)

    if not session_key or not session_secret:
        raise ValueError(
            "网页登录成功，但没有拿到 App API 所需的 SessionKey/SessionSecret。"
            "当前账号/入口可能不支持直接从 H5 Cookie 换取签到签名凭证，"
            "需要改成 App 登录流程或寻找新的 H5 签到接口。"
        )

    date_str = formatdate(timeval=None, localtime=False, usegmt=True)

    signature = make_cloud189_signature(
        method=method,
        url=url,
        session_key=session_key,
        session_secret=session_secret,
        date_str=date_str
    )

    headers = {
        "User-Agent": get_mobile_ua(),
        "Referer": referer,
        "Accept": "application/json;charset=UTF-8",
        "Date": date_str,
        "SessionKey": session_key,
        "Signature": signature,
    }

    print(f"DEBUG API Date: {date_str}")
    print(f"DEBUG API has SessionKey: {bool(session_key)}")
    print(f"DEBUG API has Signature: {bool(signature)}")

    return headers


# =========================
# 签到与抽奖
# =========================

def do_sign_and_lottery(session):
    result = {
        "sign": "",
        "lottery": "",
        "cookie_invalid": False
    }

    try:
        rand = str(random.random())

        sign_url = (
            "https://api.cloud.189.cn/mkt/userSign.action?"
            f"rand={rand}&clientType=TELEANDROID&version=8.6.3&model=SM-G9730"
        )

        try:
            headers = build_cloud189_api_headers(
                session=session,
                url=sign_url,
                method="GET",
                referer="https://m.cloud.189.cn/"
            )
        except Exception as e:
            result["sign"] = f"❌ 签到签名生成失败：{e}"
            result["lottery"] = "-"
            return result

        print(f"DEBUG sign request headers keys: {list(headers.keys())}")

        r = session.get(sign_url, headers=headers, timeout=15)
        print_response_debug("ty189_sign", r)

        try:
            print(f"DEBUG ty189_sign text: {r.text[:300]}")
        except Exception:
            pass

        data = safe_json(r)

        if not data:
            text = r.text or ""

            if "login" in text.lower() or "未登录" in text:
                result["cookie_invalid"] = True
                result["sign"] = "❌ Cookie 失效"
                result["lottery"] = "-"
                return result

            result["sign"] = f"❌ 签到返回异常：{text[:80]}"
        else:
            s = json.dumps(data, ensure_ascii=False)
            print(f"DEBUG 签到 JSON：{s}")

            if any(k in s for k in ["未登录", "登录", "SESSION", "cookie", "Cookie"]):
                result["cookie_invalid"] = True
                result["sign"] = "❌ Cookie 失效"
                result["lottery"] = "-"
                return result

            # 常见成功字段兼容
            if data.get("isSign") == "false" or data.get("isSign") is False:
                result["sign"] = "✅ 签到成功"
            elif data.get("isSign") == "true" or data.get("isSign") is True:
                result["sign"] = "✅ 今日已签到"
            elif data.get("errorCode") in ["User_Not_Chance", "Already_Signed"]:
                result["sign"] = "✅ 今日已签到"
            else:
                netdisk_bonus = (
                    data.get("netdiskBonus")
                    or data.get("bonus")
                    or data.get("data", {}).get("netdiskBonus")
                    or data.get("data", {}).get("bonus")
                )

                if netdisk_bonus:
                    result["sign"] = f"✅ 签到成功，获得 {netdisk_bonus}M 空间"
                else:
                    msg = (
                        data.get("errorMsg")
                        or data.get("msg")
                        or data.get("message")
                        or data.get("data", {}).get("msg")
                        or data.get("data", {}).get("message")
                        or s
                    )

                    # 如果接口仍然提示 date/signature，则直接说明签名没带上或凭证不对
                    if "date/signature" in str(msg):
                        result["sign"] = f"❌ 签到失败：接口要求 Date/Signature，当前签名无效或缺少凭证"
                    else:
                        result["sign"] = f"✅ 签到结果：{str(msg)[:80]}"

        # 每日抽奖
        lottery_result = daily_lottery(session)
        result["lottery"] = lottery_result

        return result

    except Exception as e:
        result["sign"] = f"❌ 签到异常：{e}"
        result["lottery"] = "-"
        return result


def daily_lottery(session):
    """
    天翼云盘每日抽奖。
    带 Date / SessionKey / Signature 签名头。
    """
    urls = [
        "https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN",
        "https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN_PHOTOS",
        "https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_2022_FLDFS_KJ",
    ]

    final_msgs = []

    for idx, url in enumerate(urls, 1):
        try:
            try:
                headers = build_cloud189_api_headers(
                    session=session,
                    url=url,
                    method="GET",
                    referer="https://m.cloud.189.cn/zhuanti/2021/shakeLottery/index.html"
                )
            except Exception as e:
                return f"❌ 抽奖签名生成失败：{e}"

            r = session.get(url, headers=headers, timeout=15)
            print_response_debug(f"ty189_lottery_{idx}", r)

            try:
                print(f"DEBUG ty189_lottery_{idx} text: {r.text[:300]}")
            except Exception:
                pass

            data = safe_json(r)

            if not data:
                text = (r.text or "").strip()
                if text:
                    final_msgs.append(text[:80])
                continue

            s = json.dumps(data, ensure_ascii=False)
            print(f"DEBUG 抽奖 JSON {idx}：{s}")

            if any(k in s for k in ["未登录", "登录", "SESSION", "cookie", "Cookie"]):
                return "❌ 抽奖失败：Cookie 失效"

            prize_name = (
                data.get("prizeName")
                or data.get("awardName")
                or data.get("name")
                or data.get("data", {}).get("prizeName")
                or data.get("data", {}).get("awardName")
                or data.get("data", {}).get("name")
            )

            error_msg = (
                data.get("errorMsg")
                or data.get("msg")
                or data.get("message")
                or data.get("data", {}).get("msg")
                or data.get("data", {}).get("message")
            )

            if prize_name:
                return f"🎉 抽奖获得：{prize_name}"

            if error_msg:
                if any(k in str(error_msg) for k in ["没有抽奖机会", "已抽", "次数不足", "机会用完"]):
                    return f"✅ {error_msg}"

                final_msgs.append(str(error_msg))
                continue

            final_msgs.append(s[:100])

        except Exception as e:
            final_msgs.append(f"接口{idx}异常：{e}")

    if final_msgs:
        return "⚠️ 抽奖结果：" + " | ".join(final_msgs[:2])

    return "⚠️ 抽奖无返回"


# =========================
# 推送
# =========================

def send_wxpusher(content):
    if not WXPUSHER_APP_TOKEN or not WXPUSHER_UIDS:
        print("⚠️ 未配置WxPusher，跳过消息推送")
        return

    url = "https://wxpusher.zjiecode.com/api/send/message"

    for uid in WXPUSHER_UIDS:
        uid = uid.strip()
        if not uid:
            continue

        payload = {
            "appToken": WXPUSHER_APP_TOKEN,
            "content": content,
            "summary": "天翼云盘签到通知",
            "contentType": 3,
            "uids": [uid]
        }

        try:
            resp = requests.post(url, json=payload, timeout=15)
            data = safe_json(resp)

            if data and data.get("code") == 1000:
                print(f"✅ 消息推送成功 UID: {uid}")
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

        sign_result = do_sign_and_lottery(session)

        if sign_result.get("cookie_invalid"):
            print("🔁 Cookie 失效，尝试重新账号密码登录后重试签到")
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

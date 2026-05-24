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
from urllib.parse import urlparse, urljoin
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


def rsa_encode(text, pub_key):
    """
    天翼登录 RSA 加密兼容版：
    - 支持 encryptConf 返回的裸 base64 公钥
    - 支持 PEM 格式公钥
    - 自动修复 base64 Incorrect padding
    """
    import base64
    import rsa

    if text is None:
        text = ""

    if not pub_key:
        raise ValueError("RSA 公钥为空")

    pub_key = str(pub_key).strip()

    # 去掉可能的 {RSA} 前缀
    pub_key = pub_key.replace("{RSA}", "").strip()

    # 情况 1：已经是 PEM
    if "BEGIN PUBLIC KEY" in pub_key:
        pem = pub_key
    else:
        # 情况 2：encryptConf 返回的裸 base64
        # 清理换行、空格
        key_b64 = re.sub(r"\s+", "", pub_key)

        # 修复 base64 padding
        missing_padding = len(key_b64) % 4
        if missing_padding:
            key_b64 += "=" * (4 - missing_padding)

        pem = (
            "-----BEGIN PUBLIC KEY-----\n"
            + "\n".join([key_b64[i:i + 64] for i in range(0, len(key_b64), 64)])
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


# 登录调试开关：默认开启。正常跑通后可以在环境变量里设置 TY_DEBUG_LOGIN=0 关闭。
TY_DEBUG_LOGIN = os.getenv("TY_DEBUG_LOGIN", "1") != "0"


def is_probably_image_url(url):
    """判断 URL 是否明显是图片/静态资源"""
    if not url:
        return False

    lower = url.lower().split("?")[0]
    image_exts = [
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
        ".svg", ".bmp", ".css", ".js", ".woff", ".woff2", ".ttf"
    ]
    return any(lower.endswith(ext) for ext in image_exts)


def dump_debug_response(resp, filename_prefix):
    """
    保存调试响应。
    - HTML/文本保存为 .html
    - 图片保存为 .png/.bin
    - 同时保存 meta 信息
    """
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


def print_response_debug(label, resp):
    """打印每一步请求信息"""
    ct = resp.headers.get("Content-Type", "")
    print(f"DEBUG {label}: status={resp.status_code}, ct={ct}, len={len(resp.content)}, url={resp.url}")


def is_html_response(resp):
    """判断是否可以当成 HTML 解析"""
    ct = resp.headers.get("Content-Type", "").lower()

    if "image/" in ct:
        return False

    if "text/html" in ct:
        return True

    if "application/xhtml" in ct:
        return True

    # 有些接口 Content-Type 不规范，兜底判断内容
    text_head = resp.text[:500].lower() if resp.text else ""
    if "<html" in text_head or "<!doctype html" in text_head:
        return True

    return False


def html_has_login_params(html):
    """判断当前 HTML 是否像真正的天翼登录页"""
    if not html:
        return False

    keywords = [
        "j_rsaKey",
        "paramId",
        "returnUrl",
        "loginSubmit.do",
        "captchaToken",
    ]

    return any(k in html for k in keywords)


def find_first(patterns, text, name, required=True, default=""):
    """
    多规则提取参数。
    匹配到第一个就返回。
    """
    for pattern in patterns:
        m = re.search(pattern, text, re.S)
        if m:
            value = m.group(1)
            if value is not None:
                return value.strip()

    if required:
        raise ValueError(f"登录页参数提取失败：{name}")

    return default


def extract_candidate_urls(html, base_url):
    """
    从页面中提取可能的登录跳转 URL。
    重点：只提取可能是页面的链接，过滤图片、css、js、统计像素。
    """
    candidates = []

    if not html:
        return candidates

    patterns = [
        # JS 跳转
        r"location\.href\s*=\s*['\"]([^'\"]+)['\"]",
        r"window\.location\.href\s*=\s*['\"]([^'\"]+)['\"]",
        r"window\.location\s*=\s*['\"]([^'\"]+)['\"]",
        r"location\.replace\(\s*['\"]([^'\"]+)['\"]\s*\)",
        r"top\.location\.href\s*=\s*['\"]([^'\"]+)['\"]",
        r"self\.location\.href\s*=\s*['\"]([^'\"]+)['\"]",

        # href/action
        r'href=["\']([^"\']+)["\']',
        r'action=["\']([^"\']+)["\']',

        # 纯 URL
        r'(https?://[^\s\'"<>]+)',
    ]

    for pattern in patterns:
        for m in re.findall(pattern, html, re.S):
            url = m.strip().replace("&amp;", "&")

            if not url:
                continue

            if url.startswith("javascript:"):
                continue

            if url.startswith("#"):
                continue

            full_url = urljoin(base_url, url)

            # 过滤明显静态资源
            if is_probably_image_url(full_url):
                continue

            # 过滤统计/埋点/图片相关
            bad_words = [
                "favicon",
                "logo",
                "img",
                "image",
                "pixel",
                "track",
                "tongji",
                "analytics",
                "css",
                ".js",
            ]
            lower_url = full_url.lower()
            if any(w in lower_url for w in bad_words):
                continue

            # 优先保留天翼登录相关地址
            good_words = [
                "open.e.189.cn",
                "e.189.cn",
                "udb",
                "login",
                "oauth2",
                "authorize",
            ]

            if any(w in lower_url for w in good_words):
                if full_url not in candidates:
                    candidates.append(full_url)

    return candidates


def fetch_login_page(session, url, label):
    """
    请求某个候选登录页。
    如果是图片/静态资源，不当成 HTML。
    """
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


def normalize_j_rsakey(pubkey):
    """
    规范化 RSA 公钥。
    rsa_encode() 里会自己拼接 BEGIN/END，所以这里要去掉头尾。
    """
    if not pubkey:
        return ""

    pubkey = str(pubkey).strip()

    pubkey = pubkey.replace("-----BEGIN PUBLIC KEY-----", "")
    pubkey = pubkey.replace("-----END PUBLIC KEY-----", "")
    pubkey = pubkey.replace("\r", "")
    pubkey = pubkey.replace("\n", "")
    pubkey = pubkey.replace(" ", "")

    return pubkey.strip()


def extract_pubkey_from_json(data):
    """
    从不同结构的 JSON 里尝试提取公钥。
    兼容：
    {
        "data": {
            "pubKey": "..."
        }
    }

    或：
    {
        "pubKey": "..."
    }
    """
    if not isinstance(data, dict):
        return ""

    possible_keys = [
        "pubKey",
        "publicKey",
        "j_rsaKey",
        "rsaKey",
        "key",
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
    当登录页 HTML 里没有 j_rsaKey 时，尝试从天翼登录配置接口获取 RSA 公钥。
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

            enc_data = data.get("data", {})
            rsa_prefix = enc_data.get("pre") or "{RSA}"

            pubkey = extract_pubkey_from_json(data)
            if pubkey:
                print(f"✅ 已从 encryptConf 接口获取 RSA 公钥，长度：{len(pubkey)}")
                print(f"✅ 已从 encryptConf 接口获取加密前缀：{rsa_prefix}")
                return pubkey, rsa_prefix

        except Exception as e:
            print(f"⚠️ encryptConf 第 {idx} 次请求异常：{e}")

    print("❌ encryptConf 接口未能获取 RSA 公钥")
    return "", "{RSA}"

def extract_input_value(html, field_name):
    """
    从 input 标签中提取指定 name/id 的 value。
    避免 lt 被 alt="xxx" 误匹配。
    """
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

def login_by_password(username, password):
    print("🔄 正在执行账号密码登录流程...")

    # =========================
    # 登录前账号环境变量自检
    # =========================
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

        # =========================
        # Step 1：请求 m.cloud.189.cn 登录入口
        # =========================
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
            # =========================
            # Step 2：从 Step1 页面提取候选登录 URL
            # =========================
            candidates = extract_candidate_urls(html1, resp1.url)

            print(f"DEBUG Step1 提取候选登录 URL 数量：{len(candidates)}")
            for i, u in enumerate(candidates[:10], 1):
                print(f"DEBUG candidate1-{i}: {u}")

            if not candidates:
                print("❌ Step1 未找到候选登录 URL")
                return None

            visited = set()

            # 最多尝试前 8 个候选，避免乱跳
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

                # =========================
                # Step 3：如果 Step2 不是最终登录页，继续从 Step2 里找下一层
                # =========================
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

        captcha_token = extract_input_value(html, "captchaToken")
        if not captcha_token:
            captcha_token = find_first([
                r"captchaToken['\"]?\s*[:=]\s*['\"]([^'\"]*)['\"]",
                r"captchaToken'\s+value='([^']*)'",
                r'captchaToken"\s+value="([^"]*)"',
            ], html, "captchaToken", required=False, default="")

        lt = extract_input_value(html, "lt")
        if not lt:
            lt = find_first([
                r'(?<![A-Za-z0-9_])lt\s*=\s*["\']([^"\']+)["\']',
                r'["\']lt["\']\s*:\s*["\']([^"\']+)["\']',
            ], html, "lt", required=False, default="")

        if not lt:
            raise ValueError("登录页参数提取失败：lt")

        try:
            lt.encode("latin-1")
        except Exception:
            print(f"❌ lt 提取异常，当前值不是合法 token：{lt[:50]}")
            raise ValueError("lt 提取结果异常，可能误匹配到页面中文文本")

        return_url = extract_input_value(html, "returnUrl")
        if not return_url:
            return_url = find_first([
                r"(?<![A-Za-z0-9_])returnUrl\s*=\s*['\"]([^'\"]+)['\"]",
                r'["\']returnUrl["\']\s*:\s*["\']([^"\']+)["\']',
            ], html, "returnUrl")

        param_id = extract_input_value(html, "paramId")
        if not param_id:
            param_id = find_first([
                r'(?<![A-Za-z0-9_])paramId\s*=\s*["\']([^"\']+)["\']',
                r'["\']paramId["\']\s*:\s*["\']([^"\']+)["\']',
            ], html, "paramId")

        j_rsakey = find_first([
            r'name=["\']j_rsaKey["\']\s+value=["\']([^"\']+)["\']',
            r'value=["\']([^"\']+)["\']\s+name=["\']j_rsaKey["\']',
            r'id=["\']j_rsaKey["\']\s+value=["\']([^"\']+)["\']',
            r'value=["\']([^"\']+)["\']\s+id=["\']j_rsaKey["\']',
            r'j_rsaKey["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'pubKey["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'publicKey["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        ], html, "j_rsaKey", required=False, default="")

        j_rsakey = normalize_j_rsakey(j_rsakey)

        if not j_rsakey:
            j_rsakey, rsa_prefix = fetch_j_rsakey_from_api(s, final_login_url)

        if not j_rsakey:
            raise ValueError("登录页和 encryptConf 接口均未获取到 j_rsaKey")
        
       
        rsa_prefix = rsa_prefix if "rsa_prefix" in locals() else "{RSA}"

        print(f"DEBUG rsa_prefix: {rsa_prefix}")
        print(f"DEBUG username_enc length: {len(username_enc)}")
        print(f"DEBUG password_enc length: {len(password_enc)}")
        print(f"DEBUG username_enc head: {username_enc[:20]}")




        print("✅ 登录页参数提取成功")
        print(f"DEBUG captchaToken: {'有' if captcha_token else '空'}")
        print(f"DEBUG lt: {lt[:20]}...")
        print(f"DEBUG paramId: {param_id[:20]}...")
        print(f"DEBUG returnUrl: {return_url[:60]}...")
        print(f"DEBUG j_rsaKey length: {len(j_rsakey)}")


        # =========================
        # 账号标准化 + RSA 加密 + 提交登录
        # =========================

        def normalize_login_account(raw_account):
            """
            标准化登录账号：
            - 手机号：accountType=01, mailSuffix=''
            - 邮箱：accountType=02, userName=邮箱前缀, mailSuffix=@域名
            """
            if raw_account is None:
                raise ValueError("账号为空")

            account = str(raw_account).strip().replace(" ", "")

            if not account:
                raise ValueError("账号为空")

            if "*" in account:
                raise ValueError("当前账号是打码后的值，不能用于登录，请填写完整手机号或邮箱原文")

            # 手机号
            if re.fullmatch(r"1\d{10}", account):
                return account, "01", ""

            # 邮箱
            if "@" in account:
                local, domain = account.split("@", 1)
                if not local or not domain:
                    raise ValueError(f"邮箱格式不合法：{account}")
                return local, "02", f"@{domain}"

            # 其他情况先按普通账号处理
            return account, "01", ""

        login_user, account_type, mail_suffix = normalize_login_account(username)

        print(
            f"🔎 账号标准化后：accountType={account_type}, "
            f"mailSuffix={mail_suffix!r}, userName={login_user[:3]}..."
        )

        # 注意：username_enc / password_enc 必须在这里生成
        username_enc = rsa_encode(login_user, j_rsakey)
        password_enc = rsa_encode(password, j_rsakey)

        submit_url = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"

        headers = {
            "User-Agent": get_pc_ua(),
            "Referer": final_login_url or "https://open.e.189.cn/",
            "Origin": "https://open.e.189.cn",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }

        if lt:
            try:
                lt.encode("latin-1")
                headers["lt"] = lt
            except Exception:
                print("⚠️ lt 包含非 latin-1 字符，未写入请求头")

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

        r = s.post(
            submit_url,
            data=data,
            headers=headers,
            timeout=15
        )

        print_response_debug("ty189_login_submit", r)
        dump_debug_response(r, "ty189_login_submit")

        login_json = safe_json(r)
        if not login_json:
            print("❌ 登录接口返回非 JSON：")
            print(r.text[:1000])
            return None

        print(f"DEBUG 登录接口 JSON：{json.dumps(login_json, ensure_ascii=False)}")

        if login_json.get("result", 1) != 0:
            msg = login_json.get("msg", "未知错误")
            print(f"❌ 登录错误：{msg}")
            print(f"📦 登录接口返回：{json.dumps(login_json, ensure_ascii=False)}")

            msg_str = str(msg)

            if "用户名不合法" in msg_str:
                print("⚠️ 用户名不合法，请重点检查：")
                print("1. 环境变量里的账号是否是完整手机号，不是 199****3303")
                print("2. 账号前后是否有空格")
                print("3. 如果是邮箱账号，请填写完整邮箱，例如 xxx@189.cn")

            if "设备ID不存在" in msg_str or "二次设备校验" in msg_str:
                print("⚠️ 当前账号触发设备二次校验。")
                print("👉 建议先用浏览器或天翼云盘 App 手动登录一次该账号，再运行脚本。")

            if "验证码" in msg_str or "validateCode" in msg_str:
                print("⚠️ 当前账号触发图形验证码，脚本暂不支持自动识别。")

            if "密码" in msg_str:
                print("⚠️ 请检查账号密码是否正确。")

            return None

        to_url = login_json.get("toUrl")
        if not to_url:
            print("❌ 登录接口没有返回 toUrl")
            print(json.dumps(login_json, ensure_ascii=False))
            return None

        # =========================
        # 跟随登录成功跳转，拿云盘 Cookie
        # =========================
        r = s.get(to_url, timeout=15, allow_redirects=True)
        print_response_debug("ty189_login_toUrl", r)
        dump_debug_response(r, "ty189_login_toUrl")

        print("✅ 账号密码登录成功")

        save_session_cookie(username, s)

        return s

    except Exception as e:
        print(f"⚠️ 登录异常：{str(e)}")
        print("👉 请查看脚本目录下生成的 ty189_step*.html / .meta.txt / ty189_final_login_page.html")
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本名称：铛铛一下签到
脚本作者：3iXi
创建时间：2026-03-06
抓包说明：打开小程序"旧衣服回收 铛铛一下"，登录后抓任意请求头中的 token 字段值。
环境变量：
        变量名：dd1x
        变量值：token 或 token#base_url=https://vues.dd1x.cn，每行一个账号
奖励内容：现金，满 0.3 可提现(满足条件后，脚本自动申请提现)

【自动刷新缓存说明】
- 脚本会在同目录下生成 dd1x_token_cache.json 缓存文件
- 每次 API 请求自动检查响应中是否有新 token，有则自动写入缓存
- 下次运行优先读取缓存中的 token，缓存失效时回退到环境变量中的初始 token
- 只需首次配置环境变量，后续 token 自动续期（需服务端返回新 token）
"""

import base64
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from urllib.parse import quote, urljoin, urlparse

try:
    from SendNotify import capture_output
except Exception as exc:
    print(f"[警告] 通知模块 SendNotify.py 导入失败：{exc}，将跳过通知推送。")

    def capture_output(title: str = "脚本运行结果"):
        def decorator(func):
            return func

        return decorator

import requests


DEFAULT_BASE_URL = "https://vues.dd1x.cn"
COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090a13) UnifiedPCWindowsWechat(0xf2541022) XWEB/16467",
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Referer": "https://servicewechat.com/wxe378d2d7636c180e/801/page-frame.html",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# ==================== 缓存配置 ====================
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dd1x_token_cache.json")


def load_token_cache() -> dict[str, str]:
    """读取本地 token 缓存，返回 {openid: token}"""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception as e:
        print(f"[警告] 读取缓存文件失败: {e}，将使用环境变量中的 token")
    return {}


def save_token_cache(open_id: str, token: str) -> bool:
    """将单个账号的 token 合并写入本地缓存文件（先读再写，不覆盖其他账号）"""
    if not open_id or not token:
        return False
    existing = load_token_cache()
    existing[open_id] = token
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[警告] 写入缓存文件失败: {e}")
        return False


@dataclass
class AccountConfig:
    token: str
    base_url: str
    raw: str
    open_id: str = ""
    # 运行时更新 token 的回调
    on_token_refreshed: callable = field(default=None, repr=False)


def split_accounts(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def parse_account_line(line: str) -> AccountConfig | None:
    parts = [part.strip() for part in line.split("#") if part.strip()]
    if not parts:
        return None

    token = parts[0]
    base_url = DEFAULT_BASE_URL
    for part in parts[1:]:
        if part.lower().startswith("base_url="):
            base_url = part.split("=", 1)[1].strip()

    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return AccountConfig(token=token, base_url=f"{parsed.scheme}://{parsed.netloc}", raw=line)


def decode_openid_from_jwt(token: str) -> str:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return ""
        payload = parts[1].replace("-", "+").replace("_", "/")
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.b64decode(payload).decode("utf-8"))
        return data.get("openid") or data.get("openId") or ""
    except Exception:
        return ""


def assert_ok(resp: dict) -> None:
    if resp.get("code") == 0:
        return
    raise RuntimeError(str(resp.get("msg") or resp.get("message") or "请求失败"))


def call_api(acc: AccountConfig, method: str, path: str, body: dict | list | None = None) -> dict:
    url = urljoin(acc.base_url, path)
    headers = {**COMMON_HEADERS, "token": acc.token}
    if method.upper() == "GET":
        response = requests.get(url, headers=headers, timeout=30)
    else:
        response = requests.post(url, headers=headers, json=body or {}, timeout=30)

    # 自动检测响应头中的新 token 并更新缓存
    new_token = response.headers.get("token") or response.headers.get("new-token") or response.headers.get("x-token")
    if new_token and new_token != acc.token:
        acc.token = new_token
        if acc.on_token_refreshed:
            acc.on_token_refreshed(new_token)

    text = response.text
    try:
        resp_json = response.json()
    except Exception as exc:
        return {"code": -1, "msg": f"JSON解析失败: {exc}; body={text[:500]}{'...' if len(text) > 500 else ''}"}

    # 自动检测响应体中的新 token 并更新缓存
    resp_data = resp_json.get("data") if isinstance(resp_json.get("data"), dict) else None
    if resp_data:
        body_token = resp_data.get("token") or resp_data.get("newToken") or resp_data.get("access_token")
        if body_token and body_token != acc.token:
            acc.token = body_token
            if acc.on_token_refreshed:
                acc.on_token_refreshed(body_token)

    return resp_json


def api_get(acc: AccountConfig, path: str) -> dict:
    return call_api(acc, "GET", path)


def api_post(acc: AccountConfig, path: str, body: dict | list | None = None) -> dict:
    return call_api(acc, "POST", path, body)


def send_tracking(open_id: str, path: str, action: str, page_query_obj: dict | None = None, random_args: dict | None = None) -> None:
    payload = {
        "type": "1",
        "platform": "weapp",
        "appLaunch": {
            "path": "pages/index/index",
            "query": {},
            "scene": 1256,
            "referrerInfo": {},
            "apiCategory": "default",
        },
        "pageQueryObj": page_query_obj or {},
        "appHeader": {
            "platformVersion": "4.1.0.34",
            "resolution": "978*519",
            "pixelRatio": 1.25,
            "os": "windows",
            "fontSizeSetting": 15,
            "deviceModel": "microsoft",
            "deviceBrand": "microsoft",
            "deviceManufacturer": "microsoft",
            "deviceManuid": "microsoft",
            "deviceName": "microsoft",
            "osVersion": "Windows 10 x64",
            "language": "zh_CN",
            "access": "wifi",
        },
        "path": path,
        "uuid": str(uuid.uuid4()),
        "randomArgs": random_args or {},
        "appid": "wxe378d2d7636c180e",
        "channelId": "154",
        "openId": open_id,
        "action": action,
    }
    try:
        requests.post("https://data.dd1x.cn/api/test_api", headers=COMMON_HEADERS, json=payload, timeout=15)
    except Exception:
        pass


def xcx_point(acc: AccountConfig, process_id: str, note: str, page_name: str) -> None:
    if not process_id:
        return
    try:
        api_get(acc, f"/front/xcxPoint?processId={process_id}&processNote={quote(note)}&channel=154&pageName={quote(page_name)}")
    except Exception:
        pass


def run_for_account(acc: AccountConfig) -> None:
    open_id = decode_openid_from_jwt(acc.token)
    acc.open_id = open_id

    print("正在初始化会话...")
    access_res = api_get(acc, "/front/accessXcx?channelId=154&processId=")
    process_id = str(access_res.get("data") or "")
    if process_id:
        print(f"会话初始化成功: {process_id}")
        api_get(acc, f"/front/accessXcx?channelId=154&processId={process_id}")
    else:
        print("警告: 未获取到 processId，部分任务可能失效")

    send_tracking(open_id, "pages/index/index", "page_show")
    send_tracking(open_id, "pages/index/index", "page_click", random_args={"event_name": "进入小程序"})
    xcx_point(acc, process_id, "进入小程序", "首页")

    user_info = api_get(acc, "/ali/getUserInfo")
    assert_ok(user_info)
    nick_name = str(user_info.get("data", {}).get("nickName") or "未知")
    print(f"账号【{nick_name}】Token有效")

    send_tracking(open_id, "pages/index/index", "page_show")
    member_info = api_get(acc, "/api/v2/get_member_info")
    assert_ok(member_info)
    print(f"当前余额{member_info.get('data', {}).get('money', '-')}元")

    sign = api_get(acc, "/api/v2/sign_join")
    if sign.get("code") == 0:
        print(f"签到成功，获得【{sign.get('data', {}).get('name', '未知奖励')}】")
        send_tracking(open_id, "pages/index/index", "page_click", random_args={"event_name": "首页-立即签到"})
        xcx_point(acc, process_id, "首页-立即签到", "首页")
    else:
        msg = str(sign.get("msg") or sign.get("message") or "签到失败")
        if "签" in msg and ("过" in msg or "已经" in msg):
            print("今天已经签到过")
        else:
            raise RuntimeError(msg)

    send_tracking(open_id, "pages/mine/mine", "page_show")
    send_tracking(open_id, "pages/index/index", "page_click", random_args={"event_name": "底部导航-我的"})

    member_info = api_get(acc, "/api/v2/get_member_info")
    assert_ok(member_info)
    current_money = float(member_info.get("data", {}).get("money") or 0)
    print(f"任务完毕，当前余额{member_info.get('data', {}).get('money', '-')}元")

    if current_money < 0.3:
        return

    print("余额满足提现要求，准备提现...")
    send_tracking(open_id, "pages/mine/mine", "page_click", random_args={"event_name": "设置-我的钱包"})
    xcx_point(acc, process_id, "中心首页-我的钱包", "我的")
    send_tracking(open_id, "pages/mine/withdrawal/index", "page_show", page_query_obj={"channelId": "154"})
    xcx_point(acc, process_id, "进入钱包", "提现")
    send_tracking(open_id, "pages/mine/withdrawal/index", "page_click", random_args={"event_name": "钱包-提现"})
    xcx_point(acc, process_id, "钱包-提现", "提现")

    withdrawal_list = api_get(acc, "/api/h/get_withdrawal_trade_list")
    if isinstance(withdrawal_list, list):
        trade_list = withdrawal_list
    else:
        trade_list = withdrawal_list.get("data") if isinstance(withdrawal_list.get("data"), list) else []

    available = [item for item in trade_list if not item.get("disabled") and float(item.get("money") or 0) >= 0.3]
    if not available:
        print("没有满足提现金额(>=0.3元)的订单")
        return

    total_money = f"{sum(float(item.get('money') or 0) for item in available):.2f}"
    print(f"检测到可提现订单 {len(available)} 个，合计 {total_money} 元")
    withdraw_res = api_post(
        acc,
        "/api/h/withdrawal",
        {"totalMoney": total_money, "type": 1, "withdrawalDetailPojoList": available},
    )
    if withdraw_res.get("code") == 1:
        print(f"提现成功: {withdraw_res.get('msg') or '确定'}")
        send_tracking(open_id, "pages/mine/mine", "page_click", random_args={"event_name": "全选-提现成功"})
        xcx_point(acc, process_id, "全选-提现成功", "提现")
    else:
        print(f"提现失败: {withdraw_res.get('msg') or '未知错误'}")


@capture_output("铛铛一下签到运行结果")
def main() -> None:
    lines = split_accounts(os.getenv("dd1x", ""))
    if not lines:
        print("未找到环境变量 dd1x，请配置 token，每行一个账号")
        return

    # 加载本地缓存
    token_cache = load_token_cache()
    if token_cache:
        print(f"📦 已加载本地缓存，共 {len(token_cache)} 个账号的 token")

    accounts = []
    for line in lines:
        acc = parse_account_line(line)
        if acc:
            # 优先使用缓存中的 token
            open_id = decode_openid_from_jwt(acc.token)
            if open_id and open_id in token_cache:
                cached_token = token_cache[open_id]
                if cached_token and cached_token != acc.token:
                    print(f"[缓存] 找到 openid={open_id[:10]}... 的缓存 token，优先使用")
                    acc.token = cached_token

            # 设置 token 刷新回调
            def make_refresh_callback(oid):
                def callback(new_token):
                    if save_token_cache(oid, new_token):
                        print(f"[缓存] ✅ token 已自动更新并写入缓存 (openid={oid[:10]}...)")
                return callback

            acc.on_token_refreshed = make_refresh_callback(open_id)
            accounts.append(acc)
        else:
            print(f"账号配置格式错误，跳过：{line}")

    print("\n=== 任务开始 ===")
    print(f"配置账号总数: {len(accounts)}")
    for index, acc in enumerate(accounts, 1):
        print(f"\n--- 账号 {index} ---")
        try:
            run_for_account(acc)
        except Exception as exc:
            print(f"失败: {exc}")
        if index < len(accounts):
            time.sleep(2)

    print("\n=== 任务完成 ===")


if __name__ == "__main__":
    main()

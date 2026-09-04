#!/usr/bin/python
# coding=utf-8
import sys
import os
import traceback
import requests
import json
import hashlib
import time

SIGN_LOG = 'logs/kuaishou_sign.log'
work_path = os.path.dirname(os.path.abspath(__file__))
SIGN_LOG_FILE = os.path.join(work_path, SIGN_LOG)

# 调试模式：打印完整响应，方便排查接口变化
DEBUG = os.getenv('KSJSB_DEBUG', '0') == '1'

# 账号间延迟（秒），避免请求过快被限流
ACCOUNT_DELAY = int(os.getenv('KSJSB_DELAY', '3'))

# 多账号分隔符（每个环境变量内 cookie 和签名之间的分隔符）
SEP = '|||'

# 默认签名（当某个账号没有配置独立签名时使用，可能已过期）
DEFAULT_SIG3_BOX = '273770408664a7a2ea7b10787f7e62718c6a7e50b5b0f4654b2568686e6e6d6c5373'
DEFAULT_SIG3_SIGN = '0b1b5c6c1243e48ec657335453525d3e5ff0b056f69cd8490b5e4444424241407f5f'
DEFAULT_SIG4 = 'HUDR_sFnX-HFuAE5VsdPNKlLOPr4ntwVLcugxjxZz8_z61EHYFY07AGiHwMelb_ny_pMHxR_0BjgEKKQba1Uc3eSWmMYZtd0w8l4XDj-3MCjD__Ta_XvZSJ4TCB8KqqVKMgRgdptyHjC4q5WxhjlivWeuiUH73Q5s2-4u88UkwHrtgNYFpaoTLyzpjhJN-kWm8EpIT1cd-4gSarv9lyc5eoynpqIeL1p8oDC_aNVs06Eqr9eEDO9WQN6bPOljEgPJOUyOx2TUE6Zol22dloUXNTFoJdgLPRKfw_RHixi41S59Nig74-a-EOa96K3w3f2SK367nfaMVvB8TYO9Zh3FHGMRsgPwfpaekre0Ra5-ZMIxO_S1Jpimvzg8hzW00xtV2EkEfYDNFvw68MgnbnxspI6ndwP4goeqm_Gr_PeS3rmTNMpgPIhHOlYIzTyVqRydZeTwh5ckgKW0moc1WndwyJqoqIh222uMxhDr_q2L_eyoTl7L7Moo_r17aDmbuEH0je0LPc3uCfeFHFlC$HE_4b541fe2ab6646f3d69101f15f438f046f01070200376b00000041da22b49a5cf4d691019b563eda7b563e1200'


def parse_account_config(raw):
    """
    解析单个账号配置，支持两种格式：
    格式1（新）：cookie|||sig3_box|||sig3_sign|||sig4
    格式2（旧）：只有 cookie，签名用默认值
    """
    parts = [p.strip() for p in raw.split(SEP)]
    if len(parts) >= 4:
        return {
            'cookie': parts[0],
            'sig3_box': parts[1] or DEFAULT_SIG3_BOX,
            'sig3_sign': parts[2] or DEFAULT_SIG3_SIGN,
            'sig4': parts[3] or DEFAULT_SIG4,
        }
    elif len(parts) == 1:
        return {
            'cookie': parts[0],
            'sig3_box': DEFAULT_SIG3_BOX,
            'sig3_sign': DEFAULT_SIG3_SIGN,
            'sig4': DEFAULT_SIG4,
        }
    else:
        # 分隔符数量不对，尝试容错
        return {
            'cookie': parts[0] if parts else '',
            'sig3_box': parts[1] if len(parts) > 1 else DEFAULT_SIG3_BOX,
            'sig3_sign': parts[2] if len(parts) > 2 else DEFAULT_SIG3_SIGN,
            'sig4': parts[3] if len(parts) > 3 else DEFAULT_SIG4,
        }


def load_accounts():
    """
    加载所有账号配置：
    - KSJSB_COOKIE（第1个账号）
    - KSJSB_COOKIE2（第2个账号）
    - KSJSB_COOKIE3（第3个账号）
    - ...以此类推
    同时兼容旧格式：KSJSB_COOKIE 里多行（每行一个 cookie，签名用默认值）
    """
    accounts = []

    # 先读 KSJSB_COOKIE
    raw1 = os.getenv('KSJSB_COOKIE', '').strip()
    if raw1:
        # 如果包含换行，说明是旧的多账号格式（每行一个cookie）
        if '\n' in raw1 and SEP not in raw1:
            for line in raw1.splitlines():
                line = line.strip()
                if line:
                    accounts.append(parse_account_config(line))
        else:
            accounts.append(parse_account_config(raw1))

    # 再读 KSJSB_COOKIE2、KSJSB_COOKIE3...
    idx = 2
    while True:
        raw = os.getenv(f'KSJSB_COOKIE{idx}', '').strip()
        if not raw:
            break
        accounts.append(parse_account_config(raw))
        idx += 1

    return accounts


accounts = load_accounts()

if not accounts:
    print("请先配置环境变量：")
    print("  KSJSB_COOKIE = cookie|||宝箱sig3|||签到sig3|||饭补sig4")
    print("  KSJSB_COOKIE2 = 第二个账号的cookie|||宝箱sig3|||签到sig3|||饭补sig4")
    print("  KSJSB_COOKIE3 = 第三个账号的cookie|||宝箱sig3|||签到sig3|||饭补sig4")
    print("（签名留空则使用脚本内置默认值，但可能已过期）")
    exit(0)

print(f"共配置 {len(accounts)} 个账号")
for i, acc in enumerate(accounts, 1):
    cookie_preview = acc['cookie'][:30] + '...' if len(acc['cookie']) > 30 else acc['cookie']
    print(f"  账号{i}: {cookie_preview}")


def get_baoxiang(token, __NS_sig3, account_tag=""):
    print(f'{account_tag}💎💎💎💎开始领取宝箱💎💎💎💎')
    access_token = ''
    try:
        url = "https://nebula.kuaishou.com/rest/wd/encourage/unionTask/treasureBox/report?__NS_sig3=" + __NS_sig3 + "&sigCatVer=1"
        headers = {
            "Host": "nebula.kuaishou.com",
            "Connection": "keep-alive",
            "Content-Length": "2",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 23113RKC6C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.226 KsWebView/1.8.90.675 (rel) Mobile Safari/537.36 Yoda/3.1.7-alpha33-intercept1 ksNebula/12.5.20.8014 OS_PRO_BIT/64 MAX_PHY_MEM/15199 AZPREFIX/az4 ICFO/0 StatusHT/34 TitleHT/43 NetType/WIFI ISLP/0 ISDM/0 ISLB/0 locale/zh-cn DPS/19.822 DPP/99 CT/0 ISLM/0",
            "content-type": "application/json",
            "Accept": "*/*",
            "Origin": "https://nebula.kuaishou.com",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://nebula.kuaishou.com/nebula/task/earning?source=timer&layoutType=4&hyId=nebula_earning",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": token
        }
        resp = requests.post(url, headers=headers, data=json.dumps({}))
        resp_json = resp.json()
        if DEBUG:
            print(f"{account_tag}[宝箱完整响应] {json.dumps(resp_json, ensure_ascii=False)}")
        if resp_json.get('result') == 1:
            data = resp_json.get('data') or {}
            title_info = data.get('title') or {}
            title_reward = title_info.get('rewardCount', 0)
            actual_reward = (
                data.get('rewardCount')
                or data.get('amount')
                or data.get('coin')
                or data.get('gainCoin')
                or data.get('obtainCoin')
                or 0
            )
            if actual_reward and actual_reward != title_reward:
                print(f"{account_tag}宝箱标称：{title_reward} 金币，实际到账：{actual_reward} 金币")
            else:
                print(f"{account_tag}得到金币：{title_reward}")
                if title_reward == 754:
                    print(f"{account_tag}⚠️ 金币数为固定值754，可能只是宝箱标称值。建议开 KSJSB_DEBUG=1 查看完整响应")
        else:
            print(f"{account_tag}宝箱领取失败: {resp_json.get('error_msg', '未知错误')}")
    except:
        print(f"{account_tag}获取异常:{traceback.format_exc()}")

    return access_token


def get_fanbu(token, __NS_sig4, account_tag=""):
    print(f"{account_tag}🍱🍱🍱🍱开始领取饭补🍱🍱🍱🍱")
    try:
        url = "https://encourage.kuaishou.com/rest/wd/encourage/unionTask/dish/report?__NS_sig4=" + __NS_sig4 + "&sigCatVer=1"
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
        resp = requests.post(url, headers=headers, data=json.dumps({}))
        resp_json = resp.json()
        if DEBUG:
            print(f"{account_tag}[饭补完整响应] {json.dumps(resp_json, ensure_ascii=False)}")
        if resp_json.get('result') == 1:
            data = resp_json.get('data') or {}
            title = data.get('title', '饭补')
            dsd = data.get('amount', 0)
            print(f"{account_tag}{title} 共计: {dsd}")
        else:
            error_code = resp_json.get('error_code', '')
            error_msg = resp_json.get('error_msg', '未知错误')
            if error_code == 6001 or '6001' in str(error_msg):
                print(f"{account_tag}饭补今日已领取或接口限流（6001）")
            else:
                print(f"{account_tag}饭补领取失败: {error_msg}（{error_code}）")
    except:
        print(f"{account_tag}获取异常:{traceback.format_exc()}")


def get_money(token, account_tag=""):
    print(f'{account_tag}🥰🥰🥰🥰🥰开始获取当前的现金💰️💰️💰️💰️💰️')
    money = ''
    try:
        url = "https://nebula.kuaishou.com/rest/n/nebula/activity/earn/overview/basicInfo"
        headers = {
            "Host": "nebula.kuaishou.com",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 23113RKC6C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.226 KsWebView/1.8.90.675 (rel) Mobile Safari/537.36 Yoda/3.1.7-alpha33-intercept1 ksNebula/12.5.20.8014 OS_PRO_BIT/64 MAX_PHY_MEM/15199 AZPREFIX/az4 ICFO/0 StatusHT/34 TitleHT/43 NetType/WIFI ISLP/0 ISDM/0 ISLB/0 locale/zh-cn DPS/19.822 DPP/99 CT/0 ISLM/0",
            "content-type": "application/json",
            "Accept": "*/*",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://nebula.kuaishou.com/nebula/task/earning?source=timer&layoutType=4&hyId=nebula_earning",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": token
        }
        resp = requests.get(url, headers=headers)
        resp_json = resp.json()
        if DEBUG:
            print(f"{account_tag}[余额完整响应] {json.dumps(resp_json, ensure_ascii=False)}")
        data = resp_json.get('data') or {}
        money = data.get('allCash', '未知')
        print(f"{account_tag}现在的钱总共：{money}")
    except:
        print(f"{account_tag}获取异常:{traceback.format_exc()}")
    return money


def get_qiandao(token, __NS_sig3, account_tag=""):
    print(f'{account_tag}❤❤❤❤❤开始执行签到❤❤❤❤❤')
    try:
        url = "https://nebula.kuaishou.com/rest/wd/encourage/unionTask/signIn/report?__NS_sig3=" + __NS_sig3 + "&sigCatVer=1"
        headers = {
            "Host": "nebula.kuaishou.com",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; 23113RKC6C Build/UKQ1.230804.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/90.0.4430.226 KsWebView/1.8.90.675 (rel) Mobile Safari/537.36 Yoda/3.1.7-alpha33-intercept1 ksNebula/12.5.20.8014 OS_PRO_BIT/64 MAX_PHY_MEM/15199 AZPREFIX/az4 ICFO/0 StatusHT/34 TitleHT/43 NetType/WIFI ISLP/0 ISDM/0 ISLB/0 locale/zh-cn DPS/19.822 DPP/99 CT/0 ISLM/0",
            "content-type": "application/json",
            "Accept": "*/*",
            "X-Requested-With": "com.kuaishou.nebula",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://nebula.kuaishou.com/nebula/task/earning?source=timer&layoutType=4&hyId=nebula_earning",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": token
        }
        resp = requests.get(url, headers=headers)
        resp_json = resp.json()
        if DEBUG:
            print(f"{account_tag}[签到完整响应] {json.dumps(resp_json, ensure_ascii=False)}")

        if resp_json.get('result') != 1:
            error_msg = resp_json.get('error_msg', '未知错误')
            if '已领取' in str(error_msg) or '已经' in str(error_msg):
                print(f"{account_tag}今日已签到：{error_msg}")
            else:
                print(f"{account_tag}签到失败: {error_msg}")
            return

        data = resp_json.get('data') or {}

        report_result = data.get('reportRewardResult')
        if report_result:
            award_toast = report_result.get('awardToast') or {}
            title = award_toast.get('title', '签到成功')
            print(f"{account_tag}{title}")
            award_show = award_toast.get('basicSignInAwardResultShow') or {}
            bsd1 = award_show.get('bottomText', '')
            print(f"{account_tag}签到奖励：{bsd1}")
            return

        special_data = data.get('signInUnionSpecialAreaData')
        if special_data:
            subtitle = special_data.get('subtitle', '签到成功')
            today_sign_amount = special_data.get('todaySignInAmount', 0)
            print(f"{account_tag}{subtitle}")
            print(f"{account_tag}今日签到得到：{today_sign_amount}元")
            return

        print(f"{account_tag}今日已签到或无奖励信息")
    except:
        print(f"{account_tag}获取异常:{traceback.format_exc()}")


def gen_tokensig(sig, salt=""):
    v = sig + salt
    return hashlib.sha256(v.encode('utf-8')).hexdigest()


def gen_sig(params, data):
    dd = dict(params, **data)
    dict_sort_res = dict(sorted(dd.items(), key=lambda x: x[0]))
    ss = ""
    for key, value in dict_sort_res.items():
        if key not in ["sig", "__NS_sig3", "sig2"]:
            ss += f"{key}={value}"
    ss += "ca8e86efb32e"
    return hashlib.md5(ss.encode()).hexdigest()


def run_account(acc, index):
    tag = f"[账号{index}] "
    print(f"\n{'='*40}")
    print(f"{tag}开始处理")
    print(f"{'='*40}")
    get_baoxiang(acc['cookie'], acc['sig3_box'], tag)
    get_fanbu(acc['cookie'], acc['sig4'], tag)
    get_qiandao(acc['cookie'], acc['sig3_sign'], tag)
    get_money(acc['cookie'], tag)


def main():
    for idx, acc in enumerate(accounts, 1):
        try:
            run_account(acc, idx)
        except Exception as e:
            print(f"[账号{idx}] 处理异常: {e}")
            traceback.print_exc()
        if idx < len(accounts):
            print(f"\n等待 {ACCOUNT_DELAY} 秒后处理下一个账号...")
            time.sleep(ACCOUNT_DELAY)
    print(f"\n{'='*40}")
    print(f"全部 {len(accounts)} 个账号处理完成")
    print(f"{'='*40}")


if __name__ == '__main__':
    main()

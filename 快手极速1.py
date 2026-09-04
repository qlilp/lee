#!/usr/bin/python
# coding=utf-8
"""
快手极速版签到脚本
====================
版本: v1.4
修改日期: 2026-09-03

修改记录:
  v1.4 (2026-09-03):
    - 饭补增加看广告等待逻辑：返回6001时自动等待35秒后重试
    - 脚本开头增加版本号、修改日期、修改记录
    - 增加饭补等待时间环境变量 KSJSB_FANBU_WAIT（默认35秒）

  v1.3 (2026-09-03):
    - 修复宝箱状态判断：通过 reportCode 判断是否时间校验失败
    - 时间未到时显示下一个宝箱倒计时和今日进度
    - 真正领取成功才打印实际到账金币，不再显示标称奖励

  v1.2 (2026-09-03):
    - 支持多账号独立签名：KSJSB_COOKIE、KSJSB_COOKIE2、KSJSB_COOKIE3...
    - 每个账号格式：cookie|||宝箱sig3|||签到sig3|||饭补sig4
    - 修复签到接口 reportRewardResult 为 None 时报错的问题

  v1.1 (2026-09-03):
    - 增加调试模式 KSJSB_DEBUG=1，打印所有接口完整响应
    - 修复宝箱奖励字段取值，增加实际奖励字段探测

  v1.0 (原始版本):
    - 基础功能：宝箱、饭补、签到、余额查询
    - 单账号，环境变量 KSJSB_COOKIE

环境变量说明:
  KSJSB_COOKIE    第1个账号，格式：cookie|||宝箱sig3|||签到sig3|||饭补sig4
  KSJSB_COOKIE2   第2个账号（格式同上）
  KSJSB_COOKIE3   第3个账号（格式同上，以此类推）
  KSJSB_DEBUG     调试模式，设为1打印完整响应（默认0）
  KSJSB_DELAY     账号间延迟秒数（默认3）
  KSJSB_FANBU_WAIT 饭补看广告等待秒数（默认35）
"""
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

        if resp_json.get('result') != 1:
            print(f"{account_tag}宝箱接口失败: {resp_json.get('error_msg', '未知错误')}")
            return access_token

        data = resp_json.get('data') or {}
        report_code = data.get('reportCode', '')
        title_info = data.get('title') or {}
        title_text = title_info.get('text', '')
        nominal_reward = title_info.get('rewardCount', 0)
        prize_amount = data.get('prizeAmount', 0)
        toast = data.get('toast', '')

        # 从 progressBar 读取下一个可领宝箱的倒计时
        progress = data.get('progressBar') or {}
        nodes = progress.get('nodes', [])
        next_box = None
        opened_count = 0
        for node in nodes:
            style = node.get('style', 0)
            if style == 1:
                opened_count += 1
            elif style == 2 and node.get('remainSeconds', 0) > 0:
                if next_box is None:
                    next_box = node

        total_boxes = progress.get('title', '').replace('今天共有', '').replace('个宝箱可开启', '')

        # 判断是否真正领取成功
        time_check_failed = 'TIME_CHECK_FAILED' in report_code or '倒计时' in title_text
        has_reward = prize_amount > 0 or bool(toast)

        if time_check_failed:
            # 时间没到，领不到
            if next_box:
                remain = next_box.get('remainSeconds', 0)
                minutes = remain // 60
                seconds = remain % 60
                box_desc = next_box.get('desc', '')
                box_reward = next_box.get('rewardCount', '?')
                print(f"{account_tag}宝箱还在倒计时，{box_desc}还有 {minutes}分{seconds}秒（标称{box_reward}金币）")
            else:
                print(f"{account_tag}当前没有可领取的宝箱")
            if total_boxes:
                print(f"{account_tag}今日进度：已开{opened_count}个，共{total_boxes}个")
        elif has_reward:
            # 真正领到了
            print(f"{account_tag}✅ 宝箱领取成功！获得 {prize_amount} 金币")
            if toast:
                print(f"{account_tag}{toast}")
            if total_boxes:
                print(f"{account_tag}今日进度：已开{opened_count + 1}个，共{total_boxes}个")
        else:
            # 不确定状态
            print(f"{account_tag}宝箱状态：reportCode={report_code}, prizeAmount={prize_amount}")
            if toast:
                print(f"{account_tag}提示: {toast}")
            if nominal_reward:
                print(f"{account_tag}（标称奖励 {nominal_reward} 金币，未确认是否到账）")
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

        def _do_report(attempt_name):
            """执行一次饭补领取请求"""
            resp = requests.post(url, headers=headers, data=json.dumps({}))
            resp_json = resp.json()
            if DEBUG:
                print(f"{account_tag}[饭补{attempt_name}响应] {json.dumps(resp_json, ensure_ascii=False)}")
            return resp_json

        # 第一次尝试
        resp_json = _do_report("第1次")

        if resp_json.get('result') == 1:
            data = resp_json.get('data') or {}
            title = data.get('title', '饭补')
            dsd = data.get('amount', 0)
            print(f"{account_tag}✅ {title} 共计: {dsd}")
            return

        # 检查是否需要看广告（6001）
        error_code = resp_json.get('result', '') or resp_json.get('error_code', '')
        error_msg = resp_json.get('msg', '') or resp_json.get('error_msg', '')
        need_ad = (error_code == 6001 or '6001' in str(error_msg) or '广告' in str(error_msg))

        if need_ad:
            wait_seconds = int(os.getenv('KSJSB_FANBU_WAIT', '35'))
            print(f"{account_tag}需要看广告才能领取，模拟等待 {wait_seconds} 秒...")
            # 模拟看广告等待
            time.sleep(wait_seconds)
            print(f"{account_tag}广告等待完成，重试领取...")

            # 第二次尝试
            resp_json2 = _do_report("第2次")

            if resp_json2.get('result') == 1:
                data = resp_json2.get('data') or {}
                title = data.get('title', '饭补')
                dsd = data.get('amount', 0)
                print(f"{account_tag}✅ {title} 共计: {dsd}")
                return
            else:
                error_code2 = resp_json2.get('result', '') or resp_json2.get('error_code', '')
                error_msg2 = resp_json2.get('msg', '') or resp_json2.get('error_msg', '')
                print(f"{account_tag}饭补领取失败（看广告后重试）: {error_msg2}（{error_code2}）")
                print(f"{account_tag}提示：如果持续失败，可能需要真实的广告上报接口，仅等待可能不够")
                return

        # 其他错误
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

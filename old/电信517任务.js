#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { execSync } = require("child_process");
const https = require("https");
const http = require("http");
const { URL, URLSearchParams } = require("url");

// Simple DES3 and RSA implementations using Node.js crypto
function des3Encrypt(text) {
  const key = Buffer.from("1234567`90koiuyhgtfrdews");
  const iv = Buffer.alloc(8, 0);
  const cipher = crypto.createCipheriv("des-ede3-cbc", key, iv);
  let encrypted = cipher.update(text, "utf8", "hex");
  encrypted += cipher.final("hex");
  return encrypted;
}

function des3Decrypt(hexText) {
  const key = Buffer.from("1234567`90koiuyhgtfrdews");
  const iv = Buffer.alloc(8, 0);
  const decipher = crypto.createDecipheriv("des-ede3-cbc", key, iv);
  let decrypted = decipher.update(hexText, "hex", "utf8");
  decrypted += decipher.final("utf8");
  return decrypted;
}

function rsaEncryptB64(plaintext) {
  const publicKey = `-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDBkLT15ThVgz6/NOl6s8GNPofdWzWbCkWnkaAm7O2LjkM1H7dMvzkiqdxU02jamGRHLX/ZNMCXHnPcW/sDhiFCBN18qFvy8g6VYb9QtroI09e176s+ZCtiv7hbin2cCTj99iUpnEloZm19lwHyo69u5UMiPMpq0/XKBO8lYhN/gwIDAQAB
-----END PUBLIC KEY-----`;
  const buffer = Buffer.from(plaintext, "utf8");
  const encrypted = crypto.publicEncrypt(
    {
      key: publicKey,
      padding: crypto.constants.RSA_PKCS1_PADDING,
    },
    buffer
  );
  return encrypted.toString("base64");
}

function rsaEncryptHex(plaintext) {
  const publicKey = `-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC+ugG5A8cZ3FqUKDwM57GM4io6JGcStivT8UdGt67PEOihLZTw3P7371+N47PrmsCpnTRzbTgcupKtUv8ImZalYk65dU8rjC/ridwhw9ffW2LBwvkEnDkkKKRi2liWIItDftJVBiWOh17o6gfbPoNrWORcAdcbpk2L+udld5kZNwIDAQAB
-----END PUBLIC KEY-----`;
  const buffer = Buffer.from(plaintext, "utf8");
  const encrypted = crypto.publicEncrypt(
    {
      key: publicKey,
      padding: crypto.constants.RSA_PKCS1_PADDING,
    },
    buffer
  );
  return encrypted.toString("hex");
}

function rsaEncryptXbk(plaintext) {
  const publicKey = `-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDIPOHtjs6p4sTlpFvrx+ESsYkEvyT4JB/dcEbU6C8+yclpcmWEvwZFymqlKQq89laSH4IxUsPJHKIOiYAMzNibhED1swzecH5XLKEAJclopJqoO95o8W63Euq6K+AKMzyZt1SEqtZ0mXsN8UPnuN/5aoB3kbPLYpfEwBbhto6yrwIDAQAB
-----END PUBLIC KEY-----`;
  const buffer = Buffer.from(plaintext, "utf8");
  const encrypted = crypto.publicEncrypt(
    {
      key: publicKey,
      padding: crypto.constants.RSA_PKCS1_PADDING,
    },
    buffer
  );
  return encrypted.toString("base64");
}

function aesEncrypt(data, key = "34d7cb0bcdf07523") {
  if (typeof data === "object") {
    data = JSON.stringify(data);
  }
  const keyBytes = Buffer.from(key, "utf8");
  const cipher = crypto.createCipheriv("aes-128-ecb", keyBytes, "");
  let encrypted = cipher.update(data, "utf8", "hex");
  encrypted += cipher.final("hex");
  return encrypted;
}

function aesEcbEncrypt(plaintext, key) {
  const keyBytes = Buffer.from(key, "utf8");
  const cipher = crypto.createCipheriv("aes-128-ecb", keyBytes, "");
  let encrypted = cipher.update(plaintext, "utf8", "base64");
  encrypted += cipher.final("base64");
  return encrypted;
}

function encodePhone(phone) {
  return phone
    .split("")
    .map((char) => String.fromCharCode(char.charCodeAt(0) + 2))
    .join("");
}

function maskPhone(phone) {
  if (typeof phone === "string" && phone.length === 11) {
    return `${phone.slice(0, 3)}****${phone.slice(7)}`;
  }
  return phone;
}

function printn(message) {
  const now = new Date();
  const timeStr = now.toTimeString().split(" ")[0] + "." + String(now.getMilliseconds()).padStart(3, "0");
  console.log(`[${timeStr}] ${message}`);
}

function getFirstThree(value) {
  if (typeof value === "number") {
    return parseInt(String(value).slice(0, 3), 10);
  } else if (typeof value === "string") {
    return value.slice(0, 3);
  } else {
    throw new TypeError("error");
  }
}

// HTTP request helper
function httpRequest(options, data) {
  return new Promise((resolve, reject) => {
    const isHttps = options.protocol === "https:";
    const transport = isHttps ? https : http;

    const reqOptions = {
      hostname: options.hostname,
      port: options.port || (isHttps ? 443 : 80),
      path: options.path || "/",
      method: options.method || "GET",
      headers: options.headers || {},
      rejectUnauthorized: false,
    };

    const req = transport.request(reqOptions, (res) => {
      let body = "";
      res.on("data", (chunk) => (body += chunk));
      res.on("end", () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body,
          url: options.href || `${options.protocol}//${options.hostname}${reqOptions.path}`,
        });
      });
    });

    req.on("error", reject);
    if (data) {
      req.write(typeof data === "string" ? data : JSON.stringify(data));
    }
    req.end();
  });
}

async function userLoginNormal(phone, password) {
  const alphabet = "abcdef0123456789";
  const uuid = [
    Array.from({ length: 8 }, () => alphabet[Math.floor(Math.random() * alphabet.length)]).join(""),
    Array.from({ length: 4 }, () => alphabet[Math.floor(Math.random() * alphabet.length)]).join(""),
    "4" + Array.from({ length: 3 }, () => alphabet[Math.floor(Math.random() * alphabet.length)]).join(""),
    Array.from({ length: 4 }, () => alphabet[Math.floor(Math.random() * alphabet.length)]).join(""),
    Array.from({ length: 12 }, () => alphabet[Math.floor(Math.random() * alphabet.length)]).join(""),
  ];

  const timestamp = new Date()
    .toISOString()
    .replace(/[-:T.]/g, "")
    .slice(0, 14);

  const loginAuthCipherAsymmertric =
    "iPhone 14 15.4." +
    uuid[0] +
    uuid[1] +
    phone +
    timestamp +
    password.slice(0, 6) +
    "0$$$0.";

  try {
    const payload = {
      headerInfos: {
        code: "userLoginNormal",
        timestamp,
        broadAccount: "",
        broadToken: "",
        clientType: "#12.2.0#channel50#iPhone 14 Pro Max#",
        shopId: "20002",
        source: "110003",
        sourcePassword: "Sid98s",
        token: "",
        userLoginName: encodePhone(phone),
      },
      content: {
        attach: "test",
        fieldData: {
          loginType: "4",
          accountType: "",
          loginAuthCipherAsymmertric: rsaEncryptB64(loginAuthCipherAsymmertric),
          deviceUid: uuid[0] + uuid[1] + uuid[2],
          phoneNum: encodePhone(phone),
          isChinatelecom: "0",
          systemVersion: "15.4.0",
          authentication: encodePhone(password),
        },
      },
    };

    const response = await httpRequest(
      {
        protocol: "https:",
        hostname: "appgologin.189.cn",
        port: 9031,
        path: "/login/client/userLoginNormal",
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "User-Agent":
            "Mozilla/5.0 (Linux; Android 13; 22081212C Build/TKQ1.220829.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.97 Mobile Safari/537.36",
          Referer: "https://wapact.189.cn:9001/JinDouMall/JinDouMall_independentDetails.html",
        },
      },
      JSON.stringify(payload)
    );

    const result = JSON.parse(response.body);
    if (result.responseData && result.responseData.data) {
      const l = result.responseData.data;
      if (l && l.loginSuccessResult) {
        const lRes = l.loginSuccessResult;
        loadToken[phone] = lRes;
        fs.writeFileSync(loadTokenFile, JSON.stringify(loadToken, null, 2), "utf8");
        return await getTicket(phone, lRes.userId, lRes.token);
      }
    }
    printn(`   - 登录响应异常: ${JSON.stringify(result)}`);
  } catch (e) {
    printn(`   - 登录请求失败: ${e.message}`);
  }
  return false;
}

async function getTicket(phone, userId, token) {
  try {
    const xmlData = `<Request><HeaderInfos><Code>getSingle</Code><Timestamp>${new Date()
      .toISOString()
      .replace(/[-:T.]/g, "")
      .slice(0, 14)}</Timestamp><BroadAccount></BroadAccount><BroadToken></BroadToken><ClientType>#9.6.1#channel50#iPhone 14 Pro Max#</ClientType><ShopId>20002</ShopId><Source>110003</Source><SourcePassword>Sid98s</SourcePassword><Token>${token}</Token><UserLoginName>${phone}</UserLoginName></HeaderInfos><Content><Attach>test</Attach><FieldData><TargetId>${des3Encrypt(userId)}</TargetId><Url>4a6862274835b451</Url></FieldData></Content></Request>`;

    const response = await httpRequest(
      {
        protocol: "https:",
        hostname: "appgologin.189.cn",
        port: 9031,
        path: "/map/clientXML",
        method: "POST",
        headers: {
          "user-agent": "CtClient;10.4.1;Android;13;22081212C;NTQzNzgx!#!MTgwNTg1",
          "Content-Type": "application/xml;charset=utf-8",
        },
      },
      xmlData
    );

    const match = response.body.match(/<Ticket>(.*?)<\/Ticket>/);
    if (!match || match.length === 0) {
      return false;
    }
    return des3Decrypt(match[1]);
  } catch (e) {
    printn(`   - 获取Ticket失败: ${e.message}`);
    return false;
  }
}

function getSetCookieHeader(headers) {
  const setCookie = headers["set-cookie"] || "";
  if (Array.isArray(setCookie)) {
    return setCookie.join("; ");
  }
  return setCookie;
}

function extractReqparam(location) {
  if (!location) return "";
  const match = location.match(/[?&]reqparam=([^&]+)/);
  if (!match) return "";
  return decodeURIComponent(match[1]);
}

function extractNewmallsession(setCookie) {
  if (!setCookie) return "";
  const match = setCookie.match(/(newmallsession=[^;]+;)/);
  if (!match) return "";
  return match[1];
}

function getQueryParam(url, key) {
  if (!url) return "";
  const parsed = new URL(url);
  return parsed.searchParams.get(key) || "";
}

function normalizeCookieHeader(cookie) {
  return (cookie || "").trim().replace(/;$/, "");
}

async function requestMerchantsDock(reqparam, session, headers, location = "") {
  if (!reqparam) return null;

  let response;
  if (location) {
    response = await httpRequest({
      protocol: "https:",
      hostname: new URL(location).hostname,
      path: new URL(location).pathname + new URL(location).search,
      method: "GET",
      headers,
    });
  } else {
    const params = new URLSearchParams({ appcode: "HGOKHD", reqparam });
    response = await httpRequest({
      protocol: "https:",
      hostname: "m.telefen.com",
      path: `/MobileSSOv2/MerchantsDock.aspx?${params.toString()}`,
      method: "GET",
      headers,
    });
  }

  const locationHeader = response.headers.location || "";
  return {
    statusCode: response.statusCode,
    location: locationHeader,
    text: response.statusCode < 300 && response.statusCode >= 400 ? response.body.slice(0, 200) : "",
  };
}

function build517ApiContext(newmallsession, referer) {
  const token = getQueryParam(referer, "Token");
  const channel = getQueryParam(referer, "channel") || "HGOKHD";
  const promoid = getQueryParam(referer, "promoid");
  const cookie = normalizeCookieHeader(newmallsession);
  return {
    channel,
    promoid,
    token,
    referer,
    cookie,
    headers: {
      Accept: "application/json, text/plain, */*",
      "Accept-Encoding": "gzip, deflate, br",
      "Accept-Language": "zh-CN,zh;q=0.9",
      appcode: "HGOKHD",
      Connection: "keep-alive",
      "Content-Type": "application/json;charset=UTF-8",
      Cookie: cookie,
      Host: "apps.telefen.com",
      Referer: referer,
      "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
      "sec-ch-ua-mobile": "?1",
      "sec-ch-ua-platform": '"iOS"',
      "Sec-Fetch-Dest": "empty",
      "Sec-Fetch-Mode": "cors",
      "Sec-Fetch-Site": "same-origin",
      ssotoken: token,
      "User-Agent":
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1",
    },
  };
}

async function requestCk517Page(session, apiContext, referer = "") {
  if (!apiContext || !apiContext.referer) return null;

  const headers = {
    "User-Agent": apiContext.headers["User-Agent"],
    Accept:
      "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
    Cookie: apiContext.headers.Cookie,
    Referer: referer,
    "Upgrade-Insecure-Requests": "1",
    "sec-ch-ua": apiContext.headers["sec-ch-ua"],
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"iOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-site",
  };

  const response = await httpRequest({
    protocol: "https:",
    hostname: new URL(apiContext.referer).hostname,
    path: new URL(apiContext.referer).pathname + new URL(apiContext.referer).search,
    method: "GET",
    headers,
  });

  const setCookie = getSetCookieHeader(response.headers);
  const newmallsession = extractNewmallsession(setCookie);
  if (newmallsession) {
    const cookie = normalizeCookieHeader(newmallsession);
    apiContext.cookie = cookie;
    apiContext.headers.Cookie = cookie;
  }

  printn(`   - 517落地页: ${response.statusCode}`);
  return {
    statusCode: response.statusCode,
    url: response.url,
    setCookie,
    text: response.body.slice(0, 200),
  };
}

async function requestAccountCheck(session, apiContext) {
  if (!apiContext || !apiContext.token) return null;

  const params = new URLSearchParams({ noload: "true" });
  const response = await httpRequest({
    protocol: "https:",
    hostname: "apps.telefen.com",
    path: `/mallactive/api/account/check?${params.toString()}`,
    method: "GET",
    headers: apiContext.headers,
  });

  let data;
  try {
    data = JSON.parse(response.body);
  } catch {
    data = null;
  }

  const errCode = typeof data === "object" ? data.errCode : null;
  const errMsg = typeof data === "object" ? data.errMsg : response.body.slice(0, 200);
  const isLogin = !!(typeof data === "object" && data.data && data.data.deviceNo);
  printn(`   - 517登录态检查: status=${response.statusCode} code=${errCode} msg=${errMsg} login=${isLogin}`);
  return {
    statusCode: response.statusCode,
    url: response.url,
    params: Object.fromEntries(params),
    json: data,
    isLogin,
    text: data === null ? response.body.slice(0, 500) : "",
  };
}

async function requestActivityHome(session, apiContext) {
  if (!apiContext || !apiContext.token) return null;

  const params = new URLSearchParams({
    channel: apiContext.channel,
    noload: "true",
    activeCode: "2026517",
  });

  const response = await httpRequest({
    protocol: "https:",
    hostname: "apps.telefen.com",
    path: `/mallactive/api/v26517/activity/home?${params.toString()}`,
    method: "GET",
    headers: apiContext.headers,
  });

  let data;
  try {
    data = JSON.parse(response.body);
  } catch {
    data = null;
  }

  if (typeof data === "object" && data.errCode !== "0000") {
    printn(`   - 517任务列表异常: ${data?.errCode} ${data?.errMsg}`);
    printn(`   - 517任务列表URL: ${response.url}`);
    printn(`   - 517任务列表Referer: ${apiContext.headers.Referer || ""}`);
    printn(`   - 517任务列表Cookie: ${apiContext.headers.Cookie || ""}`);
    printn(`   - 517任务列表ssotoken: ${apiContext.headers.ssotoken || ""}`);
  }

  return {
    statusCode: response.statusCode,
    url: response.url,
    params: Object.fromEntries(params),
    headers: apiContext.headers,
    json: data,
    text: data === null ? response.body.slice(0, 500) : "",
  };
}

function parseActivityTasks(activityHome) {
  const data = activityHome?.json;
  if (typeof data !== "object") {
    printn("   - 517任务列表: 返回不是JSON");
    return [[], []];
  }

  const bizData = data.data || {};
  if (typeof bizData !== "object") {
    printn(`   - 517任务列表: data为空 ${data.errMsg || ""}`);
    return [[], []];
  }

  const taskList = bizData.taskList || [];
  const unfinishedTasks = [];

  for (const task of taskList) {
    const taskName = task.taskName || "";
    const taskType = task.taskType || "";
    const completedTimes = task.completedTimes || 0;
    const maxTimes = task.maxTimes || 0;
    const isFinished = task.isFinished || 0;
    const status = isFinished === 1 ? "已完成" : "未完成";
    printn(`   - 517任务: ${taskName} [${taskType}] ${completedTimes}/${maxTimes} ${status}`);
    if (isFinished !== 1) {
      unfinishedTasks.push(task);
    }
  }

  return [taskList, unfinishedTasks];
}

async function requestCompleteTask(session, apiContext, task) {
  const taskType = task.taskType || "";
  const taskName = task.taskName || taskType;
  const headers = { ...apiContext.headers, Origin: "https://apps.telefen.com" };
  const payload = {
    channel: apiContext.channel,
    taskType,
    activityId: "2026517",
    noload: true,
  };

  const response = await httpRequest({
    protocol: "https:",
    hostname: "apps.telefen.com",
    path: "/mallactive/api/v26517/task/complete",
    method: "POST",
    headers,
  }, JSON.stringify(payload));

  let data;
  try {
    data = JSON.parse(response.body);
  } catch {
    data = null;
  }

  let resultMsg = "";
  if (typeof data === "object") {
    resultMsg = data.errMsg || data.message || data.msg || "";
  } else {
    resultMsg = response.body.slice(0, 200);
  }

  printn(`   - 517完成任务: ${taskName} [${taskType}] status=${response.statusCode} ${resultMsg}`);
  return {
    statusCode: response.statusCode,
    payload,
    json: data,
    text: data === null ? response.body.slice(0, 500) : "",
  };
}

function isCompleteResponseFinished(data) {
  if (typeof data !== "object") return false;
  const values = [data.isFinished, data.finished, data.success];
  const bizData = data.data;
  if (typeof bizData === "object") {
    values.push(bizData.isFinished, bizData.finished, bizData.success);
  }
  return values.some((v) => v === true || v === 1 || v === "1");
}

async function syncSubWechatTaskStatus(session, apiContext, activityHome) {
  const data = activityHome?.json;
  const bizData = typeof data === "object" ? data.data : null;
  const taskList = typeof bizData === "object" ? bizData.taskList || [] : [];

  if (!Array.isArray(taskList)) return activityHome;

  const subWechatTask = taskList.find(
    (task) => typeof task === "object" && task.taskType === "SUB_WECHAT"
  );

  if (!subWechatTask || subWechatTask.isFinished === 1) return activityHome;

  printn("   - 517公众号任务: 按前端逻辑单独校验绑定状态");
  const result = await requestCompleteTask(session, apiContext, subWechatTask);
  subWechatTask._subWechatChecked = true;
  if (isCompleteResponseFinished(result.json)) {
    subWechatTask.isFinished = 1;
    subWechatTask.completedTimes = subWechatTask.maxTimes || 1;
    printn("   - 517公众号任务: 已关注绑定，同步为已完成");
  } else {
    printn("   - 517公众号任务: 接口仍返回未完成，继续走正常任务提交");
  }
  return activityHome;
}

const CARD_PIECES_517 = [
  [10000, "天翼云盘"],
  [10001, "天翼智铃"],
  [10002, "天翼智屏"],
  [10003, "通讯助理"],
  [10004, "云智手机"],
  [10005, "直连卫星"],
];

function toInt(value, defaultValue = 0) {
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? defaultValue : parsed;
}

function parse517PieceCollection(data) {
  const bizData = typeof data === "object" ? data.data || {} : {};
  if (typeof bizData !== "object") bizData = {};
  const pieceList = bizData.pieceList || [];
  const pieceMap = {};

  for (const piece of pieceList) {
    if (typeof piece !== "object") continue;
    const pieceId = toInt(piece.pieceId);
    const validPieceCount = toInt(piece.validPieceCount);
    const giftingPieceCount = toInt(piece.giftingPieceCount);
    const usedPieceCount = toInt(piece.usedPieceCount);
    pieceMap[pieceId] = {
      pieceId,
      pieceName: piece.pieceName || "",
      validPieceCount,
      giftingPieceCount,
      usedPieceCount,
      availableCount: validPieceCount + giftingPieceCount,
      raw: piece,
    };
  }

  const cards = [];
  const missing = [];
  for (const [pieceId, name] of CARD_PIECES_517) {
    const item = pieceMap[pieceId] || {};
    const availableCount = toInt(item.availableCount);
    const usedPieceCount = toInt(item.usedPieceCount);
    cards.push({
      pieceId,
      pieceName: item.pieceName || name,
      availableCount,
      usedPieceCount,
    });
    if (availableCount <= 0) {
      missing.push(name);
    }
  }

  return {
    cards,
    missing,
    isAllCollected: missing.length === 0,
    pieceList,
  };
}

function print517PieceCollection(collection) {
  const cards = typeof collection === "object" ? collection.cards || [] : [];
  const parts = [];
  for (const card of cards) {
    const usedCount = toInt(card.usedPieceCount);
    const suffix = usedCount > 0 ? `(已用${usedCount})` : "";
    parts.push(`${card.pieceName}x${card.availableCount || 0}${suffix}`);
  }
  if (parts.length > 0) {
    printn(`   - 517卡片: ${parts.join("，")}`);
  }

  const missing = typeof collection === "object" ? collection.missing || [] : [];
  if (missing.length > 0) {
    printn(`   - 517卡片: 未集齐，缺少 ${missing.join("、")}`);
  } else {
    printn("   - 517卡片: 已集齐，可合成");
  }
}

function has517CompositeRecordPayload(data) {
  if (typeof data === "boolean") return data;
  if (typeof data !== "object") return false;
  return !!(
    data.hasCompositeRecord ||
    data.isComposite ||
    data.isComposited ||
    data.compositeRecord ||
    data.compositeRecordId != null ||
    data.id != null ||
    data.compositeTime ||
    data.commodityId ||
    data.commodityName
  );
}

async function requestMyPieceList(session, apiContext) {
  const params = new URLSearchParams({ gameId: "10000" });
  const response = await httpRequest({
    protocol: "https:",
    hostname: "apps.telefen.com",
    path: `/mallactive/api/fragment/getMyPieceList?${params.toString()}`,
    method: "GET",
    headers: apiContext.headers,
  });

  let data;
  try {
    data = JSON.parse(response.body);
  } catch {
    data = null;
  }

  let totalChanceCount = 0;
  let collection = {
    cards: [],
    missing: CARD_PIECES_517.map(([, name]) => name),
    isAllCollected: false,
    pieceList: [],
  };

  if (typeof data === "object") {
    const bizData = data.data || {};
    if (typeof bizData === "object") {
      totalChanceCount = bizData.totalChanceCount || 0;
    }
    collection = parse517PieceCollection(data);
  }

  printn(`   - 517抽奖次数: ${totalChanceCount}`);
  print517PieceCollection(collection);

  return {
    statusCode: response.statusCode,
    params: Object.fromEntries(params),
    json: data,
    totalChanceCount,
    collection,
    text: data === null ? response.body.slice(0, 500) : "",
  };
}

async function requestFragmentCompositeRecord(session, apiContext) {
  const headers = { ...apiContext.headers, Origin: "https://apps.telefen.com" };
  const payload = { gameId: "10000" };

  const response = await httpRequest({
    protocol: "https:",
    hostname: "apps.telefen.com",
    path: "/mallactive/api/fragment/getCompositeRecord",
    method: "POST",
    headers,
  }, JSON.stringify(payload));

  let data;
  try {
    data = JSON.parse(response.body);
  } catch {
    data = null;
  }

  const bizData = typeof data === "object" ? data.data : null;
  const hasRecord = has517CompositeRecordPayload(bizData);

  if (typeof data === "object") {
    printn(`   - 517合成记录: ${hasRecord ? "已有" : "暂无"} ${data.errMsg || ""}`);
    if (hasRecord && typeof bizData === "object") {
      const prizeName = bizData.commodityName || bizData.prizeName || "";
      if (prizeName) {
        printn(`   - 517已有奖品: ${prizeName}`);
      }
    }
  } else {
    printn(`   - 517合成记录: status=${response.statusCode} ${response.body.slice(0, 200)}`);
  }

  return {
    statusCode: response.statusCode,
    payload,
    json: data,
    hasRecord,
    text: data === null ? response.body.slice(0, 500) : "",
  };
}

async function requestFragmentComposite(session, apiContext) {
  const headers = { ...apiContext.headers, Origin: "https://apps.telefen.com" };
  const payload = {
    gameId: "10000",
    appCode: apiContext.channel || "HGOKHD",
  };

  const response = await httpRequest({
    protocol: "https:",
    hostname: "apps.telefen.com",
    path: "/mallactive/api/fragment/composite",
    method: "POST",
    headers,
  }, JSON.stringify(payload));

  let data;
  try {
    data = JSON.parse(response.body);
  } catch {
    data = null;
  }

  if (typeof data === "object") {
    printn(`   - 517合成结果: ${data.errMsg || ""}`);
    const bizData = data.data || {};
    if (typeof bizData === "object") {
      const success = bizData.success;
      const recordId = bizData.compositeRecordId || bizData.id;
      const isWon = bizData.isWon;
      const prizeName = bizData.commodityName || bizData.prizeName || "";
      const prizeType = bizData.commodityType;
      const receivedStatus = bizData.receivedStatus;
      printn(
        `   - 517合成记录ID: ${recordId} success=${success} isWon=${isWon} receivedStatus=${receivedStatus}`
      );
      if (isWon === false) {
        printn("   - 517合成: 未中奖");
      } else if (prizeName) {
        printn(`   - 517合成奖品: ${prizeName} type=${prizeType}`);
      }
      if (prizeType === 1) {
        printn("   - 517合成: 实物奖品需要在页面填写收货地址");
      }
    }
  } else {
    printn(`   - 517合成结果: status=${response.statusCode} ${response.body.slice(0, 200)}`);
  }

  return {
    statusCode: response.statusCode,
    payload,
    json: data,
    text: data === null ? response.body.slice(0, 500) : "",
  };
}

async function maybeComposite517(session, apiContext, pieceInfo = null) {
  if (!pieceInfo) {
    pieceInfo = await requestMyPieceList(session, apiContext);
  }
  const collection = typeof pieceInfo === "object" ? pieceInfo.collection || {} : {};
  if (!collection.isAllCollected) return null;

  const record = await requestFragmentCompositeRecord(session, apiContext);
  if (record && record.hasRecord) {
    printn("   - 517合成: 已有合成记录，跳过");
    return record;
  }

  printn("   - 517合成: 六张卡已集齐，开始合成");
  return await requestFragmentComposite(session, apiContext);
}

async function requestFragmentDraw(session, apiContext, drawCount) {
  const headers = { ...apiContext.headers, Origin: "https://apps.telefen.com" };
  const payload = {
    drawCount,
    gameId: "10000",
    activityId: "2026517",
  };

  const response = await httpRequest({
    protocol: "https:",
    hostname: "apps.telefen.com",
    path: "/mallactive/api/fragment/draw",
    method: "POST",
    headers,
  }, JSON.stringify(payload));

  let data;
  try {
    data = JSON.parse(response.body);
  } catch {
    data = null;
  }

  if (typeof data === "object") {
    printn(`   - 517抽奖结果: ${data.errMsg || ""}`);
    const bizData = data.data || {};
    const winPieceList = typeof bizData === "object" ? bizData.winPieceList || [] : [];
    if (winPieceList.length > 0) {
      for (const piece of winPieceList) {
        printn(`   - 517抽中: ${piece.pieceName || ""} x${piece.count || 0}`);
      }
    } else {
      printn("   - 517抽奖: 未获得碎片");
    }
  } else {
    printn(`   - 517抽奖结果: status=${response.statusCode} ${response.body.slice(0, 200)}`);
  }

  return {
    statusCode: response.statusCode,
    payload,
    json: data,
    text: data === null ? response.body.slice(0, 500) : "",
  };
}

async function ck517(ticket, session) {
  try {
    const params = new URLSearchParams({
      channel: "HGOKHD",
      action: "2",
      rdurl: "https://apps.telefen.com/mallactive/ck517?channel=HGOKHD",
      promoid: "f15c4b971ecfa50b",
      ticket,
      utm_scha:
        "utm_ch-010001002009.utm_sch-hg_sy_yxtc-1.utm_af-1000000037.utm_as-456876200001.utm_sd1-S0076579",
    });

    const headers = {
      "User-Agent": "CtClient;13.2.0;Android;14;22021211RC;",
      Accept:
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
      "Accept-Encoding": "gzip, deflate, br, zstd",
      "Upgrade-Insecure-Requests": "1",
      "X-Requested-With": "com.ct.client",
      "Sec-Fetch-Site": "none",
      "Sec-Fetch-Mode": "navigate",
      "Sec-Fetch-User": "?1",
      "Sec-Fetch-Dest": "document",
      "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Android WebView";v="120"',
      "sec-ch-ua-mobile": "?1",
      "sec-ch-ua-platform": '"Android"',
      "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    };

    const response = await httpRequest({
      protocol: "https:",
      hostname: "apps.telefen.com",
      path: `/mallactive/api/access/ticket?${params.toString()}`,
      method: "GET",
      headers,
    });

    const setCookie = getSetCookieHeader(response.headers);
    const location = response.headers.location || "";
    const reqparam = extractReqparam(location);
    const newmallsession = extractNewmallsession(setCookie);

    if ([301, 302, 303, 307, 308].includes(response.statusCode)) {
      printn(`   - 517跳转: ${response.statusCode}`);
      printn(`   - 517 获取cookie成功: ${setCookie}`);
      const merchantsDock = await requestMerchantsDock(reqparam, session, headers, location);
      if (merchantsDock) {
        printn(`   - 517二跳: ${merchantsDock.statusCode}`);
        printn(`   - 517二跳 Location: ${merchantsDock.location}`);
      }
      const apiContext = build517ApiContext(
        newmallsession,
        merchantsDock?.location || ""
      );
      printn(`   - 517后续获取Token成功: ${apiContext.token}`);
      const ck517Page = await requestCk517Page(session, apiContext, location);
      const accountCheck = await requestAccountCheck(session, apiContext);
      return {
        statusCode: response.statusCode,
        setCookie,
        newmallsession,
        location,
        reqparam,
        merchantsDock,
        ck517Page,
        accountCheck,
        apiContext,
      };
    }

    printn(`   - 517接口未返回302: status=${response.statusCode}, body=${response.body.slice(0, 200)}`);
    return {
      statusCode: response.statusCode,
      setCookie,
      newmallsession,
      location,
      reqparam,
      text: response.body,
    };
  } catch (e) {
    printn(`   - 517登录: 发生错误 ❌: ${e.message}`);
    return null;
  }
}

async function ks(phone, ticket) {
  const session = {};

  const ck517Info = await ck517(ticket, session);
  if (!ck517Info || !ck517Info.apiContext) {
    printn("   - 517任务列表: 缺少后续请求参数");
    return;
  }

  const activityHome = await requestActivityHome(session, ck517Info.apiContext);
  if (activityHome) {
    printn(`   - 517任务列表: ${activityHome.statusCode}`);
    await syncSubWechatTaskStatus(session, ck517Info.apiContext, activityHome);
    const [taskList, unfinishedTasks] = parseActivityTasks(activityHome);
    printn(`   - 517任务数量: 总计${taskList.length}个，未完成${unfinishedTasks.length}个`);

    for (const task of unfinishedTasks) {
      const completedTimes = task.completedTimes || 0;
      const maxTimes = task.maxTimes || 1;
      const remainingTimes = Math.max(maxTimes - completedTimes, 1);
      for (let index = 0; index < remainingTimes; index++) {
        printn(
          `   - 517提交完成: ${task.taskName || task.taskType} 第${index + 1}/${remainingTimes}次`
        );
        await requestCompleteTask(session, ck517Info.apiContext, task);
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
    }

    const pieceInfo = await requestMyPieceList(session, ck517Info.apiContext);
    const drawCount = pieceInfo?.totalChanceCount || 0;
    if (drawCount > 0) {
      printn(`   - 517开始抽奖: 一次性抽${drawCount}次`);
      await requestFragmentDraw(session, ck517Info.apiContext, drawCount);
      await requestMyPieceList(session, ck517Info.apiContext);
    } else {
      printn("   - 517抽奖: 暂无可用次数");
    }

    await maybeComposite517(session, ck517Info.apiContext, pieceInfo);
  }
}

async function main() {
  printn(PHONES);
  if (!PHONES) {
    printn("❌ 未在环境变量中找到 `chinaTelecomAccount`, 请检查配置。");
    return;
  }

  const phoneList = PHONES.split(/[&\n@]/).filter((acc) => acc.trim());
  printn(`   - ✨ 检测到 ${phoneList.length} 个账号，准备开始执行任务...`);
  printn("-".repeat(50));

  for (let index = 0; index < phoneList.length; index++) {
    const phoneV = phoneList[index];
    printn(`   - 👤 开始处理第 ${index + 1} / ${phoneList.length} 个账号...`);
    const value = phoneV.split("#");
    if (value.length < 2) {
      printn(`   - ❌ 账号格式错误, 跳过: ${phoneV}`);
      printn("-".repeat(50));
      continue;
    }

    const [phone, password] = value;
    const maskedPhone = maskPhone(phone);
    const maxRetries = 3;
    let retryCount = 0;
    let ticket = false;

    while (retryCount < maxRetries && !ticket) {
      retryCount++;
      printn(`   - 🔄 账号 ${maskedPhone} 第 ${retryCount} 次登录尝试...`);

      if (loadToken[phone]) {
        printn(`   - 🎨 尝试使用缓存Token登录...`);
        ticket = await getTicket(phone, loadToken[phone].userId, loadToken[phone].token);
      }

      if (!ticket) {
        printn(`   - 🎨 缓存无效或不存在，尝试使用密码登录...`);
        ticket = await userLoginNormal(phone, password);
      }

      if (ticket) {
        printn(`   - 🔑 账号 ${maskedPhone} 登录成功 ✅`);
        break;
      } else {
        printn(`   - ❌ 账号 ${maskedPhone} 第 ${retryCount} 次登录失败`);
        if (retryCount < maxRetries) {
          await new Promise((resolve) => setTimeout(resolve, 2000));
        }
      }
    }

    if (ticket) {
      await ks(phone, ticket);
      printn(`   - ✅ 第 ${index + 1} 个账号 ${maskedPhone} 的所有任务执行完毕。`);
    } else {
      printn(
        `   - ❌ 账号 ${maskedPhone} 登录失败，已达最大重试次数，跳过此账号。`
      );
    }

    printn("-".repeat(50));
    if (index < phoneList.length - 1) {
      await new Promise((resolve) => setTimeout(resolve, 3000));
    }
  }
}

const loadTokenFile = path.join(__dirname, "chinaTelecom_cache.json");
let loadToken = {};
try {
  if (fs.existsSync(loadTokenFile)) {
    loadToken = JSON.parse(fs.readFileSync(loadTokenFile, "utf8"));
  }
} catch {}

const PHONES = process.env.chinaTelecomAccount;
if (require.main === module) {
  main().finally(() => {
    printn("电信任务结束");
  });
}

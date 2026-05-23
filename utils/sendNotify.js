const Env = require('./env');
const querystring = require('querystring');
const got = require('got');
const crypto = require("crypto");
const $ = new Env();
const timeout = 15000; // 超时时间(单位毫秒)
// =======================================gotify通知设置区域==============================================
// gotify_url 填写gotify地址,如https://push.example.de:8080
// gotify_token 填写gotify的消息应用token
// gotify_priority 填写推送消息优先级,默认为0
let GOTIFY_URL = '';
let GOTIFY_TOKEN = '';
let GOTIFY_PRIORITY = 0;
// =======================================go-cqhttp通知设置区域===========================================
// gobot_url 填写请求地址http://127.0.0.1/send_private_msg
// gobot_token 填写在go-cqhttp文件设置的访问密钥
// gobot_qq 填写推送到个人QQ或者QQ群号
// go-cqhttp相关API https://docs.go-cqhttp.org/api
let GOBOT_URL = ''; // 推送到个人QQ: http://127.0.0.1/send_private_msg  群：http://127.0.0.1/send_group_msg
let GOBOT_TOKEN = ''; // 访问密钥
let GOBOT_QQ = ''; // 如果GOBOT_URL设置 /send_private_msg 则需要填入 user_id=个人QQ 相反如果是 /send_group_msg 则需要填入 group_id=QQ群

// =======================================微信server酱通知设置区域===========================================
// 此处填你申请的SCKEY.
// (环境变量名 PUSH_KEY)
let SCKEY = '';

// =======================================PushDeer通知设置区域===========================================
// 此处填你申请的PushDeer KEY.
// (环境变量名 DEER_KEY)
let PUSHDEER_KEY = '';
let PUSHDEER_URL = '';

// =======================================Synology Chat通知设置区域===========================================
// 此处填你申请的CHAT_URL与CHAT_TOKEN
// (环境变量名 CHAT_URL CHAT_TOKEN)
let CHAT_URL = '';
let CHAT_TOKEN = '';

// =======================================Bark App通知设置区域===========================================
// 此处填你BarkAPP的信息(IP/设备码，例如：https://api.day.app/XXXXXXXX)
let BARK_PUSH = '';
// BARK app推送图标,自定义推送图标(需iOS15或以上)
let BARK_ICON = 'https://npm.elemecdn.com/nanshen/favicon.ico';
// BARK app推送铃声,铃声列表去APP查看复制填写
let BARK_SOUND = '';
// BARK app推送消息的分组, 默认为"QingLong"
let BARK_GROUP = 'Script';
// BARK app推送消息的时效性, 默认为"active"
let BARK_LEVEL = 'active';
// BARK app推送消息的跳转URL
let BARK_URL = '';

// =======================================telegram机器人通知设置区域===========================================
// 此处填你telegram bot 的Token，telegram机器人通知推送必填项.例如：1077xxx4424:AAFjv0FcqxxxxxxgEMGfi22B4yh15R5uw
// (环境变量名 TG_BOT_TOKEN)
let TG_BOT_TOKEN = '';
// 此处填你接收通知消息的telegram用户的id，telegram机器人通知推送必填项.例如：129xxx206
// (环境变量名 TG_USER_ID)
let TG_USER_ID = '';
// tg推送HTTP代理设置(不懂可忽略,telegram机器人通知推送功能中非必填)
let TG_PROXY_HOST = ''; // 例如:127.0.0.1(环境变量名:TG_PROXY_HOST)
let TG_PROXY_PORT = ''; // 例如:1080(环境变量名:TG_PROXY_PORT)
let TG_PROXY_AUTH = ''; // tg代理配置认证参数
// Telegram api自建的反向代理地址(不懂可忽略,telegram机器人通知推送功能中非必填),默认tg官方api(环境变量名:TG_API_HOST)
let TG_API_HOST = 'https://api.telegram.org';
// =======================================钉钉机器人通知设置区域===========================================
// 此处填你钉钉 bot 的webhook，例如：5a544165465465645d0f31dca676e7bd07415asdasd
// (环境变量名 DD_BOT_TOKEN)
let DD_BOT_TOKEN = '';
// 密钥，机器人安全设置页面，加签一栏下面显示的SEC开头的字符串
let DD_BOT_SECRET = '';

// =======================================企业微信基础设置===========================================
// 企业微信反向代理地址
// (环境变量名 QYWX_ORIGIN)
let QYWX_ORIGIN = '';
// =======================================企业微信机器人通知设置区域===========================================
// 此处填你企业微信机器人的 webhook(详见文档 https://work.weixin.qq.com/api/doc/90000/90136/91770)，例如：693a91f6-7xxx-4bc4-97a0-0ec2sifa5aaa
// (环境变量名 QYWX_KEY)
let QYWX_KEY = '';

// =======================================企业微信应用消息通知设置区域===========================================
/*
 此处填你企业微信应用消息的值(详见文档 https://work.weixin.qq.com/api/doc/90000/90135/90236)
 环境变量名 QYWX_AM依次填入 corpid,corpsecret,touser(注:多个成员ID使用|隔开),agentid,消息类型(选填,不填默认文本消息类型)
 注意用,号隔开(英文输入法的逗号)，例如：wwcff56746d9adwers,B-791548lnzXBE6_BWfxdf3kSTMJr9vFEPKAbh6WERQ,mingcheng,1000001,2COXgjH2UIfERF2zxrtUOKgQ9XklUqMdGSWLBoW_lSDAdafat
 可选推送消息类型(推荐使用图文消息（mpnews）):
 - 文本卡片消息: 0 (数字零)
 - 文本消息: 1 (数字一)
 - 图文消息（mpnews）: 素材库图片id, 可查看此教程(http://note.youdao.com/s/HMiudGkb)或者(https://note.youdao.com/ynoteshare1/index.html?id=1a0c8aff284ad28cbd011b29b3ad0191&type=note)
 */
let QYWX_AM = '';

// =======================================iGot聚合推送通知设置区域===========================================
// 此处填您iGot的信息(推送key，例如：https://push.hellyw.com/XXXXXXXX)
let IGOT_PUSH_KEY = '';

// =======================================push+设置区域=======================================
// 官方文档：http://www.pushplus.plus/
// PUSH_PLUS_TOKEN：微信扫码登录后一对一推送或一对多推送下面的token(您的Token)，不提供PUSH_PLUS_USER则默认为一对一推送
// PUSH_PLUS_USER： 一对多推送的“群组编码”（一对多推送下面->您的群组(如无则新建)->群组编码，如果您是创建群组人。也需点击“查看二维码”扫描绑定，否则不能接受群组消息推送）
let PUSH_PLUS_TOKEN = '';
let PUSH_PLUS_USER = '';

// =======================================wxpusher设置区域=======================================
// 官方文档：https://wxpusher.zjiecode.com/docs/
let WXPUSHER_TOKEN = '';
let WXPUSHER_UID = '';


// =======================================智能微秘书设置区域=======================================
// 官方文档：http://wechat.aibotk.com/docs/about
// AIBOTK_KEY： 填写智能微秘书个人中心的apikey
// AIBOTK_TYPE：填写发送的目标 room 或 contact, 填其他的不生效
// AIBOTK_NAME: 填写群名或用户昵称，和上面的type类型要对应
let AIBOTK_KEY = '';
let AIBOTK_TYPE = '';
let AIBOTK_NAME = '';

// =======================================飞书机器人设置区域=======================================
// 官方文档：https://www.feishu.cn/hc/zh-CN/articles/360024984973
// FSKEY 飞书机器人的 FSKEY
let FSKEY = '';

// =======================================SMTP 邮件设置区域=======================================
// SMTP_SERVICE: 邮箱服务名称，比如126、163、Gmail、QQ等，支持列表 https://github.com/nodemailer/nodemailer/blob/master/lib/well-known/services.json
// SMTP_EMAIL: 填写 SMTP 收发件邮箱，通知将会由自己发给自己
// SMTP_PASSWORD: 填写 SMTP 登录密码，也可能为特殊口令，视具体邮件服务商说明而定
// SMTP_NAME: 填写 SMTP 收发件人姓名，可随意填写
let SMTP_SERVICE = '';
let SMTP_EMAIL = '';
let SMTP_PASSWORD = '';
let SMTP_NAME = '';

// =======================================PushMe通知设置区域===========================================
// 官方文档：https://push.i-i.me/
// 此处填你的PushMe KEY.
let PUSHME_KEY = '';

// =======================================CHRONOCAT通知设置区域===========================================
// CHRONOCAT_URL Red协议连接地址 例： http://127.0.0.1:16530
// CHRONOCAT_TOKEN 填写在CHRONOCAT文件生成的访问密钥
// CHRONOCAT_QQ 个人:user_id=个人QQ 群则填入group_id=QQ群 多个用英文;隔开同时支持个人和群
// CHRONOCAT相关API https://chronocat.vercel.app/install/docker/official/
let CHRONOCAT_URL = ''; // CHRONOCAT Red协议连接地址
let CHRONOCAT_TOKEN = ''; // CHRONOCAT 生成的访问密钥
let CHRONOCAT_QQ = ''; // 个人:user_id=个人QQ 群则填入group_id=QQ群 多个用英文;隔开同时支持个人和群 如：user_id=xxx;group_id=xxxx;group_id=xxxxx

// =======================================自定义通知设置区域=======================================
// 自定义通知 接收回调的URL
let WEBHOOK_URL = '';
let WEBHOOK_BODY = '';
let WEBHOOK_HEADERS = '';
let WEBHOOK_METHOD = '';
let WEBHOOK_CONTENT_TYPE = '';

// ==========================云端环境变量的判断与接收=========================
if (process.env.GOTIFY_URL) {
    GOTIFY_URL = process.env.GOTIFY_URL;
}
if (process.env.GOTIFY_TOKEN) {
    GOTIFY_TOKEN = process.env.GOTIFY_TOKEN;
}
if (process.env.GOTIFY_PRIORITY) {
    GOTIFY_PRIORITY = process.env.GOTIFY_PRIORITY;
}

if (process.env.GOBOT_URL) {
    GOBOT_URL = process.env.GOBOT_URL;
}
if (process.env.GOBOT_TOKEN) {
    GOBOT_TOKEN = process.env.GOBOT_TOKEN;
}
if (process.env.GOBOT_QQ) {
    GOBOT_QQ = process.env.GOBOT_QQ;
}

if (process.env.PUSH_KEY) {
    SCKEY = process.env.PUSH_KEY;
}

if (process.env.DEER_KEY) {
    PUSHDEER_KEY = process.env.DEER_KEY;
    PUSHDEER_URL = process.env.DEER_URL;
}

if (process.env.CHAT_URL) {
    CHAT_URL = process.env.CHAT_URL;
}

if (process.env.CHAT_TOKEN) {
    CHAT_TOKEN = process.env.CHAT_TOKEN;
}

if (process.env.QQ_SKEY) {
    QQ_SKEY = process.env.QQ_SKEY;
}

if (process.env.QQ_MODE) {
    QQ_MODE = process.env.QQ_MODE;
}

if (process.env.BARK_PUSH) {
    if (
        process.env.BARK_PUSH.indexOf('https') > -1 ||
        process.env.BARK_PUSH.indexOf('http') > -1
    ) {
        // 兼容BARK自建用户
        BARK_PUSH = process.env.BARK_PUSH;
    } else {
        BARK_PUSH = `https://api.day.app/${process.env.BARK_PUSH}`;
    }
    if (process.env.BARK_ICON) {
        BARK_ICON = process.env.BARK_ICON;
    }
    if (process.env.BARK_SOUND) {
        BARK_SOUND = process.env.BARK_SOUND;
    }
    if (process.env.BARK_GROUP) {
        BARK_GROUP = process.env.BARK_GROUP;
    }
    if (process.env.BARK_LEVEL) {
        BARK_LEVEL = process.env.BARK_LEVEL;
    }
    if (process.env.BARK_URL) {
        BARK_URL = process.env.BARK_URL;
    }
} else {
    if (
        BARK_PUSH &&
        BARK_PUSH.indexOf('https') === -1 &&
        BARK_PUSH.indexOf('http') === -1
    ) {
        // 兼容BARK本地用户只填写设备码的情况
        BARK_PUSH = `https://api.day.app/${BARK_PUSH}`;
    }
}
if (process.env.TG_BOT_TOKEN) {
    TG_BOT_TOKEN = process.env.TG_BOT_TOKEN;
}
if (process.env.TG_USER_ID) {
    TG_USER_ID = process.env.TG_USER_ID;
}
if (process.env.TG_PROXY_AUTH) TG_PROXY_AUTH = process.env.TG_PROXY_AUTH;
if (process.env.TG_PROXY_HOST) TG_PROXY_HOST = process.env.TG_PROXY_HOST;
if (process.env.TG_PROXY_PORT) TG_PROXY_PORT = process.env.TG_PROXY_PORT;
if (process.env.TG_API_HOST) TG_API_HOST = process.env.TG_API_HOST;

if (process.env.DD_BOT_TOKEN) {
    DD_BOT_TOKEN = process.env.DD_BOT_TOKEN;
    if (process.env.DD_BOT_SECRET) {
        DD_BOT_SECRET = process.env.DD_BOT_SECRET;
    }
}

if (process.env.QYWX_ORIGIN) {
    QYWX_ORIGIN = process.env.QYWX_ORIGIN;
} else {
    QYWX_ORIGIN = 'https://qyapi.weixin.qq.com';
}

if (process.env.QYWX_KEY) {
    QYWX_KEY = process.env.QYWX_KEY;
}

if (process.env.QYWX_AM) {
    QYWX_AM = process.env.QYWX_AM;
}

if (process.env.IGOT_PUSH_KEY) {
    IGOT_PUSH_KEY = process.env.IGOT_PUSH_KEY;
}

if (process.env.PUSH_PLUS_TOKEN) {
    PUSH_PLUS_TOKEN = process.env.PUSH_PLUS_TOKEN;
}

if (process.env.PUSH_PLUS_USER) {
    PUSH_PLUS_USER = process.env.PUSH_PLUS_USER;
}

if (process.env.WXPUSHER_TOKEN) {
    WXPUSHER_TOKEN = process.env.WXPUSHER_TOKEN;
}
if (process.env.WXPUSHER_UID) {
    WXPUSHER_UID = process.env.WXPUSHER_UID;
}

if (process.env.AIBOTK_KEY) {
    AIBOTK_KEY = process.env.AIBOTK_KEY;
}
if (process.env.AIBOTK_TYPE) {
    AIBOTK_TYPE = process.env.AIBOTK_TYPE;
}
if (process.env.AIBOTK_NAME) {
    AIBOTK_NAME = process.env.AIBOTK_NAME;
}

if (process.env.FSKEY) {
    FSKEY = process.env.FSKEY;
}

if (process.env.SMTP_SERVICE) {
    SMTP_SERVICE = process.env.SMTP_SERVICE;
}
if (process.env.SMTP_EMAIL) {
    SMTP_EMAIL = process.env.SMTP_EMAIL;
}
if (process.env.SMTP_PASSWORD) {
    SMTP_PASSWORD = process.env.SMTP_PASSWORD;
}
if (process.env.SMTP_NAME) {
    SMTP_NAME = process.env.SMTP_NAME;
}
if (process.env.PUSHME_KEY) {
    PUSHME_KEY = process.env.PUSHME_KEY;
}

if (process.env.CHRONOCAT_URL) {
    CHRONOCAT_URL = process.env.CHRONOCAT_URL;
}
if (process.env.CHRONOCAT_QQ) {
    CHRONOCAT_QQ = process.env.CHRONOCAT_QQ;
}
if (process.env.CHRONOCAT_TOKEN) {
    CHRONOCAT_TOKEN = process.env.CHRONOCAT_TOKEN;
}

if (process.env.WEBHOOK_URL) {
    WEBHOOK_URL = process.env.WEBHOOK_URL;
}
if (process.env.WEBHOOK_BODY) {
    WEBHOOK_BODY = process.env.WEBHOOK_BODY;
}
if (process.env.WEBHOOK_HEADERS) {
    WEBHOOK_HEADERS = process.env.WEBHOOK_HEADERS;
}
if (process.env.WEBHOOK_METHOD) {
    WEBHOOK_METHOD = process.env.WEBHOOK_METHOD;
}
if (process.env.WEBHOOK_CONTENT_TYPE) {
    WEBHOOK_CONTENT_TYPE = process.env.WEBHOOK_CONTENT_TYPE;
}

// ==========================云端环境变量的判断与接收=========================

/**
 * sendNotify 推送通知功能
 * @param text 通知头
 * @param desp 通知体
 * @param params 某些推送通知方式点击弹窗可跳转, 例：{ url: 'https://abc.com' }
 * @param author
 * @returns {Promise<unknown>}
 */
async function sendNotify(text, desp, params = {}, author = '') {
    // 提供6种通知
    // desp += author;

    // 根据标题跳过一些消息推送，环境变量：SKIP_PUSH_TITLE 用回车分隔
    let skipTitle = process.env.SKIP_PUSH_TITLE;
    if (skipTitle) {
        if (skipTitle.split('\n').includes(text)) {
            console.info(text + '在SKIP_PUSH_TITLE环境变量内，跳过推送！');
            return;
        }
    }
    await Promise.all([
        serverNotify(text, desp), // 微信server酱
        pushPlusNotify(text, desp), // pushplus(推送加)
        wxPusherNotify(text, desp),
    ]);
    // 由于上述两种微信通知需点击进去才能查看到详情，故text(标题内容)携带了账号序号以及昵称信息，方便不点击也可知道是哪个京东哪个活动
    text = text.match(/.*?(?=\s?-)/g) ? text.match(/.*?(?=\s?-)/g)[0] : text;
    await Promise.all([
        BarkNotify(text, desp, params), // iOS Bark APP
        tgBotNotify(text, desp), // telegram 机器人
        ddBotNotify(text, desp), // 钉钉机器人
        qywxBotNotify(text, desp), // 企业微信机器人
        qywxamNotify(text, desp), // 企业微信应用消息推送
        iGotNotify(text, desp, params), // iGot
        gobotNotify(text, desp), // go-cqhttp
        gotifyNotify(text, desp), // gotify
        ChatNotify(text, desp), // synolog chat
        PushDeerNotify(text, desp), // PushDeer
        aibotkNotify(text, desp), // 智能微秘书
        fsBotNotify(text, desp), // 飞书机器人
        smtpNotify(text, desp), // SMTP 邮件
        pushMeNotify(text, desp, params), // PushMe
        chronocatNotify(text, desp), // Chronocat
        webhookNotify(text, desp), // 自定义通知
    ]);
}

function gotifyNotify(text, desp) {
    return new Promise((resolve) => {
        if (GOTIFY_URL && GOTIFY_TOKEN) {
            const options = {
                url: `${GOTIFY_URL}/message?token=${GOTIFY_TOKEN}`,
                body: `title=${encodeURIComponent(text)}&message=${encodeURIComponent(
                    desp,
                )}&priority=${GOTIFY_PRIORITY}`,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            };
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log('\ngotify发送通知调用API失败！！\n');
                        console.log(err);
                    } else {
                        data = JSON.parse(data);
                        if (data.id) {
                            console.log('\ngotify发送通知消息成功🎉\n');
                        } else {
                            console.log(`${data.message}\n`);
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve();
                }
            });
        } else {
            resolve();
        }
    });
}

function gobotNotify(text, desp) {
    return new Promise((resolve) => {
        if (GOBOT_URL) {
            const options = {
                url: `${GOBOT_URL}?access_token=${GOBOT_TOKEN}&${GOBOT_QQ}`,
                json: {message: `${text}\n${desp}`},
                headers: {
                    'Content-Type': 'application/json',
                },
                timeout,
            };
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log('\n发送go-cqhttp通知调用API失败！！\n');
                        console.log(err);
                    } else {
                        data = JSON.parse(data);
                        if (data.retcode === 0) {
                            console.log('\ngo-cqhttp发送通知消息成功🎉\n');
                        } else if (data.retcode === 100) {
                            console.log(`\ngo-cqhttp发送通知消息异常: ${data.errmsg}\n`);
                        } else {
                            console.log(`\ngo-cqhttp发送通知消息异常\n${JSON.stringify(data)}`);
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve(data);
                }
            });
        } else {
            resolve();
        }
    });
}

function serverNotify(text, desp) {
    return new Promise((resolve) => {
        if (SCKEY) {
            // 微信server酱推送通知一个\n不会换行，需要两个\n才能换行，故做此替换
            desp = desp.replace(/[\n\r]/g, '\n\n');
            const options = {
                url: SCKEY.includes('SCT')
                    ? `https://sctapi.ftqq.com/${SCKEY}.send`
                    : `https://sc.ftqq.com/${SCKEY}.send`,
                body: `text=${text}&desp=${desp}`,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                timeout,
            };
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log('\n发送通知调用API失败！！\n');
                        console.log(err);
                    } else {
                        data = JSON.parse(data);
                        // server酱和Server酱·Turbo版的返回json格式不太一样
                        if (data.errno === 0 || data.data.errno === 0) {
                            console.log('\nserver酱发送通知消息成功🎉\n');
                        } else if (data.errno === 1024) {
                            // 一分钟内发送相同的内容会触发
                            console.log(`\nserver酱发送通知消息异常: ${data.errmsg}\n`);
                        } else {
                            console.log(`\nserver酱发送通知消息异常\n${JSON.stringify(data)}`);
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve(data);
                }
            });
        } else {
            resolve();
        }
    });
}

function PushDeerNotify(text, desp) {
    return new Promise((resolve) => {
        if (PUSHDEER_KEY) {
            // PushDeer 建议对消息内容进行 urlencode
            desp = encodeURI(desp);
            const options = {
                url: PUSHDEER_URL || `https://api2.pushdeer.com/message/push`,
                body: `pushkey=${PUSHDEER_KEY}&text=${text}&desp=${desp}&type=markdown`,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                timeout,
            };
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log('\n发送通知调用API失败！！\n');
                        console.log(err);
                    } else {
                        data = JSON.parse(data);
                        // 通过返回的result的长度来判断是否成功
                        if (
                            data.content.result.length !== undefined &&
                            data.content.result.length > 0
                        ) {
                            console.log('\nPushDeer发送通知消息成功🎉\n');
                        } else {
                            console.log(`\nPushDeer发送通知消息异常\n${JSON.stringify(data)}`);
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve(data);
                }
            });
        } else {
            resolve();
        }
    });
}

function ChatNotify(text, desp) {
    return new Promise((resolve) => {
        if (CHAT_URL && CHAT_TOKEN) {
            // 对消息内容进行 urlencode
            desp = encodeURI(desp);
            const options = {
                url: `${CHAT_URL}${CHAT_TOKEN}`,
                body: `payload={"text":"${text}\n${desp}"}`,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            };
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log('\n发送通知调用API失败！！\n');
                        console.log(err);
                    } else {
                        data = JSON.parse(data);
                        if (data.success) {
                            console.log('\nChat发送通知消息成功🎉\n');
                        } else {
                            console.log(`\nChat发送通知消息异常\n${JSON.stringify(data)}`);
                        }
                    }
                } catch (e) {
                    $.logErr(e);
                } finally {
                    resolve(data);
                }
            });
        } else {
            resolve();
        }
    });
}

function BarkNotify(text, desp, params = {}) {
    return new Promise((resolve) => {
        if (BARK_PUSH) {
            const options = {
                url: `${BARK_PUSH}/${encodeURIComponent(text)}/${encodeURIComponent(
                    desp,
                )}?icon=${BARK_ICON}&sound=${BARK_SOUND}&group=${BARK_GROUP}&level=${BARK_LEVEL}&url=${BARK_URL}&${querystring.stringify(
                    params,
                )}`,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                timeout,
            };
            $.get(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log('\nBark APP发送通知调用API失败！！\n');
                        console.log(err);
                    } else {
                        data = JSON.parse(data);
                        if (data.code === 200) {
                            console.log('\nBark APP发送通知消息成功🎉\n');
                        } else {
                            console.log(`${data.message}\n`);
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve();
                }
            });
        } else {
            resolve();
        }
    });
}

function tgBotNotify(text, desp) {
    return new Promise((resolve) => {
        if (TG_BOT_TOKEN && TG_USER_ID) {
            const options = {
                url: `${TG_API_HOST}/bot${TG_BOT_TOKEN}/sendMessage`,
                json: {
                    chat_id: `${TG_USER_ID}`,
                    text: `${text}\n\n${desp}`,
                    disable_web_page_preview: true,
                },
                headers: {
                    'Content-Type': 'application/json',
                },
                timeout,
            };
            if (TG_PROXY_HOST && TG_PROXY_PORT) {
                const {HttpProxyAgent, HttpsProxyAgent} = require('hpagent');
                const options = {
                    keepAlive: true,
                    keepAliveMsecs: 1000,
                    maxSockets: 256,
                    maxFreeSockets: 256,
                    proxy: `http://${TG_PROXY_AUTH}${TG_PROXY_HOST}:${TG_PROXY_PORT}`,
                };
                const httpAgent = new HttpProxyAgent(options);
                const httpsAgent = new HttpsProxyAgent(options);
                const agent = {
                    http: httpAgent,
                    https: httpsAgent,
                };
                Object.assign(options, {agent});
            }
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log('\ntelegram发送通知消息失败！！\n');
                        console.log(err);
                    } else {
                        data = JSON.parse(data);
                        if (data.ok) {
                            console.log('\nTelegram发送通知消息成功🎉。\n');
                        } else if (data.error_code === 400) {
                            console.log(
                                '\n请主动给bot发送一条消息并检查接收用户ID是否正确。\n',
                            );
                        } else if (data.error_code === 401) {
                            console.log('\nTelegram bot token 填写错误。\n');
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve(data);
                }
            });
        } else {
            resolve();
        }
    });
}

function ddBotNotify(text, desp) {
    return new Promise((resolve) => {
        const options = {
            url: `https://oapi.dingtalk.com/robot/send?access_token=${DD_BOT_TOKEN}`,
            json: {
                msgtype: 'text',
                text: {
                    content: `${text}\n\n${desp}`,
                },
            },
            headers: {
                'Content-Type': 'application/json',
            },
            timeout,
        };
        if (DD_BOT_TOKEN && DD_BOT_SECRET) {
            const crypto = require('crypto');
            const dateNow = Date.now();
            const hmac = crypto.createHmac('sha256', DD_BOT_SECRET);
            hmac.update(`${dateNow}\n${DD_BOT_SECRET}`);
            const result = encodeURIComponent(hmac.digest('base64'));
            options.url = `${options.url}&timestamp=${dateNow}&sign=${result}`;
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log('\n钉钉发送通知消息失败！！\n');
                        console.log(err);
                    } else {
                        data = JSON.parse(data);
                        if (data.errcode === 0) {
                            console.log('\n钉钉发送通知消息成功🎉。\n');
                        } else {
                            console.log(`${data.errmsg}\n`);
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve(data);
                }
            });
        } else if (DD_BOT_TOKEN) {
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log('\n钉钉发送通知消息失败！！\n');
                        console.log(err);
                    } else {
                        data = JSON.parse(data);
                        if (data.errcode === 0) {
                            console.log('\n钉钉发送通知消息完成。\n');
                        } else {
                            console.log(`${data.errmsg}\n`);
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve(data);
                }
            });
        } else {
            resolve();
        }
    });
}

function qywxBotNotify(text, desp) {
  return new Promise((resolve) => {
    const qywxOrigin =
      typeof push_config !== 'undefined' && push_config.QYWX_ORIGIN
        ? push_config.QYWX_ORIGIN
        : typeof QYWX_ORIGIN !== 'undefined' && QYWX_ORIGIN
        ? QYWX_ORIGIN
        : 'https://qyapi.weixin.qq.com';

    const qywxKey =
      typeof push_config !== 'undefined' && push_config.QYWX_KEY
        ? push_config.QYWX_KEY
        : typeof QYWX_KEY !== 'undefined'
        ? QYWX_KEY
        : '';

    if (!qywxKey) {
      resolve();
      return;
    }

    const payload = {
      msgtype: 'text',
      text: {
        content: `${text}\n\n${desp}`,
      },
    };

    const options = {
      url: `${qywxOrigin}/cgi-bin/webhook/send?key=${qywxKey}`,
      body: JSON.stringify(payload),
      headers: {
        'Content-Type': 'application/json',
      },
      timeout,
    };

    $.post(options, (err, resp, data) => {
      try {
        if (err) {
          console.log('企业微信发送通知消息失败😞\n', err);
        } else {
          if (typeof data === 'string') {
            try {
              data = JSON.parse(data);
            } catch (e) {
              console.log('企业微信返回内容不是合法 JSON：\n', data);
              resolve(data);
              return;
            }
          }

          if (data && data.errcode === 0) {
            console.log('企业微信发送通知消息成功🎉。\n');
          } else {
            console.log(
              `企业微信发送通知消息异常 ${
                data && data.errmsg ? data.errmsg : 'unknown error'
              }\n`,
            );
          }
        }
      } catch (e) {
        $.logErr(e, resp);
      } finally {
        resolve(data);
      }
    });
  });
}

function ChangeUserId(desp) {
    const QYWX_AM_AY = QYWX_AM.split(',');
    if (QYWX_AM_AY[2]) {
        const userIdTmp = QYWX_AM_AY[2].split('|');
        let userId = '';
        for (let i = 0; i < userIdTmp.length; i++) {
            const count = '账号' + (i + 1);
            const count2 = '签到号 ' + (i + 1);
            if (desp.match(count2)) {
                userId = userIdTmp[i];
            }
        }
        if (!userId) userId = QYWX_AM_AY[2];
        return userId;
    } else {
        return '@all';
    }
}

async function qywxamNotify(text, desp) {
    const MAX_LENGTH = 900;
    if (desp.length > MAX_LENGTH) {
        let d = desp.substr(0, MAX_LENGTH) + '\n==More==';
        await do_qywxamNotify(text, d);
        await qywxamNotify(text, desp.substr(MAX_LENGTH));
    } else {
        return await do_qywxamNotify(text, desp);
    }
}

function do_qywxamNotify(text, desp) {
    return new Promise((resolve) => {
        if (QYWX_AM) {
            const QYWX_AM_AY = QYWX_AM.split(',');
            const options_accesstoken = {
                url: `${QYWX_ORIGIN}/cgi-bin/gettoken`,
                json: {
                    corpid: `${QYWX_AM_AY[0]}`,
                    corpsecret: `${QYWX_AM_AY[1]}`,
                },
                headers: {
                    'Content-Type': 'application/json',
                },
                timeout,
            };
            $.post(options_accesstoken, (err, resp, data) => {
                let html = desp.replace(/\n/g, '<br/>');
                let json = JSON.parse(data);
                let accesstoken = json.access_token;
                let options;

                switch (QYWX_AM_AY[4]) {
                    case '0':
                        options = {
                            msgtype: 'textcard',
                            textcard: {
                                title: `${text}`,
                                description: `${desp}`,
                                url: 'https://github.com/whyour/qinglong',
                                btntxt: '更多',
                            },
                        };
                        break;

                    case '1':
                        options = {
                            msgtype: 'text',
                            text: {
                                content: `${text}\n\n${desp}`,
                            },
                        };
                        break;

                    default:
                        options = {
                            msgtype: 'mpnews',
                            mpnews: {
                                articles: [
                                    {
                                        title: `${text}`,
                                        thumb_media_id: `${QYWX_AM_AY[4]}`,
                                        author: `智能助手`,
                                        content_source_url: ``,
                                        content: `${html}`,
                                        digest: `${desp}`,
                                    },
                                ],
                            },
                        };
                }
                if (!QYWX_AM_AY[4]) {
                    // 如不提供第四个参数,则默认进行文本消息类型推送
                    options = {
                        msgtype: 'text',
                        text: {
                            content: `${text}\n\n${desp}`,
                        },
                    };
                }
                options = {
                    url: `${QYWX_ORIGIN}/cgi-bin/message/send?access_token=${accesstoken}`,
                    json: {
                        touser: `${ChangeUserId(desp)}`,
                        agentid: `${QYWX_AM_AY[3]}`,
                        safe: '0',
                        ...options,
                    },
                    headers: {
                        'Content-Type': 'application/json',
                    },
                };

                $.post(options, (err, resp, data) => {
                    try {
                        if (err) {
                            console.log(
                                '\n成员ID:' +
                                ChangeUserId(desp) +
                                '企业微信应用消息发送通知消息失败！！\n',
                            );
                            console.log(err);
                        } else {
                            data = JSON.parse(data);
                            if (data.errcode === 0) {
                                console.log(
                                    '\n成员ID:' +
                                    ChangeUserId(desp) +
                                    '企业微信应用消息发送通知消息成功🎉。\n',
                                );
                            } else {
                                console.log(`${data.errmsg}\n`);
                            }
                        }
                    } catch (e) {
                        $.logErr(e, resp);
                    } finally {
                        resolve(data);
                    }
                });
            });
        } else {
            resolve();
        }
    });
}

function iGotNotify(text, desp, params = {}) {
    return new Promise((resolve) => {
        if (IGOT_PUSH_KEY) {
            // 校验传入的IGOT_PUSH_KEY是否有效
            const IGOT_PUSH_KEY_REGX = new RegExp('^[a-zA-Z0-9]{24}$');
            if (!IGOT_PUSH_KEY_REGX.test(IGOT_PUSH_KEY)) {
                console.log('您所提供的IGOT_PUSH_KEY无效\n');
                resolve();
                return;
            }
            const options = {
                url: `https://push.hellyw.com/${IGOT_PUSH_KEY.toLowerCase()}`,
                body: `title=${text}&content=${desp}&${querystring.stringify(params)}`,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                timeout,
            };
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log('\n发送通知调用API失败！！\n');
                        console.log(err);
                    } else {
                        if (typeof data === 'string') data = JSON.parse(data);
                        if (data.ret === 0) {
                            console.log('\niGot发送通知消息成功🎉\n');
                        } else {
                            console.log(`\niGot发送通知消息失败：${data.errMsg}\n`);
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve(data);
                }
            });
        } else {
            resolve();
        }
    });
}

function pushPlusNotify(text, desp) {
    return new Promise((resolve) => {
        if (PUSH_PLUS_TOKEN) {
            desp = desp.replace(/[\n\r]/g, '<br>'); // 默认为html, 不支持plaintext
            const body = {
                token: `${PUSH_PLUS_TOKEN}`,
                title: `${text}`,
                content: `${desp}`,
                topic: `${PUSH_PLUS_USER}`,
            };
            const options = {
                url: `https://www.pushplus.plus/send`,
                body: JSON.stringify(body),
                headers: {
                    'Content-Type': ' application/json',
                },
                timeout,
            };
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log(
                            `\npush+发送${
                                PUSH_PLUS_USER ? '一对多' : '一对一'
                            }通知消息失败！！\n`,
                        );
                        console.log(err);
                    } else {
                        data = JSON.parse(data);
                        if (data.code === 200) {
                            console.log(
                                `\npush+发送${
                                    PUSH_PLUS_USER ? '一对多' : '一对一'
                                }通知消息完成。\n`,
                            );
                        } else {
                            console.log(
                                `\npush+发送${
                                    PUSH_PLUS_USER ? '一对多' : '一对一'
                                }通知消息失败：${data.msg}\n`,
                            );
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve(data);
                }
            });
        } else {
            resolve();
        }
    });
}

function wxPusherNotify(text, desp) {
    return new Promise((resolve) => {
        if (WXPUSHER_TOKEN && WXPUSHER_UID) {
            desp = desp.replace(/[\n\r]/g, '<br>');
            const body = {
                appToken: `${WXPUSHER_TOKEN}`,
                uids: [WXPUSHER_UID],
                summary: `${text}`,
                content: `${desp}`,
                contentType: 2,
                url: 'https://github.com/sudojia/AutoTaskScript',
            };
            const options = {
                url: `https://wxpusher.zjiecode.com/api/send/message`,
                body: JSON.stringify(body),
                headers: {
                    'Content-Type': ' application/json',
                },
                timeout,
            };
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.error(err);
                    } else {
                        data = JSON.parse(data);
                        if (1000 === data.code) {
                            console.log(
                                `\nwxpusher发送通知消息完成🎉\n`,
                            );
                        } else {
                            console.log(
                                `\nwxpusher发送通知消息失败：${data.msg}\n`,
                            );
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve(data);
                }
            });
        } else {
            resolve();
        }
    });
}

function aibotkNotify(text, desp) {
    return new Promise((resolve) => {
        if (AIBOTK_KEY && AIBOTK_TYPE && AIBOTK_NAME) {
            let json = {};
            let url = '';
            switch (AIBOTK_TYPE) {
                case 'room':
                    url = 'https://api-bot.aibotk.com/openapi/v1/chat/room';
                    json = {
                        apiKey: `${AIBOTK_KEY}`,
                        roomName: `${AIBOTK_NAME}`,
                        message: {
                            type: 1,
                            content: `【青龙快讯】\n\n${text}\n${desp}`,
                        },
                    };
                    break;
                case 'contact':
                    url = 'https://api-bot.aibotk.com/openapi/v1/chat/contact';
                    json = {
                        apiKey: `${AIBOTK_KEY}`,
                        name: `${AIBOTK_NAME}`,
                        message: {
                            type: 1,
                            content: `【青龙快讯】\n\n${text}\n${desp}`,
                        },
                    };
                    break;
            }
            const options = {
                url: url,
                json,
                headers: {
                    'Content-Type': 'application/json',
                },
                timeout,
            };
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log('\n智能微秘书发送通知消息失败！！\n');
                        console.log(err);
                    } else {
                        data = JSON.parse(data);
                        if (data.code === 0) {
                            console.log('\n智能微秘书发送通知消息成功🎉。\n');
                        } else {
                            console.log(`${data.error}\n`);
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve(data);
                }
            });
        } else {
            resolve();
        }
    });
}

function fsBotNotify(text, desp) {
    return new Promise((resolve) => {
        if (FSKEY) {
            const options = {
                url: `https://open.feishu.cn/open-apis/bot/v2/hook/${FSKEY}`,
                json: {msg_type: 'text', content: {text: `${text}\n\n${desp}`}},
                headers: {
                    'Content-Type': 'application/json',
                },
                timeout,
            };
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log('\n发送通知调用API失败！！\n');
                        console.log(err);
                    } else {
                        data = JSON.parse(data);
                        if (data.StatusCode === 0 || data.code === 0) {
                            console.log('\n飞书发送通知消息成功🎉\n');
                        } else {
                            console.log(`${data.msg}\n`);
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve(data);
                }
            });
        } else {
            resolve();
        }
    });
}

async function smtpNotify(text, desp) {
    if (![SMTP_EMAIL, SMTP_PASSWORD].every(Boolean) || !SMTP_SERVICE) {
        return;
    }

    try {
        const nodemailer = require('nodemailer');
        const transporter = nodemailer.createTransport({
            service: SMTP_SERVICE,
            auth: {
                user: SMTP_EMAIL,
                pass: SMTP_PASSWORD,
            },
        });

        const addr = SMTP_NAME ? `"${SMTP_NAME}" <${SMTP_EMAIL}>` : SMTP_EMAIL;
        const info = await transporter.sendMail({
            from: addr,
            to: addr,
            subject: text,
            html: `${desp.replace(/\n/g, '<br/>')}`,
        });

        transporter.close();

        if (info.messageId) {
            console.log('\nSMTP发送通知消息成功🎉\n');
            return true;
        }
        console.log('\nSMTP发送通知消息失败！！\n');
    } catch (e) {
        console.log('\nSMTP发送通知消息出现错误！！\n');
        console.log(e);
    }
}

function pushMeNotify(text, desp, params = {}) {
    return new Promise((resolve) => {
        if (PUSHME_KEY) {
            const options = {
                url: `https://push.i-i.me?push_key=${PUSHME_KEY}`,
                json: {title: text, content: desp, ...params},
                headers: {
                    'Content-Type': 'application/json',
                },
                timeout,
            };
            $.post(options, (err, resp, data) => {
                try {
                    if (err) {
                        console.log('\nPushMeNotify发送通知调用API失败！！\n');
                        console.log(err);
                    } else {
                        if (data === 'success') {
                            console.log('\nPushMe发送通知消息成功🎉\n');
                        } else {
                            console.log(`\n${data}\n`);
                        }
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve(data);
                }
            });
        } else {
            resolve();
        }
    });
}

function chronocatNotify(title, desp) {
    return new Promise((resolve) => {
        if (!CHRONOCAT_TOKEN || !CHRONOCAT_QQ || !CHRONOCAT_URL) {
            resolve();
            return;
        }
        let user_idsMatches = CHRONOCAT_QQ.match(/user_id=(\d+)/g);
        let group_idsMatches = CHRONOCAT_QQ.match(/group_id=(\d+)/g);
        const user_ids = user_idsMatches ? user_idsMatches.map(match => match.split('=')[1]) : [];
        const group_ids = group_idsMatches ? group_idsMatches.map(match => match.split('=')[1]) : [];
        // const user_ids = CHRONOCAT_QQ.match(/user_id=(\d+)/g)?.map(
        //     (match) => match.split('=')[1],
        // );
        // const group_ids = CHRONOCAT_QQ.match(/group_id=(\d+)/g)?.map(
        //     (match) => match.split('=')[1],
        // );
        const url = `${CHRONOCAT_URL}/api/message/send`;
        const headers = {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${CHRONOCAT_TOKEN}`,
        };

        for (const [chat_type, ids] of [
            [1, user_ids],
            [2, group_ids],
        ]) {
            if (!ids) {
                continue;
            }
            for (const chat_id of ids) {
                const data = {
                    peer: {
                        chatType: chat_type,
                        peerUin: chat_id,
                    },
                    elements: [
                        {
                            elementType: 1,
                            textElement: {
                                content: `${title}\n\n${desp}`,
                            },
                        },
                    ],
                };
                const options = {
                    url: url,
                    json: data,
                    headers,
                    timeout,
                };
                $.post(options, (err, resp, data) => {
                    try {
                        if (err) {
                            console.log('\nChronocat发送QQ通知消息失败！！\n');
                            console.log(err);
                        } else {
                            data = JSON.parse(data);
                            if (chat_type === 1) {
                                console.log(`\nQQ个人消息:${ids}推送成功！`);
                            } else {
                                console.log(`\nQQ群消息:${ids}推送成功！`);
                            }
                        }
                    } catch (e) {
                        $.logErr(e, resp);
                    } finally {
                        resolve(data);
                    }
                });
            }
        }
    });
}

function replacePlaceholders(value, title, content) {
    if (value) {
        value = value.replaceAll('$title', title);
        return value.replaceAll('$content', content);
    }
    return value;
}

function webhookNotify(text, desp) {
    return new Promise((resolve) => {
        if (!WEBHOOK_URL.includes('$title') && !WEBHOOK_BODY.includes('$title')) {
            resolve();
            return;
        }
        const headers = parseHeaders(WEBHOOK_HEADERS);
        // const body = parseBody(WEBHOOK_BODY, WEBHOOK_CONTENT_TYPE, (v) =>
        //     v?.replaceAll('$title', text)?.replaceAll('$content', desp),
        // );
        const body = parseBody(WEBHOOK_BODY, WEBHOOK_CONTENT_TYPE, v => replacePlaceholders(v, text, desp));
        const bodyParam = formatBodyFun(WEBHOOK_CONTENT_TYPE, body);
        const options = {
            method: WEBHOOK_METHOD,
            headers,
            allowGetBody: true,
            ...bodyParam,
            timeout,
            retry: 1,
        };

        if (WEBHOOK_METHOD) {
            const formatUrl = WEBHOOK_URL.replaceAll(
                '$title',
                encodeURIComponent(text),
            ).replaceAll('$content', encodeURIComponent(desp));
            got(formatUrl, options).then((resp) => {
                try {
                    if (resp.statusCode !== 200) {
                        console.log(`\n自定义发送通知消息失败！！\n${resp.body}`);
                    } else {
                        console.log(`\n自定义发送通知消息成功🎉。\n${resp.body}`);
                    }
                } catch (e) {
                    $.logErr(e, resp);
                } finally {
                    resolve(resp.body);
                }
            });
        } else {
            resolve();
        }
    });
}

function parseString(input, valueFormatFn) {
    const regex = /(\w+):\s*((?:(?!\n\w+:).)*)/g;
    const matches = {};

    let match;
    while ((match = regex.exec(input)) !== null) {
        const [, key, value] = match;
        const _key = key.trim();
        if (!_key || matches[_key]) {
            continue;
        }

        let _value = value.trim();

        try {
            _value = valueFormatFn ? valueFormatFn(_value) : _value;
            matches[_key] = JSON.parse(_value);
        } catch (error) {
            matches[_key] = _value;
        }
    }

    return matches;
}

function parseHeaders(headers) {
    if (!headers) return {};

    const parsed = {};
    let key;
    let val;
    let i;

    headers &&
    headers.split('\n').forEach(function parser(line) {
        i = line.indexOf(':');
        key = line.substring(0, i).trim().toLowerCase();
        val = line.substring(i + 1).trim();

        if (!key) {
            return;
        }

        parsed[key] = parsed[key] ? parsed[key] + ', ' + val : val;
    });

    return parsed;
}

function parseBody(body, contentType, valueFormatFn) {
    if (contentType === 'text/plain' || !body) {
        return valueFormatFn && body ? valueFormatFn(body) : body;
    }

    const parsed = parseString(body, valueFormatFn);

    switch (contentType) {
        case 'multipart/form-data':
            return Object.keys(parsed).reduce((p, c) => {
                p.append(c, parsed[c]);
                return p;
            }, new FormData());
        case 'application/x-www-form-urlencoded':
            return Object.keys(parsed).reduce((p, c) => {
                return p ? `${p}&${c}=${parsed[c]}` : `${c}=${parsed[c]}`;
            });
    }

    return parsed;
}

function formatBodyFun(contentType, body) {
    if (!body) return {};
    switch (contentType) {
        case 'application/json':
            return {json: body};
        case 'multipart/form-data':
            return {form: body};
        case 'application/x-www-form-urlencoded':
        case 'text/plain':
            return {body};
    }
    return {};
}

function formatNotifyContentFun(url, body, title, content) {
    if (!url.includes('$title') && !body.includes('$title')) {
        return {};
    }

    return {
        formatUrl: url
            .replaceAll('$title', encodeURIComponent(title))
            .replaceAll('$content', encodeURIComponent(content)),
        formatBody: body
            .replaceAll('$title', title)
            .replaceAll('$content', content),
    };
}

module.exports = {
    sendNotify,
    BARK_PUSH,
};

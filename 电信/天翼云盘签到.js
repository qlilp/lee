/**
 * 变量名：CLOUD_189
 * 值：手机号#密码
 * 多账号：一行一个，例如：
 * 199xxxx3303#密码1
 * 189xxxx6964#密码2
 *
 * 依赖：
 * cloud189-sdk
 *
 * 定时规则：
 * 每天早上8点、晚上8点签到
 * cron: 0 0 8,20 * * *
 */

const { CloudClient } = require("cloud189-sdk");

// 手机号脱敏
const mask = (s, start, end) => {
  if (!s) return "";
  return s.split("").fill("*", start, end).join("");
};

// 个人签到
const doSignTask = async (cloudClient) => {
  const res = await cloudClient.userSign();

  return `${res.isSign ? "已经签到过了，" : ""}签到获得${res.netdiskBonus}M空间`;
};

// 查询容量
const getCapacityInfo = async (cloudClient) => {
  const { cloudCapacityInfo, familyCapacityInfo } =
    await cloudClient.getUserSizeInfo();

  const personalSize = cloudCapacityInfo && cloudCapacityInfo.totalSize
    ? (cloudCapacityInfo.totalSize / 1024 / 1024 / 1024).toFixed(2)
    : "0.00";

  const familySize = familyCapacityInfo && familyCapacityInfo.totalSize
    ? (familyCapacityInfo.totalSize / 1024 / 1024 / 1024).toFixed(2)
    : "0.00";

  return `个人：${personalSize}G，家庭：${familySize}G`;
};

// 执行单个账号
async function main(userName, password) {
  if (!userName || !password) {
    console.log("账号或密码为空，跳过");
    return;
  }

  const userNameInfo = mask(userName, 3, 7);

  try {
    console.log(`账户 ${userNameInfo}开始执行`);

    const cloudClient = new CloudClient({
      username: userName,
      password: password
    });

    // 只执行个人签到
    const signText = await doSignTask(cloudClient);
    console.log(signText);

    // 查询容量，失败也不影响签到
    try {
      const capacityText = await getCapacityInfo(cloudClient);
      console.log(capacityText);
    } catch (e) {
      console.log("容量查询失败，已跳过：" + (e.message || e));
    }

    console.log("任务执行完毕");
  } catch (e) {
    console.error(`账户 ${userNameInfo}执行失败：${e.message || e}`);

    if (e.code === "ECONNRESET") {
      throw e;
    }
  } finally {
    console.log(`账户 ${userNameInfo}执行完毕`);
  }
}

// 程序入口
(async () => {
  const c189s = process.env.CLOUD_189;

  if (!c189s) {
    console.log("未获取到天翼云盘 CLOUD_189");
    return;
  }

  const accounts = c189s
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);

  for (const account of accounts) {
    const [userName, password] = account.split("#").map((item) => item.trim());

    if (!userName || !password) {
      console.log(`账号格式错误，正确格式为：手机号#密码，当前值：${account}`);
      continue;
    }

    await main(userName, password);
  }
})();

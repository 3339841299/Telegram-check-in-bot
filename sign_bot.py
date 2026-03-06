import os
import json
import uuid
from datetime import datetime

import pytz
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telethon import TelegramClient, events
from telethon.tl import types, functions  # <--- 新增：用于设置Bot菜单
import logging
import asyncio

# =============== 日志配置 ===============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sign_bot")

# Telethon & APScheduler 日志级别
logging.getLogger("telethon").setLevel(logging.INFO)
logging.getLogger("apscheduler").setLevel(logging.INFO)

logger.info("=== 签到机器人启动中（带详细日志）===")

# =============== 加载配置 ===============
load_dotenv()
logger.info("尝试从 .env 加载配置...")

try:
    API_ID = int(os.getenv("API_ID", "0"))
except ValueError:
    API_ID = 0

API_HASH = os.getenv("API_HASH", "")
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Shanghai")
TASK_FILE = "tasks.json"

# 只允许这个用户 ID 控制机器人（从 @userinfobot 获取）
try:
    ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))
except ValueError:
    ALLOWED_USER_ID = 0

logger.info(f"读取到配置：API_ID={API_ID}, TIMEZONE={TIMEZONE}")
logger.info(f"PHONE_NUMBER={PHONE_NUMBER!r}")
logger.info(f"BOT_TOKEN 是否存在={bool(BOT_TOKEN)}")
logger.info(f"ALLOWED_USER_ID={ALLOWED_USER_ID}")

if not API_ID or not API_HASH or not PHONE_NUMBER or not BOT_TOKEN or not ALLOWED_USER_ID:
    logger.error(
        "配置缺失：API_ID / API_HASH / PHONE_NUMBER / BOT_TOKEN / ALLOWED_USER_ID 有空值"
    )
    raise RuntimeError(
        "请先在 .env 中正确配置 API_ID / API_HASH / PHONE_NUMBER / BOT_TOKEN / ALLOWED_USER_ID"
    )

# =============== 初始化客户端 ===============
logger.info("初始化 Telethon 客户端（用户账号 & Bot）...")
# 用于实际发送签到消息的用户账号
user_client = TelegramClient("user_session", API_ID, API_HASH)

# 用于接收控制命令的 Bot
bot_client = TelegramClient("bot_session", API_ID, API_HASH)

# 定时任务调度器
scheduler = AsyncIOScheduler(timezone=pytz.timezone(TIMEZONE))

# 任务结构: {task_id: {"target": str, "hour": int, "minute": int, "text": str}}
tasks = {}


# =============== 持久化相关 ===============
def save_tasks():
    logger.info(f"保存任务到 {TASK_FILE}（共 {len(tasks)} 个）...")
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def load_tasks():
    global tasks
    if os.path.exists(TASK_FILE):
        logger.info(f"发现任务文件 {TASK_FILE}，开始加载...")
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        logger.info(f"已从文件加载 {len(tasks)} 个任务。")
    else:
        logger.info(f"未发现 {TASK_FILE}，从空任务集开始。")
        tasks = {}


# =============== 定时任务执行 ===============
async def execute_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        logger.warning(f"执行任务时发现 task_id={task_id} 不存在，跳过。")
        return

    target = task["target"]
    text = task["text"]

    logger.info(f"[任务执行] task_id={task_id}, target={target}, text={text!r}")
    try:
        entity = await user_client.get_entity(target)
        await user_client.send_message(entity, text)
        logger.info(f"[任务成功] {task_id} → {target}: {text}")
    except Exception as e:
        logger.exception(f"[任务失败] {task_id} 发送到 {target} 出错: {e}")


def schedule_task(task_id: str):
    t = tasks[task_id]
    logger.info(
        f"注册定时任务：id={task_id}, target={t['target']}, "
        f"time={t['hour']:02d}:{t['minute']:02d}, text={t['text']!r}"
    )
    scheduler.add_job(
        execute_task,
        "cron",
        hour=t["hour"],
        minute=t["minute"],
        args=[task_id],
        id=task_id,
        replace_existing=True,
    )


def restore_tasks():
    logger.info("开始恢复所有任务到调度器...")
    for tid in tasks:
        schedule_task(tid)
    logger.info(f"已恢复 {len(tasks)} 个任务。")


# =============== 权限辅助函数 ===============
def _check_permission(event: events.NewMessage.Event) -> bool:
    """检查这个消息的发送者是否有权限"""
    if event.sender_id != ALLOWED_USER_ID:
        logger.warning(
            f"收到来自未授权用户的命令：user_id={event.sender_id}, chat_id={event.chat_id}"
        )
        return False
    return True


# =============== Bot 控制指令（在 bot_client 上监听） ===============
@bot_client.on(events.NewMessage(pattern=r"^/start"))
async def bot_start(event: events.NewMessage.Event):
    if not _check_permission(event):
        await event.reply("❌ 你没有权限使用这个控制机器人。")
        return

    logger.info(f"收到 /start 命令，来自 chat_id={event.chat_id}, user_id={event.sender_id}")
    await event.reply(
        "我是你的签到控制Bot ✅\n\n"
        "指令：\n"
        "/add 目标 HH:MM 文本  - 添加每日定时任务\n"
        "/list                 - 查看所有任务\n"
        "/del 任务id           - 删除任务\n\n"
        "示例：\n"
        "/add @my_sign_bot 09:30 /sign\n"
        "/add -1001234567890 08:00 早上打卡"
    )


@bot_client.on(events.NewMessage(pattern=r"^/add"))
async def bot_add(event: events.NewMessage.Event):
    """
    格式：
    /add 目标 HH:MM 文本
    """
    if not _check_permission(event):
        await event.reply("❌ 你没有权限使用这个控制机器人。")
        return

    text = event.raw_text.strip()
    logger.info(
        f"收到 /add 命令，来自 chat_id={event.chat_id}, user_id={event.sender_id}, raw_text={text!r}"
    )

    parts = text.split(" ", 3)
    if len(parts) < 4:
        await event.reply(
            "用法：\n/add 目标 HH:MM 文本\n例如：\n/add @my_sign_bot 09:30 /sign"
        )
        return

    _, target, time_str, msg_text = parts
    logger.info(f"/add 解析参数：target={target}, time={time_str}, text={msg_text!r}")

    # 解析时间
    try:
        hour_str, minute_str = time_str.split(":")
        hour = int(hour_str)
        minute = int(minute_str)
        assert 0 <= hour <= 23 and 0 <= minute <= 59
    except Exception:
        logger.warning(f"/add 时间解析失败：time_str={time_str!r}")
        await event.reply("时间格式错误，应为 HH:MM，例如 09:30")
        return

    # 验证目标是否存在（用 user_client 去解析）
    try:
        logger.info(f"用 user_client 解析目标：{target}")
        await user_client.get_entity(target)
    except Exception as e:
        logger.exception(f"/add 校验目标失败：target={target}, error={e}")
        await event.reply(f"无法解析目标 {target}：{e}")
        return

    task_id = uuid.uuid4().hex[:8]
    tasks[task_id] = {
        "target": target,
        "hour": hour,
        "minute": minute,
        "text": msg_text,
    }
    save_tasks()
    schedule_task(task_id)

    await event.reply(
        f"✅ 已添加任务：\n"
        f"id: `{task_id}`\n"
        f"目标: {target}\n"
        f"时间: {hour:02d}:{minute:02d}\n"
        f"内容: {msg_text}"
    )


@bot_client.on(events.NewMessage(pattern=r"^/list"))
async def bot_list(event: events.NewMessage.Event):
    if not _check_permission(event):
        await event.reply("❌ 你没有权限使用这个控制机器人。")
        return

    logger.info(f"收到 /list 命令，来自 chat_id={event.chat_id}, user_id={event.sender_id}")
    if not tasks:
        await event.reply("当前没有任何任务。")
        return

    lines = ["📋 当前任务：\n"]
    for tid, t in tasks.items():
        lines.append(
            f"🆔 `{tid}`\n"
            f"🎯 {t['target']}\n"
            f"⏰ {t['hour']:02d}:{t['minute']:02d}\n"
            f"💬 {t['text']}\n"
        )

    await event.reply("\n".join(lines))


@bot_client.on(events.NewMessage(pattern=r"^/del"))
async def bot_del(event: events.NewMessage.Event):
    if not _check_permission(event):
        await event.reply("❌ 你没有权限使用这个控制机器人。")
        return

    text = event.raw_text.strip()
    logger.info(
        f"收到 /del 命令，来自 chat_id={event.chat_id}, user_id={event.sender_id}, raw_text={text!r}"
    )

    parts = text.split(" ", 1)
    if len(parts) < 2:
        await event.reply("用法：/del 任务id\n可先用 /list 查看任务列表。")
        return

    _, task_id = parts
    task_id = task_id.strip()

    if task_id not in tasks:
        logger.warning(f"/del 找不到任务：task_id={task_id}")
        await event.reply("找不到该任务 id。")
        return

    try:
        scheduler.remove_job(task_id)
        logger.info(f"/del 已从调度器删除任务：task_id={task_id}")
    except Exception as e:
        logger.warning(f"/del 从调度器删除任务失败：task_id={task_id}, error={e}")

    tasks.pop(task_id)
    save_tasks()

    await event.reply(f"已删除任务 `{task_id}`。")


# =============== 主入口 ===============
async def main():
    try:
        logger.info("=== Step 1：登录用户账号（用于实际发送签到）===")
        logger.info(
            "如果此处终端看起来“卡住”，很可能是在等你输入验证码或二步验证密码。"
        )
        await user_client.start(phone=PHONE_NUMBER)
        me = await user_client.get_me()
        logger.info(f"用户账号登录成功：id={me.id}, name={me.first_name!r}")

        logger.info("=== Step 2：启动控制Bot（用于接收 /add /list /del 指令）===")
        await bot_client.start(bot_token=BOT_TOKEN)
        me_bot = await bot_client.get_me()
        logger.info(
            f"控制Bot 启动成功：username=@{me_bot.username}, id={me_bot.id}"
        )

        # ================== 新增：自动设置机器人菜单 ==================
        try:
            logger.info("正在设置 Bot 快捷菜单...")
            await bot_client(functions.bots.SetBotCommandsRequest(
                scope=types.BotCommandScopeDefault(),
                lang_code='',
                commands=[
                    types.BotCommand(command='start', description='查看使用帮助'),
                    types.BotCommand(command='list', description='📋 查看所有签到任务'),
                    types.BotCommand(command='add', description='➕ 添加任务 (需补全参数)'),
                    types.BotCommand(command='del', description='❌ 删除任务 (需补全任务id)'),
                ]
            ))
            logger.info("Bot 快捷菜单设置成功！")
        except Exception as e:
            logger.warning(f"Bot 快捷菜单设置失败：{e}")
        # ==============================================================

        logger.info("=== Step 3：加载历史任务并注册到调度器 ===")
        load_tasks()
        restore_tasks()

        logger.info("=== Step 4：启动 APScheduler 定时器 ===")
        scheduler.start()
        logger.info(f"当前已生效的定时任务数量：{len(tasks)}")

        logger.info(
            "=== 初始化完成 ===\n"
            "现在可以在 Telegram 中对你的 Bot 发送指令：\n"
            "  /start  查看帮助\n"
            "  /add    添加每日签到任务\n"
            "  /list   查看任务\n"
            "  /del    删除任务\n"
            f"仅限 user_id={ALLOWED_USER_ID} 使用。"
        )

        # 保持 bot_client 连接，user_client 会一起保活
        await bot_client.run_until_disconnected()
        logger.info("bot_client 已断开连接，程序结束。")

    except Exception as e:
        logger.exception(f"主流程出现未捕获异常：{e}")


if __name__ == "__main__":
    logger.info("主程序入口启动...")
    asyncio.run(main())
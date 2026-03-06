# Telegram-check-in-bot
一个基于 Python 的 Telegram 自动签到机器人，支持用户ID权限验证、环境变量配置和日志输出，部署简单，适用于自动化每日签到任务。
# Telegram Check-in Bot

一个基于 Python 的 **Telegram 自动签到机器人**，用于自动执行每日签到任务。

支持 **用户权限验证、环境变量配置、日志输出**，部署简单，适合个人自动化使用。

---

# 功能特点

- 自动执行每日签到
- Telegram 指令触发
- 用户 ID 权限控制（防止他人滥用）
- 使用 `.env` 文件配置
- 简单易部署
- 日志输出方便排查问题

---

# 项目结构

```
Telegram-check-in-bot
│
├── sign_bot.py        # 主程序
├── .env               # 环境变量配置
├── requirements.txt   # Python依赖
└── README.md          # 项目说明
```

---

# 安装环境

需要 Python 3.8 及以上版本。

安装依赖：

```bash
pip install -r requirements.txt
```

如果没有 `requirements.txt`，可以安装：

```bash
pip install python-telegram-bot python-dotenv
```

---

# 配置

在项目目录创建 `.env` 文件：

```
BOT_TOKEN=你的TelegramBotToken
USER_ID=你的Telegram用户ID
```

### 获取 Telegram 用户ID

可以通过 Telegram 机器人：

```
@userinfobot
```

发送消息即可获取自己的 ID。

---

# 运行机器人

在项目目录执行：

```bash
python sign_bot.py
```

如果运行成功，机器人就会开始监听 Telegram 指令。

---

# 使用方法

在 Telegram 中向你的机器人发送命令即可触发签到，例如：

```
/sign
```

机器人会验证用户 ID，只有授权用户才能执行。

---

# 注意事项

- 请勿泄露 `.env` 文件
- 建议服务器长期运行（如 VPS）
- 如果部署在服务器，可以使用 `screen` 或 `pm2` 保持后台运行

---

# 免责声明

本项目仅用于学习和自动化技术研究，请勿用于违反相关平台规则的用途。

使用本项目所产生的任何后果由使用者自行承担。

---

# License

MIT License

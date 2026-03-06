# Telegram Check-in Bot

一个基于 **Python** 的 Telegram 自动签到机器人。

该项目通过 **Telegram 用户账号执行签到**，并使用 **Telegram Bot 接收指令进行控制**，支持用户权限验证、环境变量配置和日志输出，适合部署在服务器长期运行，实现自动化签到。

---

# 功能特点

- 自动执行每日签到
- 使用 Telegram Bot 发送指令控制
- 通过 Telegram 用户账号执行签到
- 用户 ID 权限控制，防止他人滥用
- 使用 `.env` 进行配置
- 支持时区设置
- 日志输出便于调试和排错
- 轻量级、易部署

---

# 项目结构

```
Telegram-check-in-bot
│
├── sign_bot.py        # 主程序
├── .env               # 配置文件（需自行创建）
├── requirements.txt   # Python依赖
└── README.md          # 项目说明
```

---

# 环境要求

- Python 3.8 或更高版本

安装依赖：

```bash
pip install -r requirements.txt
```

如果没有 `requirements.txt` 可以手动安装：

```bash
pip install telethon python-telegram-bot python-dotenv pytz
```

---

# 配置

在项目目录创建 `.env` 文件：

```
# Telegram 用户账号（用于执行签到）
API_ID=
API_HASH=
PHONE_NUMBER=

# 控制机器人（用于收指令，不负责签到）
BOT_TOKEN=

# 允许控制机器人的 Telegram 用户 ID
ALLOWED_USER_ID=

# 时区
TIMEZONE=Asia/Shanghai
```

---

# 参数说明

### API_ID

Telegram API ID  
获取地址：

https://my.telegram.org

登录后进入：

```
API development tools
```

创建应用即可获取 `API_ID` 和 `API_HASH`。

---

### API_HASH

Telegram API HASH  
与 `API_ID` 一起使用。

---

### PHONE_NUMBER

Telegram 账号手机号，例如：

```
+8613800000000
```

首次运行时需要输入 Telegram 验证码。

---

### BOT_TOKEN

Telegram 机器人 Token。

通过机器人：

```
@BotFather
```

创建机器人后获取 Token。

---

### ALLOWED_USER_ID

允许控制机器人的 Telegram 用户 ID。

获取方法：

使用机器人：

```
@userinfobot
```

发送消息即可获取你的用户 ID。

---

### TIMEZONE

机器人使用的时区，例如：

```
Asia/Shanghai
```

---

# 运行机器人

在项目目录运行：

```bash
python sign_bot.py
```

首次运行时：

1. Telegram 会发送验证码
2. 在终端输入验证码完成登录

登录成功后会自动生成会话文件，下次无需再次登录。

---

# 使用方法

在 Telegram 中向你的机器人发送命令即可触发签到，例如：

```
/sign
```

机器人会验证用户 ID，只有授权用户才能执行。

---

# 服务器部署（推荐）

建议部署在 VPS 或云服务器长期运行。

可以使用：

### screen

```
screen -S bot
python sign_bot.py
```

后台运行。

---

# 安全建议

- 不要泄露 `.env` 文件
- 不要公开 `BOT_TOKEN`
- 建议将 `.env` 加入 `.gitignore`

示例 `.gitignore`：

```
.env
__pycache__/
*.pyc
```

---

# 免责声明

本项目仅用于学习和自动化技术研究。

请遵守相关平台的使用规则，因使用本项目造成的任何问题由使用者自行承担。

---

# License

MIT License

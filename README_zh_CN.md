# OpenClaw SiYuan

这是一个给 OpenClaw Agent 使用的思源笔记技能。它会在你的思源工作空间中准备一个独立的 Inbox，帮助 Agent 捕获笔记、补充标签、筛选相关笔记，并写入初步 AI 分析，同时尽量不打扰你原有的笔记结构。

英文说明见 [README.md](README.md)。

## 🧰 核心指令一览

在 OpenClaw 聊天界面中直接使用这些命令：

- `/cap [内容]`：快速记录一条笔记
- `/sh [关键词]`：搜索笔记
- `/inbox`：查看最近捕获到 Inbox 的笔记
- `/tags`：查看近期笔记中的标签汇总
- `/init`：初始化专用 Inbox
- `/doctor`：检查思源 API 和本地环境状态

## 🌟 为什么使用这个技能

- 快速记录：直接告诉 Agent 你要记什么，不必先打开思源整理格式。
- 自动补充：Agent 通常会根据内容生成标签，只保留真正相关的关联笔记，并写入初步分析。
- 独立空间：AI 生成的笔记统一进入 `Openclaw Inbox`，不改动你原有的笔记本结构。
- 快速回顾：可以直接在聊天里搜索过去的记录，或者查看最近捕获的 Inbox 笔记。

## 🚀 快速部署

使用前请确认：

- 思源桌面端正在运行，并已开启 API
- 本地已安装 Python 3.11 或更高版本

安装依赖：

```bash
python -m pip install -r requirements.txt
```

加载技能：

- 将本仓库放到 OpenClaw 可加载技能的位置

可选配置：

- 如果思源 API 使用了 Token，或者端口不是默认值，请按下文配置环境变量

## 💬 如何与 Agent 交互

技能加载完成后，日常使用都在 OpenClaw 聊天界面里完成。

### 1. 首次初始化

让 Agent 检查环境并准备专用 Inbox：

```text
/init
```

或者：

```text
帮我初始化思源笔记工作区。
```

### 2. 随手记笔记

使用 `/cap` 加上你要记录的内容：

```text
/cap 本周五前需要整理一版春季活动发布方案。
```

Agent 通常会：

- 在 `Openclaw Inbox` 中新建一篇笔记
- 根据内容生成标签
- 只保留真正相关的关联笔记
- 补充初步 AI 分析，例如风险、下一步行动或准备事项
- 在写入完成后回复结果

### 3. 搜索与回顾

仅在 OpenClaw Inbox 中搜索：

```text
/sh 活动方案 --local
```

在思源全局范围搜索：

```text
/sh 深圳
```

查看最近捕获的笔记：

```text
/inbox
```

查看近期笔记中的标签汇总：

```text
/tags
```

## ⚙️ 环境变量配置

这个技能通过本地接口连接思源。你可以使用这些环境变量调整配置：

- `SIYUAN_BASE_URL`：思源 API 地址。默认：`http://127.0.0.1:6806`
- `SIYUAN_TOKEN`：思源 API Token。可选。
- `OPENCLAW_SIYUAN_NOTEBOOK`：目标笔记本名称。默认：`Openclaw Inbox`
- `OPENCLAW_SIYUAN_INDEX_PATH`：索引文档路径。默认：`/index`
- `OPENCLAW_SIYUAN_SERVER_URL`：本地 helper service 地址。默认：`http://127.0.0.1:6868`

## 🛠️ 开发者 / 命令行接口

这一节只用于调试，或者在没有 Agent 的情况下直接从终端调用脚本。

根据你的集成方式，OpenClaw 可能会直接调用仓库里的脚本，也可能通过本地 helper service 调用。若要本地测试，可执行：

```bash
# 检查环境状态
python scripts/siyuan_ai_notes.py doctor

# 初始化专用 Inbox
python scripts/siyuan_ai_notes.py init

# 手动捕获一条笔记
python scripts/siyuan_ai_notes.py cap "下周二去深圳博物馆" --tag 行程

# 搜索和查看笔记
python scripts/siyuan_ai_notes.py sh "博物馆" --local
python scripts/siyuan_ai_notes.py list --limit 10
python scripts/siyuan_ai_notes.py tags
```

## ✅ 校验与测试

```bash
python scripts/validate_skill.py
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile scripts\siyuan_notes_core.py scripts\siyuan_ai_notes.py scripts\siyuan_server.py scripts\siyuan_client.py
```

## 📄 许可证

本项目使用 MIT License。详见 [LICENSE](LICENSE)。

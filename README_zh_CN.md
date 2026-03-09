OpenClaw SiYuan

专为 OpenClaw AI 智能体打造的思源笔记（SiYuan）交互技能。

它可以让你的 Agent 在思源笔记中拥有一个专属的“收件箱”（Inbox），在不打乱你原有笔记结构的前提下，帮你记录灵感、自动打标签、寻找上下文关联，并给出初步的 AI 建议。

For the English documentation, see README.md.

🧰 核心指令一览 (Cheat Sheet)

在 OpenClaw 的聊天框中，你可以直接对 AI 使用以下快捷指令：

/cap [内容]：闪电记录笔记（例如：/cap 下周二去博物馆）

/sh [关键词]：搜索历史笔记（例如：/sh 博物馆）

/inbox：查看最近被 AI 捕获的笔记列表

/tags：查看近期笔记中的标签汇总

/init：首次使用时，初始化专属工作区

/doctor：诊断思源 API 和本地环境状态

🌟 核心场景

告别手动排版和整理，直接在聊天框里向 AI 下达指令：

闪电捕捉：随手发给 AI 一句话（例如：/cap 下周二上午 10 点要去深圳博物馆看展）。

AI 自动丰富：Agent 会尝试提取 #深圳 #展会 等标签，从你的历史笔记中翻出真正相关的记录，并补充“出行准备”或“待办建议”等初步分析。

无感隔离：所有 AI 帮你生成的笔记都会统一放进 Openclaw Inbox 笔记本中，保持你原有资料库的纯净。

快速回顾：让 AI 帮你搜索最近的记录或特定的关键词。

🚀 快速部署

使用前，请确保你的思源笔记桌面端正在运行（并开放了 API 端口），且本地已安装 Python 3.11+。

安装依赖：

python -m pip install -r requirements.txt


加载技能：将此技能目录放入你的 OpenClaw 运行时可加载的位置。

配置参数 (可选)：如果你的思源笔记设置了 API Token 或修改了默认端口，请配置下方提到的环境变量。

💬 如何与 Agent 交互 (日常使用)

环境准备好后，你无需再触碰命令行。所有的操作都在 OpenClaw 的聊天界面中完成。

1. 首次初始化

让 Agent 检查环境并建立专属笔记本：

你： "/init" 或 "帮我初始化思源笔记工作区"

2. 随手记笔记

使用 /cap 命令加上你要记录的内容：

你： "/cap 本周五前需要草拟一份春季活动的发布方案。"

✨ 在你发送后，Agent 通常会在后台完成以下工作：

在 Openclaw Inbox 中新建一篇文档。

根据你的内容，自动生成精准的标签（Tags）。

检索你的历史笔记，把真正相关的内容作为双链插入。

对这则笔记进行初步分析（例如列出下一步行动、潜在风险等）。

全部排版完成后，在聊天框回复你最终的结果。

3. 检索与回顾

你： "/sh 活动方案 --local" (仅在 AI 专属 Inbox 中搜索相关笔记)
你： "/sh 深圳" (在思源笔记全局搜索)
你： "/inbox" (查看最近被 Agent 捕获的笔记列表)
你： "/tags" (查看近期笔记中的标签汇总)

⚙️ 环境变量配置

此技能通过本地接口与思源笔记通信，你可以通过设置环境变量来修改默认配置：

SIYUAN_BASE_URL：思源 API 地址（默认：http://127.0.0.1:6806）

SIYUAN_TOKEN：思源 API 鉴权 Token（默认为空）

OPENCLAW_SIYUAN_NOTEBOOK：专属笔记本名称（默认：Openclaw Inbox）

OPENCLAW_SIYUAN_INDEX_PATH：索引文档的路径（默认：/index）

OPENCLAW_SIYUAN_SERVER_URL：本地辅助服务地址（默认：http://127.0.0.1:6868）

🛠️ 开发者 / 命令行接口 (进阶用法)

仅当你想脱离 AI Agent 单独在终端使用，或者进行代码调试时，才需要看这一部分。

OpenClaw 会按具体集成方式调用这些本地能力；你也可以在终端里手动执行：

# 检查 API 和环境状态
python scripts/siyuan_ai_notes.py doctor

# 初始化空间
python scripts/siyuan_ai_notes.py init

# 手动触发捕获
python scripts/siyuan_ai_notes.py cap "下周二去深圳博物馆" --tag 旅游

# 搜索与列表查询
python scripts/siyuan_ai_notes.py sh "博物馆" --local
python scripts/siyuan_ai_notes.py list --limit 10
python scripts/siyuan_ai_notes.py tags


代码校验

python scripts/validate_skill.py
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile scripts\siyuan_notes_core.py scripts\siyuan_ai_notes.py scripts\siyuan_server.py scripts\siyuan_client.py


许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

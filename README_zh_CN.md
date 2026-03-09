# OpenClaw SiYuan

面向 OpenClaw 的思源笔记技能。

这个技能会在思源里维护一个独立的 `Openclaw Inbox`，用来承接 OpenClaw 生成的新笔记，不打乱用户原有笔记结构。它支持：

- 初始化专用空间和 `/index`
- 用 `/cap` 记录新笔记
- 自动补充标签、关联笔记和 AI 初步分析
- 用 `/sh` 搜索
- 用 `/inbox` 查看最近笔记
- 用 `/tags` 查看已提取标签

## 适合什么场景

- 快速记一条待办、计划、观察、灵感
- 让 OpenClaw 帮你补标签和初步分析
- 在思源里保留一个专门给 AI 记录和整理的 inbox

## 用户流程

### 1. 先准备环境

需要：

- 已安装并运行思源笔记
- 思源 API 可访问
- Python 3.11+

常用环境变量：

- `SIYUAN_BASE_URL`，默认 `http://127.0.0.1:6806`
- `SIYUAN_TOKEN`，可选
- `OPENCLAW_SIYUAN_NOTEBOOK`，默认 `Openclaw Inbox`
- `OPENCLAW_SIYUAN_INDEX_PATH`，默认 `/index`
- `OPENCLAW_SIYUAN_SERVER_URL`，默认 `http://127.0.0.1:6868`

### 2. 第一次使用

先检查环境：

```bash
python scripts/siyuan_ai_notes.py doctor
```

如果还没有专用空间，再初始化：

```bash
python scripts/siyuan_ai_notes.py init
```

初始化后会创建：

- 一个独立笔记本 `Openclaw Inbox`
- 一个索引文档 `/index`

### 3. 日常记录

记录一条新笔记：

```bash
python scripts/siyuan_ai_notes.py cap "下周二深圳博物馆"
```

正常情况下，`/cap` 会一次完成这些事：

- 创建笔记
- 写入 `## 标签`
- 写入 `## 关联笔记`
- 写入 `## 💡 建议`
- 更新 `/index`

如果某些字段还没补齐，脚本会返回：

- `note_created_pending_enrichment`
- `missing_outputs`
- `agent_followup`

这表示内部还有后续补全过程，但对用户目标仍然是“完成同一篇笔记”，不是新建另一篇。

### 4. 搜索与回顾

全局搜索：

```bash
python scripts/siyuan_ai_notes.py sh "深圳"
```

只搜索 OpenClaw Inbox：

```bash
python scripts/siyuan_ai_notes.py sh "深圳" --local
```

查看最近笔记：

```bash
python scripts/siyuan_ai_notes.py list --limit 10
```

查看标签：

```bash
python scripts/siyuan_ai_notes.py tags
```

## 笔记格式

新笔记默认结构：

```md
# 标题

**时间**: YYYY-MM-DD HH:mm
**来源**: OpenClaw

---

## 内容

用户输入

---

## 🏷️ 标签

#tag1 #tag2 #YYYY-MM

---

## 关联笔记

- ((doc_id "title"))

---

## 💡 建议

AI 初步分析

*Created by OpenClaw*
```

## 行为说明

### 标签

- 先按内容生成，再参考 `tag_candidates`
- 明显不相关的候选标签应丢弃
- 创建阶段不会默认把历史候选标签直接当最终标签
- 更新阶段如果 `final_tags` 是空列表，不会覆盖现有标签

### 关联笔记

- `related_note_candidates` 只是候选
- 只有真正相关时才写进 `## 关联笔记`
- 没有真正相关项时留空是合理结果

### AI 分析

- `ai_analysis` 只传正文，不带 `##` 标题
- 如果误传了 `## AI 分析` 或 `## 💡 建议`，脚本会在写入前剥离
- 文档中只保留一个 `## 💡 建议` 区块

## 仓库结构

- `SKILL.md`：给 agent 的核心指令
- `agents/openai.yaml`：OpenAI / UI 元数据
- `references/`：运行与开发文档
- `scripts/`：CLI、server、client、核心逻辑

## 校验

```bash
python ..\skill-creator\scripts\quick_validate.py .
python -m py_compile scripts\siyuan_notes_core.py scripts\siyuan_ai_notes.py scripts\siyuan_server.py scripts\siyuan_client.py
```

## 许可证

本仓库使用 MIT License。详见 [LICENSE](LICENSE)。

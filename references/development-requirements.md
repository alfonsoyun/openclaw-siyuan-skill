# OpenClaw SiYuan 开发要求

## 1. 目标

- 在不破坏用户原有笔记结构的前提下，使用独立的 `Openclaw Inbox` 作为专属空间。
- 通过 `/cap` 创建固定格式的笔记。
- 由 agent 生成标签、关联笔记和 AI 初步分析。
- 持续维护 `/index`。
- 提供 `/sh`、`/inbox`、`/tags`、`/doctor`、`/init` 这些稳定入口。

## 2. 核心对象

- Notebook: `Openclaw Inbox`
- Index: `/index`
- Note: 独立文档，包含 `内容`、`标签`、`关联笔记`、`建议`

## 3. 文档结构

```md
# 标题

**时间**: YYYY-MM-DD HH:mm
**来源**: OpenClaw

---

## 内容

用户输入

---

## 标签

#tag1 #tag2 #YYYY-MM

---

## 关联笔记

- ((doc_id "title"))

---

## 💡 建议

AI 初步分析

---

_Created by OpenClaw_
```

## 4. 总流程

### 4.1 `/doctor`

- 检查 API、notebook、`/index`、helper service。

### 4.2 `/init`

- 创建专属空间 `Openclaw Inbox`。
- 创建 `/index`。

### 4.3 `/cap`

- `/cap` 优先单次完成。
- 先确认环境可用。
- agent 根据内容生成 tags。
- agent 可以参考 `tag_candidates`，但不能依赖它们直接完成最终标签。
- 把最终 tags 写入 `## 标签`。
- agent 只在内容确实相关时生成 `related_notes`，否则留空。
- 把最终 `related_notes` 写入 `## 关联笔记`。
- agent 对笔记内容本身生成 `ai_analysis`。
- 在同一次 `/cap` 中写入文档内容、`## 标签`、`## 关联笔记`、`## 💡 建议`。
- 更新 `/index`。
- 完成之前不要向用户宣告 `/cap` 已结束。
- 如果缺少 `tags`、`related_notes` 或 `ai_analysis`，脚本返回 `note_created_pending_enrichment` 和 `missing_outputs`。
- 脚本返回 `agent_followup` 时，agent 必须先按要求补全同一篇笔记，再回复用户。
- `agent_followup` 必须包含内部更新模板，用来补全同一篇笔记。
- `tag_candidates`、`related_note_candidates`、`note_payload`、`enrichment_context` 可返回用于排查或后续显式更新，但不是默认 `/cap` 成功所必需的用户可见内容。

### 4.4 `/sh`

- 默认全局搜索。
- `--local` 只搜索 `Openclaw Inbox`。

### 4.5 `/inbox`

- 查看专属空间中的最近笔记。

### 4.6 `/tags`

- 查看已提取标签。

## 5. 标签要求

- `tag_candidates` 只是候选提示。
- agent 必须先按内容生成 tags。
- agent 不能直接照搬 `tag_candidates`。
- tags 必须写入 `## 标签`。
- 创建阶段不能默认把历史候选标签直接当最终标签。
- 更新阶段如果 `final_tags` 是空列表，应视为不更新标签，不能覆盖现有标签。
- agent 可以补充不在 `tag_candidates` 中但更贴合内容的新标签。
- 明显无关的候选标签必须丢弃。
- 手动标签默认不传；只有用户明确要求时才加入。

## 6. 关联笔记要求

- `related_note_candidates` 可以返回，但不是默认 `/cap` 成功所必需。
- 最终 `related_notes` 由 agent 判断是否真正相关。
- 不相关时允许留空。
- 只有最终 `related_notes` 能写入 `## 关联笔记`。
- 候选笔记不能在 `ai_analysis` 中被写成已确认的关联事实。

## 7. AI 分析要求

- `ai_analysis` 由 OpenClaw agent 生成。
- `ai_analysis` 分析的是笔记内容本身。
- `ai_analysis` 只传正文，不包含 `##` 标题。
- 如果误传 `## AI 分析`、`## 💡 建议` 等标题，脚本要在写入前剥离。
- 文档中只能保留一个 `## 💡 建议` 区块。
- `ai_analysis` 在写入前要做换行规范化，兼容 `\n`、`` `n ``、`\r\n` 等常见格式。
- `ai_analysis` 必须提供足够的初步分析。
- `ai_analysis` 不能退化为单行泛建议。
- 短内容至少 3 个 bullet points。
- 中等内容至少 4 个 bullet points。
- 长内容至少 4 个结构化 sections。

## 8. 接口要求

### 8.1 用户侧命令

- `/init`
- `/doctor`
- `/cap`
- `/sh`
- `/inbox`
- `/tags`

### 8.2 底层 CLI / HTTP

- CLI 保持 `init`、`doctor`、`cap`、`sh`、`list`、`tags`
- 用户侧 `/inbox` 对应底层 `list`
- HTTP 保持 `GET /health`、`POST /doctor`、`POST /init`、`POST /cap`、`POST /sh`、`POST /list`、`POST /tags`

## 9. 实现约束

- 共享逻辑集中在 `scripts/siyuan_notes_core.py`
- CLI、service、client 只做入口和参数转换
- 文档、skill、实现语义保持一致
- 不把 AI 生成责任下沉为脚本内部的隐式推断

## 10. 验证

- `SKILL.md` 通过本仓库自带的 `python scripts/validate_skill.py`
- 关键脚本通过 `py_compile`
- 纯逻辑辅助函数通过 `unittest`
- `/doctor`、`/init`、`/cap`、`/sh`、`/inbox`、`/tags` 语义一致
- 单次 `/cap` 能写入 `## 标签`、`## 关联笔记`、`## 💡 建议`
- `/cap` 返回 `agent_followup` 时包含内部更新模板和用户回复模板
- `/cap` 缺少必要输出时返回 `note_created_pending_enrichment` 和 `missing_outputs`

## 11. Follow-up Execution Notes

- The normal local entrypoints are the Python scripts under `scripts/`.
- Standard local commands use `python scripts/siyuan_ai_notes.py ...`.
- When console encoding is unstable on Windows, the same commands may be run with `python -X utf8`.
- Local commands run from `workspace/skills/openclaw-siyuan/`.
- Standard `/cap` follow-up uses the helper service first when the update includes structured fields such as `final_tags`, `related_notes`, or `note_payload`.
- The CLI follow-up path is for simple `--doc-id ... --ai "..."` updates.
- A follow-up update for the same `/cap` request reuses the same `doc_id`.
- `agent_followup` should expose a helper-service request template and mark it as the preferred transport for structured follow-up.
- `agent_followup` should also expose the skill workdir and a fallback CLI template for simple updates.
- On Windows PowerShell, helper service is the stable default for structured follow-up because CLI JSON quoting is fragile.
- If a follow-up request contains enrichment data but no `doc_id`, recover the pending note first and continue that note, or return an explicit error before creating anything else.

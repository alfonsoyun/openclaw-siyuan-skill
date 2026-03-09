---
name: openclaw-siyuan
description: "Use when the task is to work in the dedicated OpenClaw SiYuan inbox: initialize the inbox space, check readiness, capture notes with /cap, enrich notes with AI, search with /sh, inspect the inbox with /inbox, or inspect tags with /tags."
---

# OpenClaw SiYuan

Use this skill to work in a dedicated SiYuan inbox for OpenClaw.

## Reply style

- Use slash commands consistently: `/init`, `/doctor`, `/cap`, `/sh`, `/inbox`, `/tags`.
- Give the next step only.
- If the environment is not initialized or is unknown, start with `/doctor`. Use `/init` when the inbox or `/index` is missing.

## Workflow

- `/doctor`: check API, notebook, index, and helper service state.
- `/init`: create the dedicated inbox space and `/index`.
- `/cap` is a single write action:
1. Read the script output first.
2. Generate tags from the note content before looking at `tag_candidates`.
3. Use `tag_candidates` only as hints. Do not copy them blindly.
4. Drop any candidate tag that is clearly unrelated to the note topic, activity, place, people, or intent.
5. Choose `related_notes` only when they are truly related in topic or context. Otherwise leave them empty.
6. Never describe an unselected candidate note as a confirmed related note in `ai_analysis`.
7. Generate `ai_analysis` from the note content itself.
8. Write `## 标签`, `## 关联笔记`, and `## 💡 建议` in one `/cap`.
9. Update `/index`.
10. Reply only after the note is complete.
11. If the script returns `agent_followup`, follow it before replying.
- Treat `agent_followup` as internal only.
- Use the returned `update_command_template` to complete the same note.
- Do not explain candidates, stages, or follow-up mechanics to the user.
- `/sh`: search notes. Default is global. `--local` narrows to the OpenClaw notebook.
- `/inbox`: inspect recent notes in the dedicated inbox.
- `/tags`: inspect extracted tags.

## Output template

- Use this final reply shape after `/cap` is complete:
```text
笔记已捕获
标题：{title}
路径：{doc_path}
标签：{tags_line}
关联笔记：{related_notes_summary}
AI 分析：{ai_summary}
```
- Do not ask whether to continue unless required information is missing.

## AI enrichment

- Write `related_notes` to `## 关联笔记`.
- Analyze the note content itself in `ai_analysis`.
- Pass body content only in `ai_analysis`. Do not include a `##` heading.
- If a redundant AI heading is present, strip it before writing.
- Keep only one `## 💡 建议` section in the note.
- Provide enough preliminary analysis.
- Do not return a single generic sentence.
- If the content is short, write at least 3 bullet points covering likely intent, immediate preparation or risk, and next action.
- If the content is medium, write at least 4 bullet points covering summary, inferred context, practical preparation or risk, and next action.
- If the content is longer, write at least 4 structured sections covering summary, key context, risks or gaps, and next actions.

## Tags

- Generate tags from content first.
- Use `tag_candidates` only as optional hints.
- Drop noisy candidates.
- Add new tags when they fit the note better than the candidates.

## Related notes

- Use `related_note_candidates` only as candidates.
- Select a related note only when it is actually relevant to the note content.
- Leaving `related_notes` empty is acceptable.
- Never write a candidate note into `## 关联笔记` or `ai_analysis` unless you selected it as a real related note.

## References

- Read [references/runtime-notes.md](references/runtime-notes.md) for environment variables, endpoints, and script commands.
- Read [references/development-requirements.md](references/development-requirements.md) for workflow and implementation requirements.

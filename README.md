# OpenClaw SiYuan

OpenClaw SiYuan is a skill for capturing and organizing notes in a dedicated SiYuan inbox.

For a user-oriented Chinese guide, see [README_zh_CN.md](README_zh_CN.md).

It creates notes in `Openclaw Inbox`, maintains `/index`, and supports:

- `/doctor` for environment checks
- `/init` for inbox and index setup
- `/cap` for note capture with tags, related notes, and AI analysis
- `/sh` for search
- `/inbox` for recent notes
- `/tags` for extracted tags

## Structure

- `SKILL.md`: agent instructions
- `agents/openai.yaml`: UI metadata
- `references/`: runtime and development references
- `scripts/`: CLI, server, client, and shared workflow logic

## Requirements

- SiYuan desktop app with API access
- Python 3.11+

Environment variables:

- `SIYUAN_BASE_URL` default `http://127.0.0.1:6806`
- `SIYUAN_TOKEN` optional
- `OPENCLAW_SIYUAN_NOTEBOOK` default `Openclaw Inbox`
- `OPENCLAW_SIYUAN_INDEX_PATH` default `/index`
- `OPENCLAW_SIYUAN_SERVER_URL` default `http://127.0.0.1:6868`

## CLI

```bash
python scripts/siyuan_ai_notes.py doctor
python scripts/siyuan_ai_notes.py init
python scripts/siyuan_ai_notes.py cap "下周二深圳博物馆"
python scripts/siyuan_ai_notes.py sh "深圳" --local
python scripts/siyuan_ai_notes.py list --limit 10
python scripts/siyuan_ai_notes.py tags
```

## Validation

```bash
python ..\skill-creator\scripts\quick_validate.py .
python -m py_compile scripts\siyuan_notes_core.py scripts\siyuan_ai_notes.py scripts\siyuan_server.py scripts\siyuan_client.py
```

## Notes

- `ai_analysis` should contain body content only, not a `##` heading.
- Related notes may be empty when no candidate is truly relevant.
- This repository is licensed under the MIT License. See [LICENSE](LICENSE).

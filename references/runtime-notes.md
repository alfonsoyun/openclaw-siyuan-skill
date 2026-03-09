# Runtime Notes

## Environment

- `SIYUAN_BASE_URL`: SiYuan API base URL. Default: `http://127.0.0.1:6806`
- `SIYUAN_TOKEN`: Optional SiYuan API token.
- `OPENCLAW_SIYUAN_NOTEBOOK`: Notebook name. Default: `Openclaw Inbox`
- `OPENCLAW_SIYUAN_INDEX_PATH`: Index document path. Default: `/index`
- `OPENCLAW_SIYUAN_SERVER_URL`: Local helper service URL. Default: `http://127.0.0.1:6868`

## Direct CLI commands

```bash
python scripts/siyuan_ai_notes.py init
python scripts/siyuan_ai_notes.py doctor
python scripts/siyuan_ai_notes.py cap "学习 SiYuan API" --tag 技术
python scripts/siyuan_ai_notes.py cap "学习 SiYuan API" --doc-id 20260306010101-abc1234 --ai "补充建议"
python scripts/siyuan_ai_notes.py sh "SiYuan" --limit 10
python scripts/siyuan_ai_notes.py sh "SiYuan" --local
python scripts/siyuan_ai_notes.py list --limit 10
python scripts/siyuan_ai_notes.py tags
```

## Service endpoints

- `GET /health`
- `POST /doctor`
- `POST /init`
- `POST /cap`
- `POST /sh`
- `POST /list`
- `POST /tags`
- `GET /shutdown`

## Validation

- Run `python ..\skill-creator\scripts\quick_validate.py .` from the skill directory to validate `SKILL.md`.
- Run `python -m py_compile scripts\siyuan_notes_core.py scripts\siyuan_ai_notes.py scripts\siyuan_server.py scripts\siyuan_client.py` to catch syntax errors.

## Troubleshooting

- Use `python -X utf8` if the Windows console shows encoding issues.
- Confirm the SiYuan desktop app is running and the API port is reachable before blaming the scripts.
- Run `doctor` before write operations if you suspect the notebook or index is missing.
- Keep the search semantics consistent with the skill contract: global by default, notebook-only with `--local`.
- Prefer the bundled scripts over ad hoc SQL so the note format and index stay consistent.

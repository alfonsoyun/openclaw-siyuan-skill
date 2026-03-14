# Runtime Notes

## Environment

- `SIYUAN_BASE_URL`: SiYuan API base URL. Default: `http://127.0.0.1:6806`
- `SIYUAN_TOKEN`: Optional SiYuan API token
- `OPENCLAW_SIYUAN_NOTEBOOK`: Notebook name. Default: `Openclaw Inbox`
- `OPENCLAW_SIYUAN_INDEX_PATH`: Index document path. Default: `/index`
- `OPENCLAW_SIYUAN_SERVER_URL`: Local helper service URL. Default: `http://127.0.0.1:6868`

## Direct CLI Commands

Use these Python entrypoints for normal local execution.
Run them from the skill root: `workspace/skills/openclaw-siyuan/`.
If the Windows console shows encoding issues, run the same command with `python -X utf8`.

```bash
python scripts/siyuan_ai_notes.py init
python scripts/siyuan_ai_notes.py doctor
python scripts/siyuan_ai_notes.py cap "Study the SiYuan API"
python scripts/siyuan_ai_notes.py cap "Study the SiYuan API" --tag tech
python scripts/siyuan_ai_notes.py cap "Study the SiYuan API" --doc-id 20260306010101-abc1234 --ai "Add follow-up suggestions"
python scripts/siyuan_ai_notes.py sh "SiYuan" --limit 10
python scripts/siyuan_ai_notes.py sh "SiYuan" --local
python scripts/siyuan_ai_notes.py list --limit 10
python scripts/siyuan_ai_notes.py tags
```

Use `--doc-id` to continue the same note during follow-up updates. This simple CLI path is for body-only updates or manual tags.

```bash
python scripts/siyuan_ai_notes.py cap "Study the SiYuan API" --doc-id 20260306010101-abc1234 --tag tech --ai "Add follow-up suggestions"
```

## Helper Service

Start the local HTTP helper:

```bash
python scripts/siyuan_server.py --host 127.0.0.1 --port 6868
```

Available endpoints:

- `GET /health`
- `POST /doctor`
- `POST /init`
- `POST /cap`
- `POST /sh`
- `POST /list`
- `POST /tags`
- `GET /shutdown`

For structured follow-up updates, the helper service is the standard path when the runtime can send JSON safely.
This is the stable default on Windows PowerShell because JSON quoting is much less fragile than CLI flags.

```bash
python scripts/siyuan_server.py --host 127.0.0.1 --port 6868
```

```json
POST /cap
{
  "content": "Study the SiYuan API",
  "doc_id": "20260306010101-abc1234",
  "final_tags": ["tech", "2026-03"],
  "related_notes": [],
  "ai_analysis": "- Confirm the endpoint scope\n- Check authentication\n- Keep one working example",
  "note_payload": {
    "title": "Study the SiYuan API",
    "timestamp": "2026-03-06 01:01",
    "source": "OpenClaw",
    "content": "Study the SiYuan API",
    "tags": ["2026-03"],
    "tags_line": "#2026-03"
  }
}
```

## Validation

- Run `python scripts/validate_skill.py` to validate `SKILL.md` frontmatter.
- Run `python -m unittest discover -s tests -p "test_*.py"` to validate pure workflow helpers.
- Run `python -m py_compile scripts\siyuan_notes_core.py scripts\siyuan_ai_notes.py scripts\siyuan_server.py scripts\siyuan_client.py` to catch syntax errors.

## Troubleshooting

- Use `python -X utf8` if the Windows console shows encoding issues.
- If a script says it cannot find `scripts/...`, check that the working directory is `workspace/skills/openclaw-siyuan/`.
- Confirm the SiYuan desktop app is running and the API port is reachable before blaming the scripts.
- Run `doctor` before write operations if you suspect the notebook or index is missing.
- Keep the search semantics consistent with the skill contract: global by default, notebook-only with `--local`.
- Prefer the bundled scripts over ad hoc SQL so the note format and index stay consistent.
- Use the helper service first when a follow-up update needs structured JSON fields.
- Use the documented CLI follow-up path for simple `--doc-id ... --ai "..."` updates.

# OpenClaw SiYuan

OpenClaw SiYuan is a skill for the OpenClaw agent. It gives the agent a dedicated inbox inside your SiYuan workspace so it can capture notes, add tags, suggest related notes, and write preliminary AI analysis without changing your existing notebook structure.

For a Chinese guide, see [README_zh_CN.md](README_zh_CN.md).

## 🧰 Cheat Sheet

Use these commands directly in the OpenClaw chat:

- `/cap [content]`: capture a quick note
- `/sh [keyword]`: search notes
- `/inbox`: show recently captured inbox notes
- `/tags`: show collected tags from recent notes
- `/init`: initialize the dedicated inbox
- `/doctor`: check SiYuan API and local environment status

## 🌟 Why Use This Skill

- Quick capture: tell the agent to remember something without opening SiYuan manually.
- Guided enrichment: the agent will usually add tags, keep only truly relevant related notes, and write preliminary analysis.
- Dedicated workspace: AI-created notes go to `Openclaw Inbox`, so your existing notebooks stay untouched.
- Fast retrieval: search past notes or inspect recent inbox items from chat.

## 🚀 Quick Setup

Before using the skill, make sure:

- the SiYuan desktop app is running with API access enabled
- Python 3.11 or newer is available locally

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Load the skill:

- place this repository where your OpenClaw runtime can load it

Optional configuration:

- if your SiYuan API uses a token or a different port, set the environment variables listed below

## 💬 How to Talk to Your Agent

After the skill is loaded, daily use happens in the OpenClaw chat UI.

### 1. First-Time Initialization

Ask the agent to check the environment and prepare the dedicated inbox:

```text
/init
```

or:

```text
Help me initialize the SiYuan workspace.
```

### 2. Capture a Note

Use `/cap` followed by the content you want to record:

```text
/cap We need to draft launch ideas for the spring campaign by this Friday.
```

The agent will usually:

- create a new note in `Openclaw Inbox`
- generate tags from the content
- keep related notes only when they are clearly relevant
- add preliminary AI analysis such as risks, next actions, or preparation notes
- reply after the note is written

### 3. Search and Review

Search only inside the OpenClaw inbox:

```text
/sh campaign --local
```

Search globally across all SiYuan notebooks:

```text
/sh museum
```

Review recent inbox notes:

```text
/inbox
```

Inspect collected tags from recent notes:

```text
/tags
```

## ⚙️ Environment Variables

The skill connects to SiYuan locally. You can customize the connection with these environment variables:

- `SIYUAN_BASE_URL`: SiYuan API URL. Default: `http://127.0.0.1:6806`
- `SIYUAN_TOKEN`: SiYuan API token. Optional.
- `OPENCLAW_SIYUAN_NOTEBOOK`: target notebook name. Default: `Openclaw Inbox`
- `OPENCLAW_SIYUAN_INDEX_PATH`: index document path. Default: `/index`
- `OPENCLAW_SIYUAN_SERVER_URL`: local helper service URL. Default: `http://127.0.0.1:6868`

## 🛠️ Developer / CLI Reference

This section is only for debugging or standalone terminal use.

Depending on your integration, OpenClaw may invoke the bundled scripts directly or use the helper service. For local testing, you can run:

```bash
# Check environment health
python scripts/siyuan_ai_notes.py doctor

# Initialize the dedicated inbox
python scripts/siyuan_ai_notes.py init

# Capture a note manually
python scripts/siyuan_ai_notes.py cap "Visit the city museum next Tuesday" --tag work

# Search and inspect notes
python scripts/siyuan_ai_notes.py sh "museum" --local
python scripts/siyuan_ai_notes.py list --limit 10
python scripts/siyuan_ai_notes.py tags
```

## ✅ Validation and Testing

```bash
python scripts/validate_skill.py
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile scripts\siyuan_notes_core.py scripts\siyuan_ai_notes.py scripts\siyuan_server.py scripts\siyuan_client.py
```

## 📄 License

This repository is licensed under the MIT License. See [LICENSE](LICENSE).

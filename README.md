OpenClaw SiYuan

OpenClaw SiYuan is a skill for the OpenClaw AI agent. It provides your agent with a dedicated, distraction-free inbox inside your SiYuan workspace to capture notes, automatically generate tags, find related historical context, and write preliminary AI analysis.

For a user-oriented Chinese guide, see README_zh_CN.md.

🧰 Cheat Sheet

You can use these quick commands directly in the OpenClaw chat:

/cap [content]: Capture a quick note (e.g., /cap Visit the museum next Tuesday)

/sh [keyword]: Search your notes (e.g., /sh museum)

/inbox: List recent notes captured by the AI

/tags: View the collected tag list from recent notes

/init: Initialize the dedicated workspace (first-time use)

/doctor: Diagnose SiYuan API and local environment status

🌟 Why use this skill?

Instead of opening your notebook and formatting everything manually, you can simply chat with your OpenClaw agent:

Quick Capture: Tell the AI to remember something (/cap Visit the city museum next Tuesday).

Auto-Enrichment: The agent tries to generate useful tags, search your history for truly relevant notes, and add a brief AI analysis or action plan.

Distraction-Free: All AI-generated notes go straight to a dedicated Openclaw Inbox notebook. Your existing notebooks remain untouched.

Quick Retrieval: Ask the agent to find past notes or show your recent inbox items.

🚀 Quick Setup

To use this skill, you need the SiYuan desktop app running with API access enabled, and Python 3.11+.

Install dependencies:

python -m pip install -r requirements.txt


Load the Skill: Place this repository where your OpenClaw runtime can load it.

Configure (Optional): If your SiYuan API requires a token or runs on a different port, set the Environment Variables (see below).

💬 How to Talk to Your Agent (Daily Use)

Once the skill is loaded in OpenClaw, you interact entirely through the chat interface.

1. First-time Initialization

Tell the agent to check the environment and set up the dedicated workspace:

You: "/init" or "Help me initialize the SiYuan workspace."

2. Capture a Note

Use the /cap command followed by your thought, task, or observation:

You: "/cap We need to draft launch ideas for the spring campaign by this Friday."

✨ Behind the scenes, the Agent will usually:

Create a new note in the Openclaw Inbox.

Read the content and generate relevant #tags.

Search your previous notes and link truly relevant ones.

Append a structured AI analysis (e.g., potential risks, next action steps).

Reply to you when the enriched note is fully formatted.

3. Search and Review

Ask the agent to look up information from your notes:

You: "/sh campaign --local" (Searches only inside the OpenClaw inbox)
You: "/sh museum" (Searches globally across all your SiYuan notebooks)
You: "/inbox" (Lists your most recently captured notes)
You: "/tags" (Shows the collected tags from recent notes)

⚙️ Environment Variables

The skill connects to SiYuan locally. You can customize the connection using these environment variables:

SIYUAN_BASE_URL: SiYuan API URL (Default: http://127.0.0.1:6806)

SIYUAN_TOKEN: Your SiYuan API token (Optional)

OPENCLAW_SIYUAN_NOTEBOOK: Target notebook name (Default: Openclaw Inbox)

OPENCLAW_SIYUAN_INDEX_PATH: Index document path (Default: /index)

OPENCLAW_SIYUAN_SERVER_URL: Local helper service URL (Default: http://127.0.0.1:6868)

🛠️ Developer / CLI Reference (Advanced)

You only need this section if you are debugging the skill or want to use the Python scripts standalone without the AI Agent.

Depending on the integration, OpenClaw may invoke the bundled scripts directly or use the helper service. For testing or terminal usage, you can run them directly:

# Check environment health
python scripts/siyuan_ai_notes.py doctor

# Initialize workspace
python scripts/siyuan_ai_notes.py init

# Capture a note manually via CLI
python scripts/siyuan_ai_notes.py cap "Visit the city museum next Tuesday" --tag work

# Search via CLI
python scripts/siyuan_ai_notes.py sh "museum" --local
python scripts/siyuan_ai_notes.py list --limit 10
python scripts/siyuan_ai_notes.py tags


Validation & Testing

python scripts/validate_skill.py
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile scripts\siyuan_notes_core.py scripts\siyuan_ai_notes.py scripts\siyuan_server.py scripts\siyuan_client.py


License

This repository is licensed under the MIT License. See LICENSE.

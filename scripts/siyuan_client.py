#!/usr/bin/env python3
"""Client for the local OpenClaw SiYuan helper service."""

from __future__ import annotations

import argparse
import json
import os

import requests

from siyuan_notes_core import setup_utf8_console

SERVER_URL = os.getenv("OPENCLAW_SIYUAN_SERVER_URL", "http://127.0.0.1:6868").rstrip("/")


def call_get(endpoint: str) -> dict:
    response = requests.get(f"{SERVER_URL}{endpoint}", timeout=30)
    response.raise_for_status()
    return response.json()


def call_post(endpoint: str, data: dict | None = None) -> dict:
    response = requests.post(f"{SERVER_URL}{endpoint}", json=data or {}, timeout=30)
    response.raise_for_status()
    return response.json()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenClaw SiYuan service client")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize the notebook and index")
    subparsers.add_parser("doctor", help="Check API, workspace, index, and helper service state")

    cap_parser = subparsers.add_parser("cap", help="Capture a note")
    cap_parser.add_argument("content", help="Note content")
    cap_parser.add_argument("--tag", action="append", dest="tags", help="Optional manual tag")
    cap_parser.add_argument("--ai", dest="ai_analysis", help="AI analysis to append or update")
    cap_parser.add_argument("--doc-id", dest="doc_id", help="Document ID to update")
    cap_parser.add_argument("--final-tags-json", dest="final_tags_json", help="Final tags JSON selected by the agent")
    cap_parser.add_argument("--related-notes-json", dest="related_notes_json", help="Selected related notes JSON")
    cap_parser.add_argument("--note-payload-json", dest="note_payload_json", help="Note payload JSON returned from the create step")

    sh_parser = subparsers.add_parser("sh", help="Search notes")
    sh_parser.add_argument("keyword", help="Search keyword")
    sh_parser.add_argument("--limit", type=int, default=50, help="Maximum number of results")
    sh_parser.add_argument("--local", action="store_true", help="Search only in the OpenClaw notebook")

    list_parser = subparsers.add_parser("list", help="List recent notes")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum number of results")

    subparsers.add_parser("tags", help="List extracted tags")
    subparsers.add_parser("health", help="Check service status")
    return parser


def main() -> int:
    setup_utf8_console()
    args = build_parser().parse_args()
    try:
        if args.command == "health":
            result = call_get("/health")
            print(result)
            return 0
        if args.command == "init":
            print(call_post("/init"))
            return 0
        if args.command == "doctor":
            print(call_post("/doctor"))
            return 0
        if args.command == "cap":
            payload = {"content": args.content}
            if args.tags:
                payload["tags"] = args.tags
            if args.ai_analysis:
                payload["ai_analysis"] = args.ai_analysis
            if args.doc_id:
                payload["doc_id"] = args.doc_id
            if args.final_tags_json:
                payload["final_tags"] = json.loads(args.final_tags_json)
            if args.related_notes_json:
                payload["related_notes"] = json.loads(args.related_notes_json)
            if args.note_payload_json:
                payload["note_payload"] = json.loads(args.note_payload_json)
            print(call_post("/cap", payload))
            return 0
        if args.command == "sh":
            print(call_post("/sh", {"keyword": args.keyword, "limit": args.limit, "local": args.local}))
            return 0
        if args.command == "list":
            print(call_post("/list", {"limit": args.limit}))
            return 0
        if args.command == "tags":
            print(call_post("/tags"))
            return 0
    except requests.RequestException as exc:
        print(f"Request failed: {exc}")
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

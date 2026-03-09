#!/usr/bin/env python3
"""CLI for the OpenClaw SiYuan note workflow."""

from __future__ import annotations

import argparse
import json

from siyuan_notes_core import (
    AINotesManager,
    DocumentValidationError,
    setup_utf8_console,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenClaw SiYuan notes")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize the OpenClaw notebook and index")
    subparsers.add_parser("doctor", help="Check API, workspace, index, and helper service state")

    cap_parser = subparsers.add_parser("cap", help="Capture a note")
    cap_parser.add_argument("content", help="Note content")
    cap_parser.add_argument("--tag", action="append", dest="tags", help="Optional manual tag")
    cap_parser.add_argument("--ai", dest="ai_analysis", help="AI analysis body to append or update; do not include a ## heading")
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
    return parser


def main() -> int:
    setup_utf8_console()
    args = build_parser().parse_args()
    manager = AINotesManager(logger=print)

    if args.command == "init":
        result = manager.initialize()
        print(f"Notebook ID: {result['notebook_id']}")
        print(f"Index doc ID: {result['index_doc_id']}")
        return 0

    if args.command == "doctor":
        print(json.dumps(manager.doctor(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "cap":
        try:
            final_tags = json.loads(args.final_tags_json) if args.final_tags_json else None
            related_notes = json.loads(args.related_notes_json) if args.related_notes_json else None
            note_payload = json.loads(args.note_payload_json) if args.note_payload_json else None
            result = manager.capture(
                content=args.content,
                manual_tags=args.tags,
                ai_analysis=args.ai_analysis,
                existing_doc_id=args.doc_id,
                final_tags=final_tags,
                related_notes=related_notes,
                note_payload=note_payload,
            )
        except DocumentValidationError as exc:
            print(json.dumps({"ok": False, "error": exc.to_dict()}, ensure_ascii=False, indent=2))
            return 1

        print(f"DOC_ID: {result['doc_id']}")
        if "action" in result:
            print(f"Action: {result['action']}")
        if "doc_path" in result:
            print(f"Path: {result['doc_path']}")
        if "tags" in result:
            print(f"Tags: {', '.join(result['tags'])}")
        if "missing_outputs" in result and result["missing_outputs"]:
            print(f"Missing Outputs: {', '.join(result['missing_outputs'])}")
        if "tag_candidates" in result:
            print("Tag Candidates:")
            print(json.dumps(result["tag_candidates"], ensure_ascii=False, indent=2))
        if "related_notes" in result:
            print(f"Related Notes: {len(result['related_notes'])}")
            for item in result["related_notes"]:
                print(f"  - {item['title']} ({item['id']})")
                print(f"    {item['reason']}")
        if "related_note_candidates" in result:
            print("Related Note Candidates:")
            print(json.dumps(result["related_note_candidates"], ensure_ascii=False, indent=2))
        if "note_payload" in result:
            print("Note Payload:")
            print(json.dumps(result["note_payload"], ensure_ascii=False, indent=2))
        if "agent_followup" in result:
            print("Agent Followup:")
            print(json.dumps(result["agent_followup"], ensure_ascii=False, indent=2))
        if result.get("action") == "note_enriched":
            updated_fields = result.get("updated_fields") or []
            if updated_fields:
                print(f"Updated Fields: {', '.join(updated_fields)}")
            else:
                print("Note updated.")
        return 0

    if args.command == "sh":
        results = manager.search(args.keyword, limit=args.limit, local=args.local)
        print(f"Found {len(results)} results")
        for item in results:
            preview = (item.get("content", "") or "").replace("\n", " ")[:100]
            print(f"[{item.get('created', '')[:10]}] {item.get('hpath', '')}")
            print(f"  {preview}")
        return 0

    if args.command == "list":
        notes = manager.list_notes(limit=args.limit)
        print(f"Found {len(notes)} notes")
        for item in notes:
            print(f"[{item.get('created', '')[:10]}] {item.get('hpath', '')}")
        return 0

    if args.command == "tags":
        tags = manager.list_tags()
        print(f"Found {len(tags)} tags")
        for tag in tags:
            print(f"#{tag}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

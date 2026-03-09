#!/usr/bin/env python3
"""Local HTTP wrapper around the OpenClaw SiYuan workflow."""

from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from siyuan_notes_core import AINotesManager, DocumentValidationError, setup_utf8_console

manager: AINotesManager | None = None


def get_manager() -> AINotesManager:
    global manager
    if manager is None:
        manager = AINotesManager()
    manager.ensure_initialized()
    return manager


class SiYuanHandler(BaseHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        return

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_payload(self) -> dict:
        size = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(size).decode("utf-8") if size else ""
        if not raw_body:
            return {}
        try:
            return json.loads(raw_body)
        except json.JSONDecodeError:
            return {key: value[0] for key, value in parse_qs(raw_body).items()}

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json({"status": "ok", "initialized": manager is not None})
            return
        if parsed.path == "/shutdown":
            self._send_json({"status": "shutting_down"})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        payload = self._read_payload()
        try:
            if parsed.path == "/init":
                result = get_manager().initialize()
                self._send_json({"status": "ok", **result})
                return
            if parsed.path == "/doctor":
                result = get_manager().doctor(skip_service_check=True)
                self._send_json({"status": "ok", **result})
                return
            if parsed.path == "/cap":
                result = get_manager().capture(
                    content=payload.get("content", ""),
                    manual_tags=_coerce_tags(payload.get("tags")),
                    ai_analysis=payload.get("ai_analysis"),
                    existing_doc_id=payload.get("doc_id"),
                    final_tags=_coerce_tags(payload.get("final_tags")),
                    related_notes=_coerce_related_notes(payload.get("related_notes")),
                    note_payload=_coerce_note_payload(payload.get("note_payload")),
                )
                self._send_json({"status": "ok", **result})
                return
            if parsed.path == "/sh":
                results = get_manager().search(
                    keyword=payload.get("keyword", ""),
                    limit=int(payload.get("limit", 50)),
                    local=_coerce_bool(payload.get("local", False)),
                )
                self._send_json({"status": "ok", "count": len(results), "results": results})
                return
            if parsed.path == "/list":
                notes = get_manager().list_notes(limit=int(payload.get("limit", 20)))
                self._send_json({"status": "ok", "count": len(notes), "results": notes})
                return
            if parsed.path == "/tags":
                tags = get_manager().list_tags()
                self._send_json({"status": "ok", "count": len(tags), "tags": tags})
                return
            self._send_json({"error": "Not found"}, status=404)
        except DocumentValidationError as exc:
            self._send_json({"error": exc.message, "code": exc.code}, status=400)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)


def _coerce_tags(value: object) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return None


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if isinstance(value, (int, float)):
        return bool(value)
    return False


def _coerce_related_notes(value: object) -> list[dict] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return None


def _coerce_note_payload(value: object) -> dict | None:
    if isinstance(value, dict):
        return value
    return None


def main() -> int:
    setup_utf8_console()
    parser = argparse.ArgumentParser(description="OpenClaw SiYuan helper service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6868)
    args = parser.parse_args()

    get_manager()
    server = HTTPServer((args.host, args.port), SiYuanHandler)
    print(f"Serving OpenClaw SiYuan on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

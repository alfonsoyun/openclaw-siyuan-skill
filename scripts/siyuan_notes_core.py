#!/usr/bin/env python3
"""Shared SiYuan note workflow used by the CLI and local service."""

from __future__ import annotations

import io
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime
from typing import Callable, Optional

import requests

SIYUAN_BASE_URL = os.getenv("SIYUAN_BASE_URL", "http://127.0.0.1:6806")
SIYUAN_TOKEN = os.getenv("SIYUAN_TOKEN", "")
NOTEBOOK_NAME = os.getenv("OPENCLAW_SIYUAN_NOTEBOOK", "Openclaw Inbox")
INDEX_DOC_PATH = os.getenv("OPENCLAW_SIYUAN_INDEX_PATH", "/index")
SERVER_URL = os.getenv("OPENCLAW_SIYUAN_SERVER_URL", "http://127.0.0.1:6868").rstrip("/")
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_ANALYSIS_SECTION = "💡 建议"
RELATED_NOTES_SECTION = "关联笔记"
AI_PLACEHOLDER_TEXT = "- 待补充"
FOOTER_TEXT = "_Created by OpenClaw_"
AUTO_TAG_LIMIT = 50
AUTO_TAG_TOP_K = 5
RELATED_NOTES_LIMIT = max(1, int(os.getenv("OPENCLAW_SIYUAN_RELATED_LIMIT", "5")))
RELATED_NOTES_FINAL_LIMIT = max(1, int(os.getenv("OPENCLAW_SIYUAN_RELATED_FINAL_LIMIT", "3")))
IGNORE_TAGS = {
    "AI",
    "AI笔记",
    "AI 笔记",
    "完成",
    "测试",
    "index",
    "正确",
}
GENERIC_DOC_TITLES = {
    "index",
    "Index",
    "inbox",
    "Inbox",
    "Openclaw Inbox",
    "OpenClaw Inbox",
    "未命名",
    "Sparks",
    "名单",
}
SUMMARY_SKIP_TEXTS = {
    "内容",
    "标签",
    "关联笔记",
    "建议",
    "💡 建议",
    "🏷️ 标签",
}


class DocumentValidationError(RuntimeError):
    """Raised when a requested document cannot be safely updated."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message}


class CaptureRequestError(RuntimeError):
    """Raised when a capture request is internally inconsistent."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message}


def setup_utf8_console() -> None:
    """Normalize stdout/stderr encoding on Windows consoles."""
    if sys.platform != "win32":
        return
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _extract_tags(text: str) -> list[str]:
    return re.findall(r"#([\w\u4e00-\u9fff-]+)", text or "")


def _meaningful_tags(tags: list[str]) -> list[str]:
    unique_tags = {
        tag
        for tag in tags
        if len(tag) > 1 and not tag.isdigit() and tag not in IGNORE_TAGS
    }
    return sorted(unique_tags)


def _escape_sql(value: str) -> str:
    return (value or "").replace("'", "''")


def _first_line(content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return "笔记"


def _title_from_hpath(hpath: str) -> str:
    tail = (hpath or "").split("/")[-1]
    title = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", tail)
    return title or "笔记"


def _extract_keywords(content: str, limit: int = 6) -> list[str]:
    tokens = [
        token.strip()
        for token in re.split(r"[\s,，。.!?;:：/\n]+", content or "")
        if len(token.strip()) >= 2
    ]
    cjk_sequences = re.findall(r"[\u4e00-\u9fff]{2,}", content or "")
    for sequence in cjk_sequences:
        tokens.append(sequence)
        max_window = min(4, len(sequence))
        for window in range(2, max_window + 1):
            for index in range(0, len(sequence) - window + 1):
                tokens.append(sequence[index : index + window])
    seen: set[str] = set()
    keywords: list[str] = []
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        keywords.append(token)
        if len(keywords) >= limit:
            break
    if keywords:
        return keywords
    fallback = _first_line(content)[:20].strip()
    return [fallback] if fallback else []


def _is_generic_doc(title: str, hpath: str) -> bool:
    clean_title = (title or "").strip()
    if clean_title in GENERIC_DOC_TITLES:
        return True
    if not hpath:
        return True
    if hpath in {INDEX_DOC_PATH, INDEX_DOC_PATH.lstrip("/")}:
        return True
    return False


def _clean_summary_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    cleaned = cleaned.lstrip("#*- ")
    cleaned = cleaned.replace("_Created by OpenClaw_", "").strip()
    if cleaned in SUMMARY_SKIP_TEXTS:
        return ""
    return cleaned[:120]


def _analysis_requirements(content: str) -> dict:
    clean = (content or "").strip()
    length = len(clean)
    if length <= 24:
        return {
            "depth": "light",
            "minimum_points": 3,
            "format": "bullet_list",
            "focus": ["possible intent", "immediate preparation or risk", "next useful question or action"],
            "rule": "Do not return a single generic sentence.",
        }
    if length <= 120:
        return {
            "depth": "standard",
            "minimum_points": 4,
            "format": "bullet_list",
            "focus": ["summary", "context inference", "practical preparation or risk", "next action"],
            "rule": "Keep it concrete and tied to the user content.",
        }
    return {
        "depth": "detailed",
        "minimum_points": 4,
        "format": "sections",
        "focus": ["summary", "key context", "risks or gaps", "next actions"],
        "rule": "Provide a structured preliminary analysis instead of a short suggestion.",
    }


def _tag_selection_requirements() -> dict:
    return {
        "rule": "Generate tags from the note content first, then keep only relevant tags from tag_candidates.",
        "allow_new_tags": True,
        "drop_noisy_candidates": True,
    }


def _normalize_ai_analysis(ai_analysis: Optional[str]) -> Optional[str]:
    if ai_analysis is None:
        return None
    clean = str(ai_analysis)
    replacements = [
        ("\\r\\n", "\n"),
        ("\\n", "\n"),
        ("\\r", "\n"),
        ("`r`n", "\n"),
        ("`n", "\n"),
        ("`r", "\n"),
        ("\r\n", "\n"),
        ("\r", "\n"),
    ]
    for old, new in replacements:
        clean = clean.replace(old, new)
    clean = clean.strip()
    lines = clean.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines:
        first = lines[0].strip()
        first_normalized = re.sub(r"^[#\s]+", "", first).strip().lower()
        if first_normalized in {
            "ai 分析",
            "ai分析",
            "ai analysis",
            "分析",
            "建议",
            "suggestion",
            "suggestions",
            "💡 建议",
            "💡建议",
        }:
            lines.pop(0)
            while lines and not lines[0].strip():
                lines.pop(0)
    clean = "\n".join(lines).strip()
    return clean or None


def _missing_cap_outputs(
    *,
    final_tags_provided: bool,
    related_notes_provided: bool,
    ai_analysis_provided: bool,
) -> list[str]:
    missing: list[str] = []
    if not final_tags_provided:
        missing.append("tags")
    if not related_notes_provided:
        missing.append("related_notes")
    if not ai_analysis_provided:
        missing.append("ai_analysis")
    return missing


def _has_enrichment_payload(
    *,
    final_tags: Optional[list[str]],
    related_notes: Optional[list[dict]],
    ai_analysis: Optional[str],
    note_payload: Optional[dict],
) -> bool:
    return any(item is not None for item in (final_tags, related_notes, ai_analysis, note_payload))


def _is_ai_heading_text(text: str) -> bool:
    clean = re.sub(r"^[#\s]+", "", (text or "").strip()).strip().lower()
    return clean in {
        AI_ANALYSIS_SECTION.lower(),
        "ai 分析",
        "ai分析",
        "ai analysis",
        "分析",
        "建议",
        "suggestion",
        "suggestions",
        "💡建议",
    }


def _is_footer_block(block: dict) -> bool:
    content = str(block.get("content", "") or "")
    return "Created by OpenClaw" in content


def _agent_followup_instruction(
    *,
    content: str,
    doc_id: str,
    doc_path: str,
    note_payload: dict,
    missing_outputs: list[str],
) -> dict:
    arg_map = {
        "tags": "--final-tags-json",
        "related_notes": "--related-notes-json",
        "ai_analysis": "--ai",
    }
    required_args = [arg_map[item] for item in missing_outputs if item in arg_map]
    if "tags" in missing_outputs:
        required_args.append("--note-payload-json")
    helper_payload_fields = ["content", "doc_id"]
    if "tags" in missing_outputs:
        helper_payload_fields.extend(["final_tags", "note_payload"])
    if "related_notes" in missing_outputs:
        helper_payload_fields.append("related_notes")
    if "ai_analysis" in missing_outputs:
        helper_payload_fields.append("ai_analysis")
    return {
        "action": "complete_cap",
        "internal_only": True,
        "rule": "Do not explain this follow-up to the user. Complete the same note first, then reply with the final result only.",
        "workdir": SKILL_ROOT,
        "required_outputs": missing_outputs,
        "preferred_transport": "helper_service",
        "write_sections": ["## 标签", "## 关联笔记", "## 💡 建议"],
        "helper_service_template": {
            "method": "POST",
            "url": f"{SERVER_URL}/cap",
            "health_url": f"{SERVER_URL}/health",
            "start_command": "python scripts/siyuan_server.py --host 127.0.0.1 --port 6868",
            "encoding_hint": "If the Windows console shows encoding issues, run the same command with python -X utf8.",
            "json_fields": helper_payload_fields,
            "payload": {
                "content": content,
                "doc_id": doc_id,
                "final_tags": [],
                "related_notes": [],
                "ai_analysis": "",
                "note_payload": note_payload,
            },
        },
        "update_command_template": {
            "command": "cap",
            "workdir": SKILL_ROOT,
            "content": content,
            "doc_id": doc_id,
            "note_payload": note_payload,
            "required_args": required_args,
        },
        "fallback_cli_template": {
            "workdir": SKILL_ROOT,
            "command": "python scripts/siyuan_ai_notes.py cap \"<content>\" --doc-id <doc_id> --tag <tag> --ai \"<body-only-ai-analysis>\"",
            "encoding_hint": "If the Windows console shows encoding issues, run the same command with python -X utf8.",
            "rule": "Use this fallback when helper service is unavailable. For structured tags or related notes, prefer helper service over CLI JSON on Windows PowerShell.",
        },
        "user_reply_template": {
            "rule": "Do not mention agent_followup, internal stages, candidate lists, or script coordination.",
            "format": [
                "笔记已捕获",
                "标题：{title}",
                "路径：{doc_path}",
                "标签：{tags_line}",
                "关联笔记：{related_notes_summary}",
                "AI 分析：{ai_summary}",
            ],
        },
    }


class SiYuanClient:
    """Thin wrapper around the SiYuan HTTP API."""

    def __init__(self, base_url: str = SIYUAN_BASE_URL, token: str = SIYUAN_TOKEN):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Token {token}"
        self.session.headers.update(headers)

    def _post(self, endpoint: str, data: Optional[dict] = None) -> dict:
        response = self.session.post(f"{self.base_url}{endpoint}", json=data or {}, timeout=30)
        response.raise_for_status()
        result = response.json()
        if result.get("code") != 0:
            raise RuntimeError(f"SiYuan API error: {result.get('msg', 'Unknown error')}")
        return result

    def list_notebooks(self) -> list[dict]:
        return self._post("/api/notebook/lsNotebooks").get("data", {}).get("notebooks", [])

    def create_notebook(self, name: str) -> dict:
        return self._post("/api/notebook/createNotebook", {"name": name}).get("data", {}).get("notebook", {})

    def get_or_create_notebook(self, name: str) -> dict:
        for notebook in self.list_notebooks():
            if notebook.get("name") == name:
                return notebook
        return self.create_notebook(name)

    def create_doc(self, notebook_id: str, path: str, markdown: str) -> str:
        return self._post(
            "/api/filetree/createDocWithMd",
            {"notebook": notebook_id, "path": path, "markdown": markdown},
        ).get("data", "")

    def append_block(self, parent_id: str, markdown: str) -> dict:
        return self._post(
            "/api/block/appendBlock",
            {"parentID": parent_id, "dataType": "markdown", "data": markdown},
        )

    def get_child_blocks(self, parent_id: str) -> list[dict]:
        return self._post("/api/block/getChildBlocks", {"id": parent_id}).get("data", [])

    def delete_block(self, block_id: str) -> None:
        self._post("/api/block/deleteBlock", {"id": block_id})

    def delete_child_blocks(self, parent_id: str) -> None:
        for child in reversed(self.get_child_blocks(parent_id)):
            block_id = child.get("id")
            if not block_id:
                continue
            try:
                self.delete_block(block_id)
            except Exception:
                continue

    def sql_query(self, stmt: str) -> list[dict]:
        return self._post("/api/query/sql", {"stmt": stmt}).get("data", [])

    def get_ids_by_hpath(self, notebook_id: str, hpath: str) -> list[str]:
        return self._post(
            "/api/filetree/getIDsByHPath",
            {"notebook": notebook_id, "path": hpath},
        ).get("data", [])

    def get_doc_by_hpath(self, notebook_id: str, hpath: str) -> Optional[dict]:
        rows = self.sql_query(
            f"""
            SELECT id, box, hpath, content, created, type
            FROM blocks
            WHERE box = '{_escape_sql(notebook_id)}'
              AND hpath = '{_escape_sql(hpath)}'
              AND type = 'd'
            LIMIT 1
            """
        )
        return rows[0] if rows else None

    def replace_doc_blocks(self, doc_id: str, markdown: str) -> None:
        self.delete_child_blocks(doc_id)
        self.append_block(doc_id, markdown)

    def update_block(self, block_id: str, markdown: str) -> None:
        self._post(
            "/api/block/updateBlock",
            {"id": block_id, "dataType": "markdown", "data": markdown},
        )

    def list_docs_in_notebook(self, notebook_id: str, limit: Optional[int] = None) -> list[dict]:
        limit_clause = f"LIMIT {limit}" if limit is not None else ""
        stmt = f"""
            SELECT id, content, created, hpath, box, type
            FROM blocks
            WHERE box = '{_escape_sql(notebook_id)}' AND type = 'd'
            ORDER BY created DESC
            {limit_clause}
        """
        return self.sql_query(stmt)

    def get_recent_blocks(self, limit: int = AUTO_TAG_LIMIT, notebook_id: Optional[str] = None) -> list[dict]:
        scope = f"WHERE box = '{_escape_sql(notebook_id)}'" if notebook_id else ""
        stmt = f"""
            SELECT id, content, created, hpath, box, type
            FROM blocks
            {scope}
            ORDER BY created DESC
            LIMIT {limit}
        """
        return self.sql_query(stmt)

    def get_doc_meta(self, doc_id: str) -> Optional[dict]:
        rows = self.sql_query(
            f"""
            SELECT id, content, created, hpath, box, type
            FROM blocks
            WHERE id = '{_escape_sql(doc_id)}'
            LIMIT 1
            """
        )
        return rows[0] if rows else None


class AINotesManager:
    """High-level workflow for OpenClaw notes inside SiYuan."""

    def __init__(self, client: Optional[SiYuanClient] = None, logger: Optional[Callable[[str], None]] = None):
        self.client = client or SiYuanClient()
        self.logger = logger or (lambda _: None)
        self.notebook: Optional[dict] = None
        self.index_doc_id: Optional[str] = None

    def log(self, message: str) -> None:
        self.logger(message)

    def initialize(self) -> dict:
        self.notebook = self.client.get_or_create_notebook(NOTEBOOK_NAME)
        docs = self.client.list_docs_in_notebook(self.notebook["id"], limit=200)
        index_doc = next((doc for doc in docs if self._is_index_doc(doc)), None)
        if index_doc is None:
            self.index_doc_id = self.client.create_doc(
                self.notebook["id"],
                INDEX_DOC_PATH,
                self._build_index_markdown([], []),
            )
            self.log(f"Created index document {self.index_doc_id}")
        else:
            self.index_doc_id = index_doc["id"]
            self.log(f"Using existing index document {self.index_doc_id}")
        return {"notebook_id": self.notebook["id"], "index_doc_id": self.index_doc_id}

    def ensure_initialized(self) -> None:
        if self.notebook and self.index_doc_id:
            return
        self.initialize()

    def doctor(self, skip_service_check: bool = False) -> dict:
        issues: list[dict] = []
        notebook_ok = False
        index_ok = False
        api_ok = False
        service_ok = False
        notebook_id: Optional[str] = None
        index_doc_id: Optional[str] = None

        try:
            notebooks = self.client.list_notebooks()
            api_ok = True
            target = next((item for item in notebooks if item.get("name") == NOTEBOOK_NAME), None)
            if target:
                notebook_ok = True
                notebook_id = target.get("id")
                self.notebook = target
                docs = self.client.list_docs_in_notebook(target["id"], limit=200)
                index_doc = next((doc for doc in docs if self._is_index_doc(doc)), None)
                if index_doc:
                    index_ok = True
                    index_doc_id = index_doc.get("id")
                    self.index_doc_id = index_doc_id
                else:
                    issues.append({"code": "missing_index", "message": "Index document is missing"})
            else:
                issues.append({"code": "missing_notebook", "message": "OpenClaw notebook is missing"})
        except Exception as exc:
            issues.append({"code": "api_unreachable", "message": str(exc)})

        if skip_service_check:
            service_ok = True
        else:
            try:
                response = requests.get(f"{SERVER_URL}/health", timeout=3)
                service_ok = response.ok
                if not service_ok:
                    issues.append({"code": "service_unreachable", "message": f"Helper service returned {response.status_code}"})
            except Exception as exc:
                issues.append({"code": "service_unreachable", "message": str(exc)})

        return {
            "api_ok": api_ok,
            "notebook_ok": notebook_ok,
            "index_ok": index_ok,
            "service_ok": service_ok,
            "notebook_id": notebook_id,
            "index_doc_id": index_doc_id,
            "issues": issues,
        }

    def analyze_auto_tags(self, content: str, limit: int = AUTO_TAG_LIMIT, top_k: int = AUTO_TAG_TOP_K) -> list[str]:
        return [item["tag"] for item in self.retrieve_tag_candidates(content, limit=limit, top_k=top_k)]

    def retrieve_tag_candidates(
        self,
        content: str,
        manual_tags: Optional[list[str]] = None,
        limit: int = AUTO_TAG_LIMIT,
        top_k: int = AUTO_TAG_TOP_K,
    ) -> list[dict]:
        recent_blocks = self.client.get_recent_blocks(limit=limit)
        counts = Counter(tag for block in recent_blocks for tag in _extract_tags(block.get("content", "")))
        candidate_counts = {
            tag: count
            for tag, count in counts.items()
            if len(tag) > 1 and not tag.isdigit() and tag not in IGNORE_TAGS
        }

        keywords = _extract_keywords(content, limit=8)
        relevant: list[tuple[str, int]] = []
        for tag, count in candidate_counts.items():
            score = count
            for keyword in keywords:
                if keyword in tag or tag in keyword:
                    score += 3
            if score > count:
                relevant.append((tag, score))

        if len(relevant) < top_k:
            relevant.extend(
                (tag, count)
                for tag, count in sorted(candidate_counts.items(), key=lambda item: (-item[1], item[0]))
                if tag not in {existing_tag for existing_tag, _ in relevant}
            )

        seen: set[str] = set()
        results: list[dict] = []
        for tag, score in sorted(relevant, key=lambda item: (-item[1], item[0]))[:top_k]:
            if tag in seen:
                continue
            seen.add(tag)
            results.append(
                {
                    "tag": tag,
                    "source": "history_match",
                    "reason": "matched recent tags and current content",
                    "score": score,
                }
            )

        for manual_tag in manual_tags or []:
            clean = str(manual_tag).strip().lstrip("#")
            if not clean or clean in seen:
                continue
            seen.add(clean)
            results.append(
                {
                    "tag": clean,
                    "source": "manual",
                    "reason": "explicitly provided by user",
                    "score": 999,
                }
            )
        return results

    def retrieve_related_notes(
        self,
        content: str,
        limit: int = RELATED_NOTES_LIMIT,
        exclude_doc_ids: Optional[set[str]] = None,
    ) -> list[dict]:
        keywords = _extract_keywords(content)
        if not keywords:
            return []

        rows: list[dict] = []
        for keyword in keywords[:8]:
            stmt = f"""
                SELECT id, box, hpath, content, created, type
                FROM blocks
                WHERE hpath != ''
                  AND (content LIKE '%{_escape_sql(keyword)}%' OR hpath LIKE '%{_escape_sql(keyword)}%')
                ORDER BY created DESC
                LIMIT 40
            """
            rows.extend(self.client.sql_query(stmt))
        candidates: dict[tuple[str, str], dict] = {}
        for row in rows:
            box = row.get("box")
            hpath = row.get("hpath")
            if not box or not hpath:
                continue
            if box == (self.notebook or {}).get("id") and hpath in {INDEX_DOC_PATH, INDEX_DOC_PATH.lstrip("/")}:
                continue

            candidate = candidates.setdefault(
                (box, hpath),
                {
                    "box": box,
                    "hpath": hpath,
                    "created": row.get("created", ""),
                    "matched_keywords": set(),
                    "score": 0,
                    "snippets": [],
                    "doc_id": None,
                },
            )
            text = row.get("content", "") or ""
            matched = [keyword for keyword in keywords if keyword in text or keyword in hpath]
            if matched:
                candidate["matched_keywords"].update(matched)
                candidate["score"] += len(matched) * 3
            if row.get("type") == "d":
                candidate["score"] += 2
                candidate["doc_id"] = row.get("id")
            snippet = _clean_summary_text(text)
            if snippet and snippet not in candidate["snippets"]:
                candidate["snippets"].append(snippet)
            candidate["score"] += 1

        ranked = sorted(
            candidates.values(),
            key=lambda item: (-item["score"], item["created"]),
        )
        results: list[dict] = []
        excluded = exclude_doc_ids or set()
        for candidate in ranked:
            doc_id = candidate.get("doc_id")
            if not doc_id:
                doc = self.client.get_doc_by_hpath(candidate["box"], candidate["hpath"])
                if doc is None:
                    continue
                doc_id = doc.get("id")
                candidate["doc_id"] = doc_id
                doc_content = _clean_summary_text(doc.get("content", ""))
                if doc_content and doc_content not in candidate["snippets"]:
                    candidate["snippets"].insert(0, doc_content)
            if not doc_id:
                continue
            if doc_id in excluded:
                continue
            title = _title_from_hpath(candidate["hpath"])
            reason_keywords = sorted(candidate["matched_keywords"])
            summary_parts = [title]
            for snippet in candidate["snippets"]:
                if snippet != title and snippet not in summary_parts:
                    summary_parts.append(snippet)
                if len(summary_parts) >= 3:
                    break
            summary = " | ".join(summary_parts)[:180]
            results.append(
                {
                    "id": doc_id,
                    "title": title,
                    "summary": summary,
                    "hpath": candidate["hpath"],
                    "box": candidate["box"],
                    "reason": f"关键词匹配: {', '.join(reason_keywords)}" if reason_keywords else "最近相关内容",
                    "score": candidate["score"],
                    "created": candidate["created"],
                }
            )
            if len(results) >= limit:
                break
        return results

    def select_related_notes(
        self,
        content: str,
        candidates: list[dict],
        limit: int = RELATED_NOTES_FINAL_LIMIT,
    ) -> list[dict]:
        keywords = set(_extract_keywords(content, limit=12))
        selected: list[dict] = []
        for candidate in candidates:
            title = candidate.get("title", "")
            hpath = candidate.get("hpath", "")
            if _is_generic_doc(title, hpath):
                continue
            matched_keywords = {
                keyword
                for keyword in keywords
                if keyword and (keyword in title or keyword in hpath or keyword in candidate.get("reason", ""))
            }
            score = int(candidate.get("score", 0))
            score += len(matched_keywords) * 2
            if len(matched_keywords) == 0 and score < 6:
                continue
            candidate = {**candidate, "score": score}
            selected.append(candidate)

        selected.sort(key=lambda item: (-int(item.get("score", 0)), item.get("created", "")), reverse=False)
        return selected[:limit]

    def generate_doc_path(self, content: str) -> str:
        title = re.sub(r"[^\w\u4e00-\u9fff\-_]", "", _first_line(content)[:30])
        if not title:
            title = "笔记"
        return f"/{datetime.now().strftime('%Y-%m-%d')}-{title}"

    def validate_doc_id(self, doc_id: str, require_workspace: bool = True) -> dict:
        self.ensure_initialized()
        clean_doc_id = (doc_id or "").strip()
        if not clean_doc_id:
            raise DocumentValidationError("missing_doc_id", "Document ID is required")

        meta = self.client.get_doc_meta(clean_doc_id)
        if meta is None:
            raise DocumentValidationError("doc_not_found", f"Document {clean_doc_id} was not found")
        if meta.get("type") != "d":
            raise DocumentValidationError("not_document", f"Block {clean_doc_id} is not a document")
        if require_workspace and self.notebook and meta.get("box") != self.notebook.get("id"):
            raise DocumentValidationError(
                "workspace_mismatch",
                f"Document {clean_doc_id} is outside the OpenClaw notebook",
            )
        if require_workspace and self.notebook and self.notebook.get("closed"):
            raise DocumentValidationError(
                "not_writable",
                f"Notebook {NOTEBOOK_NAME} is closed and cannot be updated",
            )
        return meta

    def build_note_payload(
        self,
        content: str,
        tags: list[str],
        timestamp: str,
        source: str = "OpenClaw",
    ) -> dict:
        return {
            "title": _first_line(content)[:30],
            "timestamp": timestamp,
            "source": source,
            "content": content,
            "tags": tags,
            "tags_line": " ".join(f"#{tag}" for tag in tags),
        }

    def normalize_related_notes(self, related_notes: Optional[list[dict]]) -> list[dict]:
        normalized: list[dict] = []
        for item in related_notes or []:
            doc_id = str(item.get("id", "")).strip()
            title = str(item.get("title", "")).strip()
            if not doc_id or not title:
                continue
            normalized.append(
                {
                    "id": doc_id,
                    "title": title,
                    "summary": str(item.get("summary", "")).strip(),
                    "hpath": str(item.get("hpath", "")).strip(),
                    "reason": str(item.get("reason", "")).strip(),
                    "score": item.get("score", 0),
                    "created": str(item.get("created", "")).strip(),
                }
            )
        return normalized[:RELATED_NOTES_FINAL_LIMIT]

    def normalize_final_tags(self, final_tags: Optional[list[str]]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in final_tags or []:
            clean = str(item).strip().lstrip("#")
            if not clean or clean in seen:
                continue
            seen.add(clean)
            normalized.append(clean)
        return normalized

    def _section_heading_matches(self, heading: str, expected: str) -> bool:
        clean_heading = (heading or "").strip()
        clean_expected = (expected or "").strip()
        return bool(clean_heading) and (
            clean_heading == clean_expected
            or clean_heading.endswith(clean_expected)
            or clean_expected.endswith(clean_heading)
        )

    def _find_note_sections(self, doc_id: str) -> dict[str, Optional[dict]]:
        children = self.client.get_child_blocks(doc_id)
        sections: dict[str, Optional[dict]] = {
            "tags_heading": None,
            "tags_body": None,
            "related_heading": None,
            "related_body": None,
            "ai_heading": None,
            "ai_body": None,
            "ai_extra_blocks": [],
            "footer_blocks": [],
        }
        for index, block in enumerate(children):
            if _is_footer_block(block):
                sections["footer_blocks"].append(block)
            if block.get("type") != "h":
                continue
            heading = block.get("content", "") or ""
            next_block = children[index + 1] if index + 1 < len(children) else None
            if "标签" in heading:
                sections["tags_heading"] = block
                sections["tags_body"] = next_block
            elif self._section_heading_matches(heading, RELATED_NOTES_SECTION):
                sections["related_heading"] = block
                sections["related_body"] = next_block
            elif _is_ai_heading_text(heading):
                ai_extra_blocks = sections["ai_extra_blocks"]
                if sections["ai_heading"] is None:
                    sections["ai_heading"] = block
                    sections["ai_body"] = next_block if next_block and next_block.get("type") != "h" else None
                else:
                    ai_extra_blocks.append(block)
                    if next_block and next_block.get("type") != "h":
                        ai_extra_blocks.append(next_block)
        return sections

    def _doc_needs_ai_enrichment(self, doc_id: str) -> bool:
        sections = self._find_note_sections(doc_id)
        ai_body = sections.get("ai_body")
        if not ai_body:
            return True
        content = str(ai_body.get("content", "") or "").strip()
        if not content:
            return True
        return content == AI_PLACEHOLDER_TEXT

    def _find_pending_doc_by_path(self, doc_path: str) -> Optional[dict]:
        assert self.notebook is not None
        doc = self.client.get_doc_by_hpath(self.notebook["id"], doc_path)
        if not doc:
            return None
        if not self._doc_needs_ai_enrichment(doc["id"]):
            return None
        return doc

    def _update_note_sections(
        self,
        doc_id: str,
        final_tags: Optional[list[str]] = None,
        related_notes: Optional[list[dict]] = None,
        ai_analysis: Optional[str] = None,
    ) -> None:
        sections = self._find_note_sections(doc_id)
        if final_tags is not None:
            tags_markdown = " ".join(f"#{tag}" for tag in final_tags)
            tags_body = sections.get("tags_body")
            if tags_body and tags_body.get("id"):
                self.client.update_block(tags_body["id"], tags_markdown)
            else:
                self.client.append_block(doc_id, f"\n## 标签\n\n{tags_markdown}\n")
        if related_notes is not None:
            related_markdown = self._build_related_notes_section(related_notes)
            related_body = sections.get("related_body")
            if related_body and related_body.get("id"):
                self.client.update_block(related_body["id"], related_markdown)
            else:
                self.client.append_block(doc_id, f"\n## {RELATED_NOTES_SECTION}\n\n{related_markdown}\n")
        if ai_analysis is not None:
            ai_markdown = self._build_ai_body(ai_analysis)
            footer_blocks = sections.get("footer_blocks") or []
            extra_blocks = sections.get("ai_extra_blocks") or []
            for block in reversed(extra_blocks):
                block_id = block.get("id")
                if block_id:
                    self.client.delete_block(block_id)
            ai_body = sections.get("ai_body")
            if ai_body and ai_body.get("id"):
                self.client.update_block(ai_body["id"], ai_markdown)
            else:
                ai_heading = sections.get("ai_heading")
                blocks_to_delete = []
                if ai_heading and ai_heading.get("id"):
                    blocks_to_delete.append(ai_heading["id"])
                for footer in footer_blocks:
                    footer_id = footer.get("id")
                    if footer_id:
                        blocks_to_delete.append(footer_id)
                for block_id in reversed(blocks_to_delete):
                    self.client.delete_block(block_id)
                self.client.append_block(doc_id, self._build_ai_section(ai_analysis, include_rule=True) + FOOTER_TEXT)

    def capture(
        self,
        content: str,
        manual_tags: Optional[list[str]] = None,
        source: str = "OpenClaw",
        ai_analysis: Optional[str] = None,
        existing_doc_id: Optional[str] = None,
        final_tags: Optional[list[str]] = None,
        related_notes: Optional[list[dict]] = None,
        note_payload: Optional[dict] = None,
    ) -> dict:
        self.ensure_initialized()
        assert self.notebook is not None
        now = datetime.now()
        normalized_ai_analysis = _normalize_ai_analysis(ai_analysis)
        doc_path = self.generate_doc_path(content)
        fallback_note_payload = self.build_note_payload(
            content=content,
            tags=[now.strftime("%Y-%m")],
            timestamp=now.strftime("%Y-%m-%d %H:%M"),
            source=source,
        )

        if note_payload is not None and not existing_doc_id:
            raise CaptureRequestError(
                "missing_doc_id_for_followup",
                "Follow-up note updates must include doc_id; do not call cap with note_payload alone.",
            )

        if not existing_doc_id and _has_enrichment_payload(
            final_tags=final_tags,
            related_notes=related_notes,
            ai_analysis=normalized_ai_analysis,
            note_payload=note_payload,
        ):
            pending_doc = self._find_pending_doc_by_path(doc_path)
            if pending_doc:
                existing_doc_id = pending_doc["id"]
                if note_payload is None:
                    note_payload = fallback_note_payload

        if existing_doc_id:
            meta = self.validate_doc_id(existing_doc_id, require_workspace=True)
            tag_input = final_tags if final_tags is not None else manual_tags
            selected_final_tags = self.normalize_final_tags(tag_input) if tag_input is not None else None
            if selected_final_tags == []:
                selected_final_tags = None
            if selected_final_tags is not None and note_payload and isinstance(note_payload.get("tags"), list):
                month_tags = [
                    str(tag)
                    for tag in note_payload.get("tags", [])
                    if re.fullmatch(r"\d{4}-\d{2}", str(tag))
                ]
                selected_final_tags = sorted(set(selected_final_tags + month_tags))
            selected_related_notes = (
                self.normalize_related_notes(related_notes) if related_notes is not None else None
            )
            updated_fields: list[str] = []
            if selected_final_tags is not None:
                updated_fields.append("tags")
            if selected_related_notes is not None:
                updated_fields.append("related_notes")
            if normalized_ai_analysis is not None:
                updated_fields.append("ai_analysis")
            if not updated_fields:
                return {
                    "doc_id": meta["id"],
                    "action": "nothing",
                    "validation": {"ok": True, "doc_id": meta["id"], "hpath": meta.get("hpath")},
                }
            self._update_note_sections(
                meta["id"],
                final_tags=selected_final_tags,
                related_notes=selected_related_notes,
                ai_analysis=normalized_ai_analysis,
            )
            self.update_index()
            return {
                "doc_id": meta["id"],
                "action": "note_enriched",
                "validation": {"ok": True, "doc_id": meta["id"], "hpath": meta.get("hpath")},
                "updated_fields": updated_fields,
                "tags": selected_final_tags or [],
                "related_notes": selected_related_notes or [],
                "ai_analysis": normalized_ai_analysis,
            }

        related_note_candidates = self.retrieve_related_notes(content)
        tag_candidates = self.retrieve_tag_candidates(content, manual_tags=manual_tags)
        selected_related_notes = self.normalize_related_notes(related_notes)
        selected_final_tags = self.normalize_final_tags(final_tags)
        final_tags_provided = final_tags is not None or manual_tags is not None
        related_notes_provided = related_notes is not None
        ai_analysis_provided = normalized_ai_analysis is not None
        missing_outputs = _missing_cap_outputs(
            final_tags_provided=final_tags_provided,
            related_notes_provided=related_notes_provided,
            ai_analysis_provided=ai_analysis_provided,
        )
        all_tags = sorted(set((selected_final_tags or []) + (manual_tags or []) + [now.strftime("%Y-%m")]))
        base_payload = self.build_note_payload(
            content=content,
            tags=all_tags,
            timestamp=now.strftime("%Y-%m-%d %H:%M"),
            source=source,
        )
        markdown = self._build_note_markdown(
            title=base_payload["title"],
            timestamp=base_payload["timestamp"],
            source=base_payload["source"],
            content=base_payload["content"],
            tags_line=base_payload["tags_line"],
            related_notes=selected_related_notes,
            ai_analysis=normalized_ai_analysis,
        )
        doc_id = self.client.create_doc(self.notebook["id"], doc_path, markdown)
        self.update_index()
        result = {
            "doc_id": doc_id,
            "doc_path": doc_path,
            "action": "note_captured" if not missing_outputs else "note_created_pending_enrichment",
            "missing_outputs": missing_outputs,
            "tags": all_tags,
            "tag_candidates": tag_candidates,
            "note_payload": base_payload,
            "related_note_candidates": related_note_candidates,
            "related_notes": selected_related_notes,
            "ai_analysis": normalized_ai_analysis,
            "enrichment_context": {
                "content": content,
                "tags": all_tags,
                "tag_candidates": tag_candidates,
                "tag_selection_requirements": _tag_selection_requirements(),
                "note_payload": base_payload,
                "related_note_candidates": related_note_candidates,
                "related_notes": selected_related_notes,
                "section": AI_ANALYSIS_SECTION,
                "analysis_requirements": _analysis_requirements(content),
            },
        }
        if missing_outputs:
            followup = _agent_followup_instruction(
                content=content,
                doc_id=doc_id,
                doc_path=doc_path,
                note_payload=base_payload,
                missing_outputs=missing_outputs,
            )
            result["agent_followup"] = followup
            result["enrichment_context"]["agent_followup"] = followup
        return result

    def search(self, keyword: str, limit: int = 50, local: bool = False) -> list[dict]:
        self.ensure_initialized()
        scope = f"AND box = '{_escape_sql(self.notebook['id'])}'" if local and self.notebook else ""
        stmt = f"""
            SELECT id, content, created, hpath, box, type
            FROM blocks
            WHERE content LIKE '%{_escape_sql(keyword)}%'
            {scope}
            ORDER BY created DESC
            LIMIT {limit}
        """
        return self.client.sql_query(stmt)

    def list_notes(self, limit: int = 20) -> list[dict]:
        self.ensure_initialized()
        assert self.notebook is not None
        docs = self.client.list_docs_in_notebook(self.notebook["id"], limit=limit)
        return [doc for doc in docs if not self._is_index_doc(doc)]

    def list_tags(self) -> list[str]:
        self.ensure_initialized()
        tags = [
            tag
            for block in self.client.get_recent_blocks(limit=200)
            for tag in _extract_tags(block.get("content", ""))
        ]
        return _meaningful_tags(tags)

    def update_index(self) -> None:
        self.ensure_initialized()
        assert self.notebook is not None
        assert self.index_doc_id is not None
        docs = self.client.list_docs_in_notebook(self.notebook["id"], limit=None)
        docs = [doc for doc in docs if not self._is_index_doc(doc)]
        tags = [
            tag
            for block in self.client.get_recent_blocks(limit=500)
            for tag in _extract_tags(block.get("content", ""))
        ]
        self.client.delete_child_blocks(self.index_doc_id)
        self.client.append_block(
            self.index_doc_id,
            self._build_index_markdown(docs, _meaningful_tags(tags)[:50]),
        )

    def _is_index_doc(self, doc: dict) -> bool:
        hpath = doc.get("hpath", "")
        return hpath in {INDEX_DOC_PATH, INDEX_DOC_PATH.lstrip("/")}

    def _build_note_markdown(
        self,
        title: str,
        timestamp: str,
        source: str,
        content: str,
        tags_line: str,
        related_notes: list[dict],
        ai_analysis: Optional[str] = None,
    ) -> str:
        related_section = self._build_related_notes_section(related_notes)
        ai_section = self._build_ai_section(ai_analysis, include_rule=True)
        return f"""# 📝 {title}

**时间**: {timestamp}
**来源**: {source}

---

## 内容

{content}

---

## 🏷️ 标签

{tags_line}

---

## {RELATED_NOTES_SECTION}

{related_section}

{ai_section}{FOOTER_TEXT}
"""

    def _build_related_notes_section(self, related_notes: list[dict]) -> str:
        if not related_notes:
            return "- 暂无匹配的相关笔记"
        return "\n".join(
            f'- (({item["id"]} "{item["title"]}"))  \n  相关性: {item["reason"]}'
            for item in related_notes
        )

    def _build_ai_section(self, ai_analysis: Optional[str], include_rule: bool = False) -> str:
        body = self._build_ai_body(ai_analysis)
        prefix = "---\n\n" if include_rule else ""
        return f"""{prefix}## {AI_ANALYSIS_SECTION}

{body}

"""

    def _build_ai_body(self, ai_analysis: Optional[str]) -> str:
        clean = (ai_analysis or "").strip()
        return clean or AI_PLACEHOLDER_TEXT

    def _build_index_markdown(self, docs: list[dict], tags: list[str]) -> str:
        note_lines = [
            f'- [{doc.get("created", "")[:10]}] (({doc.get("id", "")} "{_title_from_hpath(doc.get("hpath", ""))}"))'
            for doc in docs
        ]
        tags_cloud = " ".join(f"#{tag}" for tag in tags) if tags else "<!-- 自动更新 -->"
        notes_block = "\n".join(note_lines) if note_lines else "<!-- 自动更新 -->"
        return f"""# 📚 OpenClaw Inbox

> 自动索引 - 工作台

---

## 📥 最近笔记

{notes_block}

---

## 🏷️ 标签云

{tags_cloud}

---

_最后更新：{datetime.now().strftime("%Y-%m-%d %H:%M")}_
"""


def format_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)

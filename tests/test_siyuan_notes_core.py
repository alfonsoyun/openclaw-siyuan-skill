from __future__ import annotations

import sys
from pathlib import Path
import unittest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from siyuan_notes_core import (
    AI_PLACEHOLDER_TEXT,
    AINotesManager,
    CaptureRequestError,
    _agent_followup_instruction,
    _analysis_requirements,
    _has_enrichment_payload,
    _missing_cap_outputs,
    _normalize_ai_analysis,
)


class NormalizeAiAnalysisTests(unittest.TestCase):
    def test_strips_heading_prefix(self) -> None:
        analysis = "## AI Analysis\n\nFirst point\nSecond point"
        self.assertEqual(_normalize_ai_analysis(analysis), "First point\nSecond point")

    def test_keeps_plain_body(self) -> None:
        analysis = "First point\nSecond point"
        self.assertEqual(_normalize_ai_analysis(analysis), analysis)


class MissingCapOutputsTests(unittest.TestCase):
    def test_reports_all_missing_outputs(self) -> None:
        self.assertEqual(
            _missing_cap_outputs(
                final_tags_provided=False,
                related_notes_provided=False,
                ai_analysis_provided=False,
            ),
            ["tags", "related_notes", "ai_analysis"],
        )

    def test_reports_no_missing_outputs(self) -> None:
        self.assertEqual(
            _missing_cap_outputs(
                final_tags_provided=True,
                related_notes_provided=True,
                ai_analysis_provided=True,
            ),
            [],
        )


class AnalysisRequirementsTests(unittest.TestCase):
    def test_short_content_uses_light_requirements(self) -> None:
        requirements = _analysis_requirements("short note")
        self.assertEqual(requirements["depth"], "light")
        self.assertEqual(requirements["minimum_points"], 3)

    def test_long_content_uses_detailed_requirements(self) -> None:
        content = "This is a much longer note body. " * 20
        requirements = _analysis_requirements(content)
        self.assertEqual(requirements["depth"], "detailed")
        self.assertEqual(requirements["format"], "sections")


class EnrichmentPayloadTests(unittest.TestCase):
    def test_detects_followup_payload(self) -> None:
        self.assertTrue(
            _has_enrichment_payload(
                final_tags=None,
                related_notes=None,
                ai_analysis="Need follow-up",
                note_payload=None,
            )
        )

    def test_ignores_empty_payload(self) -> None:
        self.assertFalse(
            _has_enrichment_payload(
                final_tags=None,
                related_notes=None,
                ai_analysis=None,
                note_payload=None,
            )
        )


class AgentFollowupInstructionTests(unittest.TestCase):
    def test_prefers_helper_service_for_structured_followup(self) -> None:
        followup = _agent_followup_instruction(
            content="same note",
            doc_id="doc-1",
            doc_path="/2026-03-13-same-note",
            note_payload={"title": "same note", "tags": ["2026-03"]},
            missing_outputs=["tags", "related_notes", "ai_analysis"],
        )

        self.assertEqual(followup["preferred_transport"], "helper_service")
        self.assertTrue(followup["workdir"].endswith("openclaw-siyuan"))
        self.assertEqual(followup["helper_service_template"]["method"], "POST")
        self.assertEqual(followup["helper_service_template"]["url"], "http://127.0.0.1:6868/cap")
        self.assertEqual(
            followup["helper_service_template"]["start_command"],
            "python scripts/siyuan_server.py --host 127.0.0.1 --port 6868",
        )
        self.assertIn("python -X utf8", followup["helper_service_template"]["encoding_hint"])
        self.assertEqual(
            followup["helper_service_template"]["json_fields"],
            ["content", "doc_id", "final_tags", "note_payload", "related_notes", "ai_analysis"],
        )
        self.assertEqual(
            followup["helper_service_template"]["payload"]["doc_id"],
            "doc-1",
        )
        self.assertIn("--doc-id <doc_id>", followup["fallback_cli_template"]["command"])
        self.assertIn("python -X utf8", followup["fallback_cli_template"]["encoding_hint"])


class FakeClient:
    def __init__(self) -> None:
        self.created_docs = 0
        self.updated_blocks: list[tuple[str, str]] = []
        self.doc_by_hpath: dict[str, dict] = {}
        self.doc_children: dict[str, list[dict]] = {}

    def get_doc_by_hpath(self, _notebook_id: str, hpath: str) -> dict | None:
        return self.doc_by_hpath.get(hpath)

    def get_child_blocks(self, parent_id: str) -> list[dict]:
        return self.doc_children.get(parent_id, [])

    def create_doc(self, _notebook_id: str, _path: str, _markdown: str) -> str:
        self.created_docs += 1
        return f"new-doc-{self.created_docs}"

    def update_block(self, block_id: str, markdown: str) -> None:
        self.updated_blocks.append((block_id, markdown))

    def append_block(self, _parent_id: str, _markdown: str) -> dict:
        return {}

    def delete_block(self, _block_id: str) -> None:
        return None

    def list_docs_in_notebook(self, _notebook_id: str, limit: int | None = None) -> list[dict]:
        return []

    def sql_query(self, _stmt: str) -> list[dict]:
        return []


class TestManager(AINotesManager):
    def __init__(self, client: FakeClient) -> None:
        super().__init__(client=client)
        self.notebook = {"id": "nb-1", "name": "Openclaw Inbox"}
        self.index_doc_id = "index-1"
        self.updated_sections: list[dict] = []

    def ensure_initialized(self) -> None:
        return None

    def validate_doc_id(self, doc_id: str, require_workspace: bool = True) -> dict:
        return {"id": doc_id, "hpath": "/2026-03-13-same-note", "box": "nb-1", "type": "d"}

    def update_index(self) -> None:
        return None

    def _update_note_sections(
        self,
        doc_id: str,
        final_tags: list[str] | None = None,
        related_notes: list[dict] | None = None,
        ai_analysis: str | None = None,
    ) -> None:
        self.updated_sections.append(
            {
                "doc_id": doc_id,
                "final_tags": final_tags,
                "related_notes": related_notes,
                "ai_analysis": ai_analysis,
            }
        )


class CaptureFollowupSafetyTests(unittest.TestCase):
    def test_rejects_note_payload_without_doc_id(self) -> None:
        manager = TestManager(FakeClient())
        with self.assertRaises(CaptureRequestError):
            manager.capture(
                content="same note",
                ai_analysis="analysis",
                note_payload={"title": "same note", "tags": ["2026-03"]},
            )

    def test_resumes_pending_doc_when_enrichment_is_retried_without_doc_id(self) -> None:
        client = FakeClient()
        manager = TestManager(client)
        doc_path = manager.generate_doc_path("same note")
        client.doc_by_hpath[doc_path] = {
            "id": "doc-1",
            "hpath": doc_path,
            "type": "d",
        }
        client.doc_children["doc-1"] = [
            {"id": "h-ai", "type": "h", "content": "## 💡 建议"},
            {"id": "b-ai", "type": "p", "content": AI_PLACEHOLDER_TEXT},
        ]

        result = manager.capture(
            content="same note",
            final_tags=["plan"],
            ai_analysis="First point\nSecond point",
        )

        self.assertEqual(result["doc_id"], "doc-1")
        self.assertEqual(result["action"], "note_enriched")
        self.assertEqual(client.created_docs, 0)
        self.assertEqual(manager.updated_sections[0]["doc_id"], "doc-1")


if __name__ == "__main__":
    unittest.main()

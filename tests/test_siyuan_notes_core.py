from __future__ import annotations

import sys
from pathlib import Path
import unittest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from siyuan_notes_core import _analysis_requirements, _missing_cap_outputs, _normalize_ai_analysis


class NormalizeAiAnalysisTests(unittest.TestCase):
    def test_strips_heading_prefix(self) -> None:
        analysis = "## AI 分析\n\n第一点\n第二点"
        self.assertEqual(_normalize_ai_analysis(analysis), "第一点\n第二点")

    def test_keeps_plain_body(self) -> None:
        analysis = "第一点\n第二点"
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
        requirements = _analysis_requirements("短笔记")
        self.assertEqual(requirements["depth"], "light")
        self.assertEqual(requirements["minimum_points"], 3)

    def test_long_content_uses_detailed_requirements(self) -> None:
        content = "这是一个比较长的笔记内容。" * 20
        requirements = _analysis_requirements(content)
        self.assertEqual(requirements["depth"], "detailed")
        self.assertEqual(requirements["format"], "sections")


if __name__ == "__main__":
    unittest.main()

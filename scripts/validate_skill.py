#!/usr/bin/env python3
"""Minimal standalone validator for SKILL.md frontmatter."""

from __future__ import annotations

import re
import sys
from pathlib import Path

NAME_PATTERN = re.compile(r"^[a-z0-9-]{1,64}$")


def fail(message: str) -> int:
    print(f"Invalid skill: {message}")
    return 1


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    closing = text.find("\n---\n", 4)
    if closing == -1:
        raise ValueError("SKILL.md frontmatter is not closed with ---")
    raw = text[4:closing]
    parsed: dict[str, str] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if ":" not in stripped:
            raise ValueError(f"Invalid frontmatter line: {line}")
        key, value = stripped.split(":", 1)
        parsed[key.strip()] = value.strip().strip('"').strip("'")
    return parsed


def main() -> int:
    skill_path = Path(__file__).resolve().parent.parent / "SKILL.md"
    if not skill_path.exists():
        return fail("SKILL.md not found")

    text = skill_path.read_text(encoding="utf-8")
    try:
        frontmatter = parse_frontmatter(text)
    except ValueError as exc:
        return fail(str(exc))

    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")

    if not name:
        return fail("missing frontmatter field: name")
    if not NAME_PATTERN.fullmatch(name):
        return fail("name must use lowercase letters, digits, and hyphens only")
    if not description:
        return fail("missing frontmatter field: description")

    print("Skill metadata is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

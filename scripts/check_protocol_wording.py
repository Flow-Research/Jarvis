#!/usr/bin/env python3
"""Validate wording against the Jarvis protocol boundary."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
FILES = [
    *ROOT.glob("*.md"),
    *ROOT.joinpath("docs").rglob("*.md"),
    *ROOT.joinpath("demo").rglob("*.html"),
]
NORMATIVE_TERMS = {"MUST", "MUST NOT", "SHOULD", "SHOULD NOT", "MAY"}
NORMATIVE_TERM_PATTERN = re.compile(
    r"`(?:MUST|MUST NOT|SHOULD|SHOULD NOT|MAY)`"
)

PATTERNS = [
    r"personal\s+agent\s+harness",
    r"host implementation active work",
    r"schema-first contract",
    r"demo-first plan",
    r"host owns Jarvis",
    r"Jarvis owns auth",
    r"Jarvis owns runtime",
    r"Jarvis owns database",
    r"Jarvis owns cloud",
    r"Jarvis owns UI",
    r"\bmaybe\b",
    r"\bprobably\b",
    r"\bcould\b",
    r"\bshould\b",
    r"\bcan\b",
    r"\bwould\b",
    r"\bmight\b",
    r"\brecommend\b",
    r"\brecommended\b",
    r"\bconsider\b",
    r"\bsuggest\b",
    r"\badvice\b",
    r"\bguidance\b",
    r"\bcandidate\b",
    r"implementation concerns",
    r"those are implementation concerns",
    r"if accepted",
    r"if this is approved",
]
LOWERCASE_PATTERNS = [
    r"\bmay\b",
]


def main() -> int:
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in PATTERNS]
    lowercase_compiled = [re.compile(pattern) for pattern in LOWERCASE_PATTERNS]
    failures: list[tuple[Path, int, str]] = []

    for path in sorted(FILES):
        text = path.read_text(encoding="utf-8")
        in_code_block = False
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            line_to_check = NORMATIVE_TERM_PATTERN.sub("", line)
            for pattern in [*compiled, *lowercase_compiled]:
                if pattern.search(line_to_check):
                    failures.append((path.relative_to(ROOT), line_number, line))
                    break

    if failures:
        for path, line_number, line in failures:
            print(f"{path}:{line_number}: rejected wording: {line}")
        return 1

    print("protocol wording ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())

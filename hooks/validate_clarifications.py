#!/usr/bin/env python3
"""Validates clarifications.md — required sections present."""
import os
import re
import sys


REQUIRED_SECTIONS = [
    "## Questions",
    "## User Answers",
    "## Open Questions",
    "## Planning Decisions",
]


def validate(file_path):
    errors = []

    if not os.path.exists(file_path):
        print(f"FAIL: File does not exist: {file_path}", file=sys.stderr)
        return 1

    with open(file_path, "r") as f:
        content = f.read()

    if not content.strip():
        print("FAIL: File is empty", file=sys.stderr)
        return 1

    # Check required sections
    for section in REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"Missing required section: {section}")

    # Check that Questions section has content
    questions_match = re.search(
        r"## Questions\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL
    )
    if questions_match:
        questions_content = questions_match.group(1).strip()
        if not questions_content:
            errors.append("## Questions section is empty")
        # Check for at least some question groups
        group_count = len(re.findall(r"### Group \d", questions_content))
        if group_count < 1:
            # Also accept numbered questions without group headers
            question_count = len(re.findall(r"^\d+\.", questions_content, re.MULTILINE))
            if question_count < 3:
                errors.append(
                    "## Questions section has fewer than 3 questions "
                    "(expected coverage of multiple question groups)"
                )

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1

    print("PASS: clarifications.md is valid")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_clarifications.py <path>", file=sys.stderr)
        sys.exit(1)
    sys.exit(validate(sys.argv[1]))

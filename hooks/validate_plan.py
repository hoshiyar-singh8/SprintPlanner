#!/usr/bin/env python3
"""Validates high_level_plan.md — required sections, SP estimates exist."""
import os
import re
import sys


REQUIRED_SECTIONS = [
    (r"##\s+(Overview|Feature Overview)", "Overview"),
    (r"##\s+(Architecture|Architecture Decisions)", "Architecture"),
    (r"##\s+(Phases|Implementation Phases|Implementation Plan)", "Phases"),
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
    for pattern, name in REQUIRED_SECTIONS:
        if not re.search(pattern, content, re.IGNORECASE):
            errors.append(f"Missing required section: {name}")

    # Check SP estimates exist
    sp_patterns = [
        r"\d+\s*SP",
        r"\d+\s*story\s*point",
        r"\d+\s*pts?",
        r"SP\s*:\s*\d+",
        r"Story Points?\s*:\s*\d+",
    ]
    has_sp = any(re.search(p, content, re.IGNORECASE) for p in sp_patterns)
    if not has_sp:
        errors.append("No story point estimates found in the plan")

    # Check for Risks section (recommended)
    if not re.search(r"##\s*(Risks|Risks?\s*(&|and)\s*Mitigations?)", content, re.IGNORECASE):
        print("WARN: No Risks section found — recommended but not required")

    # Check for Scope section (recommended)
    if not re.search(r"##\s*(Scope|In Scope|Scope\s*(&|and)\s*Boundaries)", content, re.IGNORECASE):
        print("WARN: No Scope section found — recommended but not required")

    # Check for Task Granularity Guidance (recommended)
    if not re.search(r"##\s*Task\s*Granularity", content, re.IGNORECASE):
        print("WARN: No Task Granularity Guidance section — recommended to prevent over/under-splitting")

    # Check for reference file paths in phase details (anti-hallucination)
    phase_section = re.search(
        r"##\s*(?:Phase Details|Implementation Phases)\s*\n(.*?)(?=\n## |\Z)",
        content, re.DOTALL | re.IGNORECASE
    )
    if phase_section:
        phase_text = phase_section.group(1)
        # Look for file path references (contain / and file extension)
        file_refs = re.findall(r"[A-Za-z][A-Za-z0-9_/]+\.\w{1,5}", phase_text)
        if not file_refs:
            print(
                "WARN: No file path references found in phase details — "
                "planner should cite specific files from context_pack for each phase"
            )

    # Basic content length check
    if len(content.strip()) < 500:
        errors.append("Plan appears too short (< 500 chars) — likely incomplete")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1

    print("PASS: high_level_plan.md is valid")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_plan.py <path>", file=sys.stderr)
        sys.exit(1)
    sys.exit(validate(sys.argv[1]))

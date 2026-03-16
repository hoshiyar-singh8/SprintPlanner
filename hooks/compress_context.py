#!/usr/bin/env python3
"""Trims context_pack.yaml if oversized (>10K chars). Keeps essential paths."""
import os
import sys
import yaml


MAX_CHARS = 10000


def compress(file_path):
    if not os.path.exists(file_path):
        print(f"FAIL: File does not exist: {file_path}", file=sys.stderr)
        return 1

    with open(file_path, "r") as f:
        content = f.read()

    if len(content) <= MAX_CHARS:
        print(f"PASS: context_pack.yaml is {len(content)} chars (under {MAX_CHARS} limit)")
        return 0

    print(f"WARN: context_pack.yaml is {len(content)} chars — compressing to under {MAX_CHARS}")

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"FAIL: Invalid YAML, cannot compress: {e}", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        print("FAIL: Root element must be a mapping", file=sys.stderr)
        return 1

    # Compression strategy:
    # 1. Trim descriptions in key_files to max 80 chars
    # 2. Trim file lists in relevant_modules to max 5 files
    # 3. Remove optional sections if still too large

    # Step 1: Trim key_files descriptions
    key_files = data.get("key_files", [])
    if isinstance(key_files, list):
        for entry in key_files:
            if isinstance(entry, dict) and "role" in entry:
                if len(str(entry["role"])) > 80:
                    entry["role"] = str(entry["role"])[:77] + "..."

    # Step 2: Trim module file lists
    modules = data.get("relevant_modules", [])
    if isinstance(modules, list):
        for mod in modules:
            if isinstance(mod, dict) and "files" in mod:
                files = mod["files"]
                if isinstance(files, list) and len(files) > 5:
                    mod["files"] = files[:5]
                    mod["_note"] = f"Trimmed from {len(files)} files"

    # Step 3: Trim figma_context details if present
    figma = data.get("figma_context", {})
    if isinstance(figma, dict) and "screens" in figma:
        for screen in figma.get("screens", []):
            if isinstance(screen, dict):
                # Keep only essential fields
                for key in list(screen.keys()):
                    if key not in ("name", "changes_summary", "new_components", "modified_components"):
                        del screen[key]

    # Write compressed version
    compressed = yaml.dump(data, default_flow_style=False, allow_unicode=True, width=120)

    if len(compressed) > MAX_CHARS:
        # Step 4: Remove optional sections entirely
        for optional_key in ("figma_context", "conventions"):
            if optional_key in data:
                del data[optional_key]
        compressed = yaml.dump(data, default_flow_style=False, allow_unicode=True, width=120)

    with open(file_path, "w") as f:
        f.write(compressed)

    print(f"PASS: Compressed to {len(compressed)} chars")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: compress_context.py <path>", file=sys.stderr)
        sys.exit(1)
    sys.exit(compress(sys.argv[1]))

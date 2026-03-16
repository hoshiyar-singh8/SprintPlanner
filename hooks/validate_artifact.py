#!/usr/bin/env python3
"""PostToolUse dispatcher — routes to correct validator by filename.

Reads hook input from stdin (JSON with tool_input.file_path).
Only validates files in .ai/features/ directories.
Returns {"decision": "block", "reason": "..."} on failure.
"""
import json
import os
import subprocess
import sys

HOOKS_DIR = os.path.dirname(os.path.abspath(__file__))

VALIDATORS = {
    "feature_input.yaml": "validate_input.py",
    "clarifications.md": "validate_clarifications.py",
    "context_pack.yaml": "validate_context.py",
    "high_level_plan.md": "validate_plan.py",
    "task_specs.yaml": "validate_task_specs.py",
}


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        # If we can't parse input, allow the write (don't block on hook errors)
        print(json.dumps({"decision": "allow", "reason": "Could not parse hook input"}))
        return

    # Extract file path from tool input
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only validate files in .ai/features/ directories
    if "/.ai/features/" not in file_path:
        print(json.dumps({"decision": "allow", "reason": "Not a pipeline artifact"}))
        return

    # Get the filename
    filename = os.path.basename(file_path)

    # Find the appropriate validator
    validator_script = VALIDATORS.get(filename)
    if not validator_script:
        print(json.dumps({"decision": "allow", "reason": f"No validator for {filename}"}))
        return

    validator_path = os.path.join(HOOKS_DIR, validator_script)
    if not os.path.exists(validator_path):
        print(json.dumps({
            "decision": "allow",
            "reason": f"Validator {validator_script} not found, allowing write"
        }))
        return

    # Run the validator
    try:
        result = subprocess.run(
            ["python3", validator_path, file_path],
            capture_output=True,
            text=True,
            timeout=25
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Validation failed"
            print(json.dumps({
                "decision": "block",
                "reason": f"Validation failed for {filename}: {error_msg}"
            }))
        else:
            print(json.dumps({"decision": "allow", "reason": "Validation passed"}))
    except subprocess.TimeoutExpired:
        print(json.dumps({
            "decision": "allow",
            "reason": f"Validator {validator_script} timed out, allowing write"
        }))
    except Exception as e:
        print(json.dumps({
            "decision": "allow",
            "reason": f"Validator error: {str(e)}, allowing write"
        }))


if __name__ == "__main__":
    main()

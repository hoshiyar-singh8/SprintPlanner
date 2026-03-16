#!/usr/bin/env python3
"""Validates feature_input.yaml — required fields, repo source, platform, file paths."""
import os
import sys
import yaml


REQUIRED_FIELDS = ["feature_name", "detected_platform", "repo_source", "rfc_path"]
VALID_PLATFORMS = {"ios", "android", "web", "backend", "flutter", "both", "other"}
VALID_REPO_SOURCES = {"local", "github", "both"}
VALID_SKILLS_STATUS = {"ready", "generated", "user_supplied"}


def validate(file_path):
    errors = []

    if not os.path.exists(file_path):
        print(f"FAIL: File does not exist: {file_path}", file=sys.stderr)
        return 1

    with open(file_path, "r") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"FAIL: Invalid YAML: {e}", file=sys.stderr)
            return 1

    if not isinstance(data, dict):
        print("FAIL: Root element must be a mapping", file=sys.stderr)
        return 1

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in data or not data[field]:
            errors.append(f"Missing or empty required field: {field}")

    # Platform validation
    platform = data.get("detected_platform", "")
    if platform and str(platform).lower() not in VALID_PLATFORMS:
        errors.append(
            f"Invalid detected_platform '{platform}' — "
            f"must be one of: {', '.join(sorted(VALID_PLATFORMS))}"
        )

    # Repo source validation
    repo_source = data.get("repo_source", "")
    if repo_source and str(repo_source).lower() not in VALID_REPO_SOURCES:
        errors.append(
            f"Invalid repo_source '{repo_source}' — "
            f"must be one of: {', '.join(VALID_REPO_SOURCES)}"
        )

    # Repo path/URL validation based on source
    repo_source_lower = str(repo_source).lower() if repo_source else ""
    if repo_source_lower in ("local", "both"):
        repo_path = data.get("repo_path", "")
        if not repo_path:
            errors.append("repo_path is required when repo_source is 'local' or 'both'")
        elif not os.path.isdir(repo_path):
            errors.append(f"Repository path is not a directory: {repo_path}")

    if repo_source_lower in ("github", "both"):
        repo_url = data.get("repo_url", "")
        if not repo_url:
            errors.append("repo_url is required when repo_source is 'github' or 'both'")

    # RFC path validation (only check existence for local files, not URLs)
    rfc_path = data.get("rfc_path", "")
    if rfc_path and not rfc_path.startswith("http"):
        if not os.path.exists(rfc_path):
            errors.append(f"RFC file does not exist: {rfc_path}")

    # Skills status validation
    skills_status = data.get("skills_status")
    if skills_status is not None:
        if str(skills_status).lower() not in VALID_SKILLS_STATUS:
            errors.append(
                f"Invalid skills_status '{skills_status}' — "
                f"must be one of: {', '.join(VALID_SKILLS_STATUS)}"
            )

    # SP max validation
    sp_max = data.get("sp_max")
    if sp_max is not None:
        if not isinstance(sp_max, int) or sp_max < 1 or sp_max > 3:
            errors.append(f"sp_max must be integer 1-3, got: {sp_max}")

    # UI scope validation
    ui_scope = data.get("ui_scope")
    if ui_scope is not None:
        if not isinstance(ui_scope, int) or ui_scope < 1 or ui_scope > 4:
            errors.append(f"ui_scope must be integer 1-4, got: {ui_scope}")

    # Figma URLs validation
    figma_urls = data.get("figma_urls", [])
    if figma_urls:
        if not isinstance(figma_urls, list):
            errors.append("figma_urls must be a list")
        else:
            for i, entry in enumerate(figma_urls):
                if isinstance(entry, dict):
                    if "url" not in entry:
                        errors.append(f"figma_urls[{i}] missing 'url' field")
                elif not isinstance(entry, str):
                    errors.append(
                        f"figma_urls[{i}] must be a dict with 'url' or a string"
                    )

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1

    print("PASS: feature_input.yaml is valid")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_input.py <path-to-feature_input.yaml>", file=sys.stderr)
        sys.exit(1)
    sys.exit(validate(sys.argv[1]))

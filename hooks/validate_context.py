#!/usr/bin/env python3
"""Validates context_pack.yaml — has architecture/relevant_modules/key_files."""
import os
import sys
import yaml


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

    # Check architecture section
    arch = data.get("architecture")
    if not arch or not isinstance(arch, dict):
        errors.append("Missing or invalid 'architecture' section")
    else:
        arch_required = ["pattern", "di_framework", "networking", "ui_framework"]
        for field in arch_required:
            if field not in arch or not arch[field]:
                errors.append(f"architecture.{field} is missing or empty")

        # Validate pattern
        valid_patterns = {
            "viper", "mvvm", "mvi", "clean", "mvp", "mvc",
            "bloc", "hexagonal", "layered", "microservice",
            "component-based", "feature-sliced", "atomic",
            "redux", "flux", "clean_architecture",
        }
        pattern = str(arch.get("pattern", "")).lower()
        if pattern and pattern not in valid_patterns:
            errors.append(
                f"architecture.pattern '{arch.get('pattern')}' not recognized "
                f"(expected one of: {', '.join(valid_patterns)})"
            )

    # Check relevant_modules section
    modules = data.get("relevant_modules")
    if not modules or not isinstance(modules, list) or len(modules) < 1:
        errors.append("Missing or empty 'relevant_modules' section (need ≥1 entry)")
    else:
        for i, mod in enumerate(modules):
            if isinstance(mod, dict):
                if "name" not in mod:
                    errors.append(f"relevant_modules[{i}] missing 'name'")
                if "path" not in mod:
                    errors.append(f"relevant_modules[{i}] missing 'path'")

    # Check key_files section
    key_files = data.get("key_files")
    if not key_files or not isinstance(key_files, list) or len(key_files) < 1:
        errors.append("Missing or empty 'key_files' section (need ≥1 entry)")
    else:
        for i, kf in enumerate(key_files):
            if isinstance(kf, dict):
                if "path" not in kf:
                    errors.append(f"key_files[{i}] missing 'path'")
                path_val = kf.get("path", "")
                if path_val and "." not in os.path.basename(str(path_val)):
                    errors.append(
                        f"key_files[{i}].path '{path_val}' doesn't look like a file (no extension)"
                    )

    # Check key_files paths against repo (when repo_path is available)
    if key_files and isinstance(key_files, list):
        # Try to find feature_input.yaml in same directory for repo_path
        feature_dir = os.path.dirname(file_path)
        fi_path = os.path.join(feature_dir, "feature_input.yaml")
        repo_path = None
        if os.path.exists(fi_path):
            try:
                with open(fi_path, "r") as fi:
                    fi_data = yaml.safe_load(fi) or {}
                rp = fi_data.get("repo_path")
                if rp and os.path.isdir(str(rp)):
                    repo_path = str(rp)
            except (yaml.YAMLError, OSError):
                pass

        if repo_path:
            missing_files = []
            for kf in key_files:
                if not isinstance(kf, dict):
                    continue
                kf_path = kf.get("path", "")
                if not kf_path:
                    continue
                full_path = os.path.join(repo_path, kf_path)
                if not os.path.exists(full_path):
                    missing_files.append(kf_path)
            if missing_files:
                for mf in missing_files:
                    print(f"WARN: key_file not found on disk: {mf}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1

    print("PASS: context_pack.yaml is valid")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_context.py <path>", file=sys.stderr)
        sys.exit(1)
    sys.exit(validate(sys.argv[1]))

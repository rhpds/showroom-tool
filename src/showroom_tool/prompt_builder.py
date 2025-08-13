#!/usr/bin/env python

"""
Prompt builder that sources defaults from built-in constants and allows project/user overrides.

Requirement 11.11: Separate prompts/settings data from builder logic and support auto-discovery of
project-level and user-level configuration files.
"""

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

# Reuse existing builder functions and defaults from prompts module
from showroom_tool.prompts import (
    SHOWROOM_DESCRIPTION_BASE_SYSTEM_PROMPT,
    SHOWROOM_REVIEW_BASE_SYSTEM_PROMPT,
    SHOWROOM_SUMMARY_BASE_SYSTEM_PROMPT,
    build_showroom_description_structured_prompt,
    build_showroom_review_structured_prompt,
    build_showroom_summary_structured_prompt,
)


def _load_py_constants(path: Path) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location(f"_showroom_cfg_{path.stem}", str(path))
    if not spec or not spec.loader:  # type: ignore[truthy-function]
        return {}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return {k: getattr(module, k) for k in dir(module) if k.isupper()}


def _load_json_constants(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {str(k): v for k, v in data.items() if str(k).isupper()}
    except Exception:
        return {}


def _discover_overrides() -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    project_cfg_dir = Path.cwd() / "config"
    user_cfg_dir = Path(os.path.expanduser("~")) / ".config" / "showroom-tool"

    for folder in (project_cfg_dir, user_cfg_dir):
        if not folder.exists():
            continue
        for name in ("prompts.py", "prompts.json", "settings.py", "settings.json"):
            path = folder / name
            if not path.exists():
                continue
            loaded: dict[str, Any] = {}
            if path.suffix == ".py":
                loaded = _load_py_constants(path)
            elif path.suffix == ".json":
                loaded = _load_json_constants(path)
            overrides.update(loaded)
    return overrides


def get_prompts_and_settings() -> dict[str, Any]:
    """Return merged constants with precedence: project > user > built-in defaults."""
    merged: dict[str, Any] = {
        "SHOWROOM_SUMMARY_BASE_SYSTEM_PROMPT": SHOWROOM_SUMMARY_BASE_SYSTEM_PROMPT,
        "SHOWROOM_REVIEW_BASE_SYSTEM_PROMPT": SHOWROOM_REVIEW_BASE_SYSTEM_PROMPT,
        "SHOWROOM_DESCRIPTION_BASE_SYSTEM_PROMPT": SHOWROOM_DESCRIPTION_BASE_SYSTEM_PROMPT,
    }
    merged.update(_discover_overrides())
    return merged


__all__ = [
    "build_showroom_summary_structured_prompt",
    "build_showroom_review_structured_prompt",
    "build_showroom_description_structured_prompt",
    "get_prompts_and_settings",
]



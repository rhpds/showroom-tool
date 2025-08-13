#!/usr/bin/env python

"""
Prompt building utilities for Showroom AI summarization.

This module contains prompts and utilities for generating AI-powered
summaries, reviews, and descriptions of Showroom lab content using
structured prompts.

Requirement 11.9: Supports loading prompt and temperature overrides from
an external file via `--prompts-file`.
"""

import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

# Built-in default prompts (Requirement 11.11)
try:
    from showroom_tool.config.defaults import (
        SHOWROOM_DESCRIPTION_BASE_SYSTEM_PROMPT,
        SHOWROOM_REVIEW_BASE_SYSTEM_PROMPT,
        SHOWROOM_SUMMARY_BASE_SYSTEM_PROMPT,
    )
except Exception:
    # Fallback empty strings if defaults module not available
    SHOWROOM_SUMMARY_BASE_SYSTEM_PROMPT = ""
    SHOWROOM_REVIEW_BASE_SYSTEM_PROMPT = ""
    SHOWROOM_DESCRIPTION_BASE_SYSTEM_PROMPT = ""


def extract_field_descriptions(model_class: type[BaseModel]) -> str:
    """
    Extract field descriptions from a Pydantic model and format them with behavioral directives.
    Uses strong behavioral boundaries to prevent instruction bleeding between fields.

    Args:
        model_class: The Pydantic model class to extract descriptions from

    Returns:
        Formatted string with behavioral field instructions for system prompt
    """
    field_sections = []

    # Get model fields using model_fields (Pydantic v2)
    for field_name, field_info in model_class.model_fields.items():
        # Skip metadata fields that are less important for instructions
        if field_name in ["git_url", "git_ref"]:
            continue

        # Get field description from Field definition
        description = ""
        if hasattr(field_info, "description") and field_info.description:
            description = field_info.description
        elif hasattr(field_info, "json_schema_extra") and field_info.json_schema_extra:
            # Check if description is in json_schema_extra
            if (
                isinstance(field_info.json_schema_extra, dict)
                and "description" in field_info.json_schema_extra
            ):
                description = field_info.json_schema_extra["description"]

        if description:
            # Create strong behavioral boundaries to prevent instruction bleeding
            field_header = f"{field_name.upper()} FIELD BEHAVIORAL INSTRUCTIONS:"
            behavioral_boundary = f"IGNORE everything except this field's specific focus. Your analytical approach for this field: {description}"
            field_sections.append(f"{field_header}\n{behavioral_boundary}\n")

    if field_sections:
        return f"""
FIELD-SPECIFIC BEHAVIORAL INSTRUCTIONS:
Each field below requires a COMPLETELY DIFFERENT analytical approach. Do not mix behaviors between fields.

{chr(10).join(field_sections)}

CRITICAL: Each field has its own FOCUS, IGNORE, and ACT LIKE instructions. Apply each field's behavioral approach independently. Do not let one field's focus contaminate another field's analysis."""
    else:
        return ""


def _get_override(name: str, default_value: Any) -> Any:
    """Get override value if present, otherwise return default."""
    return PROMPTS_FILE_OVERRIDES.get(name, default_value)


def get_summary_base_system_prompt() -> str:
    return _get_override("SHOWROOM_SUMMARY_BASE_SYSTEM_PROMPT", SHOWROOM_SUMMARY_BASE_SYSTEM_PROMPT)


def get_summary_structured_prompt() -> str:
    # Backward-compatible function name; now returns BASE_SYSTEM prompt
    return get_summary_base_system_prompt()


def get_review_base_system_prompt() -> str:
    return _get_override("SHOWROOM_REVIEW_BASE_SYSTEM_PROMPT", SHOWROOM_REVIEW_BASE_SYSTEM_PROMPT)


def get_review_structured_prompt() -> str:
    return get_review_base_system_prompt()


def get_description_base_system_prompt() -> str:
    return _get_override("SHOWROOM_DESCRIPTION_BASE_SYSTEM_PROMPT", SHOWROOM_DESCRIPTION_BASE_SYSTEM_PROMPT)


def get_description_structured_prompt() -> str:
    return get_description_base_system_prompt()


def build_showroom_summary_prompt(
    showroom_model: type[BaseModel],
    include_field_instructions: bool = True
) -> str:
    """Build an enhanced system prompt for Showroom summarization using base system prompt."""
    base_prompt = get_summary_base_system_prompt()
    if include_field_instructions:
        field_instructions = extract_field_descriptions(showroom_model)
        if field_instructions:
            return f"{base_prompt}\n\n{field_instructions}"
    return base_prompt


def build_showroom_summary_structured_prompt(
    summary_model: type[BaseModel],
    include_field_instructions: bool = True
) -> str:
    """
    Build a structured prompt specifically for ShowroomSummary generation.

    Args:
        summary_model: The ShowroomSummary Pydantic model class
        include_field_instructions: Whether to include field-specific instructions

    Returns:
        Complete system prompt for structured summary generation
    """
    base_prompt = get_summary_base_system_prompt()

    if include_field_instructions:
        field_instructions = extract_field_descriptions(summary_model)
        if field_instructions:
            enhanced_prompt = f"{base_prompt}\n\n{field_instructions}"
        else:
            enhanced_prompt = base_prompt
    else:
        enhanced_prompt = base_prompt

    return enhanced_prompt


def format_showroom_content_for_prompt(showroom_data) -> str:
    """
    Format Showroom data into a structured format suitable for LLM processing.

    Args:
        showroom_data: Showroom BaseModel instance

    Returns:
        Formatted string containing the lab content for analysis
    """
    content_sections = []

    # Add lab metadata
    content_sections.append(f"LAB TITLE: {showroom_data.lab_name}")
    content_sections.append(f"REPOSITORY: {showroom_data.git_url}")
    content_sections.append(f"BRANCH/REF: {showroom_data.git_ref}")
    content_sections.append(f"TOTAL MODULES: {len(showroom_data.modules)}")
    content_sections.append("")

    # Add each module's content
    for i, module in enumerate(showroom_data.modules, 1):
        content_sections.append(f"MODULE {i}: {module.module_name}")
        content_sections.append(f"FILENAME: {module.filename}")
        content_sections.append("CONTENT:")
        content_sections.append("-" * 50)
        content_sections.append(module.module_content)
        content_sections.append("-" * 50)
        content_sections.append("")

    return "\n".join(content_sections)


def build_complete_showroom_analysis_prompt(
    showroom_data,
    showroom_model: type[BaseModel],
    include_field_instructions: bool = True
) -> tuple[str, str]:
    """
    Build complete system and user prompts for Showroom analysis.

    Args:
        showroom_data: Showroom BaseModel instance with the lab data
        showroom_model: The Showroom Pydantic model class for field extraction
        include_field_instructions: Whether to include field-specific instructions

    Returns:
        Tuple of (system_prompt, user_content) ready for LLM
    """
    system_prompt = build_showroom_summary_prompt(
        showroom_model, include_field_instructions
    )

    user_content = format_showroom_content_for_prompt(showroom_data)

    return system_prompt, user_content


def build_showroom_summary_generation_prompt(
    showroom_data,
    summary_model: type[BaseModel],
    include_field_instructions: bool = True
) -> tuple[str, str]:
    """
    Build complete system and user prompts for ShowroomSummary generation.

    Args:
        showroom_data: Showroom BaseModel instance with the lab data
        summary_model: The ShowroomSummary Pydantic model class
        include_field_instructions: Whether to include field-specific instructions

    Returns:
        Tuple of (system_prompt, user_content) ready for LLM summary generation
    """
    system_prompt = build_showroom_summary_structured_prompt(
        summary_model, include_field_instructions
    )

    user_content = format_showroom_content_for_prompt(showroom_data)

    return system_prompt, user_content


def build_showroom_review_structured_prompt(
    review_model: type[BaseModel],
    include_field_instructions: bool = True
) -> str:
    """
    Build a structured prompt specifically for ShowroomReview generation.

    Args:
        review_model: The ShowroomReview Pydantic model class
        include_field_instructions: Whether to include field-specific instructions

    Returns:
        Complete system prompt for structured review generation
    """
    base_prompt = get_review_base_system_prompt()

    if include_field_instructions:
        field_instructions = extract_field_descriptions(review_model)
        if field_instructions:
            enhanced_prompt = f"{base_prompt}\n\n{field_instructions}"
        else:
            enhanced_prompt = base_prompt
    else:
        enhanced_prompt = base_prompt

    return enhanced_prompt


def build_showroom_review_generation_prompt(
    showroom_data,
    review_model: type[BaseModel],
    include_field_instructions: bool = True
) -> tuple[str, str]:
    """
    Build complete system and user prompts for ShowroomReview generation.

    Args:
        showroom_data: Showroom BaseModel instance with the lab data
        review_model: The ShowroomReview Pydantic model class
        include_field_instructions: Whether to include field-specific instructions

    Returns:
        Tuple of (system_prompt, user_content) ready for LLM review generation
    """
    system_prompt = build_showroom_review_structured_prompt(
        review_model, include_field_instructions
    )

    user_content = format_showroom_content_for_prompt(showroom_data)

    return system_prompt, user_content


def build_showroom_description_structured_prompt(
    description_model: type[BaseModel],
    include_field_instructions: bool = True
) -> str:
    """
    Build a structured prompt specifically for CatalogDescription generation.

    Args:
        description_model: The CatalogDescription Pydantic model class
        include_field_instructions: Whether to include field-specific instructions

    Returns:
        Complete system prompt for structured description generation
    """
    base_prompt = get_description_base_system_prompt()

    if include_field_instructions:
        field_instructions = extract_field_descriptions(description_model)
        if field_instructions:
            enhanced_prompt = f"{base_prompt}\n\n{field_instructions}"
        else:
            enhanced_prompt = base_prompt
    else:
        enhanced_prompt = base_prompt

    return enhanced_prompt


def build_showroom_description_generation_prompt(
    showroom_data,
    description_model: type[BaseModel],
    include_field_instructions: bool = True
) -> tuple[str, str]:
    """
    Build complete system and user prompts for CatalogDescription generation.

    Args:
        showroom_data: Showroom BaseModel instance with the lab data
        description_model: The CatalogDescription Pydantic model class
        include_field_instructions: Whether to include field-specific instructions

    Returns:
        Tuple of (system_prompt, user_content) ready for LLM description generation
    """
    system_prompt = build_showroom_description_structured_prompt(
        description_model, include_field_instructions
    )

    user_content = format_showroom_content_for_prompt(showroom_data)

    return system_prompt, user_content


# Temperature configuration helpers (Requirement 11.8)

DEFAULT_TEMPERATURE: float = 0.1

# In-memory overrides loaded from a prompts file (Requirement 11.9)
PROMPTS_FILE_OVERRIDES: dict[str, Any] = {}


def get_temperature_for_action(
    action: Literal["summary", "review", "description"],
    explicit_temperature: float | None = None,
) -> float:
    """
    Resolve the temperature to use for a given action with the following precedence:
    1) explicit_temperature (CLI flag)
    2) action-specific env var: SHOWROOM_SUMMARY_TEMPERATURE | SHOWROOM_REVIEW_TEMPERATURE | SHOWROOM_DESCRIPTION_TEMPERATURE
    3) global env var: LLM_TEMPERATURE
    4) DEFAULT_TEMPERATURE (0.1)

    Args:
        action: One of "summary", "review", or "description"
        explicit_temperature: Optional temperature explicitly provided by user

    Returns:
        Final temperature value as float
    """
    if explicit_temperature is not None:
        return float(explicit_temperature)

    # Check prompts-file overrides first
    temperature_override_keys = {
        "summary": "SHOWROOM_SUMMARY_TEMPERATURE",
        "review": "SHOWROOM_REVIEW_TEMPERATURE",
        "description": "SHOWROOM_DESCRIPTION_TEMPERATURE",
    }
    override_key = temperature_override_keys.get(action)
    if override_key and override_key in PROMPTS_FILE_OVERRIDES:
        try:
            return float(PROMPTS_FILE_OVERRIDES[override_key])
        except (TypeError, ValueError):
            pass

    mapping = {
        "summary": "SHOWROOM_SUMMARY_TEMPERATURE",
        "review": "SHOWROOM_REVIEW_TEMPERATURE",
        "description": "SHOWROOM_DESCRIPTION_TEMPERATURE",
    }

    specific_key = mapping.get(action)
    if specific_key:
        specific_val = os.getenv(specific_key)
        if specific_val is not None and specific_val != "":
            try:
                return float(specific_val)
            except ValueError:
                pass

    global_val = os.getenv("LLM_TEMPERATURE")
    if global_val is not None and global_val != "":
        try:
            return float(global_val)
        except ValueError:
            pass

    return DEFAULT_TEMPERATURE


def load_prompts_overrides(file_path: str) -> None:
    """
    Load prompt and temperature overrides from an external file.

    Supports:
    - Python files: define variables with the same names as defaults in this module
      e.g., SHOWROOM_SUMMARY_STRUCTURED_PROMPT = "..."
            SHOWROOM_REVIEW_TEMPERATURE = 0.2
    - JSON files: a key-value mapping of variable names to values

    Unknown keys are ignored. Missing keys fall back to defaults.
    """
    global PROMPTS_FILE_OVERRIDES

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Prompts file not found: {file_path}")

    # Reset before loading to ensure clean state per invocation
    PROMPTS_FILE_OVERRIDES = {}

    def _filter_keys(d: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            # Prompt texts (refactored names)
            "SHOWROOM_SUMMARY_BASE_SYSTEM_PROMPT",
            "SHOWROOM_REVIEW_BASE_SYSTEM_PROMPT",
            "SHOWROOM_DESCRIPTION_BASE_SYSTEM_PROMPT",
            # Temperatures
            "SHOWROOM_SUMMARY_TEMPERATURE",
            "SHOWROOM_REVIEW_TEMPERATURE",
            "SHOWROOM_DESCRIPTION_TEMPERATURE",
        }
        return {k: v for k, v in d.items() if k in allowed}

    if path.suffix.lower() == ".py":
        spec = importlib.util.spec_from_file_location("_showroom_prompts_overrides", str(path))
        if spec and spec.loader:  # type: ignore
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)  # type: ignore
            loaded = {k: getattr(module, k) for k in dir(module) if k.isupper()}
            PROMPTS_FILE_OVERRIDES = _filter_keys(loaded)
        else:
            raise RuntimeError(f"Failed to load Python prompts file: {file_path}")
    elif path.suffix.lower() == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("JSON prompts file must contain a top-level object")
            PROMPTS_FILE_OVERRIDES = _filter_keys({str(k): v for k, v in data.items()})
    else:
        raise ValueError("Unsupported prompts file type. Use .py or .json")


# Backwards-compat shim: allow imports from showroom_tool.prompts to continue working
# after introducing prompt_builder and external config discovery in Requirement 11.11.
# Existing code continues to import builder functions from this module.

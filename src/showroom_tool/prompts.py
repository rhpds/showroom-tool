#!/usr/bin/env python

"""
Prompt building utilities for Showroom AI summarization.

This module contains prompts and utilities for generating AI-powered
summaries of Showroom lab content using structured prompts.
"""

from pydantic import BaseModel

# Base prompt for Showroom lab summarization
SHOWROOM_SUMMARY_BASE_PROMPT = """You are an expert technical content analyst specializing in summarizing hands-on laboratory exercises and demo content. Your role is to analyze Showroom lab repositories and provide comprehensive, actionable summaries.

Your analysis should focus on:
- Understanding the lab's educational objectives and target audience
- Identifying key technical concepts, tools, and technologies covered
- Extracting the learning progression and module structure
- Highlighting practical skills and knowledge gained
- Noting any prerequisites or dependencies
- Summarizing the overall lab experience and outcomes

Provide detailed, accurate summaries that would help technical sellers, educators, and learners understand the full scope and value of the lab content. Focus on practical insights and concrete details rather than generic descriptions.

Your summary should be comprehensive enough to give readers a complete understanding of what the lab teaches, how it's structured, and what participants will accomplish by completing it."""


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


def build_showroom_summary_prompt(
    showroom_model: type[BaseModel],
    include_field_instructions: bool = True
) -> str:
    """
    Build an enhanced system prompt for Showroom lab summarization.

    Args:
        showroom_model: The Showroom Pydantic model class
        include_field_instructions: Whether to include field-specific instructions

    Returns:
        Complete system prompt for LLM summarization
    """
    base_prompt = SHOWROOM_SUMMARY_BASE_PROMPT

    if include_field_instructions:
        field_instructions = extract_field_descriptions(showroom_model)
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

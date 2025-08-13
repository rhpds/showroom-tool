#!/usr/bin/env python

"""
Shared utilities for Showroom AI processing and prompt generation.

This module contains reusable utilities for building enhanced system prompts,
initializing LLM clients, and processing content with structured outputs.
Based on patterns from sample-code/shared_utilities.py but adapted for showroom use.
"""

import json
import os
import time
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from showroom_tool.basemodels import CatalogDescription, ShowroomReview, ShowroomSummary

# Optional OpenAI imports for LLM functionality
try:
    from openai import OpenAI
    from openai.types.chat import ChatCompletionMessageParam
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    ChatCompletionMessageParam = None
    OPENAI_AVAILABLE = False


def initialize_llm(
    llm_provider: str | None = None, model: str | None = None
) -> tuple[Any, str]:
    """Initialize LLM client with provider detection. Defaults to Gemini."""
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI package is not installed. Install it with 'pip install openai'")

    provider = llm_provider or os.getenv("LLM_PROVIDER", "gemini")
    provider = provider.lower()

    if provider == "local":
        api_key = os.getenv("LOCAL_OPENAI_API_KEY")
        base_url = os.getenv("LOCAL_OPENAI_BASE_URL")
        model_name = model or os.getenv("LOCAL_OPENAI_MODEL")
        if not api_key or not base_url or not model_name:
            raise ValueError(
                "LOCAL_OPENAI_API_KEY, LOCAL_OPENAI_BASE_URL, and LOCAL_OPENAI_MODEL must be set for local provider"
            )
        if OpenAI is None:
            raise ImportError("OpenAI package is not installed")
        client = OpenAI(api_key=api_key, base_url=base_url)
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set for openai provider")
        if OpenAI is None:
            raise ImportError("OpenAI package is not installed")
        client = OpenAI(api_key=api_key)
    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        if not api_key:
            raise ValueError("GEMINI_API_KEY must be set for gemini provider")
        if OpenAI is None:
            raise ImportError("OpenAI package is not installed")
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Supported: local, openai, gemini")
    return client, model_name


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
        if field_name in ["git_url", "git_ref", "summary_output"]:
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


def build_enhanced_system_prompt(
    base_prompt: str,
    model_class: type[BaseModel],
    context_hints: dict[str, Any] | None = None,
) -> str:
    """
    Build an enhanced system prompt that includes field-specific descriptions and optional context hints.

    Args:
        base_prompt: The base system prompt text
        model_class: The Pydantic model class to extract field descriptions from
        context_hints: Optional context hints to include in the prompt

    Returns:
        Enhanced system prompt with field instructions and context hints
    """
    field_instructions = extract_field_descriptions(model_class)

    if field_instructions:
        enhanced_prompt = f"{base_prompt}\n\n{field_instructions}"
    else:
        enhanced_prompt = base_prompt

    if context_hints:
        context_section = "\n\nCONTEXT HINTS TO CONSIDER:\n"
        context_section += "Use these hints to improve accuracy and provide additional clarity, but do not summarize them.\n\n"

        for key, value in context_hints.items():
            context_section += f"{key.upper()}:\n"
            if isinstance(value, list):
                for item in value:
                    context_section += f"- {item}\n"
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    context_section += f"- {sub_key}: {sub_value}\n"
            elif isinstance(value, str):
                context_section += f"{value}\n"
            context_section += "\n"

        enhanced_prompt += context_section

    return enhanced_prompt


def build_context_enhanced_system_prompt(
    base_prompt: str,
    model_class: type[BaseModel],
    context_hints: dict[str, Any] | None = None
) -> str:
    """
    Build system prompt with context hints integration.
    Simpler version focusing primarily on context enhancement.

    Args:
        base_prompt: The base system prompt text
        model_class: The Pydantic model class (for future extensibility)
        context_hints: Optional context hints to include in the prompt

    Returns:
        Enhanced system prompt with context hints
    """
    enhanced_prompt = base_prompt

    if context_hints:
        context_section = "\n\nCONTEXT HINTS TO CONSIDER (but do not summarize):\n"
        context_section += "Use these hints to improve accuracy, but do not include them in your summary.\n\n"

        for key, value in context_hints.items():
            context_section += f"{key.upper()}:\n"
            if isinstance(value, list):
                for item in value:
                    context_section += f"- {item}\n"
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    context_section += f"- {sub_key}: {sub_value}\n"
            elif isinstance(value, str):
                context_section += f"{value}\n"
            context_section += "\n"

        enhanced_prompt += context_section

    return enhanced_prompt


async def process_content_with_structured_output(
    content: str,
    model_class: type[BaseModel],
    system_prompt: str,
    llm_provider: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    verbose: bool = False,
    context_hints: dict[str, Any] | None = None,
) -> tuple[BaseModel | None, bool, dict[str, Any]]:
    """
    Core function: Process text using structured output with given Pydantic model.

    Args:
        content: The content to process
        model_class: Pydantic model class for structured output
        system_prompt: System prompt for the LLM
        llm_provider: LLM provider ("openai", "local", or "gemini")
        model: Model name to use
        temperature: Temperature for response generation (defaults to 0.1)
        verbose: Enable verbose output
        context_hints: Optional context hints to enhance the prompt

    Returns:
        Tuple of (structured_output, success, metadata)
    """
    if not OPENAI_AVAILABLE:
        metadata = {
            "success": False,
            "error": "OpenAI package is not installed. Install it with 'pip install openai'",
            "processing_duration": 0.0,
        }
        return None, False, metadata

    start_time = time.monotonic()

    try:
        client, model_name = initialize_llm(llm_provider, model)
        provider = llm_provider or os.getenv("LLM_PROVIDER", "gemini")
        provider = provider.lower()

        # Enhance system prompt with field descriptions and context hints
        enhanced_system_prompt = build_enhanced_system_prompt(
            system_prompt, model_class, context_hints
        )

        messages = [
            {"role": "system", "content": enhanced_system_prompt},
            {"role": "user", "content": content},
        ]

        if verbose:
            print("🚀 PROMPT BEING SENT TO LLM:")
            print("=" * 60)
            for i, msg in enumerate(messages):
                role = msg.get("role", "unknown")
                msg_content = msg.get("content", "")
                # Handle different content types
                if isinstance(msg_content, str):
                    content_str = msg_content
                else:
                    content_str = str(msg_content)
                print(f"[{i + 1}] {str(role).upper()}:")
                print("-" * 30)
                print(content_str)
            print("=" * 60)
            print("\n🔧 STRUCTURED OUTPUT SCHEMA:")
            print(json.dumps(model_class.model_json_schema(), indent=2))
            print("=" * 60)

        print("🔄 Calling LLM with structured output..." if verbose else "", end="")

        # Use the responses API for structured output
        final_temperature = temperature if temperature is not None else float(os.getenv("LLM_TEMPERATURE", "0.1"))
        response = client.beta.chat.completions.parse(
            model=model_name,
            messages=messages,
            response_format=model_class,
            temperature=final_temperature,
        )

        processing_duration = time.monotonic() - start_time

        if response.choices[0].message.parsed:
            structured_output = response.choices[0].message.parsed

            if verbose:
                print("\n📥 SUCCESS - Structured Output Generated:")
                print(json.dumps(structured_output.model_dump(), indent=2))
                print("=" * 60)

            metadata = {
                "provider": provider,
                "model": model_name,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "processing_duration": processing_duration,
            }

            return structured_output, True, metadata
        else:
            if verbose:
                print("\n❌ PARSING FAILED")
                print(f"Raw content: {response.choices[0].message.content}")
                print(f"Raw response object: {response}")

            metadata = {
                "provider": provider,
                "model": model_name,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": "Failed to parse response to structured format",
                "processing_duration": processing_duration,
            }

            return None, False, metadata

    except Exception as e:
        if verbose:
            print(f"❌ Exception in process_content_with_structured_output: {e}")

        metadata = {
            "success": False,
            "error": str(e),
            "processing_duration": time.monotonic() - start_time,
        }

        return None, False, metadata


def save_structured_output(
    output: dict[str, Any],
    content_type: str,
    save_path: str = "workspace",
) -> str:
    """
    Save structured output to timestamped file with proper naming convention.

    Args:
        output: The structured output dictionary to save
        content_type: Type of content for filename
        save_path: Directory to save the file

    Returns:
        Path to the saved file
    """
    # Ensure save directory exists
    os.makedirs(save_path, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"summary_{content_type}_{timestamp}.json"
    full_path = os.path.join(save_path, filename)

    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return full_path


def save_summary_to_workspace(
    summary: BaseModel, save_path: str = "workspace"
) -> str:
    """
    Save a summary BaseModel to the workspace with model information included.

    Args:
        summary: BaseModel instance to save
        save_path: Directory to save the file

    Returns:
        Path to the saved file
    """
    # Extract content type from the summary (default to "showroom")
    content_type = "showroom"

    # Convert to dict for saving
    summary_dict = summary.model_dump()

    # Save using the existing function
    return save_structured_output(summary_dict, content_type, save_path)


def print_basemodel(model: BaseModel, title: str = "Model Output") -> None:
    """Print any BaseModel in a formatted way - works dynamically with any model."""
    print(f"✅ {title}")
    model_dict = model.model_dump()
    print(json.dumps(model_dict, indent=2, ensure_ascii=False))

    # Print summary stats for list fields
    list_fields = []
    for field_name, field_value in model_dict.items():
        if isinstance(field_value, list):
            list_fields.append(f"{field_name}: {len(field_value)} items")

    if list_fields:
        print(f"📊 Summary: {', '.join(list_fields)}")


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


def build_showroom_summary_prompt(
    showroom_data,
    summary_model: type[BaseModel] = ShowroomSummary,
    base_prompt: str | None = None,
    context_hints: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Build complete system and user prompts for Showroom summary generation.

    Args:
        showroom_data: Showroom BaseModel instance with the lab data
        summary_model: The summary Pydantic model class (defaults to ShowroomSummary)
        base_prompt: Optional custom base prompt (uses default if not provided)
        context_hints: Optional context hints to enhance the prompt

    Returns:
        Tuple of (system_prompt, user_content) ready for LLM processing
    """
    # Default base prompt for showroom summarization
    if base_prompt is None:
        base_prompt = """You are an expert technical content analyst specializing in analyzing Red Hat hands-on laboratory exercises and demo content. Your role is to analyze Showroom lab repositories and extract specific structured information.

ANALYSIS FOCUS:
- Identify Red Hat products explicitly mentioned in the content (not implied or assumed)
- Determine the target audience based on skill level, roles, and prerequisites
- Extract clear learning objectives that participants will achieve
- Create a concise but comprehensive summary of the entire lab experience

CRITICAL INSTRUCTIONS:
- For Red Hat products: Only include products that are explicitly named in the content
- For audience: Consider technical level, job roles, and experience requirements
- For learning objectives: Focus on specific skills and knowledge participants will gain
- For summary: Provide an objective overview in exactly 5-6 sentences

Be precise, accurate, and focus only on information that is clearly stated or directly demonstrated in the lab content."""

    # Build enhanced system prompt
    system_prompt = build_enhanced_system_prompt(
        base_prompt, summary_model, context_hints
    )

    # Format user content
    user_content = format_showroom_content_for_prompt(showroom_data)

    return system_prompt, user_content


def save_review_to_workspace(
    review: BaseModel, save_path: str = "workspace"
) -> str:
    """
    Save a review BaseModel to the workspace with model information included.

    Args:
        review: BaseModel instance to save
        save_path: Directory to save the file

    Returns:
        Path to the saved file
    """
    # Extract content type from the review (default to "showroom")
    content_type = "showroom_review"

    # Convert to dict for saving
    review_dict = review.model_dump()

    # Save using the existing function
    return save_structured_output(review_dict, content_type, save_path)


def build_showroom_review_prompt(
    showroom_data,
    review_model: type[BaseModel] = ShowroomReview,
    base_prompt: str | None = None,
    context_hints: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Build complete system and user prompts for Showroom review generation.

    Args:
        showroom_data: Showroom BaseModel instance with the lab data
        review_model: The review Pydantic model class (defaults to ShowroomReview)
        base_prompt: Optional custom base prompt (uses default if not provided)
        context_hints: Optional context hints to enhance the prompt

    Returns:
        Tuple of (system_prompt, user_content) ready for LLM processing
    """
    # Default base prompt for showroom review
    if base_prompt is None:
        base_prompt = """You are an expert technical content reviewer specializing in evaluating Red Hat hands-on laboratory exercises and demo content. Your role is to provide constructive, detailed feedback on Showroom lab repositories across multiple quality dimensions.

REVIEW FOCUS:
- Completeness: Assess if the content covers all necessary topics and provides complete learning experiences
- Clarity: Evaluate how clear and understandable the instructions, explanations, and objectives are
- Technical Detail: Analyze the depth and accuracy of technical information provided
- Usefulness: Determine practical value for the target audience and real-world applicability
- Business Value: Assess how well the content demonstrates business benefits and ROI

SCORING GUIDELINES:
- Use a 0-10 scale where 10 is exceptional, 7-8 is good, 5-6 is adequate, 3-4 needs improvement, 0-2 is poor
- Provide specific, actionable feedback for each dimension
- Focus on constructive suggestions for improvement
- Consider the target audience when evaluating appropriateness

CRITICAL INSTRUCTIONS:
- Be fair and balanced in your assessment
- Provide specific examples when giving feedback
- Consider both strengths and areas for improvement
- Ensure feedback is actionable and helpful for content creators
- Maintain professional, constructive tone throughout"""

    # Build enhanced system prompt
    system_prompt = build_enhanced_system_prompt(
        base_prompt, review_model, context_hints
    )

    # Format user content
    user_content = format_showroom_content_for_prompt(showroom_data)

    return system_prompt, user_content


def save_description_to_workspace(
    description: BaseModel, save_path: str = "workspace"
) -> str:
    """
    Save a description BaseModel to the workspace with model information included.

    Args:
        description: BaseModel instance to save
        save_path: Directory to save the file

    Returns:
        Path to the saved file
    """
    # Extract content type from the description (default to "showroom")
    content_type = "showroom_description"

    # Convert to dict for saving
    description_dict = description.model_dump()

    # Save using the existing function
    return save_structured_output(description_dict, content_type, save_path)


def build_showroom_description_prompt(
    showroom_data,
    description_model: type[BaseModel] = CatalogDescription,
    base_prompt: str | None = None,
    context_hints: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Build complete system and user prompts for Showroom description generation.

    Args:
        showroom_data: Showroom BaseModel instance with the lab data
        description_model: The description Pydantic model class (defaults to CatalogDescription)
        base_prompt: Optional custom base prompt (uses default if not provided)
        context_hints: Optional context hints to enhance the prompt

    Returns:
        Tuple of (system_prompt, user_content) ready for LLM processing
    """
    # Default base prompt for showroom description
    if base_prompt is None:
        base_prompt = """You are an expert technical catalog writer specializing in creating compelling catalog entries for Red Hat hands-on laboratory exercises and demo content. Your role is to analyze Showroom lab repositories and generate catalog descriptions that accurately represent the content and attract the right audience.

ANALYSIS FOCUS:
- Headline: Create a compelling, concise summary that captures the lab's core value proposition
- Products: Identify specific Red Hat products that are explicitly covered or used in the lab
- Audience: Determine 2-4 specific audiences who would benefit most from this content
- Lab Benefits: Extract 3-6 key takeaways that participants will gain from completing the lab

CRITICAL INSTRUCTIONS:
- For headline: Make it compelling but accurate, avoid marketing hyperbole
- For products: Only include Red Hat products that are explicitly mentioned or demonstrated
- For audience: Be specific about roles, skill levels, and use cases (e.g., "DevOps engineers new to containers")
- For lab bullets: Focus on concrete skills, knowledge, or outcomes participants will achieve
- Keep bullets concise but specific - each should highlight a distinct value or learning outcome

Write in a professional, informative tone that appeals to technical practitioners and decision-makers."""

    # Build enhanced system prompt
    system_prompt = build_enhanced_system_prompt(
        base_prompt, description_model, context_hints
    )

    # Format user content
    user_content = format_showroom_content_for_prompt(showroom_data)

    return system_prompt, user_content

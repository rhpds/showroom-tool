import json
import os
import time
import urllib.request
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel

from config.basemodels import (
    ALLOWED_CONTENT_MODELS,
    ContentTypeDetection,
    ContextHint,
    ContextHints,
)


async def extract_text_from_url(url: str) -> str:
    """Extract and clean text content from URL."""
    # Create a request with proper headers to avoid 403 errors
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        },
    )

    try:
        with urllib.request.urlopen(req) as response:
            # Read the raw bytes first
            raw_content = response.read()

            # Check if content is gzipped
            if response.headers.get("Content-Encoding") == "gzip":
                import gzip

                html_content = gzip.decompress(raw_content).decode("utf-8")
            else:
                # Try to decode as UTF-8, fallback to other encodings if needed
                try:
                    html_content = raw_content.decode("utf-8")
                except UnicodeDecodeError:
                    # Try other common encodings
                    for encoding in ["latin-1", "cp1252", "iso-8859-1"]:
                        try:
                            html_content = raw_content.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # If all encodings fail, use 'ignore' to skip problematic characters
                        html_content = raw_content.decode("utf-8", errors="ignore")

    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise Exception(
                f"Access denied (403 Forbidden) for URL: {url}. The website may be blocking automated requests."
            )
        else:
            raise Exception(f"HTTP Error {e.code}: {e.reason} for URL: {url}")
    except urllib.error.URLError as e:
        raise Exception(f"URL Error: {e.reason} for URL: {url}")

    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup(["script", "style"]):
        script.decompose()

    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return " ".join(chunk for chunk in chunks if chunk)


def initialize_llm(
    llm_provider: str | None = None, model: str | None = None
) -> tuple[OpenAI, str]:
    """Initialize LLM client with provider detection. Fails if not set."""
    provider = llm_provider or os.getenv("LLM_PROVIDER")
    if not provider:
        raise ValueError("LLM_PROVIDER must be set in environment or passed explicitly")
    provider = provider.lower()

    if provider == "local":
        api_key = os.getenv("LOCAL_OPENAI_API_KEY")
        base_url = os.getenv("LOCAL_OPENAI_BASE_URL")
        model_name = model or os.getenv("LOCAL_OPENAI_MODEL")
        if not api_key or not base_url or not model_name:
            raise ValueError(
                "LOCAL_OPENAI_API_KEY, LOCAL_OPENAI_BASE_URL, and LOCAL_OPENAI_MODEL must be set for local provider"
            )
        client = OpenAI(api_key=api_key, base_url=base_url)
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model_name = model or os.getenv("OPENAI_MODEL")
        if not api_key or not model_name:
            raise ValueError(
                "OPENAI_API_KEY and OPENAI_MODEL must be set for openai provider"
            )
        client = OpenAI(api_key=api_key)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
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
        if field_name in ["summary_type", "processing_metadata"]:
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
    context_hints: ContextHints | None = None,
) -> str:
    """Build an enhanced system prompt that includes field-specific descriptions and context hints."""
    field_instructions = extract_field_descriptions(model_class)
    example_instruction = "Example: If the transcript says 'David' and the context hints list 'David Shawarma', output 'David Shawarma' as the participant."
    if field_instructions:
        enhanced_prompt = f"{base_prompt}\n\nWhen relevant, use the context hints below to resolve ambiguities or provide additional clarity, but do not summarize or repeat them.\n{example_instruction}\n\n{field_instructions}"
    else:
        enhanced_prompt = f"{base_prompt}\n\nWhen relevant, use the context hints below to resolve ambiguities or provide additional clarity, but do not summarize or repeat them.\n{example_instruction}"
    if context_hints and context_hints.hints:
        context_section = "\n\nCONTEXT HINTS TO CONSIDER (but do not summarize):\n"
        context_section += "Use these hints to improve accuracy (like, get Acryonim meening, or a last name from a first name), but do not summarize them.\n\n"
        for hint in context_hints.hints:
            context_section += f"{hint.hint_label.upper()}:\n"
            if isinstance(hint.hint_data, list):
                if hint.hint_data and isinstance(hint.hint_data[0], dict):
                    for item in hint.hint_data:
                        context_section += f"- {item}\n"
                else:
                    for item in hint.hint_data:
                        context_section += f"- {item}\n"
            elif isinstance(hint.hint_data, dict):
                for key, value in hint.hint_data.items():
                    context_section += f"- {key}: {value}\n"
            elif isinstance(hint.hint_data, str):
                context_section += f"{hint.hint_data}\n"
            context_section += (
                f"(Source: {hint.source}, Confidence: {hint.confidence})\n\n"
            )
        enhanced_prompt += context_section
    return enhanced_prompt


async def process_content_with_structured_output(
    content: str,
    model_class: type[BaseModel],
    system_prompt: str,
    llm_provider: str | None = None,
    model: str | None = None,
    verbose: bool = False,
    context_hints: ContextHints | None = None,  # New optional parameter
    processing_mode: str = "single",  # New parameter
) -> tuple[BaseModel | None, bool, dict[str, Any]]:
    """Core function: Process text using structured output with given Pydantic model. Supports single and iterative modes."""
    from datetime import datetime

    from pydantic import create_model

    from config.basemodels import ProcessingMetadata

    start_time = time.monotonic()
    try:
        if processing_mode == "iterative":
            if verbose:
                print("🚀 Starting iterative processing mode...")
            # Identify fields to process (skip those with avoid_processing=True)
            fields_to_process = [
                (fname, finfo)
                for fname, finfo in model_class.model_fields.items()
                if not getattr(finfo, "avoid_processing", False)
            ]
            submodels = []
            total_fields = len(fields_to_process)
            current_field = 0
            for field_name, field_info in fields_to_process:
                current_field += 1
                if verbose:
                    print(
                        f"🟦 Processing field {current_field}/{total_fields}: {field_name}"
                    )
                # Create single-field model
                SingleFieldModel = create_model(
                    f"{field_name.capitalize()}Only",
                    **{field_name: (field_info.annotation, field_info)},
                )
                field_prompt = f"You are an expert summarizer. Extract only the '{field_name}' field from the provided content.\n\nFollow the schema exactly and provide accurate, detailed information based only on what's mentioned in the content."
                if verbose:
                    print(f"   🔍 Sending request to LLM for '{field_name}'...")
                (
                    single_result,
                    success,
                    metadata,
                ) = await process_content_with_structured_output(
                    content=content,
                    model_class=SingleFieldModel,
                    system_prompt=field_prompt,
                    llm_provider=llm_provider,
                    model=model,
                    verbose=verbose,
                    context_hints=context_hints,
                    processing_mode="single",  # Always use single for subfields
                )
                if not success or single_result is None:
                    error_msg = f"Iterative processing failed for field '{field_name}': {metadata.get('error', 'Unknown error')}"
                    if verbose:
                        print(f"❌ {error_msg}")
                    return None, False, {"error": error_msg}
                submodels.append(single_result)
                if verbose:
                    print(f"   ✅ Successfully processed '{field_name}'")
            # Build dict of all field values from submodels
            fields_dict = {}
            for submodel in submodels:
                for subfield in submodel.model_fields:
                    fields_dict[subfield] = getattr(submodel, subfield)
            # Set processing_metadata after all fields are processed
            client, model_name = initialize_llm(llm_provider, model)
            provider = llm_provider or os.getenv("LLM_PROVIDER")
            processing_duration = time.monotonic() - start_time
            fields_dict["processing_metadata"] = ProcessingMetadata(
                timestamp=datetime.now().isoformat(),
                llm_provider=provider,
                model_name=model_name,
                processing_duration=processing_duration,
                success=True,
            )
            # Set content_type if present in model
            if (
                "content_type" in model_class.model_fields
                and "content_type" not in fields_dict
            ):
                default_type = getattr(model_class, "content_type", None)
                if default_type:
                    fields_dict["content_type"] = default_type
            result_instance = model_class(**fields_dict)
            if verbose:
                print("✅ Iterative processing completed successfully!")
                print_basemodel(
                    result_instance, f"{model_class.__name__} (Iterative Mode)"
                )
            metadata = {
                "provider": provider,
                "model": model_name,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "processing_duration": processing_duration,
            }
            return result_instance, True, metadata
        else:
            # Single mode (default, current logic)
            client, model_name = initialize_llm(llm_provider, model)
            provider = llm_provider or os.getenv("LLM_PROVIDER")
            if not provider:
                raise ValueError(
                    "LLM_PROVIDER must be set in environment or passed explicitly"
                )
            provider = provider.lower()
            # Enhance system prompt with field descriptions AND context hints
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
                    print(f"[{i + 1}] {msg['role'].upper()}:")
                    print("-" * 30)
                    print(msg["content"])
                print("=" * 60)
                print("\n🔧 STRUCTURED OUTPUT SCHEMA:")
                print(json.dumps(model_class.model_json_schema(), indent=2))
                print("=" * 60)
            print("🔄 Calling LLM with structured output..." if verbose else "", end="")
            response = client.beta.chat.completions.parse(
                model=model_name,
                messages=messages,
                response_format=model_class,
                temperature=0,
            )
            processing_duration = time.monotonic() - start_time
            if response.choices[0].message.parsed:
                structured_output = response.choices[0].message.parsed
                # Populate processing metadata with model information
                processing_metadata = {
                    "timestamp": datetime.now().isoformat(),
                    "llm_provider": provider,
                    "model_name": model_name,
                    "processing_duration": processing_duration,  # Now set duration
                    "success": True,
                }
                # Update the structured output with processing metadata if it has that field
                if hasattr(structured_output, "processing_metadata"):
                    structured_output.processing_metadata = processing_metadata
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
                    "processing_duration": time.monotonic() - start_time,
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


async def detect_content_type(
    content: str,
    llm_provider: str | None = None,
    model: str | None = None,
    verbose: bool = False,
) -> tuple[str, float]:
    """Auto-detect content type using structured output with ContentTypeDetection model."""
    # Build available types dynamically from registry
    available_types = list(ALLOWED_CONTENT_MODELS.keys())
    type_descriptions = {
        "meeting": "Meeting transcripts, discussion notes, team calls, etc.",
        "news_article": "News articles, political coverage, current events, press releases, journalistic content",
        "tutorial": "Educational content, how-to guides, technical tutorials",
        "technical_article": "Technical articles, blog posts, whitepapers, research papers, or in-depth technical writeups.",
    }

    # Build dynamic type list for prompt
    type_list = []
    for content_type in available_types:
        description = type_descriptions.get(content_type, f"{content_type} content")
        type_list.append(f"- {content_type}: {description}")

    system_prompt = f"""You are an expert content classifier. Analyze the provided content and determine its type.

Available types:
{chr(10).join(type_list)}
- general: Any other type of content

Consider the structure, language patterns, and content characteristics to make your determination."""

    result, success, metadata = await process_content_with_structured_output(
        content=content,
        model_class=ContentTypeDetection,
        system_prompt=system_prompt,
        llm_provider=llm_provider,
        model=model,
        verbose=verbose,
    )

    if success and result:
        return result.content_type, result.confidence
    else:
        return "general", 0.0


async def placeholder_context_agent(content_type: str) -> ContextHints | None:
    """
    Placeholder function that reads context hints from sample file.
    In real implementation, this would call your agent system.
    """
    sample_file = "./samples/context_agent_sample_reply.json"
    try:
        with open(sample_file) as f:
            hints_data = json.load(f)
        context_hints = ContextHints(
            content_type=content_type,
            hints=[ContextHint(**hint_data) for hint_data in hints_data],
        )
        return context_hints
    except FileNotFoundError:
        print(f"Warning: Context agent sample file not found: {sample_file}")
        return None
    except Exception as e:
        print(f"Warning: Failed to load context hints: {e}")
        return None


def build_context_enhanced_system_prompt(
    base_prompt: str, model_class: type, context_hints: ContextHints | None = None
) -> str:
    """Build system prompt with any context hints the agent discovered"""
    enhanced_prompt = base_prompt
    if context_hints and context_hints.hints:
        context_section = "\n\nCONTEXT HINTS TO CONSIDER (but do not summarize):\n"
        context_section += "Use these hints to improve accuracy, but do not include them in your summary.\n\n"
        for hint in context_hints.hints:
            context_section += f"{hint.hint_label.upper()}:\n"
            if isinstance(hint.hint_data, list):
                if hint.hint_data and isinstance(hint.hint_data[0], dict):
                    for item in hint.hint_data:
                        context_section += f"- {item}\n"
                else:
                    for item in hint.hint_data:
                        context_section += f"- {item}\n"
            elif isinstance(hint.hint_data, dict):
                for key, value in hint.hint_data.items():
                    context_section += f"- {key}: {value}\n"
            elif isinstance(hint.hint_data, str):
                context_section += f"{hint.hint_data}\n"
            context_section += (
                f"(Source: {hint.source}, Confidence: {hint.confidence})\n\n"
            )
        enhanced_prompt += context_section
    return enhanced_prompt


def save_structured_output(
    output: dict[str, Any],
    content_type: str,
    save_path: str = "workspace",
    processing_mode: str = None,
) -> str:
    """
    Save structured output to timestamped file with proper naming convention.
    Optionally include processing_mode as a top-level key.
    """
    # Ensure save directory exists
    os.makedirs(save_path, exist_ok=True)

    if processing_mode:
        output = dict(output)  # Make a copy to avoid mutating caller's dict
        output["processing_mode"] = processing_mode

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"summary_{content_type}_{timestamp}.json"
    full_path = os.path.join(save_path, filename)

    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    return full_path


def save_summary_to_workspace(
    summary: BaseModel, save_path: str = "workspace", processing_mode: str = None
) -> str:
    """
    Save a summary BaseModel to the workspace with model information included.
    Optionally include processing_mode as a top-level key.
    """
    # Extract content type from the summary
    content_type = getattr(summary, "content_type", "general")

    # Convert to dict for saving
    summary_dict = summary.model_dump()

    # Save using the existing function
    return save_structured_output(
        summary_dict, content_type, save_path, processing_mode=processing_mode
    )


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

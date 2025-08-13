#!/usr/bin/env python

"""
Output formatting utilities for generating AsciiDoc from Pydantic BaseModels.

This module provides functions to render BaseModels using Jinja2 templates
for human-readable AsciiDoc output.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

# Import the tool version for attribution in outputs
try:
    from . import __version__ as TOOL_VERSION
except Exception:
    TOOL_VERSION = "unknown version"

try:
    from jinja2 import Environment, FileSystemLoader, Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    Environment = FileSystemLoader = Template = None  # type: ignore

# Try to import from the installed package structure
try:
    from showroom_tool.basemodels import CatalogDescription, ShowroomReview, ShowroomSummary
except ImportError:
    # Fall back to adding src to path (for development)
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root / "src"))
    from showroom_tool.basemodels import CatalogDescription, ShowroomReview, ShowroomSummary


def get_template_directory() -> Path:
    """Get the path to the templates directory."""
    # Check if we're in development or installed mode
    current_file = Path(__file__)

    # Try project root (development mode)
    project_root = current_file.parent.parent.parent
    templates_dir = project_root / "templates"

    if templates_dir.exists():
        return templates_dir

    # Try relative to current module (installed mode)
    templates_dir = current_file.parent / "templates"
    if templates_dir.exists():
        return templates_dir

    # Fallback to current directory
    templates_dir = Path.cwd() / "templates"
    if templates_dir.exists():
        return templates_dir

    raise FileNotFoundError(
        f"Could not find templates directory. Searched: "
        f"{project_root / 'templates'}, {current_file.parent / 'templates'}, "
        f"{Path.cwd() / 'templates'}"
    )


def get_jinja_environment():  # type: ignore
    """Initialize and return a Jinja2 environment."""
    if not JINJA2_AVAILABLE:
        raise ImportError(
            "Jinja2 is required for AsciiDoc output. Install it with 'pip install jinja2'"
        )

    templates_dir = get_template_directory()
    # We know Environment is available here because JINJA2_AVAILABLE is True
    return Environment(  # type: ignore
        loader=FileSystemLoader(str(templates_dir)),  # type: ignore
        autoescape=False,  # AsciiDoc doesn't need HTML escaping
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_basemodel_to_adoc(
    model: BaseModel,
    template_name: str | None = None,
    extra_context: dict[str, Any] | None = None
) -> str:
    """
    Render a Pydantic BaseModel to AsciiDoc using a Jinja2 template.

    Args:
        model: The Pydantic BaseModel instance to render
        template_name: Optional template name. If not provided, uses model class name + '.adoc.j2'
        extra_context: Additional context variables for the template

    Returns:
        Rendered AsciiDoc content as string

    Raises:
        ImportError: If Jinja2 is not available
        FileNotFoundError: If template file is not found
    """
    env = get_jinja_environment()

    # Determine template name
    if template_name is None:
        template_name = f"{model.__class__.__name__}.adoc.j2"

    # Load template
    try:
        template = env.get_template(template_name)
    except Exception as e:
        raise FileNotFoundError(
            f"Could not load template '{template_name}': {e}"
        ) from e

    # Prepare context
    context = {
        **model.model_dump(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model_type": model.__class__.__name__,
        "version": TOOL_VERSION,
    }

    # Add extra context if provided
    if extra_context:
        context.update(extra_context)

    # Render template
    return template.render(**context)


def render_summary_to_adoc(summary: ShowroomSummary, extra_context: dict[str, Any] | None = None) -> str:
    """Render a ShowroomSummary to AsciiDoc."""
    return render_basemodel_to_adoc(summary, "ShowroomSummary.adoc.j2", extra_context)


def render_review_to_adoc(review: ShowroomReview, extra_context: dict[str, Any] | None = None) -> str:
    """Render a ShowroomReview to AsciiDoc."""
    return render_basemodel_to_adoc(review, "ShowroomReview.adoc.j2", extra_context)


def render_description_to_adoc(description: CatalogDescription, extra_context: dict[str, Any] | None = None) -> str:
    """Render a CatalogDescription to AsciiDoc."""
    return render_basemodel_to_adoc(description, "CatalogDescription.adoc.j2", extra_context)


def output_basemodel_as_adoc(
    model: BaseModel,
    extra_context: dict[str, Any] | None = None
) -> None:
    """
    Output a BaseModel as AsciiDoc to stdout.

    This function automatically detects the model type and uses the appropriate
    rendering function.

    Args:
        model: The Pydantic BaseModel instance to output
        extra_context: Additional context variables for the template
    """
    # Determine the appropriate renderer based on model type
    if isinstance(model, ShowroomSummary):
        adoc_content = render_summary_to_adoc(model, extra_context)
    elif isinstance(model, ShowroomReview):
        adoc_content = render_review_to_adoc(model, extra_context)
    elif isinstance(model, CatalogDescription):
        adoc_content = render_description_to_adoc(model, extra_context)
    else:
        # Fallback to generic rendering
        adoc_content = render_basemodel_to_adoc(model, extra_context=extra_context)

    # Output to stdout
    print(adoc_content)


def check_jinja2_availability() -> bool:
    """Check if Jinja2 is available for template rendering."""
    return JINJA2_AVAILABLE

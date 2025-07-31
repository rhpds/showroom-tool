#!/usr/bin/env python

"""
Base Pydantic models for the Showroom Tool.

This module contains all Pydantic BaseModels used throughout the application
for data validation and settings management.
"""

from typing import Any

from pydantic import BaseModel, Field


class ShowroomModule(BaseModel):
    """Pydantic BaseModel for individual lab modules within a Showroom."""

    module_name: str = Field(
        ...,
        description="The name of the lab module extracted from its level 1 header ie `^= My module name`",
    )
    filename: str = Field(
        ...,
        description="The filename of the module from the navigation file (e.g., '01-intro.adoc')",
    )
    module_content: str = Field(
        ..., description="The raw unprocessed asciidoc content of the module"
    )


class ShowroomSummary(BaseModel):
    """Pydantic BaseModel for AI-generated Showroom lab summaries."""

    redhat_products: list[str] = Field(
        ...,
        description="The Red Hat products EXPLICITLY mentioned in the content"
    )
    lab_audience: list[str] = Field(
        ...,
        description="The ideal audience for the content"
    )
    lab_learning_objectives: list[str] = Field(
        ...,
        description="Identify the 4 to 6 learning objectives in the content"
    )
    lab_summary: str = Field(
        ...,
        description="An objective 5 to 6 sentence summary of the entire content"
    )


class ShowroomReview(BaseModel):
    """Pydantic BaseModel for AI-generated Showroom lab reviews."""

    # completeness: float = Field(
    #     ...,
    #     ge=0,
    #     le=10,
    #     description="Score for completeness of content"
    # )
    completeness_feedback: str = Field(
        ...,
        description="Constructive feedback regarding completeness of content"
    )
    # clarity: float = Field(
    #     ...,
    #     ge=0,
    #     le=10,
    #     description="Score for clarity of instructions"
    # )
    clarity_feedback: str = Field(
        ...,
        description="Constructive feedback regarding clarity of content"
    )
    # technical_detail: float = Field(
    #     ...,
    #     ge=0,
    #     le=10,
    #     description="Score for technical detail"
    # )
    technical_detail_feedback: str = Field(
        ...,
        description="Constructive feedback regarding technical details of content"
    )
    # usefulness: float = Field(
    #     ...,
    #     ge=0,
    #     le=10,
    #     description="Score for usefulness to target audience"
    # )
    usefulness_feedback: str = Field(
        ...,
        description="Constructive feedback regarding usefulness of content"
    )
    # business_value: float = Field(
    #     ...,
    #     ge=0,
    #     le=10,
    #     description="Score for business value of content"
    # )
    business_value_feedback: str = Field(
        ...,
        description="Constructive feedback regarding business value of content"
    )
    review_summary: str = Field(
        ...,
        description="3-4 sentance overall review summary"
    )


class CatalogDescription(BaseModel):
    """Pydantic BaseModel for AI-generated catalog descriptions of Showroom labs."""

    headline: str = Field(
        ...,
        description="Concise summary of the catalog item"
    )
    products: list[str] = Field(
        ...,
        description="List of Red Hat Products covered in the lab"
    )
    intended_audience_bullets: list[str] = Field(
        ...,
        description="2 to 4 audiences who would benefit"
    )
    lab_bullets: list[str] = Field(
        ...,
        description="3 to 6 short 1 liners of the key takeaways of the lab"
    )


class Showroom(BaseModel):
    """Pydantic BaseModel for lab and demo content from Showroom Git repositories."""

    lab_name: str = Field(
        ..., description="The name of the lab extracted from the Showroom Git Repo"
    )
    git_url: str = Field(..., description="The url of the Showroom Git Repo")
    git_ref: str = Field(
        default="main", description="The git tag or branch to use, defaults to main"
    )
    modules: list[ShowroomModule] = Field(..., description="The Showroom Lab modules")
    summary_output: ShowroomSummary | None = Field(
        default=None, description="AI-generated summary of the lab content"
    )
    review_output: ShowroomReview | None = Field(
        default=None, description="AI-generated review of the lab content"
    )
    description_output: CatalogDescription | None = Field(
        default=None, description="AI-generated catalog description of the lab content"
    )


class ShowroomState(BaseModel):
    """LangGraph state for processing Showroom repositories."""

    git_url: str = Field(..., description="The URL of the Showroom Git repository")
    git_ref: str = Field(default="main", description="The git tag or branch to use")
    verbose: bool = Field(default=False, description="Enable verbose output")
    cache_dir: str | None = Field(default=None, description="Custom cache directory")
    no_cache: bool = Field(default=False, description="Disable caching and force fresh clone")

    # Processing results
    showroom: Showroom | None = Field(default=None, description="The processed Showroom data")
    messages: list[str] = Field(default_factory=list, description="Processing messages")
    errors: list[str] = Field(default_factory=list, description="Processing errors")
    final_output: dict[str, Any] = Field(default_factory=dict, description="Final output data")

#!/usr/bin/env python

"""
Base Pydantic models for the Showroom Tool.

This module contains all Pydantic BaseModels used throughout the application
for data validation and settings management.
"""

from typing import Any, Literal

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
        description="3-4 sentence overall review summary"
    )


class CatalogDescription(BaseModel):
    """
    Pydantic BaseModel for AI-generated catalog descriptions of Showroom labs.
   
    Note:
     The description fields are incorporated into the system prompt dynamically
     so they can, and should, contain clear guidance for the AI to follow.

    """

    headline: str = Field(
        ...,
        description="""
        CONCISE and CLEAR summary of the catalog item, in 1-2 sentences.
        First 115-120 characters are revealed on a thumbnail, so optimize for that.
        YOUR GOAL is to make the headline as INFORMATIVE and ACCURATE as possible.
        """
    )
    content_type: Literal["lab", "demo"] = Field(
        ...,
        description="""
        Type of catalog item determined by the content and narrative: 'lab' OR 'demo'. NO other content types are allowed.
        A lab is a hands-on lab with a specific learning objective.
        A demo is a demo of a product or feature, typically intended to show a product or feature in action.
        A demo is typically a one to many experience where a technical seller shows a product or feature to a customer.
        """,
    )
    products: list[str] = Field(
        ...,
        description="""
        List of Red Hat Products covered in the lab.
        Highlight the most important products in the lab.
        If the lab is not about a product, mention the product that is most relevant to the lab.
        Limit to 3-5 products.
        OMIT products that are not relevant to the lab.
        """
    )
    intended_audience_bullets: list[str] = Field(
        ...,
        description="""
        2 to 4 audiences who would benefit from this type of content.
        Typical audiences include:
        - System Admins, often content focussed on Linux, RHEL, and possibly Ansible
        - Cloud Admins, often content focussed on OpenShift, Kubernetes, and Public Cloud Providers such as AWS, Azure, and GCP
        - DevOps Engineers, often content focussed on CI/CD, GitOps, and Observability, but can be more general
        - Architects, often content focussed on the overall architecture of the solution
        - Developers, often content focussed on coding and development of the solution versus infrastructure
        - Data Scientists, often content focussed on data science, AI, ML, and DL 
        AVOID making up random new audiences types, use the above as a guide
        DO HIGHLIGHT key points for each audience type if appropriate.
        """
    )
    lab_bullets: list[str] = Field(
        ...,
        description="""
        3 to 6 short 1 liners of the key takeaways of the lab
        """
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

    # Repo fetch inputs
    git_url: str = Field(..., description="The URL of the Showroom Git repository")
    git_ref: str = Field(default="main", description="The git tag or branch to use")
    verbose: bool = Field(default=False, description="Enable verbose output")
    cache_dir: str | None = Field(default=None, description="Custom cache directory")
    no_cache: bool = Field(default=False, description="Disable caching and force fresh clone")

    # Processing verb and LLM options
    command: Literal["summary", "review", "description"] | None = Field(
        default=None,
        description="Verb to process after fetching showroom data: 'summary' | 'review' | 'description'",
    )
    llm_provider: str | None = Field(
        default=None, description="LLM provider identifier (e.g., openai, gemini, local)"
    )
    model: str | None = Field(default=None, description="LLM model name")
    temperature: float | None = Field(
        default=None, description="Temperature for LLM generation"
    )

    # Processing results
    showroom: Showroom | None = Field(default=None, description="The processed Showroom data")
    messages: list[str] = Field(default_factory=list, description="Processing messages")
    errors: list[str] = Field(default_factory=list, description="Processing errors")
    final_output: dict[str, Any] = Field(default_factory=dict, description="Final output data")

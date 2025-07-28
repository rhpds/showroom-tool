#!/usr/bin/env python

"""
Base Pydantic models for the Showroom Tool.

This module contains all Pydantic BaseModels used throughout the application
for data validation and settings management.
"""

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

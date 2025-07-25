#!/usr/bin/env python

"""
Base Pydantic models for the Showroom Tool.

This module contains all Pydantic BaseModels used throughout the application
for data validation and settings management.
"""

from typing import List
from pydantic import BaseModel, Field


class Showroom(BaseModel):
    """Pydantic BaseModel for lab and demo content from Showroom Git repositories."""
    
    lab_name: str = Field(
        ...,
        description="The name of the lab extracted from the Showroom Git Repo"
    )
    git_url: str = Field(
        ...,
        description="The url of the Showroom Git Repo"
    )
    git_ref: str = Field(
        default="main",
        description="The git tag or branch to use, defaults to main"
    )
    modules: List[str] = Field(
        ...,
        description="Array containing the raw asciidoc modules in sequence"
    ) 
# Requirements Document

## Application Overview

`showroom-tool` is a Python-based CLI tool designed to summarize, review, and validate technical lab and demo content. It is primarily intended for use in technical enablement and customer demonstration scenarios, typically by technical sellers.

The tool processes content provided as one or more AsciiDoc files typically stored in remote `antora` formatted repos or local git clones

The labs and demos are made available via a Catalog called RHDP and its associated repo which contains yaml defined Catalog Items (CIs). 

## External Resources

- Repo Structure is contained in `./specs/structure.md`
- High Level Technical Architecture is contained in `./specs/architecture.md`

## Goals

- Customizable summarization capabilities for lab and demo content
- Customizable review and recommendations capability for lab and demo content

## Requirements 

- User is familiar with python and virtual environments (`venv`)
- User already has `python3.12` or understands how to add it

### 1. Setup the repository and basic python dependencies

**User Story:** As a technical end user and/or developer I want a well maintained Python repo which is simple to:

- Clone the directory
- Follow the basic README documented steps to:
  - Create the local venv via `uv` or `python3.12 -m venv`
  - Install the requirements
  - Start using, developing, or testing the `showroom-tool`

**Implement:**

- Read ALL the rules files in `.cursor/rules/` for guidelines and context
- Create a well structured `.gitignore` for a Python based repository
- Create a `pyproject.yaml` with the following assumptions:
  - `python3.12`
  - `uv` used throughout
- Create a README.md and populate

### 2. Create the Showroom Pydantic BaseModel

**User Story:** As the developer I am going to deal frequently with the lab and demo content and need a Pydantic BaseModel called `Showroom` to hold this data

**Implement:**

- Create the Showroom BaseModel in `./config/basemodels.py`
```
lab_name: str, description="The name of the lab extracted from the Showroom Git Repo"
git_url: str, description="The url of the Showroom Git Repo"
git_ref: str(default='main`), description="The git tag or branch to use, defaults to main"
modules: array of str, description="Array containing the raw asciidoc modules in sequence"
```

**Rules**

- Simply build the BaseModel, no need to add any extra functionality at this point





**Further requirements will be added as the application progresses.**
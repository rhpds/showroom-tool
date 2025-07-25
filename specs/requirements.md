# Requirements Document

## Application Overview

`showroom-tool` is a Python-based CLI tool designed to summarize, review, and validate technical lab and demo content. It is primarily intended for use in technical enablement and customer demonstration scenarios, typically by technical sellers.

The tool processes content provided as one or more AsciiDoc files typically stored in remote `antora` formatted repos or local git clones

The labs and demos are made available via a Catalog called RHDP and its associated repo which contains yaml defined Catalog Items (CIs). 

## External Resources

- Repo Structure is contained in `./specs/structure.md`
- High Level Technical Architecture is contained in `./specs/architecture.md`
- 
## Goals

- Customizable summarization capabilities for lab and demo content
- Customizable review and recommendations capability for lab and demo content

## Requirements 

**User Story:** As a technical end user I a well maintained Python repo which is simple to:

- Clone
- Follow the basic README documented steps to:
  - Create the local venv via `uv` or `python3.12 -m venv`
  - Install the requirements
  - Start using, developing, or testing the `showroom-tool`

### 1. Setup the repository and basic python dependencies

- Read ALL the rules files in `.cursor/rules/` for guidelines and context
- Create a well structured `.gitignore` for a Python based repository
- Create a `pyproject.yaml` with the following assumptions:
  - `python3.12`
  - `uv` used throughout
- Create a README.md and populate

### 1. Setup the repository and basic python dependencies


**Further requirements to be added as the application progresses.**


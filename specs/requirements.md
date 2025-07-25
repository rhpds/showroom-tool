# Requirements Document

## Application Overview

`showroom-tool` is a Python-based CLI tool designed to summarize, review, and validate technical lab and demo content. It is primarily intended for use in technial enablement and customer demonstration scenarios, typically by technical sellers.

The tool processes content provided as one or more AsciiDoc files typically stored in remote `antora` formatted repos or local git clones

## Goals

- Customizable summarization capabilities for lab and demo content
- Customizable review and recommendations capability for lab and demo content

## Requirements 

### 1. Setup the repository and basic python dependencies

- Read ALL the rules files in `.cursor/rules/` for guidelines and context
- Create a well structured `.gitignore` for a Python based repository
- Create a `pyproject.yaml` with the following assumptions:
  - `python3.12`
  - `uv` used throughout
- Create a README.md and populate



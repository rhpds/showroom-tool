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

### ✅ 1. Setup the repository and basic python dependencies - COMPLETED

**User Story:** As a technical end user and/or developer I want a well maintained Python repo which is simple to:

- Clone the directory
- Follow the basic README documented steps to:
  - Create the local venv via `uv` or `python3.12 -m venv`
  - Install the requirements
  - Start using, developing, or testing the `showroom-tool`

**✅ Implemented:**

- ✅ Read ALL the rules files in `.cursor/rules/` for guidelines and context
- ✅ Created a well structured `.gitignore` for a Python based repository
- ✅ Created `pyproject.toml` with:
  - `python3.12`
  - `uv` used throughout
  - Proper package discovery and entry points
- ✅ Created README.md and populated

### ✅ 2. Create the Showroom Pydantic BaseModel - COMPLETED

**User Story:** As the developer I am going to deal frequently with the lab and demo content and need a Pydantic BaseModel called `Showroom` to hold this data

**✅ Implemented:**

- ✅ Created the Showroom BaseModel in `./src/config/basemodels.py`
```python
lab_name: str = Field(..., description="The name of the lab extracted from the Showroom Git Repo")
git_url: str = Field(..., description="The url of the Showroom Git Repo")
git_ref: str = Field(default="main", description="The git tag or branch to use, defaults to main")
modules: list[ShowroomModule] = Field(..., description="The Showroom Lab modules")
```

**Rules**

- ✅ Built the BaseModel with clean implementation following Pydantic V2 best practices

### ✅ 2.1 Add a new Showroom Module BaseModel - COMPLETED

**User Story:** Lab developers will, at a future point, want to see analysis on an individual module within a showroom lab

**✅ Implemented:**

- ✅ Created the ShowroomModule BaseModel in `./src/config/basemodels.py`
```python
module_name: str = Field(..., description="The name of the lab module extracted from its level 1 header ie `^= My module name`")
filename: str = Field(..., description="The filename of the module from the navigation file (e.g., '01-intro.adoc')")
module_content: str = Field(..., description="The raw unprocessed asciidoc content of the module")
```
- ✅ Updated the Showroom BaseModel so that its `modules` array is now an array of ShowroomModule:
```python
modules: list[ShowroomModule] = Field(..., description="The Showroom Lab modules")
```

### ✅ 2.2 Clean up codebase - COMPLETED

**User Story:** As the developer I want to ensure the existing code is clean and lints perfectly before moving on

**✅ Implemented:**

- ✅ Ran `ruff` over the existing codebase (ignoring the `sample-code` directory)
- ✅ Fixed all linting errors and warnings appropriately
- ✅ Updated `pyproject.toml` to use modern ruff configuration structure
- ✅ Ensured clean codebase with all checks passing

### ✅ 3.1 Create the Showroom Fetcher - COMPLETED

**User Story:** As the end user I want to supply the application with the git repository containing my showroom lab so it can be processed ie summarized, reviewed etc.

**✅ Implemented:**

- ✅ Created the `showroom-tool` CLI entry point
- ✅ Created CLI argument processor in `src/showroom_tool/cli.py` that supports:
  - `--repo` argument pointing to the repository
  - Positional argument support: `showroom-tool http://example.com/my_showroom`
  - `--ref` flag for git branches/tags/commits
  - `--verbose` flag for detailed output
- ✅ Populated the Showroom BaseModel:
  - `git_url`: Extracted from CLI arguments
  - `lab_name`: Extracted from `./default-site.yml` → `site.title`
  - `start_page`: Extracted from `./default-site.yml` → `site.start_page`
- ✅ Populated the modules array with ShowroomModule instances:
  - ✅ Read the module navigation file at `content/modules/ROOT/nav.adoc`
  - ✅ Processed only level 1 navigation entries to avoid duplicates
  - ✅ Read each file from the navigation into `ShowroomModule` array
  - ✅ Extract `module_name` from level 1 OR level 2 headers
  - ✅ Store filename and entire file content

### ✅ 4.1 Create the basic LangGraph entry point - COMPLETED

**User Story:** As the developer I intend this application to, in future, make use of LangGraph's Agentic AI capabilities, so want to create a basic linear graph with one node that fetches the Showroom repositories and modules. 

**✅ Implemented:**

- ✅ Read the example code in `./sample-code/graph_factory.py` especially function `graph_factory`
- ✅ Implemented LangGraph integration with:
  - ✅ `ShowroomState` Pydantic BaseModel for LangGraph state management in `src/config/basemodels.py`
  - ✅ `get_showroom` function encapsulating existing logic as a LangGraph node in `src/showroom_tool/graph_factory.py`
  - ✅ `graph_factory` function creating simple `START -> get_showroom -> END` graph
  - ✅ `process_showroom_with_graph` async function for easy graph execution
- ✅ Updated the main CLI client to invoke the graph:
  - ✅ Modified `src/showroom_tool/cli.py` to use async LangGraph processing
  - ✅ Fixed `src/showroom_tool/__main__.py` to import from correct CLI module
  - ✅ Added proper async/await support with `asyncio.run()` wrapper


### ✅ 5.1 Refactor and fix regressions - COMPLETED

**User Story:** As the developer I want this application to be easy to maintain and to be well structured, some key files are bloated ie `cli.py` 

**✅ Implemented:**

- ✅ Fixed regression where the summary line output for each module no longer lists the module filename - now shows filename in both normal and verbose modes
- ✅ Refactored `cli.py` - dramatically reduced from 684 lines to 183 lines (73% reduction)
  - ✅ Moved all cache functions to `src/showroom_tool/showroom.py` library:
    - `get_cache_directory`, `generate_cache_key`, `is_cached_repo_current`, `update_cached_repo`
  - ✅ Moved all showroom processing functions to `src/showroom_tool/showroom.py`:
    - `get_or_clone_repository`, `extract_lab_info_from_site_yaml`, `parse_navigation_file`
    - `extract_module_name_from_content`, `read_module_content`, `fetch_showroom_repository`
    - `count_words_and_lines`
  - ✅ Updated CLI to import functions from new showroom library
  - ✅ Updated LangGraph integration to use new showroom library
  - ✅ All components tested and working correctly
  - ✅ Clean separation of concerns: CLI handles UI/arguments, showroom.py handles business logic
  

### ✅ 6.1 Add the AI based Showroom Summarizer prompt builder - COMPLETED

**User Story:** As a user, I want to be able to use an LLM to perform Various summarization tasks on the showroom such as generating a 5 to 6 line summary as to the actual lab itself.

**✅ Implemented:**

- ✅ Read and understood the patterns in the prompt building code in `./sample-code/shared_utilities.py`  
  - ✅ Analyzed how `build_enhanced_system_prompt` builds prompts from Pydantic BaseModels
  - ✅ Understood field description extraction and behavioral directive patterns
- ✅ Implemented comprehensive prompt building capability:
  - ✅ Created `SHOWROOM_SUMMARY_BASE_PROMPT` with expert technical content analysis instructions
  - ✅ Built `src/showroom_tool/prompts.py` library with full prompt building utilities:
    - `extract_field_descriptions()` - Extracts Pydantic field descriptions with behavioral boundaries
    - `build_showroom_summary_prompt()` - Builds enhanced system prompts from Showroom model
    - `format_showroom_content_for_prompt()` - Formats lab content for LLM analysis
    - `build_complete_showroom_analysis_prompt()` - Complete prompt generation pipeline
- ✅ Created `--output-summary-prompt` CLI argument with rich formatted output:
  - ✅ Displays complete system prompt with field-specific instructions
  - ✅ Shows formatted user content with lab data structure
  - ✅ Provides prompt size metrics and truncation for large content
  - ✅ Beautiful console output with Rich formatting and clear sections   


### ✅ 6.2 Add the Showroom Summarizer BaseModel - COMPLETED

**User Story:** As a user, I want to be able to use an LLM to perform Various summarization tasks on the showroom such as generating a 5 to 6 line summary as to the actual lab itself.

**✅ Implemented:**

- ✅ Implemented a ShowroomSummary Pydantic BaseModel to hold the result of the Summarization:
```python
redhat_products: list[str] = Field(..., description="The Red Hat products EXPLICITLY mentioned in the content")
lab_audience: list[str] = Field(..., description="The ideal audience for the content")
lab_learning_objectives: list[str] = Field(..., description="Identify the 4 to 6 learning objectives in the content")
lab_summary: str = Field(..., description="An objective 5 to 6 sentence summary of the entire content")
```
- ✅ Added an instance of the ShowroomSummary Pydantic BaseModel to the Showroom Base Model:
  - ✅ Added `summary_output: Optional[ShowroomSummary]` field to enable AI summary storage
  - ✅ Set as Optional since summaries are generated on-demand
- ✅ Enhanced prompt building system with ShowroomSummary support:
  - ✅ Created `SHOWROOM_SUMMARY_STRUCTURED_PROMPT` specialized for structured summary generation
  - ✅ Built `build_showroom_summary_structured_prompt()` function for targeted prompts
  - ✅ Added `build_showroom_summary_generation_prompt()` for complete summary workflow
  - ✅ Maintains field-specific behavioral instructions for precise AI analysis

### 6.3 

**User Story:** As a user I need to be able to summarize the content of a showroom repo and need to dynamically build a powerful system prompt. This pattern is done well in the sample-code/shared_utilities.py.

**Tasks:**

- Examine the patterns in sample-code/shared_utilities.py especially:
  - `build_context_enhanced_system_prompt`
- Copy this library as closely as possible and reimplement a new shared_utilities for showroom
- Do not implement
  - `extract_text_from_url`
  - Any function that is not necessary except those needed to generate the system prompt


### 7

**User Story:** User needs to now pass the showroom content to a LLM with the system prompt to get the LLM feedback in s structured format

**Tasks:**

- Add the OpenAI LLM calling capability to the shared_utilities
  - Use OpenAI API `responses`
  - Ensure structured outputs in the form of `ShowroomSummary` BaseModel
    - HINT: Use context7 MCP server to 
    - Sample Code: https://platform.openai.com/docs/guides/structured-outputs?api-mode=responses
- Use variables to allow changing the following
  - `llm_provider`: LLM Provider - default to Google Gemini
  - `model`: LLM Model - default to gemini-2.5-pro
  - `temperature`: temperature - default to 0.1
- Assume LLM auth e.g API Keys will be env vars
- Add `summary` verb so the following command will work
  - `uv run showroom-tool summary https://github.com/rhpds/showroom-summit2025-lb2960-llamastack.git`

### ✅ 7.1 - COMPLETED

**User Story:** User needs a clean JSON output from summary to redirect to file, pipe to commands such as `jq`, or send to another tool

**✅ Implemented:**

- ✅ Added `--output` flag with two modes:
  - `--output verbose` (default) - rich console output with colors, progress indicators, and saved file notifications
  - `--output json` - clean JSON output suitable for piping to `jq` or other tools
- ✅ JSON mode suppresses all console output and sends errors to stderr
- ✅ Verbose mode maintains existing rich user experience
- ✅ Perfect for automation and shell scripting workflows  


### ✅ 7.2 Add more detail to `--output verbose` - COMPLETED

**User Story:** User wants a clear understanding of the lab and modules including name, word and line count from the showroom loading stage

**✅ Implemented:**

- ✅ Enhanced `--output verbose` mode with comprehensive showroom details display:
  - ✅ Colorized lab metadata (Name, Git Repo, Git Ref, Module Count)
  - ✅ Detailed module breakdown with numbered list showing:
    - ✅ Module name with Rich markup escaping for safety
    - ✅ Module filename with cyan highlighting
    - ✅ Word and line counts with thousand separators
  - ✅ Summary totals across all modules
  - ✅ Beautiful console formatting with emojis and colors
  - ✅ Only displays in verbose mode, hidden in JSON mode

### ✅ 7.2 Add more detail to `--output verbose` - COMPLETED

**User Story:** User wants a clear understanding of the lab and modules including name, word and line count from the showroom loading stage

**✅ Implemented:**

### 7.3 Reuse the `--output verbose` option with `showroom-tool fetch`

**User Story:** User wants consistent outputs for similar operations

**Tasks:**

- Ensure the output of `showroom-tool fetch` matches the initial output of `showroom-tool ... --output verbose` 
<EXAMPLE>
```txt
📚 Showroom Lab Details
============================================================
Lab Name: Experience Red Hat OpenShift Virtualization
Git Repository: https://github.com/rhpds/openshift-virt-roadshow-cnv-multi-user
Git Reference: main
Total Modules: 9

📖 Module Breakdown
------------------------------------------------------------
   1. Welcome to {lab_name}!
      File: index.adoc | 1,342 words | 77 lines
   2. Virtual Machine Management
      File: module-01-intro.adoc | 2,784 words | 185 lines
   3. Migrating Existing Virtual Machines
      File: module-02-mtv.adoc | 2,465 words | 184 lines
   4. Storage Management
      File: module-04-storage.adoc | 1,545 words | 117 lines
   5. Backup and Recovery for Virtual Machines
      File: module-05-bcdr.adoc | 1,054 words | 129 lines
   6. Template and InstanceType Management
      File: module-07-tempinst.adoc | 2,679 words | 346 lines
   7. Working with Virtual Machines and Applications
      File: module-08-workingvms.adoc | 1,190 words | 118 lines
   8. Network Management for Virtual Machines
      File: module-09-networking.adoc | 2,220 words | 223 lines
   9. Key Takeaways
      File: conclusion.adoc | 503 words | 34 lines
------------------------------------------------------------
📊 Totals: 15,782 words | 1,413 lines across 9 modules
============================================================
```
</EXAMPLE>

## ✅ Additional Enhancements Implemented

Beyond the original requirements, the following enhancements were added during development:

### ✅ Enhanced Navigation Parsing
- **Level 1 Only Processing**: Only processes top-level navigation entries (`* xref:...`)
- **Duplicate Prevention**: Uses `seen_files` set to ensure each module is read exactly once
- **Sequential Processing**: Maintains navigation order and reads each module one time

### ✅ Enhanced Module Name Extraction
- **Multi-Level Header Support**: Extracts titles from both level 1 (`= Title`) and level 2 (`== Title`) headers
- **Format Support**: Handles both prefix-style (`= Title`) and underline-style (`Title\n=====`) headers
- **Priority System**: Attempts level 1 headers first, falls back to level 2 if no level 1 found
- **Site Title Fallback**: Uses site title for start page module when no content header found

### ✅ Enhanced BaseModel Structure
- **Filename Tracking**: Added `filename` field to ShowroomModule for full traceability
- **Content Metrics**: Built-in word and line counting for meaningful content analysis
- **Rich Typing**: Modern Python 3.12+ type annotations throughout

### ✅ Enhanced CLI Output
- **Beautiful Colorization**: Rich console output with:
  - Bright white numbering for clear module indexing
  - Bold module names for easy identification
  - Cyan filenames in verbose mode
  - Dim content metrics for unobtrusive display
  - Colorful summary header with logical information hierarchy
- **Meaningful Metrics**: Displays word count and line count instead of character count
- **Verbose Mode**: Detailed processing information with filename visibility

### ✅ Technical Excellence
- **Package Structure**: Proper src-layout with `src/showroom_tool/` and `src/config/`
- **Entry Point**: Installable CLI tool via `uv pip install -e .`
- **Error Handling**: Graceful handling of missing files, git errors, and malformed content
- **Progress Indicators**: Rich progress bars for git operations
- **Rich Markup Safety**: Proper escaping to handle special characters in module titles

## Status Summary

All original requirements **COMPLETED** ✅:
- ✅ Requirement 1: Repository setup and dependencies
- ✅ Requirement 2: Showroom Pydantic BaseModel  
- ✅ Requirement 2.1: ShowroomModule BaseModel
- ✅ Requirement 2.2: Codebase cleanup
- ✅ Requirement 3.1: Showroom Fetcher
- ✅ Requirement 4.1: Basic LangGraph Agentic AI Entry Point
- ✅ Requirement 5.1: Refactor and fix regressions
- ✅ Requirement 6.1: AI-based Showroom Summarizer prompt builder
- ✅ Requirement 6.2: Showroom Summarizer BaseModel
- ✅ Requirement 6.3: Shared utilities library for system prompt generation
- ✅ Requirement 7: Complete LLM integration with summary command
- ✅ Requirement 7.1: Clean JSON output for automation and piping
- ✅ Requirement 7.2: Enhanced verbose output with detailed lab and module information

**Additional enhancements** implemented for superior user experience and robustness.

The showroom-tool is now a **professional-grade CLI application** ready for production use in technical enablement scenarios.

## Usage Examples

```bash
# Basic usage
showroom-tool https://github.com/example/my-showroom

# With specific branch and verbose output  
showroom-tool --repo https://github.com/example/my-showroom --ref develop --verbose

# AI-powered summary generation
showroom-tool summary https://github.com/example/my-showroom

# Clean JSON output for automation/piping
showroom-tool summary https://github.com/example/my-showroom --output json | jq
showroom-tool summary https://github.com/example/my-showroom --output json > summary.json

# With LLM options
showroom-tool summary https://github.com/example/my-showroom --llm-provider gemini --temperature 0.2

# Display AI prompt template
showroom-tool prompt

# Help
showroom-tool --help
showroom-tool summary --help
```

**Production Ready**: Complete LLM integration with structured output, automation support, and professional CLI experience.
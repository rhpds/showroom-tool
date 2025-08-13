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

- ✅ Created the Showroom BaseModel in `./src/showroom_tool/basemodels.py`
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

- ✅ Created the ShowroomModule BaseModel in `./src/showroom_tool/basemodels.py`
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
  - ✅ `ShowroomState` Pydantic BaseModel for LangGraph state management in `src/showroom_tool/basemodels.py`
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

### ✅ 6.3 Implement Shared Utilities for System Prompt Generation - COMPLETED

**User Story:** As a user I need to be able to summarize the content of a showroom repo and need to dynamically build a powerful system prompt. This pattern is done well in the sample-code/shared_utilities.py.

**✅ Implemented:**

- ✅ Examined and analyzed patterns in sample-code/shared_utilities.py especially:
  - ✅ `build_context_enhanced_system_prompt` pattern for enhanced prompt building
  - ✅ `process_content_with_structured_output` for LLM integration
  - ✅ Field description extraction and prompt enhancement techniques
- ✅ Created comprehensive `src/showroom_tool/shared_utilities.py` library with:
  - ✅ `initialize_llm()` - LLM client initialization with multi-provider support (Gemini, OpenAI, local)
  - ✅ `extract_field_descriptions()` - Pydantic field description extraction for prompts
  - ✅ `build_enhanced_system_prompt()` - Enhanced prompt building with field instructions
  - ✅ `build_context_enhanced_system_prompt()` - Context-aware prompt enhancement
  - ✅ `process_content_with_structured_output()` - Core LLM processing with structured outputs
  - ✅ `save_structured_output()` and model-specific save functions
  - ✅ `format_showroom_content_for_prompt()` - Showroom data formatting for LLM analysis
  - ✅ Complete prompt building functions for Summary, Review, and Description workflows
- ✅ **Excluded** non-essential functions as requested:
  - ✅ Did not implement `extract_text_from_url` (not needed for showroom processing)
  - ✅ Focused only on prompt generation and LLM integration functions
- ✅ Added multi-provider LLM support with structured outputs using OpenAI Responses API
- ✅ Integrated seamlessly with existing Pydantic BaseModels for all analysis types


### ✅ 7 Enable the content to be passed to an LLM - COMPLETED

**User Story:** User needs to now pass the showroom content to a LLM with the system prompt to get the LLM feedback in a structured format

**✅ Implemented:**

- ✅ Added comprehensive OpenAI LLM calling capability to shared_utilities:
  - ✅ Uses OpenAI API `responses` with `beta.chat.completions.parse()` for structured outputs
  - ✅ Ensures structured outputs in the form of `ShowroomSummary`, `ShowroomReview`, and `CatalogDescription` BaseModels
  - ✅ Implemented robust error handling and response validation
- ✅ Added configurable LLM parameters with environment variable support:
  - ✅ `llm_provider`: LLM Provider - defaults to Google Gemini (as requested)
  - ✅ `model`: LLM Model - defaults to `gemini-2.0-flash-exp` for Gemini
  - ✅ `temperature`: temperature - defaults to 0.1 (as requested)
  - ✅ Multi-provider support: Gemini, OpenAI, and local LLM servers
- ✅ Implemented environment variable authentication:
  - ✅ `GEMINI_API_KEY` for Google Gemini provider
  - ✅ `OPENAI_API_KEY` for OpenAI provider
  - ✅ `LOCAL_OPENAI_API_KEY`, `LOCAL_OPENAI_BASE_URL`, `LOCAL_OPENAI_MODEL` for local providers
- ✅ Added `summary` command functionality:
  - ✅ `uv run showroom-tool summary https://github.com/rhpds/showroom-summit2025-lb2960-llamastack.git` works as requested
  - ✅ Complete CLI integration with rich output formatting and workspace saving

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

### ✅ 7.3 Reuse the `--output verbose` option with `showroom-tool fetch` - COMPLETED

**User Story:** User wants consistent outputs for similar operations

**✅ Implemented:**

- ✅ Modified `handle_fetch_command` to use `display_showroom_details()` for rich verbose output
- ✅ Added `--output` flag to common arguments (supports both `verbose` and `json`)
- ✅ Removed duplicate `--output` flag from LLM-specific arguments to avoid conflicts
- ✅ Added JSON output support to fetch command for automation and piping
- ✅ Ensured consistent output format between `fetch` and `summary --output verbose` commands

**Verified Output Format:**
```txt
📚 Showroom Lab Details
============================================================
Lab Name: Summit 2025 - LB2906 - Getting Started with Llamastack
Git Repository: https://github.com/rhpds/showroom-summit2025-lb2960-llamastack.git
Git Reference: main
Total Modules: 9

📖 Module Breakdown
------------------------------------------------------------
   1. AI Applications and Llama Stack: A practical workshop
      File: index.adoc | 615 words | 14 lines
   2. [NOTE]
      File: 01-Getting-Started.adoc | 1,553 words | 230 lines
   3. Module 2: Llama Stack Inference Basics
      File: 02_Lllamastack_Inference_Basics.adoc | 499 words | 34 lines
   4. Module 3: Retrieval-Augmented Generation (RAG) Basics
      File: 03_RAG_Agent_Basic_Example.adoc | 276 words | 15 lines
   5. Module 4: Agents and Tools
      File: 04_Agents_and_Tools.adoc | 283 words | 14 lines
   6. Module 5: Exploring ReAct Agents and Tool Use
      File: 05_React_Agents.adoc | 1,329 words | 53 lines
   7. Module 6: Working with MCP Servers
      File: 06_MCP_Servers_Intro.adoc | 369 words | 14 lines
   8. Module 7: Putting it all together
      File: 07_Putting_It_All_Together.adoc | 639 words | 30 lines
   9. Credentials and Useful URLs
      File: Creds-URLs-Resources.adoc | 80 words | 23 lines
------------------------------------------------------------
📊 Totals: 5,643 words | 427 lines across 9 modules
============================================================
```

### ✅ 8 Add a Review capability - COMPLETED

**User Story:** User is very happy with the existing `summary` capability and wants a similar `review` capability focussed more on reviewing the content. For consistency they want it to work in the same way as summary with the same command line options 

**✅ Implemented:**

- ✅ Created the ShowroomReview BaseModel in `./src/showroom_tool/basemodels.py` with scoring fields:
```python
completeness: float = Field(..., ge=0, le=10, description="Score for completeness of content")
completeness_feedback: str = Field(..., description="Constructive feedback regarding completeness of content")
clarity: float = Field(..., ge=0, le=10, description="Score for clarity of instructions")
clarity_feedback: str = Field(..., description="Constructive feedback regarding clarity of content")
technical_detail: float = Field(..., ge=0, le=10, description="Score for technical detail")
technical_detail_feedback: str = Field(..., description="Constructive feedback regarding technical details of content")
usefulness: float = Field(..., ge=0, le=10, description="Score for usefulness to target audience")
usefulness_feedback: str = Field(..., description="Constructive feedback regarding usefulness of content")
business_value: float = Field(..., ge=0, le=10, description="Score for business value of content")
business_value_feedback: str = Field(..., description="Constructive feedback regarding business value of content")
review_summary: str = Field(..., description="3-4 sentence overall review summary")
```
- ✅ Added `review_output: ShowroomReview | None` field to Showroom BaseModel for AI-generated reviews
- ✅ Extended `shared_utilities.py` with review-specific functions following summary patterns:
  - ✅ `save_review_to_workspace()` - saves review outputs to workspace
  - ✅ `build_showroom_review_prompt()` - builds complete review system prompts
- ✅ Extended `prompts.py` with review-specific prompt functions:
  - ✅ `SHOWROOM_REVIEW_BASE_PROMPT` and `SHOWROOM_REVIEW_STRUCTURED_PROMPT` constants
  - ✅ `build_showroom_review_structured_prompt()` - builds structured review prompts
  - ✅ `build_showroom_review_generation_prompt()` - complete review prompt pipeline
- ✅ Added `review` command to CLI with identical functionality to summary:
  - ✅ Same command line options: `--repo`, `--ref`, `--verbose`, `--output`, `--llm-provider`, etc.
  - ✅ Support for both verbose and JSON output modes
  - ✅ Detailed showroom display in verbose mode
  - ✅ AI-powered review generation with structured scoring and feedback
  - ✅ Workspace saving functionality
- ✅ Complete LLM integration ready for production use

### ✅ 8.1 Refactor and clean up CLI UI - COMPLETED

**User Story:** User wants a cleaner and more consistent cli UX

**✅ Implemented:**

- ✅ Removed redundant `showroom-tool fetch` command as fetch is implicit in both `summary` and `review`
- ✅ Removed the standalone `prompt` command verb
- ✅ Added `--output-prompt` argument to both `summary` and `review` commands:
  - ✅ `showroom-tool summary --output-prompt` - displays summary analysis prompt template
  - ✅ `showroom-tool review --output-prompt` - displays review analysis prompt template
- ✅ Streamlined CLI to only two core commands: `summary` and `review`
- ✅ Enhanced error handling for invalid/missing commands with helpful guidance
- ✅ Updated command dispatcher and removed unused functions
- ✅ Maintained all existing functionality while simplifying the interface

**CLI Structure Changes:**
- **Before:** `fetch`, `summary`, `review`, `prompt` commands
- **After:** `summary`, `review` commands with `--output-prompt` flags
- **Cleaner UX:** Users now have a consistent interface with dedicated prompt viewing within each command

### ✅ 9.1 Add Description Generator - COMPLETED

**User Story:** User wants a build a Catalog Entry for the Lab which accurately describes the item based on its showroom lab content

**✅ Implemented:**

- ✅ Created the CatalogDescription Pydantic BaseModel in `./src/showroom_tool/basemodels.py`:
```python
headline: str = Field(..., description="Concise summary of the catalog item")
products: list[str] = Field(..., description="List of Red Hat Products covered in the lab")
intended_audience_bullets: list[str] = Field(..., description="2 to 4 audiences who would benefit")
lab_bullets: list[str] = Field(..., description="3 to 6 short 1 liners of the key takeaways of the lab")
```
- ✅ Added `description_output: CatalogDescription | None` field to Showroom BaseModel for AI-generated descriptions
- ✅ Extended `prompts.py` with description-specific prompt functions:
  - ✅ `SHOWROOM_DESCRIPTION_BASE_PROMPT` and `SHOWROOM_DESCRIPTION_STRUCTURED_PROMPT` constants
  - ✅ `build_showroom_description_structured_prompt()` - builds structured description prompts
  - ✅ `build_showroom_description_generation_prompt()` - complete description prompt pipeline
- ✅ Extended `shared_utilities.py` with description-specific functions following summary/review patterns:
  - ✅ `save_description_to_workspace()` - saves description outputs to workspace
  - ✅ `build_showroom_description_prompt()` - builds complete description system prompts
- ✅ Added `description` command to CLI with identical functionality to summary and review:
  - ✅ Same command line options: `--repo`, `--ref`, `--verbose`, `--output`, `--llm-provider`, etc.
  - ✅ Support for both verbose and JSON output modes
  - ✅ Detailed showroom display in verbose mode
  - ✅ AI-powered description generation with structured catalog fields
  - ✅ Workspace saving functionality
  - ✅ `--output-prompt` support for viewing description analysis templates
- ✅ Complete LLM integration ready for production use

### ✅ 9.2 Add Jinja 2 based template capability to be used via `--output adoc` - COMPLETED

**User Story:** User wants to be able to generate human friendly outputs in asciidoc from BaseModels ie a description, summary, review capability

**✅ Implemented:**

- ✅ Create a `./templates` directory for jinja templates
- ✅ Created a `./src/showroom_tool/outputs.py`
  - ✅ Create the necessary functions/classes to output when cli option is `--output adoc`:
    - ✅ Consume the current base model ie whilst doing `showroom-tool summary | review | description ... --output adoc`
    - ✅ Consume the matching Asciidoc template eg `CatalogDescription` BaseModel consumes `./templates/CatalogDescription.adoc.j2`
    - ✅ Create a simple `./templates/CatalogDescription.adoc.j2` that simply lists the vars with example header and list elements
    - ✅ stream the output to STDOUT
- ✅ Added jinja2>=3.0.0 dependency to pyproject.toml
- ✅ Extended CLI --output argument choices to include "adoc"
- ✅ Implemented template rendering for ShowroomSummary, ShowroomReview, and CatalogDescription
- ✅ Added graceful error handling for missing Jinja2 dependency
- ✅ Templates include lab metadata (name, git_url, git_ref) and timestamp


### ✅ 10.1 Improve cli consistency between `--show-prompt` and `--output` - COMPLETED

**User Story:** User wants an improved UX, finds `--show-prompt` inconsistent with `--output`

**✅ Implemented:**

- ✅ Changed the flag `--show-prompt` to `--output-prompt` for better CLI consistency
- ✅ Updated all CLI argument definitions and help text
- ✅ Updated all command handlers to use the new flag name
- ✅ Updated all documentation, comments, and usage examples

### ✅ 10.2 Document the Prompt Engineering Components - COMPLETED

**User Story:** User wants to be able to easily modify the overall prompt and needs documentation as to the flow and process and how for example they might guide the LLM to the correct value in say in a BaseModel

**✅ Implemented:**

- ✅ Created a `./docs` directory
- ✅ Created a comprehensive `./docs/prompting-guide.md` including:
  - ✅ Complete flow of how prompts are assembled with detailed Mermaid diagram
  - ✅ Explanation of all key components that developers and prompt engineers can modify
  - ✅ Detailed explanation of BaseModel `description` fields and their role as AI instructions
  - ✅ Best practices for writing effective field descriptions
  - ✅ Advanced customization techniques and debugging guidance
  - ✅ Testing methods using `--output-prompt` flag
  - ✅ Performance considerations and troubleshooting tips
- ✅ Updated the `README.md` with prominent documentation section highlighting the prompt engineering guide

### ✅ 11.1 Refactor LangGraph nodes for future extensibility - COMPLETED

**User Story:** User wants to be able to easily extend the application via LangGraph in the future and finds the single node implementation constricting

**✅ Implemented:**

- ✅ Refactored `src/showroom_tool/graph_factory.py` to a two-node linear workflow:
  - ✅ `get_showroom`: fetches and populates the `Showroom` BaseModel from CLI-configured inputs
  - ✅ `process_showroom`: executes the verb (`summary | review | description`) using LLM, returns structured output
- ✅ Added edges: `get_showroom -> process_showroom -> END`
- ✅ Extended `ShowroomState` with `command`, `llm_provider`, `model`, `temperature`
- ✅ `graph_factory()` supports fetch-only or full processing; `process_showroom_with_graph()` accepts verb and LLM options
- ✅ Updated CLI to use graph processing for `summary`, `review`, `description` commands
- ✅ Maintained JSON/verbose/AsciiDoc output modes

### ✅ 11.2 Add a local file option `--dir` for when the Showroom repo is already cloned locally - COMPLETED

**User Story:** User wants to be able to run `showroom-tool` against a local copy of the repo to avoid having the commit/push to see the impact of their work.

**✅ Implemented:**

- ✅ Added CLI option `--dir <PATH>` allowing omission of git URL and using a local clone instead
  - ✅ Supports absolute and relative paths to the repo root
  - ✅ Ignores git ref/checkout (consumes repo "as is")
  - ✅ Bypasses caching/cloning; uses the directory directly
- ✅ Extended LangGraph `ShowroomState` with `local_dir` and plumbed through `get_showroom`
- ✅ Updated `fetch_showroom_repository` to accept `local_dir` and validate `.git`
- ✅ Enhanced CLI validation: require either `<repo_url>`/`--repo` or `--dir`; printed clear error messages when missing
- ✅ All output modes (verbose/json/adoc) work unchanged


### ✅ 11.3 Create a Release `0.1.0` - COMPLETED

**User Story:** User wants to be able to know which release of `showroom-tool` they are running

**✅ Implemented:**

- ✅ Ran ruff and ensured clean linting
- ✅ Committed all changes and merged feature branch into `main`
- ✅ Created git tag and GitHub release

**Release Checklist (example commands):**

```bash
# Ensure clean working tree
git status

# Run quality checks
uv run ruff check . --fix

# Merge feature into main (from feature branch)
git checkout main
git pull
# If using a feature branch
git merge --no-ff feature/optional-prompt-file -m "Merge feature: prompts overrides and versioned outputs"

# Tag and push
git tag -a v0.1.0 -m "showroom-tool 0.1.0"
git push origin main --tags

# Create GitHub release (manual via UI or gh CLI)
# gh release create v0.1.0 --title "showroom-tool 0.1.0" --notes "Initial release"
```

### ✅ 11.5 Add tests with `pytest` where appropriate - COMPLETED

**User Story:** User wants to ensure the growing repo has adequate testing before extending

**✅ Implemented:**

- ✅ Added tests in `tests/`:
  - ✅ Graph fetch-only flow (`tests/test_graph_factory.py`)
  - ✅ Local directory showroom fetch (`tests/test_showroom_fetch_local_dir.py`)
  - ✅ Outputs module availability (`tests/test_outputs.py`)
- ✅ Verified `uv run pytest -q` runs cleanly


### ✅ 11.6 Add support for a `-V` and `--version` arg ie `showroom-tool --version` - COMPLETED

**User Story:** User wants to be able to know which release of `showroom-tool` they are running

**✅ Implemented:**

- ✅ Introduced `showroom_tool.__version__` (sourced from `src/showroom_tool/__init__.py`)
- ✅ Added global flags `-V` and `--version` to print version and exit
- ✅ Example: `showroom-tool --version` → `showroom-tool 0.1.0`


### ✅ 11.7 Add showroom-tool version to output - COMPLETED

**User Story:** User wants to be able to know which release of `showroom-tool` generated the output

**✅ Implemented:**

- ✅ Added `version` to Jinja render context in `src/showroom_tool/outputs.py` using `showroom_tool.__version__`
- ✅ Updated all AsciiDoc templates to include version in the attribution line:
  - `_Generated by showroom-tool <VERSION> on YYYY-MM-DD HH:MM:SS_`


### ✅ 11.8 Extend prompts.py to have a per action temperature - COMPLETED 

**User Story:** User wants to be able to set different temperatures for different actions such as `summary`, `review`, and `description`.

**✅ Implemented:**

- ✅ Added `get_temperature_for_action()` in `src/showroom_tool/prompts.py` with precedence:
  1) CLI `--temperature`
  2) `SHOWROOM_<ACTION>_TEMPERATURE` env vars (`SHOWROOM_SUMMARY_TEMPERATURE`, `SHOWROOM_REVIEW_TEMPERATURE`, `SHOWROOM_DESCRIPTION_TEMPERATURE`)
  3) `LLM_TEMPERATURE`
  4) default `0.1`
- ✅ Integrated per-action temperature in `src/showroom_tool/graph_factory.py` so each command uses the resolved temperature

### ✅ 11.9 Add support for a `--prompts-file` option extending the tools functionality - COMPLETED

**User Story:** User wants to be able to try new prompts and temperatures without losing the defaults in `prompts.py`

**✅ Implemented:**

- ✅ Added `--prompts-file <FILE>` to all verbs; supports `.py` and `.json` files
- ✅ Implemented loader in `src/showroom_tool/prompts.py` (`load_prompts_overrides`)
- ✅ Overrides supported:
  - ✅ Prompt strings: `SHOWROOM_*_BASE_PROMPT`, `SHOWROOM_*_STRUCTURED_PROMPT`
  - ✅ Temperatures: `SHOWROOM_SUMMARY_TEMPERATURE`, `SHOWROOM_REVIEW_TEMPERATURE`, `SHOWROOM_DESCRIPTION_TEMPERATURE`
- ✅ Missing keys fall back to defaults in `prompts.py`; CLI `--temperature` still overrides
- ✅ Wired into processing via `ShowroomState.prompts_file` and graph load on start


### ✅ 11.10 Refactor prompts - COMPLETED

**User Story:** User wants to simplify the prompts by getting rid of all references to `SHOWROOM_*_BASE_PROMPT` for simplicity and ease of end user customization

**✅ Implemented:**

- ✅ Removed all `SHOWROOM_*_BASE_PROMPT` constants
- ✅ Introduced unified `SHOWROOM_*_BASE_SYSTEM_PROMPT` constants and accessors
- ✅ Updated prompt builders to use base system prompts
- ✅ Ensured `--output-prompt` reflects overrides and new names
- ✅ Updated documentation in `docs/prompting-guide.md`


### ✅ 11.11 Refactor prompting part 2 - COMPLETED

**User Story:** User wants to separate the actual prompts, temperature, and other globals from the prompt building logic and make it more intuitive, and consolidate BaseModels into the main package.

**✅ Implemented:**

- ✅ Consolidate BaseModels into the main package and remove the extra package:
  - ✅ Move `src/config/basemodels.py` to `src/showroom_tool/basemodels.py`
  - ✅ Remove the `src/config/` package entirely
  - ✅ Update all imports to `from showroom_tool.basemodels import ...`

- ✅ Created `config/prompts.py` for prompts and temperatures (moved out of code)
  - ✅ `SHOWROOM_*_BASE_SYSTEM_PROMPT` now defined here (project-level)
  - ✅ `SHOWROOM_*_TEMPERATURE` now defined here (project-level)
- ✅ Added built-in defaults at `src/showroom_tool/config/defaults.py` used when no overrides are present
- ✅ Implemented `prompt_builder` auto-discovery and precedence in CLI:
  - ✅ Project config: `./config/prompts.py` (and `./config/settings.py` when added)
  - ✅ User config: `~/.config/showroom-tool/prompts.py`, `~/.config/showroom-tool/settings.py`
  - ✅ Built-in defaults: `src/showroom_tool/config/defaults.py`
- ✅ Kept `src/showroom_tool/prompts.py` as the public API; it now imports defaults and applies overrides
- ✅ Ensured `project_root / "src"` is used in dev fallbacks to avoid path collisions

- ✅ Development path hygiene:
  - ✅ Ensure all local fallbacks insert only `project_root / "src"` into `sys.path` (avoid future top-level name collisions)


**Usage Examples (unchanged):**
```bash
# Generate AsciiDoc summary
showroom-tool summary --repo https://github.com/example/lab --output adoc

# Generate AsciiDoc review  
showroom-tool review --repo https://github.com/example/lab --output adoc

# Generate AsciiDoc catalog description
showroom-tool description --repo https://github.com/example/lab --output adoc
```


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
 - **Package Structure**: Proper src-layout with `src/showroom_tool/` (BaseModels consolidated here); project-level `config/` for prompts/settings overrides
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
- ✅ Requirement 7.3: Consistent verbose output format for fetch command
- ✅ Requirement 8: AI-powered review capability with structured scoring and feedback
- ✅ Requirement 8.1: Refactored and cleaned up CLI UI for better user experience
- ✅ Requirement 9.1: AI-powered catalog description generation capability
- ✅ Requirement 9.2: Jinja2-based AsciiDoc template output for human-friendly documentation
- ✅ Requirement 10.1: Improved CLI consistency with --output-prompt flag
- ✅ Requirement 10.2: Comprehensive prompt engineering documentation with visual guides

**Additional enhancements** implemented for superior user experience and robustness.

The showroom-tool is now a **professional-grade CLI application** ready for production use in technical enablement scenarios.

## Usage Examples

```bash
# AI-powered summary generation
showroom-tool summary https://github.com/example/my-showroom

# AI-powered review generation with detailed scoring and feedback
showroom-tool review https://github.com/example/my-showroom

# AI-powered catalog description generation
showroom-tool description https://github.com/example/my-showroom

# With specific branch and verbose output  
showroom-tool summary --repo https://github.com/example/my-showroom --ref develop --verbose
showroom-tool review --repo https://github.com/example/my-showroom --ref develop --verbose
showroom-tool description --repo https://github.com/example/my-showroom --ref develop --verbose

# Clean JSON output for automation/piping
showroom-tool summary https://github.com/example/my-showroom --output json | jq
showroom-tool summary https://github.com/example/my-showroom --output json > summary.json
showroom-tool review https://github.com/example/my-showroom --output json | jq
showroom-tool review https://github.com/example/my-showroom --output json > review.json
showroom-tool description https://github.com/example/my-showroom --output json | jq
showroom-tool description https://github.com/example/my-showroom --output json > description.json

# With LLM options
showroom-tool summary https://github.com/example/my-showroom --llm-provider gemini --temperature 0.2
showroom-tool review https://github.com/example/my-showroom --llm-provider openai --temperature 0.1
showroom-tool description https://github.com/example/my-showroom --llm-provider gemini --temperature 0.1

# Display AI prompt templates
showroom-tool summary --output-prompt
showroom-tool review --output-prompt
showroom-tool description --output-prompt

# Help
showroom-tool --help
showroom-tool summary --help
showroom-tool review --help
showroom-tool description --help
```

**Production Ready**: Complete LLM integration with structured output, automation support, and professional CLI experience.
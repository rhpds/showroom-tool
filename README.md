# Showroom Tool

A Python-based CLI tool designed to summarize, review, and validate technical lab and demo content. Primarily intended for use in technical enablement and customer demonstration scenarios by technical sellers.

The tool processes content provided as one or more AsciiDoc files typically stored in remote `antora` formatted repositories or local git clones. Labs and demos are made available via a Catalog called RHDP and its associated repository which contains YAML defined Catalog Items (CIs).

## Features

- **AI-Powered Analysis**: Generate summaries, reviews, and catalog descriptions using LLM
- **Repository Processing**: Clone and analyze showroom repositories with intelligent caching
- **Content Analysis**: Parse AsciiDoc modules and extract structured data
- **Multi-Provider LLM Support**: Works with Gemini, OpenAI, and local LLM servers
- **Structured Outputs**: JSON and verbose output modes for automation and human consumption
- **Smart Caching**: Avoid repeated clones with automatic cache invalidation
- **CLI Interface**: Easy-to-use command-line interface with rich, colorized output
- **AsciiDoc Support**: Native support for AsciiDoc formatted content with header extraction
- **Performance**: ~50% faster on subsequent runs thanks to intelligent caching
- **Flexible Options**: Support for different git refs, custom cache directories, and cache control
- **No Installation Required**: Use the wrapper script without `pip install`

## Quick Start

### Prerequisites

- **Python 3.12+ or Python 3.13** (recommended)
- **Git** (for repository operations)
- Choose your preferred toolchain:
  - **Option A**: `uv` (modern, fast Python package manager)
  - **Option B**: Standard `pip` and `venv`

### Installation

#### Option A: Using `uv` (Recommended)

`uv` is a fast Python package manager that handles virtual environments automatically.

1. **Install uv** (if not already installed):
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

   # Or with pip
   pip install uv
   ```

2. **Clone and install**:
   ```bash
   git clone <repository-url>
   cd showroom-tool

   # Create virtual environment and install in one step
   uv sync
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

#### Option B: Using Standard Python/pip

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd showroom-tool
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Using Python 3.13 (recommended)
   python3.13 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Or Python 3.12
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install the package**:
   ```bash
   pip install -e .
   ```

### Verify Installation

```bash
showroom-tool --help
```

## Usage

### Option 1: Quick Start (No Installation Required)

If you prefer not to install the package, you can use the included wrapper script directly:

```bash
# Clone the repository
git clone <repository-url>
cd showroom-tool

# Create virtual environment and install dependencies
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt  # or pip install -r requirements.txt

# Use the clean wrapper script syntax
python showroom-tool.py --help
python showroom-tool.py summary https://github.com/example/my-showroom
python showroom-tool.py review https://github.com/example/my-showroom
python showroom-tool.py description https://github.com/example/my-showroom
```

### Option 2: Installed Package Commands

After installation with `pip install -e .`, use the installed commands:

```bash
# AI-powered summary generation
showroom-tool summary https://github.com/example/my-showroom

# AI-powered review with scoring and feedback
showroom-tool review https://github.com/example/my-showroom

# AI-powered catalog description generation
showroom-tool description https://github.com/example/my-showroom

# Use specific branch or tag
showroom-tool summary https://github.com/example/my-showroom --ref develop

# Enable verbose output for detailed processing
showroom-tool summary https://github.com/example/my-showroom --verbose

# Clean JSON output for automation and piping
showroom-tool summary https://github.com/example/my-showroom --output json | jq

# View AI prompt templates
showroom-tool summary --output-prompt
showroom-tool review --output-prompt
showroom-tool description --output-prompt
```

### LLM Configuration

The tool supports multiple LLM providers and defaults to Google Gemini. Configure using environment variables:

```bash
# Google Gemini (default) - no additional setup needed for provider selection
export GEMINI_API_KEY="your-gemini-api-key"

# OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# Local LLM server (OpenAI-compatible)
export LOCAL_OPENAI_API_KEY="your-local-api-key"
export LOCAL_OPENAI_BASE_URL="http://localhost:8000/v1"
export LOCAL_OPENAI_MODEL="your-local-model"

# Optional: Customize model and temperature
export GEMINI_MODEL="gemini-2.0-flash-exp"  # default
export OPENAI_MODEL="gpt-4o-2024-08-06"     # default
export LLM_TEMPERATURE="0.1"                # default

# Per-action temperatures (optional; override global)
export SHOWROOM_SUMMARY_TEMPERATURE="0.1"
export SHOWROOM_REVIEW_TEMPERATURE="0.1"
export SHOWROOM_DESCRIPTION_TEMPERATURE="0.1"
```

Choose your LLM provider with command line options:
```bash
# Use specific provider
python showroom-tool.py summary <repo-url> --llm-provider gemini
python showroom-tool.py summary <repo-url> --llm-provider openai
python showroom-tool.py summary <repo-url> --llm-provider local

# Override prompts/temperatures from a file (optional)
showroom-tool summary <repo-url> --prompts-file ./my_prompts_overrides.py
showroom-tool review <repo-url> --prompts-file ./overrides.json
```

### Example Output

```
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
   2. Module 1: Getting Started
      File: 01-Getting-Started.adoc | 1,553 words | 230 lines
   3. Module 2: Llama Stack Inference Basics
      File: 02_Lllamastack_Inference_Basics.adoc | 499 words | 34 lines
   ...
============================================================

🤖 AI Analysis Results:
{
  "redhat_products": ["Red Hat OpenShift AI", "Llama Stack"],
  "lab_audience": ["AI/ML developers", "Data scientists", "DevOps engineers"],
  "lab_learning_objectives": [
    "Set up and configure Llama Stack environment",
    "Implement basic inference with Llama models",
    "Build RAG applications with Llama Stack",
    "Deploy AI applications on OpenShift"
  ],
  "lab_summary": "This hands-on lab introduces participants to Llama Stack..."
}
```

### Caching System

The tool includes an intelligent caching system that:
- **Stores repositories** in `~/.showroom-tool/cache/` by default
- **Checks for updates** automatically and refreshes when needed
- **Supports different refs** with separate cache entries
- **Improves performance** by ~50% on subsequent runs

Cache is managed automatically, but you can control it:
- `--no-cache`: Disable caching completely
- `--cache-dir <path>`: Use custom cache location
- Cache is invalidated automatically when remote repository has updates

## Development

### Development Setup

#### Using uv (Recommended)

```bash
git clone <repository-url>
cd showroom-tool

# Create development environment
uv venv
source .venv/bin/activate
uv pip install -e .

# Install development dependencies (if available)
# uv pip install -e ".[dev]"
```

#### Using pip

```bash
git clone <repository-url>
cd showroom-tool

# Create development environment
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e .

# Install development dependencies (if available)
# pip install -e ".[dev]"
```

### Development Workflow

- **Code formatting**: `ruff format .`
- **Linting**: `ruff check . --fix`
- **Testing**: `pytest` (when tests are available)
- **Install changes**: `uv pip install -e . --force-reinstall` or `pip install -e . --force-reinstall`

### Project Structure

```
showroom-tool/
├── src/                         # Source code (Python package layout)
│   ├── showroom_tool/          # Main CLI package
│   │   ├── __init__.py         # Package initialization
│   │   ├── __main__.py         # Module entry point
│   │   └── cli.py              # CLI implementation and core logic
│   └── config/                 # Configuration package
│       ├── __init__.py         # Config package init
│       └── basemodels.py       # Pydantic BaseModels (Showroom, ShowroomModule)
├── specs/                       # Project specifications
│   ├── requirements.md         # Detailed requirements and status
│   ├── structure.md            # Project structure documentation
│   ├── tech.md                 # Technology stack information
│   └── product.md              # Product overview
├── sample-code/                # Example/sample code (ignored by linter)
├── pyproject.toml              # Project configuration, dependencies, and build
├── README.md                   # This file
└── .gitignore                  # Git ignore patterns
```

### Technology Stack

- **Programming Language**: Python 3.12+ (3.13 recommended)
- **CLI Framework**: `argparse` with `rich` for enhanced output
- **Data Models**: `pydantic` v2 for structured data validation
- **Git Operations**: `GitPython` for repository management
- **YAML Processing**: `pyyaml` for configuration file parsing
- **Package Management**: `uv` (recommended) or `pip`
- **Code Quality**: `ruff` for linting and formatting
- **Build System**: `hatchling` via `pyproject.toml`

## Advanced Usage

### Working with Different Git References

```bash
# Use specific branch
showroom-tool <repo-url> --ref feature-branch

# Use specific tag
showroom-tool <repo-url> --ref v1.2.3

# Use specific commit
showroom-tool <repo-url> --ref a1b2c3d4
```

### Cache Management

```bash
# Check current cache
ls ~/.showroom-tool/cache/

# Clear cache manually (if needed)
rm -rf ~/.showroom-tool/cache/

# Use temporary location
showroom-tool <repo-url> --cache-dir /tmp/temp-cache
```

### Running as Python Module

```bash
# Method 1: Clean wrapper script (recommended)
python showroom-tool.py --help
python showroom-tool.py summary https://github.com/example/my-showroom
python showroom-tool.py review https://github.com/example/my-showroom --verbose
python showroom-tool.py description https://github.com/example/my-showroom --output json

# Method 2: Direct module execution
python -m src.showroom_tool summary https://github.com/example/my-showroom
python -m src.showroom_tool --help
```

## Installation Troubleshooting

### Common Issues

**ModuleNotFoundError**: If you get import errors after installation:
```bash
# Reinstall in development mode
uv pip install -e . --force-reinstall
# or
pip install -e . --force-reinstall
```

**Git Command Not Found**: Ensure Git is installed:
```bash
# macOS
brew install git

# Ubuntu/Debian
sudo apt-get install git

# Windows
# Download from https://git-scm.com/
```

**Permission Errors**: On macOS/Linux, you might need:
```bash
# Ensure proper permissions
chmod +x ~/.local/bin/showroom-tool
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the existing code style
4. Test your changes with real repositories
5. Run linting: `ruff check . --fix`
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style Guidelines

- Use `ruff` for formatting and linting
- Follow existing patterns in the codebase
- Add type hints to all functions
- Use descriptive variable names
- Add docstrings to public functions

## Current Status

✅ **Completed Features:**
- Repository cloning and caching system
- AsciiDoc content parsing and module extraction
- Pydantic BaseModel data structures (`Showroom`, `ShowroomModule`, `ShowroomSummary`, `ShowroomReview`, `CatalogDescription`)
- CLI with argument parsing and rich output
- Git reference support (branches, tags, commits)
- Comprehensive error handling
- **AI-Powered Analysis**: Complete LLM integration with structured outputs
- **Summary Generation**: Extract Red Hat products, audience, objectives, and summaries
- **Review Capabilities**: Score and provide feedback on completeness, clarity, technical detail, usefulness, and business value
- **Catalog Descriptions**: Generate compelling headlines, product lists, audience bullets, and key takeaways
- **Multi-Provider LLM Support**: Gemini (default), OpenAI, and local LLM servers
- **Output Formats**: Both JSON (for automation) and verbose (for humans) output modes
- **Clean Usage Options**: Wrapper script for easy execution without installation

🎯 **Production Ready**: The tool is now a complete AI-powered analysis platform ready for technical enablement scenarios.

## Documentation

### Prompt Engineering Guide

For advanced users who want to customize AI behavior and understand how prompts are assembled:

📖 **[Prompt Engineering Guide](docs/prompting-guide.md)** - Comprehensive guide covering:
- How prompt assembly works (with flow diagrams)
- Key components you can modify
- Role of BaseModel description fields in guiding AI behavior
- Best practices for customizing analysis types
- Testing and debugging prompt changes
- Advanced customization techniques

This guide is essential for developers and prompt engineers who want to fine-tune the AI analysis behavior or create custom analysis types.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Create an issue for bug reports or feature requests
- Check existing issues before creating new ones
- Provide detailed information about your environment and the problem
- Include the output of `showroom-tool --help` and your Python version

---

**Example Repository for Testing:**
```bash
# Using wrapper script (no installation required)
python showroom-tool.py summary https://github.com/rhpds/showroom-summit2025-lb2960-llamastack.git --verbose

# Using installed package
showroom-tool summary https://github.com/rhpds/showroom-summit2025-lb2960-llamastack.git --verbose
showroom-tool review https://github.com/rhpds/showroom-summit2025-lb2960-llamastack.git --output json
showroom-tool description https://github.com/rhpds/showroom-summit2025-lb2960-llamastack.git
```

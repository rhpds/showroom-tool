# Showroom Tool

A Python-based CLI tool designed to summarize, review, and validate technical lab and demo content. Primarily intended for use in technical enablement and customer demonstration scenarios by technical sellers.

The tool processes content provided as one or more AsciiDoc files typically stored in remote `antora` formatted repositories or local git clones. Labs and demos are made available via a Catalog called RHDP and its associated repository which contains YAML defined Catalog Items (CIs).

## Features

- **Repository Processing**: Clone and analyze showroom repositories with intelligent caching
- **Content Analysis**: Parse AsciiDoc modules and extract structured data
- **Smart Caching**: Avoid repeated clones with automatic cache invalidation
- **CLI Interface**: Easy-to-use command-line interface with rich, colorized output
- **AsciiDoc Support**: Native support for AsciiDoc formatted content with header extraction
- **Performance**: ~50% faster on subsequent runs thanks to intelligent caching
- **Flexible Options**: Support for different git refs, custom cache directories, and cache control

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
   cd showroom-reviewer-pydantic

   # Create virtual environment and install in one step
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

#### Option B: Using Standard Python/pip

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd showroom-reviewer-pydantic
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

### Basic Commands

```bash
# Analyze a repository (uses caching by default)
showroom-tool https://github.com/example/my-showroom

# Use a specific branch or tag
showroom-tool https://github.com/example/my-showroom --ref develop

# Enable verbose output to see detailed processing
showroom-tool https://github.com/example/my-showroom --verbose

# Force fresh clone (disable caching)
showroom-tool https://github.com/example/my-showroom --no-cache

# Use custom cache directory
showroom-tool https://github.com/example/my-showroom --cache-dir /tmp/my-cache

# Alternative syntax
showroom-tool --repo https://github.com/example/my-showroom --ref main --verbose
```

### Example Output

```
Showroom Lab Summary:
  Name: Summit 2025 - LB2906 - Getting Started with Llamastack
  URL: https://github.com/rhpds/showroom-summit2025-lb2960-llamastack.git
  Ref: main
  Modules: 9
    1. AI Applications and Llama Stack: A practical workshop [index.adoc] (615 words, 14 lines)
    2. Module 1: Getting Started [01-Getting-Started.adoc] (1553 words, 230 lines)
    3. Module 2: Llama Stack Inference Basics [02_Lllamastack_Inference_Basics.adoc] (499 words, 34 lines)
    ...
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
cd showroom-reviewer-pydantic

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
cd showroom-reviewer-pydantic

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
showroom-reviewer-pydantic/
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
# Alternative execution methods
python -m showroom_tool <repo-url>
python -m showroom_tool --help
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
- Pydantic BaseModel data structures (`Showroom`, `ShowroomModule`)
- CLI with argument parsing and rich output
- Git reference support (branches, tags, commits)
- Comprehensive error handling

🚀 **Ready for Next Phase:**
- Content summarization capabilities
- Review and validation features
- Advanced analysis tools

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
showroom-tool https://github.com/rhpds/showroom-summit2025-lb2960-llamastack.git --verbose
```

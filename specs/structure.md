# Project Structure

This document outlines the organization and folder structure of the Showroom Tool project to help navigate and understand the codebase.

## Directory Organization

```
/
├── .git/                    # Git repository metadata
├── .github/                 # GitHub workflows and configuration
├── .cursor/                 # Cursor AI assistant configuration
│   └── rules/               # Cursor rules for AI assistance
├── .venv/                   # Virtual environment (not committed)
├── config/                  # Source code
│   ├── basemodels.py        # All Pydantic BaseModels
├── src/                     # Source code
│   └── showroom_tool        # Main executable
├── libs/                    # Source code
│   └── llm.py/              # OpenAI LLM and Prompt Building Code
├── tests/                   # Test suite
│   ├── conftest.py          # Test configuration
│   ├── test_analyzer.py     # Tests for analyzer
│   └── fixtures/            # Test fixtures
├── docs/                    # Documentation
├── examples/                # Example usage and demos
├── .gitignore               # Git ignore patterns
├── pyproject.toml           # Project configuration and dependencies
├── README.md                # Project overview
└── LICENSE                  # License information
```

## Key Directories and Files

### Root Level
- `.git/`: Git repository metadata
- `.kiro/`: Configuration for Kiro AI assistant
- `pyproject.toml`: Project configuration, build settings, and dependencies
- `README.md`: Project overview, installation, and usage instructions
- `LICENSE`: Project license information

## Naming Conventions
- Use descriptive, lowercase names for directories
- Use snake_case for Python files, modules, and packages
- Use PascalCase for classes
- Use UPPER_CASE for constants
- Prefix test files with `test_`

## Module Organization
- Each module should have a clear, single responsibility
- Related functionality should be grouped together
- Avoid deep nesting of directories (aim for max 3-4 levels)
- Use `__init__.py` files to expose public APIs

## Import/Export Patterns
- Use absolute imports within the package
- Avoid circular imports
- Export public APIs in `__init__.py` files
- Follow isort conventions for import ordering

## Configuration Files
- Keep configuration files at the root level
- Use pyproject.toml for project configuration
- Use environment variables and .env files for runtime configuration

## Documentation
- Include docstrings for all public functions, classes, and methods
- Follow Google docstring format
- Include README files in key directories
- Document complex components and utilities
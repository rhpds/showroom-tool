# Showroom Tool

A Python-based CLI tool designed to summarize, review, and validate technical lab and demo content. Primarily intended for use in technical enablement and customer demonstration scenarios by technical sellers.

The tool processes content provided as one or more AsciiDoc files typically stored in remote `antora` formatted repositories or local git clones. Labs and demos are made available via a Catalog called RHDP and its associated repository which contains YAML defined Catalog Items (CIs).

## Features

- **Customizable Summarization**: Generate summaries of lab and demo content tailored to your needs
- **Content Review**: Automated review and recommendations for technical content
- **Validation**: Ensure content meets quality standards and best practices
- **CLI Interface**: Easy-to-use command-line interface for quick operations
- **AsciiDoc Support**: Native support for AsciiDoc formatted content
- **Repository Integration**: Works with both remote and local git repositories

## Quick Start

### Prerequisites

- Python 3.12 or higher
- `uv` package manager (recommended) or standard `pip`

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/redhat-demo-platform/showroom-tool.git
   cd showroom-tool
   ```

2. **Create and activate a virtual environment**:
   
   Using `uv` (recommended):
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
   
   Or using standard Python:
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   
   Using `uv`:
   ```bash
   uv pip install -e .
   ```
   
   Or using pip:
   ```bash
   pip install -e .
   ```

4. **Install development dependencies** (optional):
   ```bash
   uv pip install -e ".[dev]"
   # or
   pip install -e ".[dev]"
   ```

### Basic Usage

```bash
# Basic summarization
showroom-tool summarize path/to/content.adoc

# Review content
showroom-tool review path/to/content.adoc

# Validate content
showroom-tool validate path/to/content.adoc

# Get help
showroom-tool --help
```

## Development

### Development Setup

1. **Fork and clone the repository**
2. **Set up the development environment**:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev,test,docs]"
   ```

3. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

### Development Workflow

- **Code formatting**: `ruff format .`
- **Linting**: `ruff check .`
- **Type checking**: `mypy src/`
- **Testing**: `pytest`
- **Coverage**: `pytest --cov=src --cov-report=html`

### Project Structure

```
/
├── .git/                    # Git repository metadata
├── .github/                 # GitHub workflows and configuration
├── .cursor/                 # Cursor AI assistant configuration
│   └── rules/               # Cursor rules for AI assistance
├── .venv/                   # Virtual environment (not committed)
├── config/                  # Configuration files
│   ├── basemodels.py        # All Pydantic BaseModels
├── src/                     # Source code
│   └── showroom_tool        # Main executable
├── libs/                    # Library code
│   └── llm.py               # OpenAI LLM and Prompt Building Code
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

### Technology Stack

- **Programming Language**: Python 3.12+
- **Framework**: LangChain, LangGraph
- **Key Libraries**:
  - `openai`: For building LLM applications and inference
  - `langgraph`: For creating complex AI workflows
  - `pydantic v2`: For data validation and settings management
  - `click`: For CLI interface
  - `rich`: For enhanced terminal output
  - `pytest`: For testing
  - `ruff`: For linting and formatting
  - `uv`: For dependency management

### Configuration

The tool supports configuration through:
- Environment variables
- Configuration files
- Command-line arguments

See the `config/` directory for available configuration options.

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_analyzer.py

# Run with verbose output
pytest -v
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass (`pytest`)
6. Ensure code quality (`ruff check .` and `mypy src/`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Write descriptive docstrings for all public functions and classes
- Maintain test coverage above 80%
- Use meaningful variable and function names

## Documentation

- API documentation is auto-generated from docstrings
- User guides are in the `docs/` directory
- Examples are in the `examples/` directory

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Create an issue for bug reports or feature requests
- Check existing issues before creating new ones
- Provide detailed information about your environment and the problem

## Roadmap

- [ ] Enhanced AsciiDoc parsing capabilities
- [ ] Integration with more repository types
- [ ] Advanced content analysis features
- [ ] Web interface for content management
- [ ] API endpoints for programmatic access

---

**Red Hat Demo Platform** | [Documentation](docs/) | [Issues](https://github.com/redhat-demo-platform/showroom-tool/issues) 
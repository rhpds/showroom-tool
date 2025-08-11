#!/usr/bin/env python
"""
Simple wrapper script for showroom-tool.
Allows users to run: python showroom-tool.py --help
"""
import sys
from pathlib import Path


def main():
    """Main entry point that sets up the path and calls the CLI."""
    # Add src to Python path so we can import from the package structure
    project_root = Path(__file__).parent
    src_path = project_root / "src"

    # Insert at the beginning to ensure our modules take precedence
    sys.path.insert(0, str(src_path))

    try:
        from showroom_tool.cli import main as cli_main
        cli_main()
    except ImportError as e:
        print(f"Error importing showroom_tool: {e}")
        print("Make sure you're running this from the project root directory.")
        print("Required structure: src/showroom_tool/cli.py")
        sys.exit(1)


if __name__ == "__main__":
    main()

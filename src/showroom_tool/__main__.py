#!/usr/bin/env python

"""
Main CLI entry point for showroom-tool.
"""

import sys
from pathlib import Path


def main():
    """Main entry point that sets up the path and calls the actual main function."""
    # Add the project root to the Python path so we can import from config
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    from showroom_tool.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()

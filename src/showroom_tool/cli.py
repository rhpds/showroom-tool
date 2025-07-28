#!/usr/bin/env python

"""
CLI entry point for showroom-tool that works properly when installed.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from rich.console import Console

# Try to import from the installed package structure
try:
    from showroom_tool.showroom import count_words_and_lines
except ImportError:
    # Fall back to adding the project root to path (for development)
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from showroom_tool.showroom import count_words_and_lines

console = Console()


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for showroom-tool."""
    parser = argparse.ArgumentParser(
        description="Showroom Tool - CLI for summarizing, reviewing, and validating technical lab content",
        epilog="Example: showroom-tool https://github.com/example/my-lab",
    )

    # Support both --repo flag and positional argument
    parser.add_argument(
        "repo_url", nargs="?", help="Git repository URL containing the showroom lab"
    )
    parser.add_argument(
        "--repo",
        help="Git repository URL containing the showroom lab (alternative to positional argument)",
    )
    parser.add_argument(
        "--ref",
        default="main",
        help="Git reference (branch, tag, or commit) to use (default: main)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Disable caching and force fresh clone"
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="Custom cache directory (default: ~/.showroom-tool/cache)",
    )

    return parser.parse_args()


async def main_async():
    """Main CLI entry point using LangGraph."""
    args = parse_arguments()

    # Determine the repository URL (from positional arg or --repo flag)
    repo_url = args.repo_url or args.repo

    if not repo_url:
        console.print("[red]Error: Repository URL is required[/red]")
        console.print(
            "Usage: showroom-tool <repo_url> [--ref <branch>] [--verbose] [--no-cache] [--cache-dir <dir>]"
        )
        console.print(
            "   or: showroom-tool --repo <repo_url> [--ref <branch>] [--verbose] [--no-cache] [--cache-dir <dir>]"
        )
        sys.exit(1)

    if args.verbose:
        console.print(
            f"[blue]Starting showroom-tool with repository: {repo_url}[/blue]"
        )
        console.print("[blue]Using LangGraph processing...[/blue]")
        if args.no_cache:
            console.print("[blue]Cache disabled - will use temporary clone[/blue]")
        elif args.cache_dir:
            console.print(
                f"[blue]Using custom cache directory: {args.cache_dir}[/blue]"
            )

    # Import the LangGraph function
    from showroom_tool.graph_factory import process_showroom_with_graph

    # Process the showroom repository using LangGraph
    try:
        result = await process_showroom_with_graph(
            git_url=repo_url,
            git_ref=args.ref,
            verbose=args.verbose,
            cache_dir=args.cache_dir,
            no_cache=args.no_cache
        )

        if not result.get("success", False):
            console.print(f"[red]Failed to fetch showroom repository: {result.get('error', 'Unknown error')}[/red]")
            sys.exit(1)

        showroom = result.get("showroom_data")
        if showroom is None:
            console.print("[red]No showroom data returned from graph processing[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]Error during graph processing: {e}[/red]")
        sys.exit(1)

    # For now, just display the results
    console.print("\n[bold green]Showroom Lab Summary:[/bold green]")
    console.print(
        f"  [bold]Name:[/bold] [bright_cyan]{showroom.lab_name}[/bright_cyan]"
    )
    console.print(f"  [bold]URL:[/bold] [blue]{showroom.git_url}[/blue]")
    console.print(f"  [bold]Ref:[/bold] [yellow]{showroom.git_ref}[/yellow]")
    console.print(
        f"  [bold]Modules:[/bold] [bright_magenta]{len(showroom.modules)}[/bright_magenta]"
    )

    for i, module in enumerate(showroom.modules, 1):
        if args.verbose:
            # In verbose mode, show both module name and filename with colors
            display_name = (
                module.module_name.strip()
                if module.module_name.strip()
                else "(no title)"
            )
            # Escape special characters to avoid Rich formatting conflicts
            from rich.markup import escape

            safe_display_name = escape(display_name)

            # Count words and lines for meaningful metrics
            word_count, line_count = count_words_and_lines(module.module_content)

            # Create colorized output
            module_line = (
                f"    [bright_white]{i}.[/bright_white] "
                f"[bold]{safe_display_name}[/bold] "
                f"[cyan]\\[{module.filename}][/cyan] "
                f"[dim]({word_count} words, {line_count} lines)[/dim]"
            )
            console.print(module_line)
        else:
            # In normal mode, show module name and filename with colors
            display_name = (
                module.module_name.strip()
                if module.module_name.strip()
                else "(no title)"
            )
            from rich.markup import escape

            safe_display_name = escape(display_name)

            # Count words and lines for meaningful metrics
            word_count, line_count = count_words_and_lines(module.module_content)

            module_line = (
                f"    [bright_white]{i}.[/bright_white] "
                f"[bold]{safe_display_name}[/bold] "
                f"[cyan]\\[{module.filename}][/cyan] "
                f"[dim]({word_count} words, {line_count} lines)[/dim]"
            )
            console.print(module_line)

    if args.verbose:
        console.print("\n[blue]Showroom data model successfully populated via LangGraph[/blue]")


def main():
    """Synchronous wrapper for the async main function."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

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
    from showroom_tool.basemodels import CatalogDescription, ShowroomReview, ShowroomSummary
    from showroom_tool import __version__
    from showroom_tool.outputs import (
        check_jinja2_availability,
        output_basemodel_as_adoc,
    )
    from showroom_tool.prompts import (
        build_showroom_description_structured_prompt,
        build_showroom_review_structured_prompt,
        build_showroom_summary_structured_prompt,
        load_prompts_overrides,
    )
    from showroom_tool.shared_utilities import (
        print_basemodel,
        save_description_to_workspace,
        save_review_to_workspace,
        save_summary_to_workspace,
    )
    from showroom_tool.showroom import count_words_and_lines
except ImportError:
    # Fall back to adding the project root to path (for development)
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root / "src"))
    from showroom_tool.basemodels import CatalogDescription, ShowroomReview, ShowroomSummary
    from showroom_tool import __version__
    from showroom_tool.outputs import (
        check_jinja2_availability,
        output_basemodel_as_adoc,
    )
    from showroom_tool.prompts import (
        build_showroom_description_structured_prompt,
        build_showroom_review_structured_prompt,
        build_showroom_summary_structured_prompt,
        load_prompts_overrides,
    )
    from showroom_tool.shared_utilities import (
        print_basemodel,
        save_description_to_workspace,
        save_review_to_workspace,
        save_summary_to_workspace,
    )
    from showroom_tool.showroom import count_words_and_lines

console = Console()


def display_showroom_details(showroom, args):
    """Display detailed showroom information in verbose mode."""
    console.print("\n[bold green]📚 Showroom Lab Details[/bold green]")
    console.print("=" * 60)

    # Lab metadata
    console.print(f"[bold]Lab Name:[/bold] [bright_cyan]{showroom.lab_name}[/bright_cyan]")
    console.print(f"[bold]Git Repository:[/bold] [blue]{showroom.git_url}[/blue]")
    console.print(f"[bold]Git Reference:[/bold] [yellow]{showroom.git_ref}[/yellow]")
    console.print(f"[bold]Total Modules:[/bold] [bright_magenta]{len(showroom.modules)}[/bright_magenta]")

    # Module details
    console.print("\n[bold green]📖 Module Breakdown[/bold green]")
    console.print("-" * 60)

    total_words = 0
    total_lines = 0

    for i, module in enumerate(showroom.modules, 1):
        # Get module display name
        display_name = module.module_name.strip() if module.module_name.strip() else "(no title)"

        # Escape special characters to avoid Rich formatting conflicts
        from rich.markup import escape
        safe_display_name = escape(display_name)

        # Count words and lines
        word_count, line_count = count_words_and_lines(module.module_content)
        total_words += word_count
        total_lines += line_count

        # Display module info with rich formatting
        console.print(
            f"  [bright_white]{i:2d}.[/bright_white] "
            f"[bold]{safe_display_name}[/bold]"
        )
        console.print(
            f"      [dim]File:[/dim] [cyan]{module.filename}[/cyan] "
            f"[dim]|[/dim] [green]{word_count:,} words[/green] "
            f"[dim]|[/dim] [blue]{line_count:,} lines[/blue]"
        )

    # Summary totals
    console.print("-" * 60)
    console.print(
        f"[bold]📊 Totals:[/bold] "
        f"[green]{total_words:,} words[/green] "
        f"[dim]|[/dim] [blue]{total_lines:,} lines[/blue] "
        f"[dim]across[/dim] [bright_magenta]{len(showroom.modules)} modules[/bright_magenta]"
    )
    console.print("=" * 60)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments for showroom-tool."""
    parser = argparse.ArgumentParser(
        description="Showroom Tool - CLI for summarizing, reviewing, and validating technical lab content",
        epilog="Examples:\n  showroom-tool summary https://github.com/example/my-lab\n  showroom-tool review https://github.com/example/my-lab\n  showroom-tool description https://github.com/example/my-lab",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global version flag
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Show the showroom-tool version and exit",
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Summary command - fetch + LLM summarization
    summary_parser = subparsers.add_parser("summary", help="Generate AI-powered summary of showroom content")
    add_common_arguments(summary_parser)
    add_llm_arguments(summary_parser)

    # Review command - fetch + LLM review
    review_parser = subparsers.add_parser("review", help="Generate AI-powered review of showroom content")
    add_common_arguments(review_parser)
    add_llm_arguments(review_parser)

    # Description command - fetch + LLM catalog description
    description_parser = subparsers.add_parser("description", help="Generate AI-powered catalog description of showroom content")
    add_common_arguments(description_parser)
    add_llm_arguments(description_parser)

    return parser.parse_args()


def add_common_arguments(parser):
    """Add common arguments to a parser."""
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
    parser.add_argument(
        "--dir",
        dest="local_dir",
        default=None,
        help="Path to a local Showroom repo directory (bypass git clone/cache)",
    )
    parser.add_argument(
        "--output",
        default="verbose",
        choices=["verbose", "json", "adoc"],
        help="Output format: 'verbose' for rich console output (default), 'json' for clean JSON output, 'adoc' for AsciiDoc output",
    )
    parser.add_argument(
        "--prompts-file",
        dest="prompts_file",
        default=None,
        help="Path to a prompts override file (.py or .json) to override defaults in prompts.py",
    )


def add_llm_arguments(parser):
    """Add LLM-specific arguments to a parser."""
    parser.add_argument(
        "--llm-provider",
        default=None,
        choices=["openai", "gemini", "local"],
        help="LLM provider to use (default: gemini)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name to use (provider-specific)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Temperature for LLM generation (default: 0.1)",
    )
    parser.add_argument(
        "--output-prompt",
        action="store_true",
        help="Display the AI prompt template instead of processing content",
    )



async def handle_summary_command(args):
    """Handle the summary command to generate AI-powered summary."""
    # Auto-discover project/user prompt overrides (Requirement 11.11)
    try:
        from showroom_tool import prompt_builder as _pb, prompts as _pr  # type: ignore
        _discovered = _pb.get_prompts_and_settings()
        for _k, _v in _discovered.items():
            _pr.PROMPTS_FILE_OVERRIDES.setdefault(_k, _v)
    except Exception:
        pass
    # Check if user wants to see the prompt template
    if args.output_prompt:
        console.print("\n[bold blue]AI Summary Prompt Template[/bold blue]")
        console.print("[blue]Displaying standard Showroom lab summary analysis prompt...[/blue]")

        try:
            # Requirement 11.9: Load prompts overrides early when showing prompt
            if args.prompts_file:
                load_prompts_overrides(args.prompts_file)

            # Build the standard prompt without requiring actual showroom data
            system_prompt = build_showroom_summary_structured_prompt(ShowroomSummary)
            console.print("\n[bold green]Summary Analysis Prompt:[/bold green]")
            console.print(f"[dim]Length: {len(system_prompt)} characters[/dim]\n")
            console.print(system_prompt)
            return
        except Exception as e:
            console.print(f"[red]Error building prompt: {e}[/red]")
            sys.exit(1)

    # Determine output mode
    is_json_output = args.output == "json"
    is_clean_output = args.output in ["json", "adoc"]  # Both modes need clean output

    if not is_clean_output:
        console.print("\n[bold blue]AI Summary Generation[/bold blue]")

    # Get repository data first
    showroom = await fetch_showroom_data(args)

    # Display detailed showroom information in verbose mode
    if not is_clean_output and args.output == "verbose":
        display_showroom_details(showroom, args)

    # Generate AI summary
    if not is_clean_output:
        console.print("\n[blue]Generating AI summary...[/blue]")

    try:
        from showroom_tool.graph_factory import process_showroom_with_graph

        result = await process_showroom_with_graph(
            git_url=showroom.git_url,
            git_ref=showroom.git_ref,
            verbose=args.verbose and not is_clean_output,
            cache_dir=args.cache_dir,
            no_cache=args.no_cache,
            local_dir=args.local_dir,
            command="summary",
            llm_provider=args.llm_provider,
            model=args.model,
            temperature=args.temperature,
            prompts_file=args.prompts_file,
        )

        if result.get("success"):
            structured = result.get("structured_output")
            if is_json_output:
                import json
                print(json.dumps(structured, indent=2, ensure_ascii=False))
            elif args.output == "adoc":
                if not check_jinja2_availability():
                    print("Error: Jinja2 is required for AsciiDoc output. Install it with 'pip install jinja2'", file=sys.stderr)
                    sys.exit(1)
                extra_context = {
                    "lab_name": result.get("lab_name"),
                    "git_url": result.get("git_url"),
                    "git_ref": result.get("git_ref"),
                }
                summary = ShowroomSummary(**(structured or {}))
                output_basemodel_as_adoc(summary, extra_context)
            else:
                console.print("\n[bold green]✅ AI Summary Generated Successfully![/bold green]")
                summary = ShowroomSummary(**(structured or {}))
                print_basemodel(summary, "Showroom Summary")
                saved_path = save_summary_to_workspace(summary)
                console.print(f"\n[blue]💾 Summary saved to: {saved_path}[/blue]")
        else:
            err = result.get("error", "Failed to generate summary")
            if is_clean_output:
                print(f"Error: {err}", file=sys.stderr)
            else:
                console.print(f"\n[red]❌ {err}[/red]")
            sys.exit(1)

    except Exception as e:
        if is_clean_output:
            # For clean output modes, print error to stderr and exit
            print(f"Error: {str(e)}", file=sys.stderr)
            if args.verbose:
                import traceback
                print(traceback.format_exc(), file=sys.stderr)
            sys.exit(1)
        else:
            console.print(f"[red]Error during AI processing: {e}[/red]")
            if args.verbose:
                import traceback
                console.print(f"[red]{traceback.format_exc()}[/red]")
            sys.exit(1)


async def handle_review_command(args):
    """Handle the review command to generate AI-powered review."""
    # Auto-discover project/user prompt overrides (Requirement 11.11)
    try:
        from showroom_tool import prompt_builder as _pb, prompts as _pr  # type: ignore
        _discovered = _pb.get_prompts_and_settings()
        for _k, _v in _discovered.items():
            _pr.PROMPTS_FILE_OVERRIDES.setdefault(_k, _v)
    except Exception:
        pass
    # Check if user wants to see the prompt template
    if args.output_prompt:
        console.print("\n[bold blue]AI Review Prompt Template[/bold blue]")
        console.print("[blue]Displaying standard Showroom lab review analysis prompt...[/blue]")

        try:
            if args.prompts_file:
                load_prompts_overrides(args.prompts_file)

            # Build the standard prompt without requiring actual showroom data
            system_prompt = build_showroom_review_structured_prompt(ShowroomReview)
            console.print("\n[bold green]Review Analysis Prompt:[/bold green]")
            console.print(f"[dim]Length: {len(system_prompt)} characters[/dim]\n")
            console.print(system_prompt)
            return
        except Exception as e:
            console.print(f"[red]Error building prompt: {e}[/red]")
            sys.exit(1)

    # Determine output mode
    is_json_output = args.output == "json"
    is_clean_output = args.output in ["json", "adoc"]  # Both modes need clean output

    if not is_clean_output:
        console.print("\n[bold blue]AI Review Generation[/bold blue]")

    # Get repository data first
    showroom = await fetch_showroom_data(args)

    # Display detailed showroom information in verbose mode
    if not is_clean_output and args.output == "verbose":
        display_showroom_details(showroom, args)

    # Generate AI review
    if not is_clean_output:
        console.print("\n[blue]Generating AI review...[/blue]")

    try:
        from showroom_tool.graph_factory import process_showroom_with_graph

        result = await process_showroom_with_graph(
            git_url=showroom.git_url,
            git_ref=showroom.git_ref,
            verbose=args.verbose and not is_clean_output,
            cache_dir=args.cache_dir,
            no_cache=args.no_cache,
            local_dir=args.local_dir,
            command="review",
            llm_provider=args.llm_provider,
            model=args.model,
            temperature=args.temperature,
            prompts_file=args.prompts_file,
        )

        if result.get("success"):
            structured = result.get("structured_output")
            if is_json_output:
                import json
                print(json.dumps(structured, indent=2, ensure_ascii=False))
            elif args.output == "adoc":
                if not check_jinja2_availability():
                    print("Error: Jinja2 is required for AsciiDoc output. Install it with 'pip install jinja2'", file=sys.stderr)
                    sys.exit(1)
                extra_context = {
                    "lab_name": result.get("lab_name"),
                    "git_url": result.get("git_url"),
                    "git_ref": result.get("git_ref"),
                }
                review = ShowroomReview(**(structured or {}))
                output_basemodel_as_adoc(review, extra_context)
            else:
                console.print("\n[bold green]✅ AI Review Generated Successfully![/bold green]")
                review = ShowroomReview(**(structured or {}))
                print_basemodel(review, "Showroom Review")
                saved_path = save_review_to_workspace(review)
                console.print(f"\n[blue]💾 Review saved to: {saved_path}[/blue]")
        else:
            err = result.get("error", "Failed to generate review")
            if is_clean_output:
                print(f"Error: {err}", file=sys.stderr)
            else:
                console.print(f"\n[red]❌ {err}[/red]")
            sys.exit(1)

    except Exception as e:
        if is_clean_output:
            # For clean output modes, print error to stderr and exit
            print(f"Error: {str(e)}", file=sys.stderr)
            if args.verbose:
                import traceback
                print(traceback.format_exc(), file=sys.stderr)
            sys.exit(1)
        else:
            console.print(f"[red]Error during AI processing: {e}[/red]")
            if args.verbose:
                import traceback
                console.print(f"[red]{traceback.format_exc()}[/red]")
            sys.exit(1)


async def handle_description_command(args):
    """Handle the description command to generate AI-powered catalog description."""
    # Auto-discover project/user prompt overrides (Requirement 11.11)
    try:
        from showroom_tool import prompt_builder as _pb, prompts as _pr  # type: ignore
        _discovered = _pb.get_prompts_and_settings()
        for _k, _v in _discovered.items():
            _pr.PROMPTS_FILE_OVERRIDES.setdefault(_k, _v)
    except Exception:
        pass
    # Check if user wants to see the prompt template
    if args.output_prompt:
        console.print("\n[bold blue]AI Description Prompt Template[/bold blue]")
        console.print("[blue]Displaying standard Showroom lab description analysis prompt...[/blue]")

        try:
            if args.prompts_file:
                load_prompts_overrides(args.prompts_file)

            # Build the standard prompt without requiring actual showroom data
            system_prompt = build_showroom_description_structured_prompt(CatalogDescription)
            console.print("\n[bold green]Description Analysis Prompt:[/bold green]")
            console.print(f"[dim]Length: {len(system_prompt)} characters[/dim]\n")
            console.print(system_prompt)
            return
        except Exception as e:
            console.print(f"[red]Error building prompt: {e}[/red]")
            sys.exit(1)

    # Determine output mode
    is_json_output = args.output == "json"
    is_clean_output = args.output in ["json", "adoc"]  # Both modes need clean output

    if not is_clean_output:
        console.print("\n[bold blue]AI Description Generation[/bold blue]")

    # Get repository data first
    showroom = await fetch_showroom_data(args)

    # Display detailed showroom information in verbose mode
    if not is_clean_output and args.output == "verbose":
        display_showroom_details(showroom, args)

    # Generate AI description
    if not is_clean_output:
        console.print("\n[blue]Generating AI catalog description...[/blue]")

    try:
        from showroom_tool.graph_factory import process_showroom_with_graph

        result = await process_showroom_with_graph(
            git_url=showroom.git_url,
            git_ref=showroom.git_ref,
            verbose=args.verbose and not is_clean_output,
            cache_dir=args.cache_dir,
            no_cache=args.no_cache,
            local_dir=args.local_dir,
            command="description",
            llm_provider=args.llm_provider,
            model=args.model,
            temperature=args.temperature,
            prompts_file=args.prompts_file,
        )

        if result.get("success"):
            structured = result.get("structured_output")
            if is_json_output:
                import json
                print(json.dumps(structured, indent=2, ensure_ascii=False))
            elif args.output == "adoc":
                if not check_jinja2_availability():
                    print("Error: Jinja2 is required for AsciiDoc output. Install it with 'pip install jinja2'", file=sys.stderr)
                    sys.exit(1)
                extra_context = {
                    "lab_name": result.get("lab_name"),
                    "git_url": result.get("git_url"),
                    "git_ref": result.get("git_ref"),
                }
                description = CatalogDescription(**(structured or {}))
                output_basemodel_as_adoc(description, extra_context)
            else:
                console.print("\n[bold green]✅ AI Description Generated Successfully![/bold green]")
                description = CatalogDescription(**(structured or {}))
                print_basemodel(description, "Catalog Description")
                saved_path = save_description_to_workspace(description)
                console.print(f"\n[blue]💾 Description saved to: {saved_path}[/blue]")
        else:
            err = result.get("error", "Failed to generate description")
            if is_clean_output:
                print(f"Error: {err}", file=sys.stderr)
            else:
                console.print(f"\n[red]❌ {err}[/red]")
            sys.exit(1)

    except Exception as e:
        if is_clean_output:
            # For clean output modes, print error to stderr and exit
            print(f"Error: {str(e)}", file=sys.stderr)
            if args.verbose:
                import traceback
                print(traceback.format_exc(), file=sys.stderr)
            sys.exit(1)
        else:
            console.print(f"[red]Error during AI processing: {e}[/red]")
            if args.verbose:
                import traceback
                console.print(f"[red]{traceback.format_exc()}[/red]")
            sys.exit(1)


async def fetch_showroom_data(args):
    """Fetch showroom data using LangGraph."""
    # Determine output mode
    is_json_output = getattr(args, 'output', 'verbose') == "json"

    # Determine the repository URL (from positional arg or --repo flag)
    repo_url = args.repo_url or args.repo

    if not repo_url and not args.local_dir:
        if is_json_output:
            print("Error: Repository URL or --dir PATH is required", file=sys.stderr)
            sys.exit(1)
        else:
            console.print("[red]Error: Repository URL or --dir PATH is required[/red]")
            console.print("Usage: showroom-tool <command> <repo_url> [options] or showroom-tool <command> --dir <PATH>")
        sys.exit(1)

    if args.verbose and not is_json_output:
        if args.local_dir:
            console.print(f"[blue]Using local directory: {args.local_dir}[/blue]")
        if repo_url:
            console.print(f"[blue]Processing repository: {repo_url}[/blue]")
        console.print("[blue]Using LangGraph processing...[/blue]")

    # Import the LangGraph function
    from showroom_tool.graph_factory import process_showroom_with_graph

    try:
        # For JSON output, suppress verbose output from LangGraph
        result = await process_showroom_with_graph(
            git_url=repo_url or "",
            git_ref=args.ref,
            verbose=args.verbose and not is_json_output,
            cache_dir=args.cache_dir,
            no_cache=args.no_cache,
            local_dir=args.local_dir,
            prompts_file=args.prompts_file,
        )

        if not result.get("success", False):
            error_msg = f"Failed to fetch showroom repository: {result.get('error', 'Unknown error')}"
            if is_json_output:
                print(error_msg, file=sys.stderr)
            else:
                console.print(f"[red]{error_msg}[/red]")
            sys.exit(1)

        showroom = result.get("showroom_data")
        if showroom is None:
            error_msg = "No showroom data returned from graph processing"
            if is_json_output:
                print(error_msg, file=sys.stderr)
            else:
                console.print(f"[red]{error_msg}[/red]")
            sys.exit(1)

        return showroom

    except Exception as e:
        error_msg = f"Error during repository processing: {e}"
        if is_json_output:
            print(error_msg, file=sys.stderr)
        else:
            console.print(f"[red]{error_msg}[/red]")
        sys.exit(1)



async def main_async():
    """Main CLI entry point using LangGraph."""
    args = parse_arguments()

    # Handle version output
    if getattr(args, "version", False):
        print(f"showroom-tool {__version__}")
        return

    # Handle different commands
    if args.command == "summary":
        await handle_summary_command(args)
    elif args.command == "review":
        await handle_review_command(args)
    elif args.command == "description":
        await handle_description_command(args)
    elif args.command is None:
        # No command provided - show help
        console.print("[red]Error: No command specified[/red]")
        console.print("\n[blue]Available commands:[/blue]")
        console.print("  [bold]summary[/bold]     - Generate AI-powered summary of showroom content")
        console.print("  [bold]review[/bold]      - Generate AI-powered review of showroom content")
        console.print("  [bold]description[/bold] - Generate AI-powered catalog description of showroom content")
        console.print("\n[dim]Use 'showroom-tool <command> --help' for detailed help on a command[/dim]")
        sys.exit(1)
    else:
        console.print(f"[red]Unknown command: {args.command}[/red]")
        console.print("[blue]Available commands: summary, review, description[/blue]")
        sys.exit(1)


def main():
    """Synchronous wrapper for the async main function."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

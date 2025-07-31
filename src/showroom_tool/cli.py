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
    from config.basemodels import CatalogDescription, ShowroomReview, ShowroomSummary
    from showroom_tool.outputs import output_basemodel_as_adoc, check_jinja2_availability
    from showroom_tool.prompts import (
        build_showroom_description_structured_prompt,
        build_showroom_review_structured_prompt,
        build_showroom_summary_structured_prompt,
    )
    from showroom_tool.shared_utilities import (
        build_showroom_description_prompt,
        build_showroom_review_prompt,
        build_showroom_summary_prompt,
        print_basemodel,
        process_content_with_structured_output,
        save_description_to_workspace,
        save_review_to_workspace,
        save_summary_to_workspace,
    )
    from showroom_tool.showroom import count_words_and_lines
except ImportError:
    # Fall back to adding the project root to path (for development)
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from config.basemodels import CatalogDescription, ShowroomReview, ShowroomSummary
    from showroom_tool.outputs import output_basemodel_as_adoc, check_jinja2_availability
    from showroom_tool.prompts import (
        build_showroom_description_structured_prompt,
        build_showroom_review_structured_prompt,
        build_showroom_summary_structured_prompt,
    )
    from showroom_tool.shared_utilities import (
        build_showroom_description_prompt,
        build_showroom_review_prompt,
        build_showroom_summary_prompt,
        print_basemodel,
        process_content_with_structured_output,
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
        "--output",
        default="verbose",
        choices=["verbose", "json", "adoc"],
        help="Output format: 'verbose' for rich console output (default), 'json' for clean JSON output, 'adoc' for AsciiDoc output",
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
        "--show-prompt",
        action="store_true",
        help="Display the AI prompt template instead of processing content",
    )



async def handle_summary_command(args):
    """Handle the summary command to generate AI-powered summary."""
    # Check if user wants to see the prompt template
    if args.show_prompt:
        console.print("\n[bold blue]AI Summary Prompt Template[/bold blue]")
        console.print("[blue]Displaying standard Showroom lab summary analysis prompt...[/blue]")

        try:
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
        # Build the complete prompt
        system_prompt, user_content = build_showroom_summary_prompt(showroom, ShowroomSummary)

        if args.verbose and not is_clean_output:
            console.print(f"[dim]System prompt length: {len(system_prompt)} characters[/dim]")
            console.print(f"[dim]User content length: {len(user_content)} characters[/dim]")

        # Process with LLM (disable verbose output for clean output modes)
        summary, success, metadata = await process_content_with_structured_output(
            content=user_content,
            model_class=ShowroomSummary,
            system_prompt=system_prompt,
            llm_provider=args.llm_provider,
            model=args.model,
            temperature=args.temperature,
            verbose=args.verbose and not is_clean_output,
        )

        if success and summary:
            if is_json_output:
                # Clean JSON output for piping to jq
                import json
                print(json.dumps(summary.model_dump(), indent=2, ensure_ascii=False))
            elif args.output == "adoc":
                # Check if Jinja2 is available
                if not check_jinja2_availability():
                    print("Error: Jinja2 is required for AsciiDoc output. Install it with 'pip install jinja2'", file=sys.stderr)
                    sys.exit(1)
                
                # Output AsciiDoc to stdout
                extra_context = {
                    "lab_name": showroom.lab_name,
                    "git_url": showroom.git_url,
                    "git_ref": showroom.git_ref,
                }
                output_basemodel_as_adoc(summary, extra_context)
            else:
                # Verbose console output (current behavior)
                console.print("\n[bold green]✅ AI Summary Generated Successfully![/bold green]")
                print_basemodel(summary, "Showroom Summary")

                # Save to workspace
                saved_path = save_summary_to_workspace(summary)
                console.print(f"\n[blue]💾 Summary saved to: {saved_path}[/blue]")

            # Update the showroom object with the summary
            showroom.summary_output = summary

        else:
            if is_clean_output:
                # For clean output modes, print error to stderr and exit
                print(f"Error: {metadata.get('error', 'Failed to generate summary')}", file=sys.stderr)
                sys.exit(1)
            else:
                console.print("\n[red]❌ Failed to generate AI summary[/red]")
                if metadata.get("error"):
                    console.print(f"[red]Error: {metadata['error']}[/red]")
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
    # Check if user wants to see the prompt template
    if args.show_prompt:
        console.print("\n[bold blue]AI Review Prompt Template[/bold blue]")
        console.print("[blue]Displaying standard Showroom lab review analysis prompt...[/blue]")

        try:
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
        # Build the complete prompt
        system_prompt, user_content = build_showroom_review_prompt(showroom, ShowroomReview)

        if args.verbose and not is_clean_output:
            console.print(f"[dim]System prompt length: {len(system_prompt)} characters[/dim]")
            console.print(f"[dim]User content length: {len(user_content)} characters[/dim]")

        # Process with LLM (disable verbose output for clean output modes)
        review, success, metadata = await process_content_with_structured_output(
            content=user_content,
            model_class=ShowroomReview,
            system_prompt=system_prompt,
            llm_provider=args.llm_provider,
            model=args.model,
            temperature=args.temperature,
            verbose=args.verbose and not is_clean_output,
        )

        if success and review:
            if is_json_output:
                # Clean JSON output for piping to jq
                import json
                print(json.dumps(review.model_dump(), indent=2, ensure_ascii=False))
            elif args.output == "adoc":
                # Check if Jinja2 is available
                if not check_jinja2_availability():
                    print("Error: Jinja2 is required for AsciiDoc output. Install it with 'pip install jinja2'", file=sys.stderr)
                    sys.exit(1)
                
                # Output AsciiDoc to stdout
                extra_context = {
                    "lab_name": showroom.lab_name,
                    "git_url": showroom.git_url,
                    "git_ref": showroom.git_ref,
                }
                output_basemodel_as_adoc(review, extra_context)
            else:
                # Verbose console output (current behavior)
                console.print("\n[bold green]✅ AI Review Generated Successfully![/bold green]")
                print_basemodel(review, "Showroom Review")

                # Save to workspace
                saved_path = save_review_to_workspace(review)
                console.print(f"\n[blue]💾 Review saved to: {saved_path}[/blue]")

            # Update the showroom object with the review
            showroom.review_output = review

        else:
            if is_clean_output:
                # For clean output modes, print error to stderr and exit
                print(f"Error: {metadata.get('error', 'Failed to generate review')}", file=sys.stderr)
                sys.exit(1)
            else:
                console.print("\n[red]❌ Failed to generate AI review[/red]")
                if metadata.get("error"):
                    console.print(f"[red]Error: {metadata['error']}[/red]")
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
    # Check if user wants to see the prompt template
    if args.show_prompt:
        console.print("\n[bold blue]AI Description Prompt Template[/bold blue]")
        console.print("[blue]Displaying standard Showroom lab description analysis prompt...[/blue]")

        try:
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
        # Build the complete prompt
        system_prompt, user_content = build_showroom_description_prompt(showroom, CatalogDescription)

        if args.verbose and not is_clean_output:
            console.print(f"[dim]System prompt length: {len(system_prompt)} characters[/dim]")
            console.print(f"[dim]User content length: {len(user_content)} characters[/dim]")

        # Process with LLM (disable verbose output for clean output modes)
        description, success, metadata = await process_content_with_structured_output(
            content=user_content,
            model_class=CatalogDescription,
            system_prompt=system_prompt,
            llm_provider=args.llm_provider,
            model=args.model,
            temperature=args.temperature,
            verbose=args.verbose and not is_clean_output,
        )

        if success and description:
            if is_json_output:
                # Clean JSON output for piping to jq
                import json
                print(json.dumps(description.model_dump(), indent=2, ensure_ascii=False))
            elif args.output == "adoc":
                # Check if Jinja2 is available
                if not check_jinja2_availability():
                    print("Error: Jinja2 is required for AsciiDoc output. Install it with 'pip install jinja2'", file=sys.stderr)
                    sys.exit(1)
                
                # Output AsciiDoc to stdout
                extra_context = {
                    "lab_name": showroom.lab_name,
                    "git_url": showroom.git_url,
                    "git_ref": showroom.git_ref,
                }
                output_basemodel_as_adoc(description, extra_context)
            else:
                # Verbose console output (current behavior)
                console.print("\n[bold green]✅ AI Description Generated Successfully![/bold green]")
                print_basemodel(description, "Catalog Description")

                # Save to workspace
                saved_path = save_description_to_workspace(description)
                console.print(f"\n[blue]💾 Description saved to: {saved_path}[/blue]")

            # Update the showroom object with the description
            showroom.description_output = description

        else:
            if is_clean_output:
                # For clean output modes, print error to stderr and exit
                print(f"Error: {metadata.get('error', 'Failed to generate description')}", file=sys.stderr)
                sys.exit(1)
            else:
                console.print("\n[red]❌ Failed to generate AI description[/red]")
                if metadata.get("error"):
                    console.print(f"[red]Error: {metadata['error']}[/red]")
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

    if not repo_url:
        if is_json_output:
            print("Error: Repository URL is required", file=sys.stderr)
            sys.exit(1)
        else:
            console.print("[red]Error: Repository URL is required[/red]")
            console.print("Usage: showroom-tool <command> <repo_url> [options]")
        sys.exit(1)

    if args.verbose and not is_json_output:
        console.print(f"[blue]Processing repository: {repo_url}[/blue]")
        console.print("[blue]Using LangGraph processing...[/blue]")

    # Import the LangGraph function
    from showroom_tool.graph_factory import process_showroom_with_graph

    try:
        # For JSON output, suppress verbose output from LangGraph
        result = await process_showroom_with_graph(
            git_url=repo_url,
            git_ref=args.ref,
            verbose=args.verbose and not is_json_output,
            cache_dir=args.cache_dir,
            no_cache=args.no_cache
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

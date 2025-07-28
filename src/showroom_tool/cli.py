#!/usr/bin/env python

"""
CLI entry point for showroom-tool that works properly when installed.
"""

import argparse
import hashlib
import re
import shutil
import sys
import tempfile
from pathlib import Path

import git
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Try to import from the installed package structure
try:
    from config.basemodels import Showroom, ShowroomModule
except ImportError:
    # Fall back to adding the project root to path (for development)
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from config.basemodels import Showroom, ShowroomModule

console = Console()


def get_cache_directory(custom_cache_dir: str | None = None) -> Path:
    """Get the cache directory path, creating it if it doesn't exist."""
    if custom_cache_dir:
        cache_dir = Path(custom_cache_dir)
    else:
        # Use user's home directory cache
        home = Path.home()
        cache_dir = home / ".showroom-tool" / "cache"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def generate_cache_key(git_url: str, git_ref: str) -> str:
    """Generate a unique cache key for the repo URL and ref combination."""
    # Normalize the URL (remove .git suffix, handle different protocols)
    normalized_url = git_url.lower()
    if normalized_url.endswith(".git"):
        normalized_url = normalized_url[:-4]

    # Create a hash of the URL and ref for a clean directory name
    key_string = f"{normalized_url}#{git_ref}"
    cache_key = hashlib.md5(key_string.encode()).hexdigest()
    return cache_key


def is_cached_repo_current(
    repo_path: Path, git_ref: str, verbose: bool = False
) -> bool:
    """Check if the cached repository is up to date with the remote."""
    try:
        repo = git.Repo(repo_path)

        # Fetch latest information from remote
        if verbose:
            console.print("[blue]Checking if cached repo is up to date...[/blue]")

        origin = repo.remotes.origin
        origin.fetch()

        # Get local and remote commit hashes
        try:
            local_commit = repo.commit(git_ref).hexsha
            remote_commit = repo.commit(f"origin/{git_ref}").hexsha

            is_current = local_commit == remote_commit
            if verbose:
                if is_current:
                    console.print("[green]Cached repo is up to date[/green]")
                else:
                    console.print(
                        "[yellow]Cached repo is outdated, will update[/yellow]"
                    )

            return is_current

        except git.exc.BadName:
            # Handle case where ref doesn't exist remotely
            if verbose:
                console.print(
                    f"[yellow]Reference '{git_ref}' not found, will refresh cache[/yellow]"
                )
            return False

    except Exception as e:
        if verbose:
            console.print(f"[yellow]Error checking cache status: {e}[/yellow]")
        return False


def update_cached_repo(repo_path: Path, git_ref: str, verbose: bool = False) -> bool:
    """Update the cached repository to the latest version."""
    try:
        repo = git.Repo(repo_path)

        if verbose:
            console.print("[blue]Updating cached repository...[/blue]")

        # Fetch latest changes
        origin = repo.remotes.origin
        origin.fetch()

        # Checkout the desired ref
        repo.git.checkout(git_ref)

        # If it's a branch, pull the latest changes
        try:
            if git_ref in [ref.name for ref in repo.remotes.origin.refs]:
                repo.git.pull("origin", git_ref)
        except git.exc.GitCommandError:
            # If pull fails, it might be a tag or commit hash
            pass

        if verbose:
            console.print("[green]Cached repository updated successfully[/green]")

        return True

    except Exception as e:
        if verbose:
            console.print(f"[red]Error updating cached repo: {e}[/red]")
        return False


def get_or_clone_repository(
    git_url: str,
    git_ref: str = "main",
    cache_dir: str | None = None,
    no_cache: bool = False,
    verbose: bool = False,
) -> Path | None:
    """
    Get repository from cache or clone if needed.

    Returns the path to the repository directory, or None on error.
    """
    if no_cache:
        # Use temporary directory when caching is disabled
        temp_dir = tempfile.mkdtemp()
        repo_path = Path(temp_dir) / "showroom"

        if verbose:
            console.print("[blue]Caching disabled, using temporary clone[/blue]")

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Cloning repository {git_url}...", total=None)

                repo = git.Repo.clone_from(git_url, repo_path)

                if git_ref != "main":
                    try:
                        repo.git.checkout(git_ref)
                    except git.exc.GitCommandError as e:
                        console.print(
                            f"[red]Error checking out ref '{git_ref}': {e}[/red]"
                        )
                        return None

                progress.update(task, description="Repository cloned successfully")

            return repo_path

        except git.exc.GitCommandError as e:
            console.print(f"[red]Git error: {e}[/red]")
            return None

    # Use caching
    cache_base_dir = get_cache_directory(cache_dir)
    cache_key = generate_cache_key(git_url, git_ref)
    repo_path = cache_base_dir / cache_key

    if verbose:
        console.print(f"[blue]Using cache directory: {repo_path}[/blue]")

    # Check if cached repo exists
    if repo_path.exists() and (repo_path / ".git").exists():
        # Cached repo exists, check if it's current
        if is_cached_repo_current(repo_path, git_ref, verbose):
            if verbose:
                console.print("[green]Using cached repository[/green]")
            return repo_path
        else:
            # Try to update the cached repo
            if update_cached_repo(repo_path, git_ref, verbose):
                return repo_path
            else:
                # Update failed, remove cache and re-clone
                if verbose:
                    console.print(
                        "[yellow]Update failed, removing cache and re-cloning[/yellow]"
                    )
                shutil.rmtree(repo_path, ignore_errors=True)

    # Clone fresh repository
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            if repo_path.exists():
                task = progress.add_task(
                    f"Re-cloning repository {git_url}...", total=None
                )
            else:
                task = progress.add_task(
                    f"Cloning repository {git_url} to cache...", total=None
                )

            repo = git.Repo.clone_from(git_url, repo_path)

            if git_ref != "main":
                try:
                    repo.git.checkout(git_ref)
                except git.exc.GitCommandError as e:
                    console.print(f"[red]Error checking out ref '{git_ref}': {e}[/red]")
                    return None

            progress.update(task, description="Repository cloned successfully")

        if verbose:
            console.print("[green]Repository cached for future use[/green]")

        return repo_path

    except git.exc.GitCommandError as e:
        console.print(f"[red]Git error: {e}[/red]")
        return None


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


def extract_lab_info_from_site_yaml(repo_path: Path) -> tuple[str, str]:
    """Extract lab name and start page from default-site.yml file."""
    site_yaml_path = repo_path / "default-site.yml"

    if not site_yaml_path.exists():
        console.print(
            f"[yellow]Warning: default-site.yml not found at {site_yaml_path}[/yellow]"
        )
        return "", ""

    try:
        with open(site_yaml_path, encoding="utf-8") as f:
            site_config = yaml.safe_load(f)

        lab_name = ""
        start_page = ""

        # Extract title and start_page from site section
        if isinstance(site_config, dict) and "site" in site_config:
            site_section = site_config["site"]
            if isinstance(site_section, dict):
                if "title" in site_section:
                    lab_name = site_section["title"]
                if "start_page" in site_section:
                    # Extract filename from start_page (e.g., "modules::index.adoc" -> "index.adoc")
                    start_page_value = site_section["start_page"]
                    if "::" in start_page_value:
                        start_page = start_page_value.split("::")[-1]
                    else:
                        start_page = start_page_value

        return lab_name, start_page

    except (OSError, yaml.YAMLError, KeyError) as e:
        console.print(f"[red]Error reading default-site.yml: {e}[/red]")
        return "", ""


def count_words_and_lines(content: str) -> tuple[int, int]:
    """Count words and lines in the given content."""
    if not content.strip():
        return 0, 0

    # Count lines (non-empty lines)
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    line_count = len(lines)

    # Count words (split by whitespace)
    words = content.split()
    word_count = len(words)

    return word_count, line_count


def extract_module_name_from_content(content: str) -> str:
    """Extract module name from the first level 1 or level 2 header found."""
    lines = content.split("\n")

    # Helper function to extract title from prefix-style headers
    def extract_title_from_prefix(line: str, expected_prefix: str) -> str:
        """Extract title from = Title or == Title format."""
        if line.startswith(expected_prefix) and not line.startswith(
            expected_prefix + "="
        ):
            # Remove leading = or == and any trailing = and whitespace
            title = line[len(expected_prefix) :].strip()
            if title.endswith("="):
                title = title[:-1].strip()
            return title if title else ""
        return ""

    # Helper function to check underline-style headers
    def check_underline_header(lines: list, line_idx: int, underline_char: str) -> str:
        """Check for Title\n===== or Title\n----- format."""
        if line_idx < len(lines) - 1:
            current_line = lines[line_idx].strip()
            next_line = lines[line_idx + 1].strip()
            if (
                next_line
                and all(c == underline_char for c in next_line)
                and len(next_line) >= len(current_line)
                and current_line
            ):
                return current_line
        return ""

    # First pass: Look for level 1 headers (= Title or Title\n=====)
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check prefix-style level 1 headers: = Title
        title = extract_title_from_prefix(stripped, "=")
        if title:
            return title

        # Check underline-style level 1 headers: Title\n=====
        title = check_underline_header(lines, i, "=")
        if title:
            return title

    # Second pass: Look for level 2 headers if no level 1 found
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check prefix-style level 2 headers: == Title
        title = extract_title_from_prefix(stripped, "==")
        if title:
            return title

        # Check underline-style level 2 headers: Title\n-----
        title = check_underline_header(lines, i, "-")
        if title:
            return title

    return ""


def parse_navigation_file(nav_path: Path) -> list[str]:
    """Parse the nav.adoc file to extract ordered list of level 1 module files only."""
    if not nav_path.exists():
        console.print(
            f"[yellow]Warning: Navigation file not found at {nav_path}[/yellow]"
        )
        return []

    try:
        with open(nav_path, encoding="utf-8") as f:
            content = f.read()
    except OSError as e:
        console.print(f"[red]Error reading navigation file: {e}[/red]")
        return []

    # Extract .adoc file references from level 1 navigation entries only
    # Level 1 entries start with single "*" (not "**", "***", etc.)
    module_files = []
    seen_files = set()  # Track files we've already added to avoid duplicates
    lines = content.split("\n")

    for line in lines:
        stripped = line.strip()

        # Only process level 1 navigation entries (single * at start)
        # Skip nested entries (**, ***, etc.) and non-list items
        if not stripped.startswith("* ") or stripped.startswith("** "):
            continue

        # Match xref patterns: xref:filename.adoc[Display Text]
        xref_match = re.search(r"xref:([^[\]]+\.adoc)", stripped)
        if xref_match:
            filename = xref_match.group(1)
            if filename not in seen_files:
                module_files.append(filename)
                seen_files.add(filename)
            continue

        # Match link patterns: link:filename.adoc[Display Text]
        link_match = re.search(r"link:([^[\]]+\.adoc)", stripped)
        if link_match:
            filename = link_match.group(1)
            if filename not in seen_files:
                module_files.append(filename)
                seen_files.add(filename)

    return module_files


def read_module_content(pages_dir: Path, filename: str) -> tuple[str, str]:
    """Read module content and extract module name."""
    module_path = pages_dir / filename

    if not module_path.exists():
        console.print(
            f"[yellow]Warning: Module file not found at {module_path}[/yellow]"
        )
        return "", ""

    try:
        with open(module_path, encoding="utf-8") as f:
            content = f.read()

        module_name = extract_module_name_from_content(content)
        return module_name, content

    except OSError as e:
        console.print(f"[red]Error reading module file {filename}: {e}[/red]")
        return "", ""


def fetch_showroom_repository(
    git_url: str,
    git_ref: str = "main",
    verbose: bool = False,
    cache_dir: str | None = None,
    no_cache: bool = False,
) -> Showroom | None:
    """
    Fetch a showroom repository and parse it into a Showroom BaseModel.

    Args:
        git_url: URL of the git repository
        git_ref: Git reference to checkout (branch, tag, or commit)
        verbose: Enable verbose output
        cache_dir: Custom cache directory (uses default if None)
        no_cache: Disable caching and force fresh clone

    Returns:
        Populated Showroom instance or None on error
    """

    # Get repository using caching system
    repo_path = get_or_clone_repository(git_url, git_ref, cache_dir, no_cache, verbose)

    if repo_path is None:
        return None

    try:
        # Extract lab name and start page from default-site.yml
        lab_name, start_page = extract_lab_info_from_site_yaml(repo_path)
        if verbose:
            console.print(
                f"[blue]Extracted lab name: '{lab_name}' and start page: '{start_page}'[/blue]"
            )

        # Parse navigation file to get ordered list of modules
        nav_path = repo_path / "content" / "modules" / "ROOT" / "nav.adoc"
        module_files = parse_navigation_file(nav_path)

        if verbose:
            console.print(
                f"[blue]Found {len(module_files)} modules in navigation: {module_files}[/blue]"
            )
            console.print(
                "[blue]Navigation parsing - level 1 entries only, duplicates removed[/blue]"
            )

        # Read each module file and create ShowroomModule instances
        pages_dir = repo_path / "content" / "modules" / "ROOT" / "pages"
        modules = []

        for filename in module_files:
            module_name, module_content = read_module_content(pages_dir, filename)

            if module_content:  # Only add if we successfully read content
                # Use site title for start page if no module title was extracted
                if not module_name and filename == start_page and lab_name:
                    module_name = lab_name

                showroom_module = ShowroomModule(
                    module_name=module_name,
                    filename=filename,
                    module_content=module_content,
                )
                modules.append(showroom_module)

                if verbose:
                    word_count, line_count = count_words_and_lines(module_content)
                    if filename == start_page and module_name == lab_name:
                        name_display = f"'{module_name}' (from site title)"
                    else:
                        name_display = (
                            f"'{module_name}'" if module_name else "'(no title found)'"
                        )
                    console.print(
                        f"[blue]Added module: {name_display} from {filename} ({word_count} words, {line_count} lines)[/blue]"
                    )

        # Create and return the Showroom instance
        showroom = Showroom(
            lab_name=lab_name, git_url=git_url, git_ref=git_ref, modules=modules
        )

        console.print(
            f"[green]Successfully fetched showroom lab: '{lab_name}' with {len(modules)} modules[/green]"
        )
        return showroom

    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        return None
    finally:
        # Clean up temporary directory if caching was disabled
        if no_cache and repo_path and repo_path.parent.name.startswith("tmp"):
            shutil.rmtree(repo_path.parent, ignore_errors=True)


def main():
    """Main CLI entry point."""
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
        if args.no_cache:
            console.print("[blue]Cache disabled - will use temporary clone[/blue]")
        elif args.cache_dir:
            console.print(
                f"[blue]Using custom cache directory: {args.cache_dir}[/blue]"
            )

    # Fetch the showroom repository
    showroom = fetch_showroom_repository(
        repo_url, args.ref, args.verbose, args.cache_dir, args.no_cache
    )

    if showroom is None:
        console.print("[red]Failed to fetch showroom repository[/red]")
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
            # In normal mode, just show module name with colors
            from rich.markup import escape

            safe_display_name = escape(module.module_name)

            # Count words and lines for meaningful metrics
            word_count, line_count = count_words_and_lines(module.module_content)

            module_line = (
                f"    [bright_white]{i}.[/bright_white] "
                f"[bold]{safe_display_name}[/bold] "
                f"[dim]({word_count} words, {line_count} lines)[/dim]"
            )
            console.print(module_line)

    if args.verbose:
        console.print("\n[blue]Showroom data model successfully populated[/blue]")


if __name__ == "__main__":
    main()

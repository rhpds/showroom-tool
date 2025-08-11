#!/usr/bin/env python

"""
Showroom processing library.

This module contains functions for managing Showroom repositories,
including caching, git operations, and content processing.
"""

import hashlib
import re
import shutil
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
    import sys
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from config.basemodels import Showroom, ShowroomModule

console = Console()


# Cache Management Functions

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

    # Create a hash of the URL and ref for a consistent, filesystem-safe key
    content_to_hash = f"{normalized_url}#{git_ref}"
    hash_object = hashlib.sha256(content_to_hash.encode())
    return hash_object.hexdigest()[:16]  # Use first 16 chars for brevity


def is_cached_repo_current(
    repo_path: Path, target_ref: str, verbose: bool = False
) -> bool:
    """
    Check if the cached repository is current for the target ref.

    Args:
        repo_path: Path to the cached repository
        target_ref: The git reference we want to check out
        verbose: Enable verbose output

    Returns:
        True if the cached repo is current, False otherwise
    """
    try:
        repo = git.Repo(repo_path)

        # Get current HEAD commit
        current_commit = repo.head.commit.hexsha

        # If target_ref is 'main' or 'master', we need to check the remote
        if target_ref in ["main", "master"]:
            try:
                # Fetch latest from origin without merge
                repo.remotes.origin.fetch()
                # Get the latest commit from the remote branch
                remote_branch = f"origin/{target_ref}"
                if remote_branch in [ref.name for ref in repo.refs]:
                    remote_commit = repo.refs[remote_branch].commit.hexsha
                    is_current = current_commit == remote_commit
                    if verbose:
                        if is_current:
                            console.print(
                                f"[green]Cached repo is current (commit: {current_commit[:8]})[/green]"
                            )
                        else:
                            console.print(
                                f"[yellow]Cached repo is outdated. Current: {current_commit[:8]}, Remote: {remote_commit[:8]}[/yellow]"
                            )
                    return is_current
            except Exception as e:
                if verbose:
                    console.print(
                        f"[yellow]Could not check remote ref, assuming cache is stale: {e}[/yellow]"
                    )
                return False

        # For specific commits/tags, check if we have the right commit
        try:
            target_commit = repo.commit(target_ref).hexsha
            is_current = current_commit == target_commit
            if verbose:
                status = "current" if is_current else "different"
                console.print(
                    f"[green]Cache status: {status} (target: {target_commit[:8]}, cached: {current_commit[:8]})[/green]"
                )
            return is_current
        except Exception:
            # If we can't resolve the target ref, assume cache is not current
            if verbose:
                console.print(
                    f"[yellow]Cannot resolve target ref '{target_ref}', assuming cache is stale[/yellow]"
                )
            return False

    except Exception as e:
        if verbose:
            console.print(f"[red]Error checking cached repo status: {e}[/red]")
        return False


def update_cached_repo(repo_path: Path, git_ref: str, verbose: bool = False) -> bool:
    """
    Update the cached repository to the target ref.

    Args:
        repo_path: Path to the cached repository
        git_ref: The git reference to checkout
        verbose: Enable verbose output

    Returns:
        True if update was successful, False otherwise
    """
    try:
        repo = git.Repo(repo_path)

        if verbose:
            console.print(f"[blue]Updating cached repo to ref: {git_ref}[/blue]")

        # Fetch latest changes from origin
        repo.remotes.origin.fetch()

        # Checkout the target ref
        repo.git.checkout(git_ref)

        if verbose:
            current_commit = repo.head.commit.hexsha
            console.print(
                f"[green]Successfully updated cache to {git_ref} (commit: {current_commit[:8]})[/green]"
            )

        return True

    except Exception as e:
        if verbose:
            console.print(f"[red]Failed to update cached repo: {e}[/red]")
        return False


# Git Repository Functions

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
                    except git.GitCommandError as e:
                        console.print(
                            f"[red]Error checking out ref '{git_ref}': {e}[/red]"
                        )
                        return None

                progress.update(task, description="Repository cloned successfully")

            return repo_path

        except git.GitCommandError as e:
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
                except git.GitCommandError as e:
                    if verbose:
                        console.print(f"[red]Error checking out ref '{git_ref}': {e}[/red]")
                    return None

            progress.update(task, description="Repository cloned successfully")

        if verbose:
            console.print("[green]Repository cached for future use[/green]")

        return repo_path

    except git.GitCommandError as e:
        if verbose:
            console.print(f"[red]Git error: {e}[/red]")
        return None


# Content Processing Functions

def count_words_and_lines(content: str) -> tuple[int, int]:
    """Count words and lines in content, excluding empty lines."""
    lines = [line.strip() for line in content.split("\n") if line.strip()]
    words = len(content.split())
    return words, len(lines)


def extract_lab_info_from_site_yaml(repo_path: Path) -> tuple[str, str]:
    """Extract lab name and start page from default-site.yml."""
    site_yaml_path = repo_path / "default-site.yml"

    if not site_yaml_path.exists():
        raise FileNotFoundError(f"Site configuration not found at {site_yaml_path}")

    with open(site_yaml_path, encoding="utf-8") as f:
        site_config = yaml.safe_load(f)

    # Extract required information
    lab_name = site_config.get("site", {}).get("title", "")
    start_page = site_config.get("site", {}).get("start_page", "")

    if not lab_name:
        raise ValueError("Lab name (site.title) not found in default-site.yml")

    if not start_page:
        raise ValueError("Start page (site.start_page) not found in default-site.yml")

    return lab_name, start_page


def parse_navigation_file(nav_path: Path) -> list[str]:
    """Parse navigation file and return list of module filenames."""
    if not nav_path.exists():
        raise FileNotFoundError(f"Navigation file not found at {nav_path}")

    with open(nav_path, encoding="utf-8") as f:
        nav_content = f.read()

    # Parse only level 1 navigation entries (starting with "* xref:")
    # This avoids duplicates from nested entries
    module_files = []
    seen_files = set()

    for line in nav_content.split("\n"):
        line = line.strip()

        # Look for level 1 navigation entries only
        if line.startswith("* xref:"):
            # Extract filename from xref syntax: "* xref:filename.adoc[Title]"
            match = re.search(r"\* xref:([^[\]]+)\.adoc", line)
            if match:
                filename = f"{match.group(1)}.adoc"
                if filename not in seen_files:
                    module_files.append(filename)
                    seen_files.add(filename)

    return module_files


def extract_module_name_from_content(content: str) -> str:
    """Extract module name from AsciiDoc content headers."""
    lines = content.split("\n")

    # Try to find level 1 header (= Title)
    for line in lines:
        line = line.strip()
        if line.startswith("= ") and len(line) > 2:
            return line[2:].strip()

    # Try to find level 1 underline-style header
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            line = line.strip()
            next_line = lines[i + 1].strip()
            if line and next_line and all(c == "=" for c in next_line):
                return line

    # Fallback to level 2 header (== Title)
    for line in lines:
        line = line.strip()
        if line.startswith("== ") and len(line) > 3:
            return line[3:].strip()

    # Fallback to level 2 underline-style header
    for i, line in enumerate(lines):
        if i < len(lines) - 1:
            line = line.strip()
            next_line = lines[i + 1].strip()
            if line and next_line and all(c == "-" for c in next_line):
                return line

    return ""


def read_module_content(pages_dir: Path, filename: str, verbose: bool = False) -> tuple[str, str]:
    """Read module content and extract module name."""
    module_path = pages_dir / filename

    if not module_path.exists():
        if verbose:
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
        if verbose:
            console.print(f"[red]Error reading module file {filename}: {e}[/red]")
        return "", ""


# Main Showroom Processing Function

def fetch_showroom_repository(
    git_url: str | None = None,
    git_ref: str = "main",
    verbose: bool = False,
    cache_dir: str | None = None,
    no_cache: bool = False,
    local_dir: str | None = None,
) -> Showroom | None:
    """
    Fetch a showroom repository and parse it into a Showroom BaseModel.

    Args:
        git_url: URL of the git repository (omit if using local_dir)
        git_ref: Git reference to checkout (ignored when using local_dir)
        verbose: Enable verbose output
        cache_dir: Custom cache directory (uses default if None)
        no_cache: Disable caching and force fresh clone
        local_dir: Path to a pre-cloned local Showroom repository (no caching, no checkout)

    Returns:
        Populated Showroom instance or None on error
    """

    # Determine repository path
    if local_dir:
        repo_path = Path(local_dir).resolve()
        if not repo_path.exists() or not (repo_path / ".git").exists():
            if verbose:
                console.print(f"[red]Local directory is not a git repository: {repo_path}[/red]")
            return None
        if verbose:
            console.print(f"[blue]Using local showroom repository at: {repo_path}[/blue]")
        effective_git_url = str(repo_path)
    else:
        # Get repository using caching system
        if not git_url:
            if verbose:
                console.print("[red]git_url is required when --dir is not provided[/red]")
            return None
        repo_path = get_or_clone_repository(git_url, git_ref, cache_dir, no_cache, verbose)
        effective_git_url = git_url

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
            module_name, module_content = read_module_content(pages_dir, filename, verbose)

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
            lab_name=lab_name,
            git_url=effective_git_url,
            git_ref=git_ref if not local_dir else "(local)",
            modules=modules,
        )

        if verbose:
            console.print(
                f"[green]Successfully fetched showroom lab: '{lab_name}' with {len(modules)} modules[/green]"
            )
        return showroom

    except Exception as e:
        if verbose:
            console.print(f"[red]Unexpected error: {e}[/red]")
        return None
    finally:
        # Clean up temporary directory if caching was disabled
        if no_cache and repo_path and repo_path.parent.name.startswith("tmp"):
            shutil.rmtree(repo_path.parent, ignore_errors=True)

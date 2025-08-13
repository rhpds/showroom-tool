import sys
from pathlib import Path

import pytest

# Ensure src/ is importable in tests without editable install
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@pytest.mark.asyncio
async def test_process_with_local_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """process_showroom_with_graph should accept local_dir and ignore git ops."""
    from showroom_tool.graph_factory import process_showroom_with_graph

    # Create a minimal fake repo structure
    repo_root = tmp_path / "repo"
    (repo_root / ".git").mkdir(parents=True)
    # default-site.yml
    (repo_root / "default-site.yml").write_text(
        "site:\n  title: Test Lab\n  start_page: index.adoc\n", encoding="utf-8"
    )
    # nav.adoc
    nav_dir = repo_root / "content" / "modules" / "ROOT"
    pages_dir = nav_dir / "pages"
    pages_dir.mkdir(parents=True)
    (nav_dir / "nav.adoc").write_text("* xref:index.adoc[Intro]", encoding="utf-8")
    # index.adoc page
    (pages_dir / "index.adoc").write_text("= Intro\nHello world", encoding="utf-8")

    result = await process_showroom_with_graph(
        git_url="",  # ignored when local_dir is provided
        git_ref="main",
        verbose=False,
        cache_dir=None,
        no_cache=True,
        local_dir=str(repo_root),
        command=None,
    )

    assert result.get("success") is True
    assert result.get("lab_name") == "Test Lab"
    assert result.get("module_count") == 1


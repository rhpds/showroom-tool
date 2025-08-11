import sys
from pathlib import Path
from typing import Any

import pytest


# Ensure src/ is importable in tests without editable install
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from config.basemodels import Showroom, ShowroomModule  # noqa: E402


@pytest.mark.asyncio
async def test_graph_fetch_only_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure START -> get_showroom -> END returns final_output when no command is provided."""
    from showroom_tool import graph_factory as gf  # noqa: E402

    # Create a dummy showroom to return from fetch function
    dummy_showroom = Showroom(
        lab_name="Dummy Lab",
        git_url="https://example.com/repo.git",
        git_ref="main",
        modules=[
            ShowroomModule(
                module_name="Intro",
                filename="index.adoc",
                module_content="= Intro\nHello",
            )
        ],
    )

    def fake_fetch_showroom_repository(**kwargs: Any) -> Showroom:
        return dummy_showroom

    # Patch the repository fetcher to avoid IO
    monkeypatch.setattr(gf, "fetch_showroom_repository", fake_fetch_showroom_repository)

    # Invoke graph with no command (fetch-only)
    result = await gf.process_showroom_with_graph(
        git_url="https://does-not-matter.example/repo.git",
        git_ref="main",
        verbose=False,
        cache_dir=None,
        no_cache=True,
        local_dir=None,
        command=None,
    )

    assert isinstance(result, dict)
    assert result.get("success") is True
    assert result.get("lab_name") == "Dummy Lab"
    assert result.get("module_count") == 1
    assert "showroom_data" in result


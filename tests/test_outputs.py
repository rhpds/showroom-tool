import sys
from pathlib import Path


# Ensure src/ is importable in tests without editable install
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


def test_check_jinja2_availability_imports() -> None:
    from showroom_tool.outputs import check_jinja2_availability

    # Should not raise on import, returns a boolean
    assert isinstance(check_jinja2_availability(), bool)


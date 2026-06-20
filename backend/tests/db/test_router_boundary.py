from pathlib import Path

ROUTERS_DIR = Path(__file__).resolve().parents[2] / "routers"

FORBIDDEN = (
    "from sqlalchemy.future import select",
    "from sqlalchemy import select",
    "select(",
)


def test_routers_do_not_build_queries():
    offenders = []
    for path in ROUTERS_DIR.glob("*.py"):
        source = path.read_text()
        for token in FORBIDDEN:
            if token in source:
                offenders.append(f"{path.name}: {token!r}")
    assert not offenders, f"Routers must use queries.py, not raw queries: {offenders}"

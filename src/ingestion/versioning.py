from copy import deepcopy
from datetime import datetime, timezone


def now_iso() -> str:
    """UTC timestamp used for valid_from / valid_until."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_current(row: dict) -> bool:
    return row.get("valid_until") is None


def current_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if is_current(row)]


def close_version(row: dict, valid_until: str | None = None) -> dict:
    """Mark a current version as closed. Mutates and returns the row."""
    row["valid_until"] = valid_until or now_iso()
    return row


def next_ids(rows: list[dict]) -> tuple[int, int]:
    """Return (next version id, next entity_id) from existing rows."""
    if not rows:
        return 1, 1
    next_id = max(row["id"] for row in rows) + 1
    next_entity_id = max(row["entity_id"] for row in rows) + 1
    return next_id, next_entity_id


def copy_row(row: dict) -> dict:
    return deepcopy(row)

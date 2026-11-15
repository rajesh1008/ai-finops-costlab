"""Effective-dated ownership (Chapter 6).

Each row says: from this date, this cost object belongs to this team. A lookup takes the date of
the spend, never today's date, so a reorganisation changes the future and leaves history alone.
"""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Assignment:
    cost_object: str
    team: str
    valid_from: date
    valid_to: date | None = None   # exclusive; None means open


def owner_on(table: list[Assignment], cost_object: str, day: date) -> str | None:
    hits = [a for a in table if a.cost_object == cost_object and a.valid_from <= day and (a.valid_to is None or day < a.valid_to)]
    if not hits:
        return None
    if len(hits) > 1:
        raise ValueError(f"overlapping assignments for {cost_object} on {day}")
    return hits[0].team


def latest_owner(table: list[Assignment], cost_object: str) -> str | None:
    open_rows = [a for a in table if a.cost_object == cost_object and a.valid_to is None]
    return open_rows[0].team if open_rows else None


def check_gaps_and_overlaps(table: list[Assignment], cost_object: str, start: date, end: date) -> list[str]:
    from datetime import timedelta
    problems, d = [], start
    while d <= end:
        try:
            if owner_on(table, cost_object, d) is None:
                problems.append(f"{d}: no owner")
        except ValueError as e:
            problems.append(str(e))
        d += timedelta(days=1)
    return problems


@dataclass(frozen=True)
class TeamName:
    team_id: str
    name: str
    valid_from: date
    valid_to: date | None = None


def name_on(names: list[TeamName], team_id: str, day: date) -> str | None:
    hits = [n for n in names if n.team_id == team_id and n.valid_from <= day and (n.valid_to is None or day < n.valid_to)]
    return hits[0].name if hits else None

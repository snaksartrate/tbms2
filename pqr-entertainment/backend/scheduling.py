from dbwrap import db
from datetime import datetime, timedelta

def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return max(a_start, b_start) < min(a_end, b_end)

def has_conflict(theatre_id: int, screen_number: int, start_iso: str, end_iso: str, exclude_screen_id: int = None) -> bool:
    """Return True if proposed [start,end] overlaps an existing show on same theatre+screen"""
    q = (
        "SELECT screen_id, start_time, end_time FROM scheduled_screens "
        "WHERE theatre_id = ? AND screen_number = ?"
    )
    params = [theatre_id, screen_number]
    if exclude_screen_id is not None:
        q += " AND screen_id <> ?"
        params.append(exclude_screen_id)
    rows = db.execute_query(q, tuple(params), fetch_all=True) or []
    start = datetime.fromisoformat(start_iso)
    end = datetime.fromisoformat(end_iso)
    for r in rows:
        rs = datetime.fromisoformat(r['start_time'])
        re = datetime.fromisoformat(r['end_time'])
        if _overlaps(start, end, rs, re):
            return True
    return False

def suggest_next_slot(theatre_id: int, screen_number: int, start_iso: str, duration_minutes: int, exclude_screen_id: int = None) -> str:
    """If conflict, suggest the nearest next free slot on same day after proposed start."""
    start = datetime.fromisoformat(start_iso)
    # try stepping in 15-minute increments up to same day 23:59
    for step in range(1, 60):
        candidate_start = (start.replace(second=0, microsecond=0) + timedelta(minutes=15*step))
        candidate_end = candidate_start + timedelta(minutes=duration_minutes)
        # same date
        if candidate_start.date() != start.date():
            break
        if not has_conflict(theatre_id, screen_number, candidate_start.isoformat(), candidate_end.isoformat(), exclude_screen_id):
            return candidate_start.isoformat()
    return ""

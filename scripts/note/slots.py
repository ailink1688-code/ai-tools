"""毎日06:30/12:00/18:00(JST)の予約枠のうち、次に空いている枠を計算する。"""
from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
DAILY_TIMES = (time(6, 30), time(12, 0), time(18, 0))
MIN_LEAD = timedelta(minutes=30)


def load_booked_slots(log_path: Path) -> set[datetime]:
    if not log_path.exists():
        return set()
    entries = json.loads(log_path.read_text(encoding="utf-8") or "[]")
    return {datetime.fromisoformat(e["slot"]) for e in entries}


def compute_next_slot(now: datetime, booked: set[datetime]) -> datetime:
    """now以降で、MIN_LEAD以上先、かつbookedと重複しない最初の枠を返す。"""
    if now.tzinfo is None:
        now = now.replace(tzinfo=JST)
    day = now.date()
    for _ in range(366 * 3 + 1):
        for t in DAILY_TIMES:
            candidate = datetime.combine(day, t, tzinfo=JST)
            if candidate >= now + MIN_LEAD and candidate not in booked:
                return candidate
        day += timedelta(days=1)
    raise RuntimeError("空いている予約枠が見つかりませんでした")


def record_slot(log_path: Path, title: str, slot: datetime) -> None:
    entries = []
    if log_path.exists():
        entries = json.loads(log_path.read_text(encoding="utf-8") or "[]")
    entries.append(
        {
            "title": title,
            "slot": slot.isoformat(),
            "recorded_at": datetime.now(JST).isoformat(),
        }
    )
    log_path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    demo_log = Path("/tmp/_slots_demo.json")
    demo_log.unlink(missing_ok=True)
    now = datetime.now(JST)
    for title in ["記事A", "記事B", "記事C", "記事D"]:
        booked = load_booked_slots(demo_log)
        slot = compute_next_slot(now, booked)
        record_slot(demo_log, title, slot)
        print(f"{title}: {slot.isoformat()}")

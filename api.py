import time
from datetime import datetime, timezone
from typing import Iterator, Optional

import requests

from models import Exercise, Set, Workout, infer_muscle_group

BASE_URL = "https://api.hevyapp.com/v1"
PAGE_SIZE = 10
RATE_LIMIT_RETRY_AFTER = 60


class HevyAPIError(Exception):
    pass


class HevyClient:
    def __init__(self, api_key: str):
        self.session = requests.Session()
        self.session.headers.update({
            "api-key": api_key,
            "Content-Type": "application/json",
        })

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{BASE_URL}{path}"
        for attempt in range(3):
            try:
                resp = self.session.get(url, params=params, timeout=30)
            except requests.ConnectionError as e:
                raise HevyAPIError(f"Connection failed: {e}") from e
            except requests.Timeout:
                raise HevyAPIError("Request timed out after 30s")

            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                raise HevyAPIError("Unauthorized - check that HEVY_API_KEY is correct.")
            elif resp.status_code == 404:
                raise HevyAPIError(f"Endpoint not found: {path}")
            elif resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", RATE_LIMIT_RETRY_AFTER))
                print(f"  Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after)
            else:
                raise HevyAPIError(f"API error {resp.status_code}: {resp.text[:200]}")
        raise HevyAPIError("Exceeded retry limit due to rate limiting.")

    def iter_workouts(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Iterator[Workout]:
        page = 1
        while True:
            data = self._get("/workouts", params={"page": page, "pageSize": PAGE_SIZE})
            workouts_raw = data.get("workouts", [])
            if not workouts_raw:
                break

            for raw in workouts_raw:
                workout = _parse_workout(raw)

                # API returns newest-first, so once we're past start_date we're done
                if end_date and workout.start_time > end_date:
                    continue
                if start_date and workout.start_time < start_date:
                    return

                yield workout

            page_count = data.get("page_count", 1)
            if page >= page_count:
                break
            page += 1


def _parse_set(raw: dict, index: int) -> Set:
    return Set(
        set_number=index + 1,
        set_type=raw.get("set_type", "normal"),
        weight_kg=raw.get("weight_kg"),
        reps=raw.get("reps"),
        rpe=raw.get("rpe"),
        notes=raw.get("notes"),
        duration_seconds=raw.get("duration_seconds"),
        distance_meters=raw.get("distance_meters"),
    )


def _parse_exercise(raw: dict) -> Exercise:
    sets = [_parse_set(s, i) for i, s in enumerate(raw.get("sets", []))]
    title = raw.get("title", "Unknown Exercise")
    exercise = Exercise(
        exercise_template_id=raw.get("exercise_template_id", ""),
        title=title,
        notes=raw.get("notes"),
        sets=sets,
    )
    exercise.muscle_group = infer_muscle_group(title)  # type: ignore[attr-defined]
    return exercise


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    # Hevy sends ISO 8601 with either Z or +00:00
    value = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(value)
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except ValueError:
        return None


def _parse_workout(raw: dict) -> Workout:
    exercises = [_parse_exercise(e) for e in raw.get("exercises", [])]
    return Workout(
        workout_id=raw.get("id", ""),
        title=raw.get("title", "Untitled Workout"),
        start_time=_parse_dt(raw.get("start_time")) or datetime.utcnow(),
        end_time=_parse_dt(raw.get("end_time")),
        notes=raw.get("notes"),
        exercises=exercises,
    )

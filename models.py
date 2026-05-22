from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Set:
    set_number: int
    set_type: str  # "normal", "warmup", "dropset", "failure"
    weight_kg: Optional[float]
    reps: Optional[int]
    rpe: Optional[float]
    notes: Optional[str]
    duration_seconds: Optional[int] = None
    distance_meters: Optional[float] = None


@dataclass
class Exercise:
    exercise_template_id: str
    title: str
    notes: Optional[str]
    sets: list[Set] = field(default_factory=list)

    def total_volume_kg(self) -> float:
        return sum(
            (s.weight_kg or 0) * (s.reps or 0)
            for s in self.sets
            if s.set_type == "normal"
        )

    def max_weight_kg(self) -> float:
        weights = [s.weight_kg for s in self.sets if s.weight_kg is not None]
        return max(weights) if weights else 0.0


@dataclass
class Workout:
    workout_id: str
    title: str
    start_time: datetime
    end_time: Optional[datetime]
    notes: Optional[str]
    exercises: list[Exercise] = field(default_factory=list)

    @property
    def date_str(self) -> str:
        return self.start_time.strftime("%Y-%m-%d")

    @property
    def duration_minutes(self) -> Optional[int]:
        if self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return None

    def total_volume_kg(self) -> float:
        return sum(e.total_volume_kg() for e in self.exercises)

    def total_sets(self) -> int:
        return sum(len(e.sets) for e in self.exercises)


MUSCLE_GROUP_KEYWORDS: dict[str, list[str]] = {
    "Chest": ["bench", "chest", "pec", "fly", "flye", "push up", "pushup", "dip"],
    "Back": ["row", "pull", "lat", "deadlift", "pulldown", "pullup", "chin"],
    "Shoulders": ["shoulder", "press", "lateral raise", "front raise", "delt", "overhead"],
    "Biceps": ["bicep", "curl", "hammer"],
    "Triceps": ["tricep", "extension", "pushdown", "skull"],
    "Legs": ["squat", "leg", "lunge", "calf", "hamstring", "quad", "glute", "hip thrust", "rdl"],
    "Core": ["ab", "core", "plank", "crunch", "sit up", "situp", "oblique"],
    "Cardio": ["run", "bike", "row", "jump", "cardio", "sprint"],
}


def infer_muscle_group(exercise_title: str) -> str:
    lower = exercise_title.lower()
    for group, keywords in MUSCLE_GROUP_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return group
    return "Other"

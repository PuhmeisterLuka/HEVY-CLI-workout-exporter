import csv
from collections import defaultdict

from models import Workout, infer_muscle_group


def export_sets_csv(workouts: list[Workout], output_path: str) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "date", "workout_title", "exercise_name",
            "set_number", "set_type", "weight_kg", "reps", "rpe", "notes",
        ])
        for workout in workouts:
            for exercise in workout.exercises:
                for s in exercise.sets:
                    writer.writerow([
                        workout.date_str,
                        workout.title,
                        exercise.title,
                        s.set_number,
                        s.set_type,
                        _fmt(s.weight_kg),
                        _fmt(s.reps),
                        _fmt(s.rpe),
                        s.notes or "",
                    ])


def export_summary_csv(workouts: list[Workout], output_path: str) -> None:
    volume_by_muscle: dict[str, float] = defaultdict(float)
    pr_by_exercise: dict[str, float] = defaultdict(float)
    total_volume = 0.0

    for workout in workouts:
        for exercise in workout.exercises:
            muscle = infer_muscle_group(exercise.title)
            for s in exercise.sets:
                if s.set_type == "normal" and s.weight_kg and s.reps:
                    vol = s.weight_kg * s.reps
                    volume_by_muscle[muscle] += vol
                    total_volume += vol
                if s.weight_kg:
                    pr_by_exercise[exercise.title] = max(
                        pr_by_exercise[exercise.title], s.weight_kg
                    )

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["=== OVERALL STATS ==="])
        writer.writerow(["total_workouts", len(workouts)])
        writer.writerow(["total_volume_kg", f"{total_volume:.1f}"])
        writer.writerow([])

        writer.writerow(["=== VOLUME BY MUSCLE GROUP (kg) ==="])
        writer.writerow(["muscle_group", "total_volume_kg"])
        for muscle, vol in sorted(volume_by_muscle.items(), key=lambda x: -x[1]):
            writer.writerow([muscle, f"{vol:.1f}"])
        writer.writerow([])

        writer.writerow(["=== PRs (MAX WEIGHT kg) PER EXERCISE ==="])
        writer.writerow(["exercise", "max_weight_kg"])
        for exercise, max_w in sorted(pr_by_exercise.items(), key=lambda x: -x[1]):
            writer.writerow([exercise, f"{max_w:.1f}"])


def _fmt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)

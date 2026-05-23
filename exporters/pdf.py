from collections import defaultdict
from datetime import datetime
from typing import Optional

from fpdf import FPDF, XPos, YPos

from models import Workout, infer_muscle_group

# colors
C_DARK = (30, 30, 40)
C_PRIMARY = (70, 130, 180)
C_LIGHT_BG = (245, 247, 250)
C_ROW_ALT = (235, 240, 248)
C_WHITE = (255, 255, 255)
C_MID = (110, 110, 120)
C_SUCCESS = (60, 160, 80)

PAGE_W = 210
MARGIN = 14
CONTENT_W = PAGE_W - 2 * MARGIN


class WorkoutPDF(FPDF):
    def __init__(self, date_from: str, date_to: str):
        super().__init__()
        self.date_from = date_from
        self.date_to = date_to
        self.set_margins(MARGIN, MARGIN, MARGIN)
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*C_PRIMARY)
        self.rect(0, 0, PAGE_W, 10, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*C_WHITE)
        self.set_xy(MARGIN, 1)
        self.cell(0, 8, "Hevy Workout Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*C_DARK)
        self.ln(2)

    def footer(self):
        self.set_y(-13)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*C_MID)
        self.cell(0, 6, f"Page {self.page_no()}", align="C")

    def h1(self, text: str) -> None:
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*C_PRIMARY)
        self.cell(0, 10, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(*C_DARK)

    def h2(self, text: str) -> None:
        self.ln(2)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*C_PRIMARY)
        self.cell(0, 8, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*C_PRIMARY)
        self.set_line_width(0.4)
        self.line(MARGIN, self.get_y(), PAGE_W - MARGIN, self.get_y())
        self.set_text_color(*C_DARK)
        self.ln(2)

    def h3(self, text: str) -> None:
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*C_DARK)
        self.cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def body(self, text: str, color=None) -> None:
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*(color or C_DARK))
        self.multi_cell(0, 5, text)
        self.set_text_color(*C_DARK)

    def kv_pair(self, key: str, value: str) -> None:
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*C_MID)
        self.cell(48, 6, key.upper())
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*C_DARK)
        self.cell(0, 6, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def table_header(self, cols: list[tuple[str, float, str]]) -> None:
        self.set_fill_color(*C_PRIMARY)
        self.set_text_color(*C_WHITE)
        self.set_font("Helvetica", "B", 8)
        for label, w, align in cols:
            self.cell(w, 6, label, border=0, align=align, fill=True)
        self.ln()
        self.set_text_color(*C_DARK)

    def table_row(self, values: list[tuple[str, float, str]], row_idx: int) -> None:
        fill_color = C_ROW_ALT if row_idx % 2 == 0 else C_WHITE
        self.set_fill_color(*fill_color)
        self.set_font("Helvetica", "", 8)
        for val, w, align in values:
            self.cell(w, 5.5, val, border=0, align=align, fill=True)
        self.ln()


def export_pdf(
    workouts: list[Workout],
    output_path: str,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> None:
    from_str = date_from.strftime("%Y-%m-%d") if date_from else "All time"
    to_str = date_to.strftime("%Y-%m-%d") if date_to else "Today"

    pdf = WorkoutPDF(from_str, to_str)
    _cover_page(pdf, workouts, from_str, to_str)
    _workout_sections(pdf, workouts)
    _summary_section(pdf, workouts)
    pdf.output(output_path)


def _cover_page(pdf: WorkoutPDF, workouts: list[Workout], from_str: str, to_str: str) -> None:
    pdf.add_page()

    pdf.set_fill_color(*C_PRIMARY)
    pdf.rect(0, 0, PAGE_W, 60, "F")
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*C_WHITE)
    pdf.set_xy(MARGIN, 14)
    pdf.cell(0, 12, "Hevy Workout Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 13)
    pdf.set_x(MARGIN)
    pdf.cell(0, 8, f"{from_str}  to  {to_str}")

    pdf.set_text_color(*C_DARK)
    pdf.set_xy(MARGIN, 68)

    total_volume = sum(w.total_volume_kg() for w in workouts)
    total_sets = sum(w.total_sets() for w in workouts)
    unique_exercises = len({e.title for w in workouts for e in w.exercises})

    stats = [
        ("Total Workouts", str(len(workouts))),
        ("Total Volume", f"{total_volume:,.0f} kg"),
        ("Total Sets", str(total_sets)),
        ("Unique Exercises", str(unique_exercises)),
    ]

    col_w = CONTENT_W / 2
    for i, (label, value) in enumerate(stats):
        x = MARGIN + (i % 2) * col_w
        y = 68 + (i // 2) * 24
        pdf.set_fill_color(*C_LIGHT_BG)
        pdf.rect(x, y, col_w - 4, 20, "F")
        pdf.set_xy(x + 3, y + 2)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*C_MID)
        pdf.cell(col_w - 10, 5, label.upper())
        pdf.set_xy(x + 3, y + 8)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*C_DARK)
        pdf.cell(col_w - 10, 8, value)

    pdf.set_xy(MARGIN, 125)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*C_MID)
    generated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    pdf.cell(0, 5, f"Generated: {generated}")


def _workout_sections(pdf: WorkoutPDF, workouts: list[Workout]) -> None:
    if not workouts:
        return

    pdf.add_page()
    pdf.h1("Workout Log")

    cols = [
        ("#", 10, "C"),
        ("Type", 18, "L"),
        ("Weight (kg)", 28, "R"),
        ("Reps", 16, "R"),
        ("RPE", 14, "R"),
        ("Notes", CONTENT_W - 86, "L"),
    ]

    for workout in workouts:
        if pdf.get_y() > 240:
            pdf.add_page()

        pdf.set_fill_color(*C_LIGHT_BG)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*C_PRIMARY)
        pdf.cell(0, 8, f"  {workout.date_str}  |  {workout.title}", fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*C_DARK)

        meta_parts = []
        if workout.duration_minutes:
            meta_parts.append(f"{workout.duration_minutes} min")
        vol = workout.total_volume_kg()
        if vol:
            meta_parts.append(f"{vol:,.0f} kg volume")
        if workout.notes:
            meta_parts.append(f'Note: "{workout.notes}"')
        if meta_parts:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(*C_MID)
            pdf.cell(0, 5, "  " + "  |  ".join(meta_parts),
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(*C_DARK)
        pdf.ln(1)

        for exercise in workout.exercises:
            if pdf.get_y() > 255:
                pdf.add_page()
            pdf.h3(f"    {exercise.title}")
            if exercise.notes:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(*C_MID)
                pdf.cell(0, 4, f"    {exercise.notes}",
                         new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                pdf.set_text_color(*C_DARK)

            pdf.set_x(MARGIN)
            pdf.table_header(cols)

            for idx, s in enumerate(exercise.sets):
                if pdf.get_y() > 268:
                    pdf.add_page()
                    pdf.set_x(MARGIN)
                    pdf.table_header(cols)
                pdf.set_x(MARGIN)
                pdf.table_row([
                    (str(s.set_number), 10, "C"),
                    (s.set_type, 18, "L"),
                    (_or_dash(s.weight_kg, ".1f"), 28, "R"),
                    (_or_dash(s.reps), 16, "R"),
                    (_or_dash(s.rpe, ".1f"), 14, "R"),
                    (s.notes or "", CONTENT_W - 86, "L"),
                ], idx)
            pdf.ln(3)


def _summary_section(pdf: WorkoutPDF, workouts: list[Workout]) -> None:
    pdf.add_page()
    pdf.h1("Summary")

    pdf.h2("Personal Records (max weight per exercise)")

    pr_map: dict[str, float] = defaultdict(float)
    for w in workouts:
        for e in w.exercises:
            for s in e.sets:
                if s.weight_kg:
                    pr_map[e.title] = max(pr_map[e.title], s.weight_kg)

    if pr_map:
        sorted_prs = sorted(pr_map.items(), key=lambda x: -x[1])
        pr_cols = [("Exercise", 120, "L"), ("Max Weight (kg)", CONTENT_W - 120, "R")]
        pdf.set_x(MARGIN)
        pdf.table_header(pr_cols)
        for i, (name, weight) in enumerate(sorted_prs):
            if pdf.get_y() > 265:
                pdf.add_page()
                pdf.set_x(MARGIN)
                pdf.table_header(pr_cols)
            pdf.set_x(MARGIN)
            pdf.table_row([(name, 120, "L"), (f"{weight:.1f}", CONTENT_W - 120, "R")], i)
    else:
        pdf.body("No weighted exercises found.")

    pdf.ln(4)

    if pdf.get_y() > 200:
        pdf.add_page()
    pdf.h2("Volume by Muscle Group")

    vol_map: dict[str, float] = defaultdict(float)
    for w in workouts:
        for e in w.exercises:
            muscle = infer_muscle_group(e.title)
            for s in e.sets:
                if s.set_type == "normal" and s.weight_kg and s.reps:
                    vol_map[muscle] += s.weight_kg * s.reps

    if vol_map:
        sorted_vol = sorted(vol_map.items(), key=lambda x: -x[1])
        max_vol = sorted_vol[0][1] if sorted_vol else 1
        bar_area = CONTENT_W - 80

        for muscle, vol in sorted_vol:
            bar_len = max(1, int((vol / max_vol) * bar_area))
            pct = (vol / sum(vol_map.values())) * 100

            pdf.set_text_color(*C_DARK)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(55, 6, muscle)

            pdf.set_fill_color(*C_PRIMARY)
            bar_y = pdf.get_y() + 1.5
            pdf.rect(pdf.get_x(), bar_y, bar_len, 3.5, "F")
            pdf.set_x(pdf.get_x() + bar_area + 2)

            pdf.set_text_color(*C_MID)
            pdf.cell(0, 6, f"{vol:,.0f} kg ({pct:.1f}%)",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(*C_DARK)
    else:
        pdf.body("No volume data found.")

    pdf.ln(4)

    if pdf.get_y() > 190:
        pdf.add_page()
    pdf.h2("Weekly Volume Trend")
    _weekly_volume_chart(pdf, workouts)


def _weekly_volume_chart(pdf: WorkoutPDF, workouts: list[Workout]) -> None:
    weekly: dict[str, float] = defaultdict(float)
    for w in workouts:
        key = w.start_time.strftime("%Y-W%W")
        weekly[key] += w.total_volume_kg()

    if not weekly:
        pdf.body("No data.")
        return

    ordered = dict(sorted(weekly.items()))
    max_vol = max(ordered.values()) or 1
    bar_area = CONTENT_W - 68

    pdf.set_font("Helvetica", "", 8)
    for week, vol in ordered.items():
        bar_len = max(1, int((vol / max_vol) * bar_area))
        pdf.set_text_color(*C_DARK)
        pdf.cell(30, 5.5, week)
        pdf.set_fill_color(*C_SUCCESS)
        bar_y = pdf.get_y() + 1
        pdf.rect(pdf.get_x(), bar_y, bar_len, 3.5, "F")
        pdf.set_x(pdf.get_x() + bar_area + 2)
        pdf.set_text_color(*C_MID)
        pdf.cell(0, 5.5, f"{vol:,.0f} kg", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_text_color(*C_DARK)


def _or_dash(value, fmt: str = "") -> str:
    if value is None:
        return "-"
    if fmt:
        return format(value, fmt)
    return str(value)

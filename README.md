# HEVY-CLI-workout-exporter

I wanted my own way of exporting my workout data so I built a lightweight CLI tool, that pulls your workout history from the Hevy API and exports it to a PDF report or a CSV file, so I could visualize my data better.

## Setup

pip install -r requirements.txt
cp .env.example .env

Add your Hevy API key to the .env file:
HEVY_API_KEY=your_key_here

## Usage

Export everything for a date range:
python main.py --from 2025-01-01 --to 2025-05-28 --output-dir ./reports

CSV only:
python main.py --format csv

PDF only:
python main.py --format pdf --output-dir ~/Desktop

## Output

- `*_sets.csv` - one row per set with date, exercise, weight, reps and RPE
- `*_summary.csv` - total volume, muscle group breakdown and PRs per exercise
- `*.pdf` - full report with a cover page, workout log and charts

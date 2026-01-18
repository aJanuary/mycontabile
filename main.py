import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

from dateutil.parser import parse as parse_datetime
from jinja2 import Environment, FileSystemLoader
from PIL import Image


def parse_date_flexible(date_str: str) -> datetime:
    """Parse date string, trying ISO format first, then UK format."""
    try:
        # Try ISO format first (yyyy-mm-dd)
        return parse_datetime(date_str, yearfirst=True, dayfirst=False)
    except (ValueError, TypeError):
        # Fall back to UK format (dd/mm/yyyy)
        return parse_datetime(date_str, dayfirst=True)


@dataclass
class ProgrammeItem:
    """Represents a single programme item in the schedule."""

    id: str
    title: str
    room: str
    start_datetime: str
    end_datetime: str
    start_time_label: str
    end_time_label: str


@dataclass
class Day:
    """Represents a day with multiple programme items."""

    name: str
    programme_items: list[ProgrammeItem]


def parse_schedule_csv(csv_file: Path) -> list[Day]:
    """Parse schedule CSV and return programme items grouped by day.

    Args:
        csv_file: Path to the CSV file

    Returns:
        List of Day objects containing programme items

    Raises:
        ValueError: If validation fails (missing columns, invalid ID format, duplicate ID)
    """
    days = {}
    seen_ids = set()

    required_columns = {"ID", "Start", "End", "Title", "Room"}

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header row.")

        present_columns = set(reader.fieldnames)
        missing_columns = required_columns - present_columns
        if missing_columns:
            raise ValueError(
                f"CSV is missing required columns: {', '.join(sorted(missing_columns))}"
            )

        rows = list(reader)
        for i, row in enumerate(rows, 1):
            item_id = row["ID"]

            if not re.match(r"^[a-zA-Z0-9_-]+$", item_id):
                raise ValueError(
                    f"Invalid ID '{item_id}' on row {i}. IDs must be alphanumeric with hyphens or underscores only."
                )

            if item_id in seen_ids:
                raise ValueError(f"Duplicate ID '{item_id}' on row {i}.")

            seen_ids.add(item_id)

            start_dt = parse_date_flexible(row["Start"])
            end_dt = parse_date_flexible(row["End"])
            start_time_label = row.get("Start label") or start_dt.strftime("%H:%M")
            end_time_label = row.get("End label") or end_dt.strftime("%H:%M")
            day_date = start_dt.date()

            item = ProgrammeItem(
                id=item_id,
                title=row["Title"],
                room=row["Room"],
                start_datetime=start_dt.strftime("%Y-%m-%dT%H:%M"),
                end_datetime=end_dt.strftime("%Y-%m-%dT%H:%M"),
                start_time_label=start_time_label,
                end_time_label=end_time_label,
            )

            if day_date not in days:
                days[day_date] = []
            days[day_date].append((start_dt, item))

    return [
        Day(
            name=day_date.strftime("%A"),
            programme_items=[item for _, item in sorted(day_items, key=lambda x: x[0])],
        )
        for day_date, day_items in sorted(days.items())
    ]


def validate_logo(logo_path: Path) -> Image.Image:
    """Validate and load logo image.

    Returns:
        PIL Image object of the logo.

    Raises:
        ValueError: If the logo file is not a valid image.
    """
    try:
        img = Image.open(logo_path)
        img.verify()
        # Re-open after verify() as it leaves file unusable
        img = Image.open(logo_path)
    except Exception as e:
        raise ValueError(f"Invalid image file '{logo_path}': {e}")

    width, height = img.size
    if width != height:
        print(
            f"Warning: Logo is not square ({width}x{height}). It will be stretched.",
            file=sys.stderr,
        )
    if width < 180 or height < 180:
        print(
            f"Warning: Logo is smaller than 180x180 ({width}x{height}). It will be upscaled and may appear blurry.",
            file=sys.stderr,
        )

    return img


def copy_logo(img: Image.Image, dest: Path):
    """Copy logo image to destination."""
    images_dir = dest / "images"

    # Create apple-touch-icon (180x180)
    apple_touch_icon = img.resize((180, 180), Image.Resampling.LANCZOS)
    apple_touch_icon.save(images_dir / "apple-touch-icon.png")

    # Create favicon (multiple sizes in one ico file)
    favicon_sizes = [(16, 16), (32, 32), (48, 48)]
    favicon_images = [
        img.resize(size, Image.Resampling.LANCZOS) for size in favicon_sizes
    ]
    favicon_images[0].save(
        dest / "favicon.ico",
        format="ICO",
        sizes=favicon_sizes,
        append_images=favicon_images[1:],
    )


def get_files(directory: Path) -> list[str]:
    """Get list of all files in the given directory, relative to the directory."""
    files = []
    for path in directory.rglob("*"):
        if path.is_file():
            files.append(str(path.relative_to(directory)))
    return sorted(files)


def render_index(
    env: Environment, convention_name: str, days: list[Day], destination: Path
):
    """Render the index.html file using Jinja2 template."""
    template = env.get_template("index.html")
    output_html = template.render(
        convention_name=convention_name,
        days=[asdict(day) for day in days],
    )
    output_file = destination / "index.html"
    output_file.write_text(output_html, encoding="utf-8")


def render_manifest(env: Environment, convention_name: str, destination: Path):
    """Render the manifest.json file using Jinja2 template."""
    template = env.get_template("manifest.json")
    output_json = template.render(convention_name=convention_name)
    output_file = destination / "manifest.json"
    output_file.write_text(output_json, encoding="utf-8")


def render_service_worker(env: Environment, days: list[Day], destination: Path):
    """Render the sw.js file using Jinja2 template."""
    days_json = json.dumps([asdict(day) for day in days], sort_keys=True)
    content_hash = hashlib.sha256(days_json.encode()).hexdigest()[:8]

    template = env.get_template("sw.js")
    output_js = template.render(
        static_files=get_files(destination),
        content_hash=content_hash,
    )
    output_file = destination / "sw.js"
    output_file.write_text(output_js, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Process CSV file")
    parser.add_argument("convention_name", type=str, help="Name of the convention")
    parser.add_argument("csv_file", type=Path, help="Path to the CSV file")
    parser.add_argument("logo", type=Path, help="Path to the logo image file")
    parser.add_argument("destination", type=Path, help="Output destination directory")
    parser.add_argument(
        "--override",
        action="store_true",
        help="Override destination directory if it already exists",
    )

    args = parser.parse_args()

    if not args.csv_file.exists():
        print(f"Error: CSV file not found: {args.csv_file}", file=sys.stderr)
        return 1

    if not args.logo.exists():
        print(f"Error: Logo file not found: {args.logo}", file=sys.stderr)
        return 1

    try:
        logo_img = validate_logo(args.logo)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    try:
        days = parse_schedule_csv(args.csv_file)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.destination.exists():
        if not args.override:
            print(
                f"Error: Destination directory already exists: {args.destination}. Use --override to replace it.",
                file=sys.stderr,
            )
            return 1
        shutil.rmtree(args.destination)

    shutil.copytree(Path(__file__).parent / "static", args.destination)
    copy_logo(logo_img, args.destination)

    template_dir = Path(__file__).parent / "template"
    env = Environment(loader=FileSystemLoader(template_dir))

    render_index(env, args.convention_name, days, args.destination)
    render_manifest(env, args.convention_name, args.destination)
    render_service_worker(env, days, args.destination)

    return 0


if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python
"""Create a small Python RPA task skeleton."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


TEMPLATE = '''"""RPA task: {task_name}."""

from __future__ import annotations

import argparse
from datetime import datetime
import logging
from pathlib import Path


LOGGER = logging.getLogger(__name__)


def configure_logging(run_dir: Path) -> None:
    log_dir = run_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "run.log", encoding="utf-8"),
        ],
    )


def create_run_dir(base_dir: Path, task_name: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = base_dir / f"{{stamp}}-{{task_name}}"
    (run_dir / "screenshots").mkdir(parents=True, exist_ok=True)
    (run_dir / "downloads").mkdir(parents=True, exist_ok=True)
    return run_dir


def run(input_path: Path, run_dir: Path, dry_run: bool) -> Path:
    LOGGER.info("Starting task with input=%s dry_run=%s", input_path, dry_run)
    result_path = run_dir / "results.csv"
    result_path.write_text("status,reason,processed_at,evidence_path\\n", encoding="utf-8")
    LOGGER.info("Wrote results to %s", result_path)
    return result_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the {task_name} RPA task.")
    parser.add_argument("--input", required=True, type=Path, help="Input CSV/XLSX path.")
    parser.add_argument("--runs-dir", default=Path("runs"), type=Path, help="Run output directory.")
    parser.add_argument("--dry-run", action="store_true", help="Validate without side effects.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = create_run_dir(args.runs_dir, "{task_slug}")
    configure_logging(run_dir)
    run(args.input, run_dir, args.dry_run)


if __name__ == "__main__":
    main()
'''


def normalize_task_name(raw: str) -> str:
    value = raw.strip().lower().replace("_", "-")
    value = re.sub(r"[^a-z0-9-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("task name must contain at least one letter or digit")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Python RPA task skeleton.")
    parser.add_argument("task_name", help="Task name, for example invoice-download.")
    parser.add_argument("--output", default=Path("."), type=Path, help="Directory for the new file.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing file.")
    args = parser.parse_args()

    task_slug = normalize_task_name(args.task_name)
    module_name = task_slug.replace("-", "_")
    output_dir = args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{module_name}.py"

    if target.exists() and not args.force:
        raise SystemExit(f"{target} already exists. Use --force to overwrite.")

    target.write_text(
        TEMPLATE.format(task_name=task_slug.replace("-", " ").title(), task_slug=task_slug),
        encoding="utf-8",
    )
    print(target)


if __name__ == "__main__":
    main()

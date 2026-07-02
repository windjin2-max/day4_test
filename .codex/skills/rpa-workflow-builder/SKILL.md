---
name: rpa-workflow-builder
description: Build, review, or improve reliable RPA automation workflows. Use when Codex needs to create or modify browser automation, Excel/CSV processing, file download/upload handling, scheduled jobs, retryable workflows, logging, screenshots, checkpoints, or recovery logic for Python-based RPA projects.
---

# RPA Workflow Builder

## Core Workflow

Use this skill to turn an automation request into a maintainable RPA workflow rather than a fragile one-off script.

1. Identify the business transaction, input source, target system, expected output, and failure policy.
2. Inspect the existing project before choosing tools or file locations.
3. Prefer the project's existing automation stack. If none exists, use Playwright for browser automation, pandas/openpyxl for tabular files, pathlib/shutil for files, and standard logging for observability.
4. Break the workflow into explicit stages: load inputs, normalize data, authenticate, execute each transaction, capture evidence, persist results, and summarize outcomes.
5. Add idempotency and recovery points before adding speed optimizations.
6. Verify with a small fixture or dry run before suggesting production use.

## Discovery Checklist

Gather only the details needed for the task:

- Inputs: file paths, sheet names, required columns, row filters, credentials source, environment variables.
- Browser target: URL, login flow, stable selectors, download behavior, pagination, popups, frames, and timeout risks.
- File handling: download folder, naming convention, archive policy, duplicate handling, and cleanup policy.
- Outputs: CSV/XLSX/JSON/report path, success/failure columns, screenshots, logs, and user-facing summary.
- Operations: single run, scheduled run, retry limits, resume behavior, and manual intervention points.

When these details are missing, make conservative assumptions for local scripts and clearly state them.

## Implementation Rules

- Keep secrets out of code. Read credentials from environment variables, a local ignored file, or the existing project settings mechanism.
- Use stable selectors and explicit waits for browser automation. Avoid fixed sleeps except as a last resort with a comment explaining why.
- Treat each input row as an independent transaction. Record status, reason, timestamp, and evidence path per row.
- Make file paths configurable and resolve them with `pathlib.Path`.
- Create run-specific output folders when screenshots, downloads, or logs are produced.
- Use retries only around operations that are safe to repeat. Do not retry actions that could duplicate submissions unless the target system has a confirmation check.
- Prefer dry-run modes for destructive or external-system actions.
- Keep automation modules small: orchestration, browser actions, data parsing, and reporting should be separable when the workflow grows.

## Reusable Resources

- Read `references/rpa-patterns.md` when implementing browser, Excel, file, logging, retry, or recovery behavior.
- Use `scripts/new_rpa_task.py` to create a Python task skeleton when starting a new standalone RPA workflow.

Example:

```powershell
python skills/rpa-workflow-builder/scripts/new_rpa_task.py invoice_download --output backend/app/tasks
```

If the default `python` command is unavailable, use the project's virtual environment Python.

```powershell
.\backend\.venv\Scripts\python.exe skills\rpa-workflow-builder\scripts\new_rpa_task.py invoice_download --output backend\app\tasks
```

## Verification

Before finishing an RPA change:

1. Run static checks or project tests when available.
2. Run the workflow against a tiny input fixture or use dry-run mode.
3. Confirm output files are written where expected.
4. Confirm failures produce actionable logs and do not erase prior results.
5. Report what was verified and what still needs real-system credentials or manual confirmation.

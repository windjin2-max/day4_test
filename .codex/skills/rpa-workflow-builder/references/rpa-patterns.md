# RPA Implementation Patterns

## Browser Automation

Prefer Playwright when introducing a browser automation dependency. Use Selenium only when the project already uses it or a required browser extension/integration depends on it.

Recommended structure:

- `login(page, settings)`: authenticate and verify the landing page.
- `process_item(page, item, run_dir)`: execute one business transaction.
- `capture_evidence(page, run_dir, item_id, label)`: save screenshots or downloaded files.
- `main()`: parse args, load inputs, create run folder, iterate rows, write results.

Selector rules:

- Prefer role, label, placeholder, text, and test-id selectors before brittle CSS/XPath.
- Add explicit waits for page state, network response, download events, or visible confirmation text.
- After submitting data, verify a durable confirmation value before marking success.

Download pattern:

```python
with page.expect_download() as download_info:
    page.get_by_role("button", name="Download").click()
download = download_info.value
target = run_dir / "downloads" / suggested_safe_name(download.suggested_filename)
download.save_as(target)
```

## Excel and CSV

Use `pandas` for row-oriented transformations and `openpyxl` when preserving workbook formatting matters.

Normalize inputs at the boundary:

- Strip column names.
- Validate required columns.
- Convert empty strings to null values when needed.
- Add derived IDs before processing rows.
- Preserve the original source row number for error reporting.

Result columns should usually include:

- `status`: `success`, `failed`, `skipped`, or `dry_run`.
- `reason`: short failure or skip reason.
- `processed_at`: ISO timestamp.
- `evidence_path`: screenshot, downloaded file, or log path when relevant.

## Files and Run Folders

Use one run folder per execution when the workflow creates logs, screenshots, downloads, or reports.

Recommended layout:

```text
runs/
  20260701-153012-task-name/
    logs/
    screenshots/
    downloads/
    results.csv
```

Never overwrite input files in place. Write new output files and archive old outputs only when the user asks.

## Logging

Use standard `logging` with both console and file handlers for non-trivial workflows.

Log these events:

- Run start and resolved settings.
- Input count and validation failures.
- Per-item start and end status.
- Retry attempts and final failure reason.
- Output file paths.

Avoid logging secrets, full cookies, auth headers, passwords, or private tokens.

## Retry and Recovery

Make retries narrow and explicit:

- Good retry targets: navigation timeout, transient download failure, stale element after page refresh.
- Bad retry targets: payment submission, form finalization, irreversible upload, actions with side effects and no confirmation check.

For resumable workflows:

- Read an existing result file if present.
- Skip rows already marked `success`.
- Reprocess `failed` rows only when the user requests it or a `--retry-failed` flag is provided.

## Dry Run

Add `--dry-run` when a workflow creates records, sends messages, submits forms, deletes files, or changes external system state.

Dry run should still validate inputs and produce a result file, but it must not execute side-effecting actions.

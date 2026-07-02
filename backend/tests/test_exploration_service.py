from pathlib import Path

import pandas as pd

from app.services.exploration import analyze_file, load_dataframe, summarize_dataframe


def test_load_dataframe_csv() -> None:
    content = "name,age\nAlice,30\nBob,40\n".encode("utf-8")

    df = load_dataframe("sample.csv", content)

    assert list(df.columns) == ["name", "age"]
    assert df.shape == (2, 2)


def test_summarize_dataframe_detects_quality_issues() -> None:
    df = pd.DataFrame(
        {
            "id": [1, 1, 2],
            "name": ["A", "A", "B"],
            "value": [10, 10, 20],
            "constant": [5, 5, 5],
        }
    )

    result = summarize_dataframe(df)

    assert result["summary"]["rows"] == 3
    assert result["summary"]["columns"] == 4
    assert result["summary"]["duplicate_rows"] == 1
    issue_types = {issue["type"] for issue in result["quality_issues"]}
    assert "duplicate_rows" in issue_types
    assert "constant_column" in issue_types


def test_analyze_file_supports_xlsx(tmp_path: Path) -> None:
    path = tmp_path / "sample.xlsx"
    pd.DataFrame({"name": ["Alice", "Bob"], "score": [90, 95]}).to_excel(path, index=False)

    result = analyze_file(path.name, path.read_bytes())

    assert result.file_type == "xlsx"
    assert result.summary["rows"] == 2
    assert "score" in result.summary["numeric_columns"]
    assert result.sample_rows[0]["name"] == "Alice"


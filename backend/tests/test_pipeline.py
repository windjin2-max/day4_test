from pathlib import Path

import pandas as pd

from app.services.pipeline import analyze_file


def test_pipeline_returns_full_flow(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    pd.DataFrame(
        {
            "category": ["A", "A", "B", "B"],
            "value": [1, 1, 3, 4],
            "missing": [10, None, 30, None],
        }
    ).to_csv(path, index=False)

    result = analyze_file(path.name, path.read_bytes())

    assert result.exploration["summary"]["rows"] == 4
    assert result.preprocessing["required"] is True
    assert result.eda["top_correlations"] is not None
    assert len(result.visualization["charts"]) >= 1
    assert len(result.insights["summary_points"]) >= 1
    assert "전처리" in result.report_markdown


# %% [markdown]
# # Data Exploration for Colab
# Supported file types: csv, xls, xlsx
# Outputs: summary profile, data quality checks, Markdown/JSON report

from __future__ import annotations

# %% [code]
import subprocess
import sys

subprocess.check_call(
    [
        sys.executable,
        "-m",
        "pip",
        "install",
        "pandas",
        "openpyxl",
        "xlrd==2.0.1",
        "matplotlib",
        "seaborn",
    ]
)

# %% [code]
import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from IPython.display import display

try:
    from google.colab import files
    IN_COLAB = True
except Exception:
    IN_COLAB = False

sns.set_theme(style="whitegrid")

# %% [code]
def upload_file() -> str:
    if IN_COLAB:
        uploaded = files.upload()
        if not uploaded:
            raise ValueError("업로드된 파일이 없습니다.")
        return next(iter(uploaded.keys()))
    path = input("파일 경로를 입력하세요: ").strip()
    if not path:
        raise ValueError("파일 경로가 비어 있습니다.")
    return path


def read_dataset(file_path: str) -> pd.DataFrame:
    suffix = Path(file_path).suffix.lower()

    if suffix == ".csv":
        for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr", "latin1"):
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except Exception:
                continue
        raise ValueError("CSV 파일을 읽을 수 없습니다. 인코딩을 확인하세요.")

    if suffix in {".xlsx", ".xls"}:
        engine = "openpyxl" if suffix == ".xlsx" else "xlrd"
        return pd.read_excel(file_path, engine=engine)

    raise ValueError(f"지원하지 않는 파일 형식입니다: {suffix}")


def detect_date_columns(df: pd.DataFrame, threshold: float = 0.8) -> list[str]:
    date_columns: list[str] = []
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_datetime64_any_dtype(series):
            date_columns.append(column)
            continue

        if series.dtype == "object":
            parsed = pd.to_datetime(series, errors="coerce")
            ratio = parsed.notna().mean()
            if ratio >= threshold:
                date_columns.append(column)
    return date_columns


def classify_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    date_columns = detect_date_columns(df)
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = [
        column
        for column in df.columns
        if column not in numeric_columns and column not in date_columns
    ]
    return {
        "numeric": numeric_columns,
        "categorical": categorical_columns,
        "datetime": date_columns,
    }


def build_quality_issues(df: pd.DataFrame, classified: dict[str, list[str]]) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    total_rows = len(df)

    duplicate_rows = int(df.duplicated().sum())
    if duplicate_rows > 0:
        issues.append(
            {
                "type": "duplicate_rows",
                "severity": "medium",
                "message": f"중복 행 {duplicate_rows}건 발견",
            }
        )

    missing_rate = df.isna().mean().sort_values(ascending=False)
    high_missing = missing_rate[missing_rate >= 0.5]
    for column, rate in high_missing.items():
        issues.append(
            {
                "type": "high_missing",
                "severity": "high",
                "column": column,
                "message": f"결측치 비율이 {rate:.1%}로 높음",
            }
        )

    constant_columns = [col for col in df.columns if df[col].nunique(dropna=False) <= 1]
    for column in constant_columns:
        issues.append(
            {
                "type": "constant_column",
                "severity": "low",
                "column": column,
                "message": "모든 값이 동일한 상수형 컬럼",
            }
        )

    high_cardinality = [
        col
        for col in classified["categorical"]
        if total_rows > 0 and df[col].nunique(dropna=True) / total_rows >= 0.7
    ]
    for column in high_cardinality:
        issues.append(
            {
                "type": "high_cardinality",
                "severity": "medium",
                "column": column,
                "message": "고카디널리티 범주형 컬럼",
            }
        )

    return issues


def summarize_dataframe(df: pd.DataFrame) -> dict[str, object]:
    classified = classify_columns(df)
    numeric_columns = classified["numeric"]
    categorical_columns = classified["categorical"]
    datetime_columns = classified["datetime"]

    numeric_summary = (
        df[numeric_columns].describe().T.reset_index().rename(columns={"index": "column"})
        if numeric_columns
        else pd.DataFrame(columns=["column"])
    )

    categorical_rows = []
    for column in categorical_columns:
        series = df[column]
        top_value = series.mode(dropna=True)
        categorical_rows.append(
            {
                "column": column,
                "unique_count": int(series.nunique(dropna=True)),
                "top_value": top_value.iloc[0] if not top_value.empty else None,
                "top_frequency": int(series.value_counts(dropna=True).iloc[0]) if not series.dropna().empty else 0,
            }
        )
    categorical_summary = pd.DataFrame(categorical_rows)

    profile_rows = []
    for column in df.columns:
        series = df[column]
        profile_rows.append(
            {
                "column": column,
                "dtype": str(series.dtype),
                "missing_count": int(series.isna().sum()),
                "missing_rate": float(series.isna().mean()),
                "unique_count": int(series.nunique(dropna=True)),
            }
        )
    column_profile = pd.DataFrame(profile_rows)

    memory_mb = float(df.memory_usage(deep=True).sum() / (1024 * 1024))
    quality_issues = build_quality_issues(df, classified)

    return {
        "summary": {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "memory_mb": round(memory_mb, 3),
            "duplicate_rows": int(df.duplicated().sum()),
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "datetime_columns": datetime_columns,
        },
        "column_profile": column_profile,
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "quality_issues": quality_issues,
    }


def create_report(data: dict[str, object], source_name: str) -> str:
    summary = data["summary"]
    column_profile: pd.DataFrame = data["column_profile"]
    numeric_summary: pd.DataFrame = data["numeric_summary"]
    categorical_summary: pd.DataFrame = data["categorical_summary"]
    quality_issues = data["quality_issues"]

    lines = [
        "# 데이터 탐색 리포트",
        "",
        f"- 원본 파일: {source_name}",
        f"- 행 수: {summary['rows']}",
        f"- 열 수: {summary['columns']}",
        f"- 메모리 사용량: {summary['memory_mb']} MB",
        f"- 중복 행 수: {summary['duplicate_rows']}",
        "",
        "## 컬럼 프로파일",
        column_profile.to_markdown(index=False),
        "",
        "## 숫자형 요약",
        numeric_summary.to_markdown(index=False) if not numeric_summary.empty else "없음",
        "",
        "## 범주형 요약",
        categorical_summary.to_markdown(index=False) if not categorical_summary.empty else "없음",
        "",
        "## 품질 이슈",
    ]

    if quality_issues:
        for issue in quality_issues:
            column = f" ({issue.get('column')})" if issue.get("column") else ""
            lines.append(f"- [{issue['severity']}] {issue['type']}{column}: {issue['message']}")
    else:
        lines.append("- 발견된 품질 이슈 없음")

    return "\n".join(lines)


def save_outputs(base_name: str, data: dict[str, object], report_text: str) -> None:
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "source_name": base_name,
        "summary": data["summary"],
        "column_profile": data["column_profile"].to_dict(orient="records"),
        "numeric_summary": data["numeric_summary"].to_dict(orient="records"),
        "categorical_summary": data["categorical_summary"].to_dict(orient="records"),
        "quality_issues": data["quality_issues"],
    }

    json_path = output_dir / f"{base_name}_data_exploration.json"
    md_path = output_dir / f"{base_name}_data_exploration.md"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(report_text, encoding="utf-8")

    if IN_COLAB:
        files.download(str(json_path))
        files.download(str(md_path))


# %% [code]
file_path = upload_file()
dataset = read_dataset(file_path)
result = summarize_dataframe(dataset)
report = create_report(result, Path(file_path).stem)
print(report)

# %% [code]
summary_df = pd.DataFrame([result["summary"]])
display(summary_df)

display(result["column_profile"])

if not result["numeric_summary"].empty:
    display(result["numeric_summary"])

if not result["categorical_summary"].empty:
    display(result["categorical_summary"])

# %% [code]
missing_rates = result["column_profile"].sort_values("missing_rate", ascending=False).head(15)

plt.figure(figsize=(10, 5))
sns.barplot(data=missing_rates, x="missing_rate", y="column", color="#38bdf8")
plt.title("Top Missing Rate Columns")
plt.xlabel("Missing Rate")
plt.ylabel("Column")
plt.tight_layout()
plt.show()

# %% [code]
save_outputs(Path(file_path).stem, result, report)

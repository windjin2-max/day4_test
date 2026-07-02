from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class ExplorationResult:
    source_name: str
    file_type: str
    summary: dict[str, Any]
    column_profile: list[dict[str, Any]]
    numeric_summary: list[dict[str, Any]]
    categorical_summary: list[dict[str, Any]]
    quality_issues: list[dict[str, Any]]
    sample_rows: list[dict[str, Any]]
    report_markdown: str


SUPPORTED_FILE_TYPES = {".csv", ".xls", ".xlsx"}


def load_dataframe(file_name: str, content: bytes) -> pd.DataFrame:
    suffix = Path(file_name).suffix.lower()
    if suffix not in SUPPORTED_FILE_TYPES:
        raise ValueError("지원하지 않는 파일 형식입니다. csv, xls, xlsx만 허용됩니다.")

    if suffix == ".csv":
        for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr", "latin1"):
            try:
                text = content.decode(encoding)
                return pd.read_csv(StringIO(text))
            except Exception:
                continue
        raise ValueError("CSV 파일을 읽을 수 없습니다. 인코딩을 확인하세요.")

    engine = "openpyxl" if suffix == ".xlsx" else "xlrd"
    return pd.read_excel(BytesIO(content), engine=engine)


def detect_date_columns(df: pd.DataFrame, threshold: float = 0.8) -> list[str]:
    date_columns: list[str] = []
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_datetime64_any_dtype(series):
            date_columns.append(column)
            continue
        if series.dtype == "object":
            parsed = pd.to_datetime(series, errors="coerce")
            if parsed.notna().mean() >= threshold:
                date_columns.append(column)
    return date_columns


def classify_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    date_columns = detect_date_columns(df)
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = [
        column for column in df.columns if column not in numeric_columns and column not in date_columns
    ]
    return {
        "numeric": numeric_columns,
        "categorical": categorical_columns,
        "datetime": date_columns,
    }


def build_quality_issues(df: pd.DataFrame, classified: dict[str, list[str]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    total_rows = len(df)

    duplicate_rows = int(df.duplicated().sum())
    if duplicate_rows:
        issues.append(
            {
                "type": "duplicate_rows",
                "severity": "medium",
                "message": f"중복 행 {duplicate_rows}건 발견",
            }
        )

    missing_rate = df.isna().mean().sort_values(ascending=False)
    for column, rate in missing_rate[missing_rate >= 0.5].items():
        issues.append(
            {
                "type": "high_missing",
                "severity": "high",
                "column": column,
                "message": f"결측치 비율이 {rate:.1%}로 높음",
            }
        )

    for column in [col for col in df.columns if df[col].nunique(dropna=False) <= 1]:
        issues.append(
            {
                "type": "constant_column",
                "severity": "low",
                "column": column,
                "message": "모든 값이 동일한 상수형 컬럼",
            }
        )

    for column in classified["categorical"]:
        unique_ratio = df[column].nunique(dropna=True) / total_rows if total_rows else 0
        if unique_ratio >= 0.7:
            issues.append(
                {
                    "type": "high_cardinality",
                    "severity": "medium",
                    "column": column,
                    "message": "고카디널리티 범주형 컬럼",
                }
            )

    return issues


def summarize_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    classified = classify_columns(df)
    numeric_columns = classified["numeric"]
    categorical_columns = classified["categorical"]
    datetime_columns = classified["datetime"]

    numeric_summary = (
        df[numeric_columns].describe().T.reset_index().rename(columns={"index": "column"})
        if numeric_columns
        else pd.DataFrame(columns=["column"])
    )

    categorical_rows: list[dict[str, Any]] = []
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

    profile_rows: list[dict[str, Any]] = []
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

    return {
        "summary": {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "memory_mb": round(float(df.memory_usage(deep=True).sum() / (1024 * 1024)), 3),
            "duplicate_rows": int(df.duplicated().sum()),
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "datetime_columns": datetime_columns,
        },
        "column_profile": column_profile.to_dict(orient="records"),
        "numeric_summary": numeric_summary.to_dict(orient="records"),
        "categorical_summary": categorical_summary.to_dict(orient="records"),
        "quality_issues": build_quality_issues(df, classified),
        "sample_rows": df.head(10).replace({np.nan: None}).to_dict(orient="records"),
    }


def build_report_markdown(source_name: str, file_type: str, data: dict[str, Any]) -> str:
    summary = data["summary"]
    lines = [
        "# 데이터 탐색 리포트",
        "",
        f"- 원본 파일: {source_name}",
        f"- 파일 형식: {file_type}",
        f"- 행 수: {summary['rows']}",
        f"- 열 수: {summary['columns']}",
        f"- 메모리 사용량: {summary['memory_mb']} MB",
        f"- 중복 행 수: {summary['duplicate_rows']}",
        "",
        "## 컬럼 분류",
        f"- 숫자형: {', '.join(summary['numeric_columns']) if summary['numeric_columns'] else '없음'}",
        f"- 범주형: {', '.join(summary['categorical_columns']) if summary['categorical_columns'] else '없음'}",
        f"- 날짜형: {', '.join(summary['datetime_columns']) if summary['datetime_columns'] else '없음'}",
        "",
        "## 품질 이슈",
    ]

    if data["quality_issues"]:
        for issue in data["quality_issues"]:
            column = f" ({issue.get('column')})" if issue.get("column") else ""
            lines.append(f"- [{issue['severity']}] {issue['type']}{column}: {issue['message']}")
    else:
        lines.append("- 발견된 품질 이슈 없음")

    lines.extend(
        [
            "",
            "## 샘플 데이터",
            json.dumps(data["sample_rows"], ensure_ascii=False, indent=2),
        ]
    )
    return "\n".join(lines)


def analyze_file(file_name: str, content: bytes) -> ExplorationResult:
    df = load_dataframe(file_name, content)
    base_data = summarize_dataframe(df)
    suffix = Path(file_name).suffix.lower()
    report = build_report_markdown(file_name, suffix.lstrip("."), base_data)
    return ExplorationResult(
        source_name=file_name,
        file_type=suffix.lstrip("."),
        summary=base_data["summary"],
        column_profile=base_data["column_profile"],
        numeric_summary=base_data["numeric_summary"],
        categorical_summary=base_data["categorical_summary"],
        quality_issues=base_data["quality_issues"],
        sample_rows=base_data["sample_rows"],
        report_markdown=report,
    )


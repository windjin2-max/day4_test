from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager as fm

SUPPORTED_FILE_TYPES = {".csv", ".xls", ".xlsx"}


@dataclass
class PipelineResult:
    source_name: str
    file_type: str
    exploration: dict[str, Any]
    preprocessing: dict[str, Any]
    eda: dict[str, Any]
    visualization: dict[str, Any]
    insights: dict[str, Any]
    report_markdown: str


def _configure_matplotlib_font() -> bool:
    candidates = ["Malgun Gothic", "AppleGothic", "NanumGothic"]
    available = {font.name for font in fm.fontManager.ttflist}
    for font_name in candidates:
        if font_name in available:
            plt.rcParams["font.family"] = font_name
            plt.rcParams["axes.unicode_minus"] = False
            return True
    plt.rcParams["axes.unicode_minus"] = False
    return False


HAS_KOREAN_FONT = _configure_matplotlib_font()


def _chart_text(korean: str, english: str) -> str:
    return korean if HAS_KOREAN_FONT else english


def load_dataframe(file_name: str, content: bytes) -> pd.DataFrame:
    suffix = Path(file_name).suffix.lower()
    if suffix not in SUPPORTED_FILE_TYPES:
        raise ValueError("지원하지 않는 파일 형식입니다. csv, xls, xlsx만 허용됩니다.")

    if suffix == ".csv":
        for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr", "latin1"):
            try:
                return pd.read_csv(StringIO(content.decode(encoding)))
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
    categorical_columns = [column for column in df.columns if column not in numeric_columns and column not in date_columns]
    return {"numeric": numeric_columns, "categorical": categorical_columns, "datetime": date_columns}


def build_preprocessing_plan(df: pd.DataFrame, classified: dict[str, list[str]]) -> dict[str, Any]:
    duplicate_rows = int(df.duplicated().sum())
    missing_rates = df.isna().mean()
    high_missing_columns = [column for column, rate in missing_rates.items() if rate >= 0.1]
    total_rows = max(len(df), 1)
    high_cardinality_columns = [
        column
        for column in classified["categorical"]
        if df[column].nunique(dropna=True) / total_rows >= 0.7
    ]

    steps: list[dict[str, Any]] = []
    if duplicate_rows:
        steps.append({"key": "remove_duplicates", "label": "중복 행 제거", "required": True})
    if classified["datetime"]:
        steps.append({"key": "convert_datetime", "label": "날짜형 컬럼 변환", "required": True})
    if classified["numeric"] and any(df[column].isna().any() for column in classified["numeric"]):
        steps.append({"key": "fill_numeric_missing", "label": "수치형 결측값 중앙값 대체", "required": True})
    if classified["categorical"] and any(df[column].isna().any() for column in classified["categorical"]):
        steps.append({"key": "fill_categorical_missing", "label": "범주형 결측값 최빈값 대체", "required": True})
    if high_missing_columns:
        steps.append(
            {
                "key": "review_high_missing",
                "label": "결측치 비율 높은 컬럼 검토",
                "required": True,
                "columns": high_missing_columns[:10],
            }
        )
    if high_cardinality_columns:
        steps.append(
            {
                "key": "review_high_cardinality",
                "label": "고카디널리티 범주형 컬럼 검토",
                "required": True,
                "columns": high_cardinality_columns[:10],
            }
        )

    reasons: list[str] = []
    if duplicate_rows:
        reasons.append("중복 행이 존재합니다.")
    if high_missing_columns:
        reasons.append("결측치 비율이 높은 컬럼이 있습니다.")
    if classified["datetime"]:
        reasons.append("날짜형 변환이 필요한 컬럼이 있습니다.")
    if high_cardinality_columns:
        reasons.append("고카디널리티 범주형 컬럼이 있습니다.")

    return {
        "required": bool(steps),
        "priority": "필수" if steps else "불필요",
        "reasons": reasons or ["특별한 전처리 이슈가 확인되지 않았습니다."],
        "steps": steps,
    }


def build_quality_issues(df: pd.DataFrame, classified: dict[str, list[str]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    total_rows = len(df)

    duplicate_rows = int(df.duplicated().sum())
    if duplicate_rows:
        issues.append({"type": "duplicate_rows", "severity": "medium", "message": f"중복 행 {duplicate_rows}개 발견"})

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
        issues.append({"type": "constant_column", "severity": "low", "column": column, "message": "모든 값이 동일한 상수형 컬럼"})

    for column in classified["categorical"]:
        unique_ratio = df[column].nunique(dropna=True) / total_rows if total_rows else 0
        if unique_ratio >= 0.7:
            issues.append({"type": "high_cardinality", "severity": "medium", "column": column, "message": "고카디널리티 범주형 컬럼"})

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
        "classified": classified,
    }


def preprocess_dataframe(df: pd.DataFrame, classified: dict[str, list[str]]) -> tuple[pd.DataFrame, dict[str, Any]]:
    processed = df.copy()
    plan = build_preprocessing_plan(df, classified)
    actions: list[str] = []
    missing_before = int(processed.isna().sum().sum())
    duplicate_before = int(df.duplicated().sum())

    if processed.duplicated().any():
        processed = processed.drop_duplicates()
        actions.append("중복 행 제거")

    for column in classified["datetime"]:
        processed[column] = pd.to_datetime(processed[column], errors="coerce")
        actions.append(f"날짜형 변환: {column}")

    for column in classified["numeric"]:
        if processed[column].isna().any():
            fill_value = processed[column].median()
            processed[column] = processed[column].fillna(fill_value)
            actions.append(f"수치형 결측값 중앙값 대체: {column}")

    for column in classified["categorical"]:
        if processed[column].isna().any():
            mode = processed[column].mode(dropna=True)
            fill_value = mode.iloc[0] if not mode.empty else "Unknown"
            processed[column] = processed[column].fillna(fill_value)
            actions.append(f"범주형 결측값 최빈값 대체: {column}")

    missing_after = int(processed.isna().sum().sum())
    duplicate_after = int(processed.duplicated().sum())
    return processed, {
        "required": plan["required"],
        "priority": plan["priority"],
        "plan": plan,
        "actions": actions,
        "rows_before": int(df.shape[0]),
        "rows_after": int(processed.shape[0]),
        "missing_before": missing_before,
        "missing_after": missing_after,
        "duplicate_before": duplicate_before,
        "duplicate_after": duplicate_after,
        "improved": missing_after < missing_before or len(processed) != len(df),
        "summary": {
            "removed_duplicates": int(df.shape[0] - processed.shape[0]),
            "filled_missing": int(missing_before - missing_after if missing_before > missing_after else 0),
        },
    }


def build_eda(processed_df: pd.DataFrame, classified: dict[str, list[str]]) -> dict[str, Any]:
    numeric_columns = classified["numeric"]
    categorical_columns = classified["categorical"]

    eda: dict[str, Any] = {
        "correlation_matrix": [],
        "top_correlations": [],
        "group_summary": [],
        "distribution_summary": [],
    }

    if numeric_columns:
        corr = processed_df[numeric_columns].corr(numeric_only=True)
        eda["correlation_matrix"] = corr.round(4).reset_index().rename(columns={"index": "column"}).to_dict(orient="records")

        corr_pairs: list[tuple[str, str, float]] = []
        for i, left in enumerate(numeric_columns):
            for right in numeric_columns[i + 1 :]:
                value = corr.loc[left, right]
                if pd.notna(value):
                    corr_pairs.append((left, right, float(value)))
        corr_pairs.sort(key=lambda item: abs(item[2]), reverse=True)
        eda["top_correlations"] = [
            {"left": left, "right": right, "correlation": round(value, 4)}
            for left, right, value in corr_pairs[:5]
        ]

        for column in numeric_columns[:5]:
            series = processed_df[column]
            eda["distribution_summary"].append(
                {
                    "column": column,
                    "mean": round(float(series.mean()), 4) if pd.notna(series.mean()) else None,
                    "median": round(float(series.median()), 4) if pd.notna(series.median()) else None,
                    "std": round(float(series.std()), 4) if pd.notna(series.std()) else None,
                    "min": round(float(series.min()), 4) if pd.notna(series.min()) else None,
                    "max": round(float(series.max()), 4) if pd.notna(series.max()) else None,
                }
            )

    if categorical_columns and numeric_columns:
        group_column = categorical_columns[0]
        grouped = processed_df.groupby(group_column, dropna=False)[numeric_columns].mean(numeric_only=True).reset_index()
        eda["group_summary"] = grouped.head(10).replace({np.nan: None}).to_dict(orient="records")

    return eda


def build_visualizations(processed_df: pd.DataFrame, classified: dict[str, list[str]]) -> dict[str, Any]:
    charts: list[dict[str, Any]] = []
    numeric_columns = classified["numeric"][:6]
    categorical_columns = classified["categorical"][:4]
    datetime_columns = classified["datetime"][:2]

    def encode_current_plot(title: str, chart_type: str) -> dict[str, Any]:
        buffer = BytesIO()
        plt.title(title)
        plt.tight_layout()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        plt.close()
        buffer.seek(0)
        encoded = base64.b64encode(buffer.read()).decode("ascii")
        return {"title": title, "chart_type": chart_type, "image_base64": encoded, "mime_type": "image/png"}

    missing_counts = processed_df.isna().sum()
    missing_counts = missing_counts[missing_counts > 0].sort_values(ascending=False).head(12)
    if not missing_counts.empty:
        plt.figure(figsize=(9, 4))
        missing_counts.plot(kind="bar", color="#f97316")
        plt.xlabel(_chart_text("컬럼", "Column"))
        plt.ylabel(_chart_text("결측값 수", "Missing count"))
        charts.append(encode_current_plot(_chart_text("컬럼별 결측값 현황", "Missing values by column"), "missing_bar"))

    if numeric_columns:
        for column in numeric_columns[:3]:
            plt.figure(figsize=(8, 4))
            processed_df[column].dropna().hist(bins=20, color="#38bdf8")
            plt.xlabel(_chart_text(f"{column} 값", f"Value of {column}"))
            plt.ylabel(_chart_text("빈도", "Frequency"))
            charts.append(encode_current_plot(_chart_text(f"{column} 분포", f"{column} distribution"), "histogram"))

        plt.figure(figsize=(9, 4))
        processed_df[numeric_columns[:5]].plot(kind="box", ax=plt.gca())
        plt.ylabel(_chart_text("값", "Value"))
        charts.append(encode_current_plot(_chart_text("수치형 컬럼 이상치 비교", "Numeric outlier comparison"), "boxplot"))

    for category in categorical_columns[:2]:
        counts = processed_df[category].astype(str).value_counts(dropna=False).head(10)
        if not counts.empty:
            plt.figure(figsize=(8, 4))
            counts.sort_values().plot(kind="barh", color="#a3e635")
            plt.xlabel(_chart_text("건수", "Count"))
            plt.ylabel(_chart_text(category, category))
            charts.append(encode_current_plot(_chart_text(f"{category} 상위 범주 분포", f"Top categories of {category}"), "category_bar"))

    if len(numeric_columns) >= 2:
        left, right = numeric_columns[0], numeric_columns[1]
        plt.figure(figsize=(6, 6))
        plt.scatter(processed_df[left], processed_df[right], alpha=0.7, color="#0ea5e9")
        plt.xlabel(_chart_text(left, left))
        plt.ylabel(_chart_text(right, right))
        charts.append(encode_current_plot(_chart_text(f"{left} 대 {right}", f"{left} vs {right}"), "scatter"))

    if categorical_columns and numeric_columns:
        for category in categorical_columns[:2]:
            for value in numeric_columns[:2]:
                order = processed_df.groupby(category)[value].mean().sort_values(ascending=False).head(10)
                if order.empty:
                    continue
                plt.figure(figsize=(8, 4))
                order.plot(kind="bar", color="#22c55e")
                plt.ylabel(_chart_text(f"{value} 평균", f"Mean of {value}"))
                plt.xlabel(_chart_text(category, category))
                charts.append(
                    encode_current_plot(_chart_text(f"{category}별 {value} 평균", f"Mean of {value} by {category}"), "group_mean_bar")
                )

    if len(numeric_columns) >= 2:
        corr = processed_df[numeric_columns].corr(numeric_only=True)
        plt.figure(figsize=(6, 5))
        plt.imshow(corr, cmap="Blues", aspect="auto")
        plt.colorbar()
        plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right")
        plt.yticks(range(len(corr.index)), corr.index)
        charts.append(encode_current_plot(_chart_text("상관관계 행렬", "Correlation matrix"), "heatmap"))

    if datetime_columns and numeric_columns:
        date_column = datetime_columns[0]
        value_column = numeric_columns[0]
        time_df = processed_df[[date_column, value_column]].dropna().copy()
        time_df[date_column] = pd.to_datetime(time_df[date_column], errors="coerce")
        time_df = time_df.dropna().sort_values(date_column)
        if not time_df.empty:
            time_series = time_df.set_index(date_column)[value_column].resample("D").mean().dropna()
            if len(time_series) >= 2:
                plt.figure(figsize=(9, 4))
                time_series.plot(color="#14b8a6")
                plt.xlabel(_chart_text("날짜", "Date"))
                plt.ylabel(_chart_text(value_column, value_column))
                charts.append(encode_current_plot(_chart_text(f"{value_column} 시계열 추세", f"Time trend of {value_column}"), "time_series"))

    recommendations: list[dict[str, Any]] = []
    if numeric_columns:
        recommendations.append({"columns": numeric_columns[:3], "chart": "histogram", "reason": _chart_text("수치형 분포와 치우침 확인", "Numeric distribution and skew check")})
        recommendations.append({"columns": numeric_columns[:5], "chart": "boxplot", "reason": _chart_text("이상치 후보 비교", "Outlier candidate comparison")})
    if categorical_columns:
        recommendations.append({"columns": categorical_columns[:2], "chart": "category_bar", "reason": _chart_text("상위 범주 집중도 확인", "Top category concentration check")})
    if len(numeric_columns) >= 2:
        recommendations.append({"columns": numeric_columns[:2], "chart": "scatter", "reason": _chart_text("두 수치형 변수 관계 확인", "Two numeric variable relationship check")})
        recommendations.append({"columns": numeric_columns, "chart": "heatmap", "reason": _chart_text("전체 수치형 상관구조 확인", "Overall numeric correlation structure check")})
    if categorical_columns and numeric_columns:
        recommendations.append({"columns": [categorical_columns[0], numeric_columns[0]], "chart": "group_mean_bar", "reason": _chart_text("그룹별 평균 차이 비교", "Group mean comparison")})
    if datetime_columns and numeric_columns:
        recommendations.append({"columns": [datetime_columns[0], numeric_columns[0]], "chart": "time_series", "reason": _chart_text("시간 흐름에 따른 추세 확인", "Trend over time check")})

    return {"charts": charts, "recommendations": recommendations}


def build_insights(
    exploration: dict[str, Any],
    preprocessing: dict[str, Any],
    eda: dict[str, Any],
    visualization: dict[str, Any],
) -> dict[str, Any]:
    summary = exploration["summary"]
    quality_issues = exploration["quality_issues"]
    top_corr = eda.get("top_correlations", [])
    distribution_summary = eda.get("distribution_summary", [])
    group_summary = eda.get("group_summary", [])
    chart_count = len(visualization.get("charts", []))

    points: list[str] = []
    detailed_findings: list[dict[str, Any]] = []
    risk_flags: list[str] = []
    opportunities: list[str] = []

    numeric_count = len(summary["numeric_columns"])
    categorical_count = len(summary["categorical_columns"])
    datetime_count = len(summary["datetime_columns"])
    missing_before = preprocessing.get("missing_before", 0)
    missing_after = preprocessing.get("missing_after", 0)
    duplicate_before = preprocessing.get("duplicate_before", summary["duplicate_rows"])
    duplicate_after = preprocessing.get("duplicate_after", 0)

    points.append(
        f"데이터는 {summary['rows']}행 {summary['columns']}열이며, 수치형 {numeric_count}개, 범주형 {categorical_count}개, 날짜형 {datetime_count}개 컬럼으로 구성되어 있습니다."
    )

    if preprocessing["required"]:
        points.append(
            f"전처리가 필요합니다. {len(preprocessing['plan']['steps'])}개의 계획이 생성되었고, 실제로 {len(preprocessing['actions'])}개의 작업이 실행되었습니다."
        )
        detailed_findings.append(
            {
                "title": "전처리 효과",
                "description": f"결측값은 {missing_before}개에서 {missing_after}개로, 중복 행은 {duplicate_before}개에서 {duplicate_after}개로 변경되었습니다.",
                "evidence": preprocessing["plan"]["reasons"],
            }
        )
    else:
        points.append("전처리 필요성이 낮습니다. 바로 EDA 단계로 이동해도 됩니다.")

    if quality_issues:
        issue_types = sorted({issue["type"] for issue in quality_issues})
        points.append(f"데이터 품질 이슈 {len(quality_issues)}건이 확인되었습니다. 주요 유형은 {', '.join(issue_types)}입니다.")
        for issue in quality_issues[:5]:
            target = f" 컬럼: {issue['column']}" if issue.get("column") else ""
            risk_flags.append(f"{issue['message']}{target}")
    else:
        points.append("명확한 데이터 품질 이슈가 발견되지 않았습니다.")

    if top_corr:
        strongest = top_corr[0]
        points.append(
            f"가장 강한 변수 관계는 {strongest['left']}와 {strongest['right']}이며 상관계수는 {strongest['correlation']}입니다."
        )
        detailed_findings.append(
            {
                "title": "상관관계 해석",
                "description": f"{strongest['left']}와 {strongest['right']}는 가장 강한 선형 관계를 보입니다. 상관계수의 절댓값이 클수록 두 변수의 동반 변화 가능성이 높습니다.",
                "evidence": [f"{item['left']} vs {item['right']}: {item['correlation']}" for item in top_corr[:3]],
            }
        )
        opportunities.append("상관관계가 높은 변수 조합을 기준으로 세부 원인 분석이나 예측 모델 후보 피처를 검토할 수 있습니다.")
    else:
        risk_flags.append("수치형 컬럼이 부족하거나 관계가 약해 상관관계 기반 해석은 제한적입니다.")

    if distribution_summary:
        highest_mean = max(
            [row for row in distribution_summary if row.get("mean") is not None],
            key=lambda row: float(row["mean"]),
            default=None,
        )
        if highest_mean:
            detailed_findings.append(
                {
                    "title": "분포 요약",
                    "description": f"{highest_mean['column']} 컬럼의 평균은 {highest_mean['mean']}이며, 수치형 컬럼 중 평균 수준이 가장 높게 나타났습니다.",
                    "evidence": [
                        f"{row['column']}: 평균 {row.get('mean')}, 중앙값 {row.get('median')}, 표준편차 {row.get('std')}"
                        for row in distribution_summary[:3]
                    ],
                }
            )

    if group_summary:
        detailed_findings.append(
            {
                "title": "그룹 분석 가능성",
                "description": f"범주형 기준 그룹 요약이 {len(group_summary)}개 행으로 생성되었습니다. 그룹 간 평균 차이를 비교해 세그먼트별 특징을 확인할 수 있습니다.",
                "evidence": [f"그룹 요약 컬럼: {', '.join(group_summary[0].keys())}"],
            }
        )
        opportunities.append("그룹별 평균 차이가 큰 컬럼을 중심으로 고객군, 상품군, 기간별 차이를 추가 분석할 수 있습니다.")

    points.append(f"시각화 {chart_count}건이 자동 생성되었습니다.")
    if chart_count:
        detailed_findings.append(
            {
                "title": "시각화 활용",
                "description": f"자동 생성된 {chart_count}개 차트는 분포, 변수 관계, 그룹 비교를 빠르게 확인하는 용도로 사용할 수 있습니다.",
                "evidence": [chart["title"] for chart in visualization.get("charts", [])[:5]],
            }
        )

    if missing_after > 0:
        risk_flags.append(f"전처리 후에도 결측값 {missing_after}개가 남아 있어 추가 규칙 검토가 필요합니다.")
    if duplicate_after > 0:
        risk_flags.append(f"전처리 후에도 중복 행 {duplicate_after}개가 남아 있습니다.")
    if not opportunities:
        opportunities.append("현재 결과는 기본 탐색 수준입니다. 목적 변수나 분석 목표를 지정하면 더 구체적인 비즈니스 인사이트를 도출할 수 있습니다.")

    return {
        "summary_points": points,
        "detailed_findings": detailed_findings,
        "risk_flags": risk_flags,
        "opportunities": opportunities,
        "next_actions": [
            "전처리 계획과 실행 결과를 검토해 업무 규칙에 맞는 결측값 처리 기준을 확정합니다.",
            "상관관계 상위 변수 조합을 기준으로 원인 분석 또는 예측 모델 후보 변수를 선정합니다.",
            "그룹 요약 결과를 기준으로 차이가 큰 세그먼트를 선별해 추가 EDA를 수행합니다.",
            "자동 생성된 차트를 리포트에 반영하고, 설명 문구를 분석 목적에 맞게 보강합니다.",
        ],
    }


def build_report_markdown(source_name: str, file_type: str, payload: dict[str, Any]) -> str:
    exploration = payload["exploration"]
    preprocessing = payload["preprocessing"]
    eda = payload["eda"]
    visualization = payload["visualization"]
    insights = payload["insights"]
    summary = exploration["summary"]

    lines = [
        "# 데이터 분석 통합 리포트",
        "",
        f"- 원본 파일: {source_name}",
        f"- 파일 형식: {file_type}",
        f"- 행 수: {summary['rows']}",
        f"- 열 수: {summary['columns']}",
        f"- 메모리 사용량: {summary['memory_mb']} MB",
        "",
        "## 1. 데이터 탐색",
        f"- 수치형 컬럼: {', '.join(summary['numeric_columns']) if summary['numeric_columns'] else '없음'}",
        f"- 범주형 컬럼: {', '.join(summary['categorical_columns']) if summary['categorical_columns'] else '없음'}",
        f"- 날짜형 컬럼: {', '.join(summary['datetime_columns']) if summary['datetime_columns'] else '없음'}",
        f"- 중복 행 수: {summary['duplicate_rows']}",
        "",
        "## 2. 전처리 필요 여부",
        f"- 필요성: {preprocessing['priority']}",
        f"- 판단 근거: {', '.join(preprocessing['plan']['reasons'])}",
        "- 수행 작업:",
    ]
    lines.extend([f"  - {action}" for action in preprocessing["actions"]] or ["  - 없음"])
    lines.extend(["", "## 3. EDA", "- 상관관계 상위 항목:"])
    if eda["top_correlations"]:
        for item in eda["top_correlations"]:
            lines.append(f"  - {item['left']} vs {item['right']}: {item['correlation']}")
    else:
        lines.append("  - 없음")

    lines.extend(["", "## 4. 시각화", f"- 자동 생성 차트 수: {len(visualization['charts'])}", "", "## 5. 인사이트"])
    lines.extend([f"- {point}" for point in insights["summary_points"]])
    return "\n".join(lines)


def analyze_file(file_name: str, content: bytes) -> PipelineResult:
    df = load_dataframe(file_name, content)
    file_type = Path(file_name).suffix.lower().lstrip(".")

    exploration = summarize_dataframe(df)
    processed_df, preprocessing = preprocess_dataframe(df, exploration["classified"])
    eda = build_eda(processed_df, exploration["classified"])
    visualization = build_visualizations(processed_df, exploration["classified"])
    insights = build_insights(exploration, preprocessing, eda, visualization)

    payload = {
        "exploration": exploration,
        "preprocessing": preprocessing,
        "eda": eda,
        "visualization": visualization,
        "insights": insights,
    }
    report_markdown = build_report_markdown(file_name, file_type, payload)

    return PipelineResult(
        source_name=file_name,
        file_type=file_type,
        exploration=exploration,
        preprocessing=preprocessing,
        eda=eda,
        visualization=visualization,
        insights=insights,
        report_markdown=report_markdown,
    )

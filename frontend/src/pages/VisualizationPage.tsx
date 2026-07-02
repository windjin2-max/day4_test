import { useState } from "react";

import type { ExploreResponse } from "../lib/api";

type VisualizationPageProps = {
  result: ExploreResponse | null;
};

type ChartItem = ExploreResponse["visualization"]["charts"][number];

function downloadVisualization(result: ExploreResponse) {
  const baseName = result.source_name.replace(/\.[^.]+$/, "");
  const blob = new Blob([JSON.stringify(result.visualization, null, 2)], {
    type: "application/json;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${baseName}_visualization.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function formatRecommendation(item: Record<string, unknown>) {
  const columns = Array.isArray(item.columns) ? item.columns.join(", ") : String(item.column ?? "");
  return {
    chart: String(item.chart ?? ""),
    columns,
    reason: String(item.reason ?? ""),
  };
}

export default function VisualizationPage({ result }: VisualizationPageProps) {
  const [selectedChart, setSelectedChart] = useState<ChartItem | null>(null);

  if (!result) {
    return (
      <section className="page">
        <div className="page-heading">
          <h2>시각화</h2>
          <p>업로드 후 시각화 결과가 표시됩니다.</p>
        </div>
        <div className="empty-state">데이터 탐색 메뉴에서 파일을 먼저 업로드하세요.</div>
      </section>
    );
  }

  return (
    <section className="page">
      <div className="section-header">
        <div className="page-heading">
          <h2>시각화 결과</h2>
          <p>분포, 이상치, 범주 구성, 변수 관계, 그룹 비교, 시계열 관점의 차트를 확인합니다.</p>
        </div>
        <button type="button" className="ghost-button" onClick={() => downloadVisualization(result)}>
          시각화 결과 다운로드
        </button>
      </div>

      <div className="result-stack">
        <article className="panel result-section">
          <h3>생성 요약</h3>
          <div className="summary-grid">
            <div>
              <strong>차트 수</strong>
              <span>{result.visualization.charts.length}</span>
            </div>
            <div>
              <strong>추천 관점</strong>
              <span>{result.visualization.recommendations.length}</span>
            </div>
            <div>
              <strong>수치형 컬럼</strong>
              <span>{result.exploration.summary.numeric_columns.length}</span>
            </div>
            <div>
              <strong>범주형 컬럼</strong>
              <span>{result.exploration.summary.categorical_columns.length}</span>
            </div>
          </div>
        </article>

        {result.visualization.recommendations.length > 0 ? (
          <article className="panel result-section">
            <h3>추천 분석 관점</h3>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>차트 유형</th>
                    <th>대상 컬럼</th>
                    <th>분석 관점</th>
                  </tr>
                </thead>
                <tbody>
                  {result.visualization.recommendations.map((item, index) => {
                    const recommendation = formatRecommendation(item);
                    return (
                      <tr key={index}>
                        <td>{recommendation.chart}</td>
                        <td>{recommendation.columns}</td>
                        <td>{recommendation.reason}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </article>
        ) : null}

        <article className="panel result-section">
          <h3>생성 차트</h3>
          {result.visualization.charts.length > 0 ? (
            <div className="chart-grid">
              {result.visualization.charts.map((chart) => (
                <figure key={`${chart.title}-${chart.chart_type}`} className="chart-card">
                  <button type="button" className="chart-preview-button" onClick={() => setSelectedChart(chart)}>
                    <img src={`data:${chart.mime_type};base64,${chart.image_base64}`} alt={chart.title} />
                  </button>
                  <figcaption>
                    <strong>{chart.title}</strong>
                    <span>{chart.chart_type}</span>
                  </figcaption>
                </figure>
              ))}
            </div>
          ) : (
            <p>생성된 차트가 없습니다.</p>
          )}
        </article>
      </div>

      {selectedChart ? (
        <div className="chart-modal-backdrop" role="presentation" onClick={() => setSelectedChart(null)}>
          <div className="chart-modal" role="dialog" aria-modal="true" aria-label={selectedChart.title} onClick={(event) => event.stopPropagation()}>
            <div className="section-header">
              <div>
                <h3>{selectedChart.title}</h3>
                <p className="muted">{selectedChart.chart_type}</p>
              </div>
              <button type="button" className="ghost-button" onClick={() => setSelectedChart(null)}>
                닫기
              </button>
            </div>
            <img
              className="chart-modal-image"
              src={`data:${selectedChart.mime_type};base64,${selectedChart.image_base64}`}
              alt={selectedChart.title}
            />
          </div>
        </div>
      ) : null}
    </section>
  );
}

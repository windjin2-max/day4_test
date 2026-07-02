import { useMemo, useState } from "react";

import { api, type ExploreResponse } from "../lib/api";

type DataExplorerPageProps = {
  result: ExploreResponse | null;
  onAnalysisComplete: (result: ExploreResponse) => void;
};

function downloadTextFile(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function DataExplorerPage({ result, onAnalysisComplete }: DataExplorerPageProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const downloadBaseName = useMemo(() => {
    if (!result) return "analysis";
    return result.source_name.replace(/\.[^.]+$/, "");
  }, [result]);

  async function handleAnalyze() {
    if (!selectedFile) {
      setError("CSV 또는 Excel 파일을 선택하세요.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.exploreFile(selectedFile);
      onAnalysisComplete(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "분석에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  function handleDownloadExploration() {
    if (!result) return;
    downloadTextFile(
      `${downloadBaseName}_exploration.json`,
      JSON.stringify(result.exploration, null, 2),
      "application/json;charset=utf-8",
    );
  }

  return (
    <section className="page">
      <div className="page-heading">
        <h2>데이터 탐색</h2>
        <p>파일을 업로드하면 기본 개요, 컬럼 유형, 품질 이슈를 확인합니다.</p>
      </div>

      <div className="upload-card">
        <input
          type="file"
          accept=".csv,.xls,.xlsx"
          onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
        />
        <button type="button" onClick={handleAnalyze} disabled={loading}>
          {loading ? "분석 중..." : "분석 시작"}
        </button>
      </div>

      {error ? <p className="error-text">{error}</p> : null}

      {result ? (
        <article className="panel result-section">
          <div className="section-header">
            <div>
              <h3>4.1 데이터 탐색 결과</h3>
              <p className="muted">{result.source_name}</p>
            </div>
            <button type="button" className="ghost-button" onClick={handleDownloadExploration}>
              탐색 결과 다운로드
            </button>
          </div>

          <div className="summary-grid">
            <div>
              <strong>행</strong>
              <span>{result.exploration.summary.rows}</span>
            </div>
            <div>
              <strong>열</strong>
              <span>{result.exploration.summary.columns}</span>
            </div>
            <div>
              <strong>메모리</strong>
              <span>{result.exploration.summary.memory_mb} MB</span>
            </div>
            <div>
              <strong>중복 행</strong>
              <span>{result.exploration.summary.duplicate_rows}</span>
            </div>
          </div>

          <div className="detail-list">
            <p>
              <strong>수치형</strong> {result.exploration.summary.numeric_columns.join(", ") || "없음"}
            </p>
            <p>
              <strong>범주형</strong> {result.exploration.summary.categorical_columns.join(", ") || "없음"}
            </p>
            <p>
              <strong>날짜형</strong> {result.exploration.summary.datetime_columns.join(", ") || "없음"}
            </p>
          </div>

          <h4>품질 이슈</h4>
          {result.exploration.quality_issues.length > 0 ? (
            <ul>
              {result.exploration.quality_issues.map((issue, index) => (
                <li key={`${issue.type}-${issue.column ?? index}`}>{issue.message}</li>
              ))}
            </ul>
          ) : (
            <p>확인된 품질 이슈가 없습니다.</p>
          )}
        </article>
      ) : (
        <div className="empty-state">분석할 파일을 업로드하세요.</div>
      )}
    </section>
  );
}

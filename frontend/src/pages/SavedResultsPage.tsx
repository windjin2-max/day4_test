import type { SavedAnalysis } from "../App";
import type { ExploreResponse } from "../lib/api";

type SavedResultsPageProps = {
  currentResult: ExploreResponse | null;
  savedResults: SavedAnalysis[];
  onDelete: (id: string) => void;
  onLoad: (item: SavedAnalysis) => void;
};

function formatSavedAt(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function downloadSavedResult(item: SavedAnalysis) {
  const baseName = item.result.source_name.replace(/\.[^.]+$/, "");
  const blob = new Blob([JSON.stringify(item.result, null, 2)], {
    type: "application/json;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${baseName}_saved_analysis.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function SavedResultsPage({ currentResult, savedResults, onDelete, onLoad }: SavedResultsPageProps) {
  return (
    <section className="page">
      <div className="page-heading">
        <h2>저장 결과</h2>
        <p>분석 완료된 결과를 다시 불러오거나 JSON으로 다운로드합니다.</p>
      </div>

      {currentResult ? (
        <article className="panel result-section">
          <h3>현재 불러온 결과</h3>
          <div className="summary-grid">
            <div>
              <strong>파일</strong>
              <span>{currentResult.source_name}</span>
            </div>
            <div>
              <strong>행</strong>
              <span>{currentResult.exploration.summary.rows}</span>
            </div>
            <div>
              <strong>열</strong>
              <span>{currentResult.exploration.summary.columns}</span>
            </div>
            <div>
              <strong>차트</strong>
              <span>{currentResult.visualization.charts.length}</span>
            </div>
          </div>
        </article>
      ) : null}

      {savedResults.length > 0 ? (
        <div className="saved-list">
          {savedResults.map((item) => (
            <article key={item.id} className="panel saved-item">
              <div>
                <h3>{item.result.source_name}</h3>
                <p className="muted">{formatSavedAt(item.savedAt)}</p>
              </div>

              <div className="summary-grid compact">
                <div>
                  <strong>행</strong>
                  <span>{item.result.exploration.summary.rows}</span>
                </div>
                <div>
                  <strong>열</strong>
                  <span>{item.result.exploration.summary.columns}</span>
                </div>
                <div>
                  <strong>전처리</strong>
                  <span>{item.result.preprocessing.priority}</span>
                </div>
                <div>
                  <strong>차트</strong>
                  <span>{item.result.visualization.charts.length}</span>
                </div>
              </div>

              <div className="button-row">
                <button type="button" className="ghost-button" onClick={() => onLoad(item)}>
                  불러오기
                </button>
                <button type="button" className="ghost-button" onClick={() => downloadSavedResult(item)}>
                  다운로드
                </button>
                <button type="button" className="danger-button" onClick={() => onDelete(item.id)}>
                  삭제
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">저장된 분석 결과가 없습니다. 데이터 탐색에서 파일을 분석하면 자동 저장됩니다.</div>
      )}
    </section>
  );
}

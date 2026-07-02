import type { ExploreResponse } from "../lib/api";

type PreprocessPageProps = {
  result: ExploreResponse | null;
};

function downloadPreprocessing(result: ExploreResponse) {
  const baseName = result.source_name.replace(/\.[^.]+$/, "");
  const blob = new Blob([JSON.stringify(result.preprocessing, null, 2)], {
    type: "application/json;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${baseName}_preprocessing.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function PreprocessPage({ result }: PreprocessPageProps) {
  if (!result) {
    return (
      <section className="page">
        <div className="page-heading">
          <h2>전처리</h2>
          <p>업로드 후 전처리 판단 결과가 표시됩니다.</p>
        </div>
        <div className="empty-state">데이터 탐색 메뉴에서 파일을 먼저 업로드하세요.</div>
      </section>
    );
  }

  return (
    <section className="page">
      <div className="section-header">
        <div className="page-heading">
          <h2>전처리 결과</h2>
          <p>판정 근거, 계획, 실행 내역, 전후 비교를 확인합니다.</p>
        </div>
        <button type="button" className="ghost-button" onClick={() => downloadPreprocessing(result)}>
          전처리 결과 다운로드
        </button>
      </div>

      <article className="panel result-section">
        <div className="summary-grid">
          <div>
            <strong>전처리 필요</strong>
            <span>{result.preprocessing.required ? "예" : "아니오"}</span>
          </div>
          <div>
            <strong>우선순위</strong>
            <span>{result.preprocessing.priority}</span>
          </div>
          <div>
            <strong>중복 전후</strong>
            <span>
              {result.preprocessing.duplicate_before} {"->"} {result.preprocessing.duplicate_after}
            </span>
          </div>
          <div>
            <strong>결측 전후</strong>
            <span>
              {result.preprocessing.missing_before} {"->"} {result.preprocessing.missing_after}
            </span>
          </div>
        </div>

        <h3>판정 근거</h3>
        <ul>
          {result.preprocessing.plan.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>

        <h3>전처리 계획</h3>
        {result.preprocessing.plan.steps.length > 0 ? (
          <ol>
            {result.preprocessing.plan.steps.map((step) => (
              <li key={step.key}>
                {step.label}
                {step.columns?.length ? ` (${step.columns.join(", ")})` : ""}
              </li>
            ))}
          </ol>
        ) : (
          <p>추가 전처리 계획이 없습니다.</p>
        )}

        <h3>실행 결과</h3>
        {result.preprocessing.actions.length > 0 ? (
          <ul>
            {result.preprocessing.actions.map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ul>
        ) : (
          <p>실행된 전처리 작업이 없습니다.</p>
        )}
      </article>
    </section>
  );
}

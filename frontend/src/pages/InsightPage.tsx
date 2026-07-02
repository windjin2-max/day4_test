import type { ExploreResponse } from "../lib/api";

type InsightPageProps = {
  result: ExploreResponse | null;
};

function downloadInsights(result: ExploreResponse) {
  const baseName = result.source_name.replace(/\.[^.]+$/, "");
  const blob = new Blob([JSON.stringify(result.insights, null, 2)], {
    type: "application/json;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${baseName}_insights.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function InsightPage({ result }: InsightPageProps) {
  if (!result) {
    return (
      <section className="page">
        <div className="page-heading">
          <h2>인사이트</h2>
          <p>업로드 후 인사이트 결과가 표시됩니다.</p>
        </div>
        <div className="empty-state">데이터 탐색 메뉴에서 파일을 먼저 업로드하세요.</div>
      </section>
    );
  }

  return (
    <section className="page">
      <div className="section-header">
        <div className="page-heading">
          <h2>인사이트 결과</h2>
          <p>핵심 요약, 상세 발견 사항, 리스크, 추가 기회를 나눠 확인합니다.</p>
        </div>
        <button type="button" className="ghost-button" onClick={() => downloadInsights(result)}>
          인사이트 결과 다운로드
        </button>
      </div>

      <div className="result-stack">
        <article className="panel result-section">
          <h3>핵심 요약</h3>
          <ul>
            {result.insights.summary_points.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        </article>

        <article className="panel result-section">
          <h3>상세 발견 사항</h3>
          {result.insights.detailed_findings.length > 0 ? (
            <div className="insight-list">
              {result.insights.detailed_findings.map((finding) => (
                <section key={finding.title} className="insight-card">
                  <h4>{finding.title}</h4>
                  <p>{finding.description}</p>
                  {finding.evidence.length > 0 ? (
                    <ul>
                      {finding.evidence.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : null}
                </section>
              ))}
            </div>
          ) : (
            <p>상세 발견 사항이 없습니다.</p>
          )}
        </article>

        <article className="panel result-section">
          <h3>주의할 점</h3>
          {result.insights.risk_flags.length > 0 ? (
            <ul>
              {result.insights.risk_flags.map((risk) => (
                <li key={risk}>{risk}</li>
              ))}
            </ul>
          ) : (
            <p>추가로 확인된 리스크가 없습니다.</p>
          )}
        </article>

        <article className="panel result-section">
          <h3>추가 분석 기회</h3>
          <ul>
            {result.insights.opportunities.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </article>

        <article className="panel result-section">
          <h3>다음 액션</h3>
          <ol>
            {result.insights.next_actions.map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ol>
        </article>
      </div>
    </section>
  );
}

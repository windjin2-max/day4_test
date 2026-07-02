import type { ExploreResponse } from "../lib/api";

type EdaPageProps = {
  result: ExploreResponse | null;
};

function downloadEda(result: ExploreResponse) {
  const baseName = result.source_name.replace(/\.[^.]+$/, "");
  const blob = new Blob([JSON.stringify(result.eda, null, 2)], {
    type: "application/json;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${baseName}_eda.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function EdaPage({ result }: EdaPageProps) {
  if (!result) {
    return (
      <section className="page">
        <div className="page-heading">
          <h2>EDA</h2>
          <p>업로드 후 EDA 결과가 표시됩니다.</p>
        </div>
        <div className="empty-state">데이터 탐색 메뉴에서 파일을 먼저 업로드하세요.</div>
      </section>
    );
  }

  return (
    <section className="page">
      <div className="section-header">
        <div className="page-heading">
          <h2>EDA 결과</h2>
          <p>상관관계, 그룹 요약, 분포 요약을 확인합니다.</p>
        </div>
        <button type="button" className="ghost-button" onClick={() => downloadEda(result)}>
          EDA 결과 다운로드
        </button>
      </div>

      <article className="panel result-section">
        <h3>상관관계 상위 항목</h3>
        {result.eda.top_correlations.length > 0 ? (
          <ul>
            {result.eda.top_correlations.map((item) => (
              <li key={`${item.left}-${item.right}`}>
                {item.left} vs {item.right}: {item.correlation}
              </li>
            ))}
          </ul>
        ) : (
          <p>수치형 컬럼이 부족해 상관분석을 수행할 수 없습니다.</p>
        )}

        <h3>분포 요약</h3>
        {result.eda.distribution_summary.length > 0 ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {Object.keys(result.eda.distribution_summary[0] ?? {}).map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.eda.distribution_summary.map((row, index) => (
                  <tr key={index}>
                    {Object.values(row).map((value, cellIndex) => (
                      <td key={cellIndex}>{String(value ?? "")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>분포 요약이 없습니다.</p>
        )}

        <h3>그룹 요약</h3>
        {result.eda.group_summary.length > 0 ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {Object.keys(result.eda.group_summary[0] ?? {}).map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.eda.group_summary.map((row, index) => (
                  <tr key={index}>
                    {Object.values(row).map((value, cellIndex) => (
                      <td key={cellIndex}>{String(value ?? "")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>그룹 요약이 없습니다.</p>
        )}
      </article>
    </section>
  );
}

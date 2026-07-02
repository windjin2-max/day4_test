import type { ExploreResponse } from "../lib/api";

type HomePageProps = {
  result: ExploreResponse | null;
};

export default function HomePage({ result }: HomePageProps) {
  return (
    <section className="page">
      <div className="page-heading">
        <h2>홈</h2>
        <p>업로드된 분석 결과의 전체 진행 상태를 확인합니다.</p>
      </div>

      {result ? (
        <div className="panel-grid">
          <article className="panel">
            <h3>파일</h3>
            <p>{result.source_name}</p>
            <p className="muted">{result.file_type.toUpperCase()}</p>
          </article>
          <article className="panel">
            <h3>데이터 규모</h3>
            <p>
              {result.exploration.summary.rows}행 / {result.exploration.summary.columns}열
            </p>
          </article>
          <article className="panel">
            <h3>자동 생성 결과</h3>
            <p>차트 {result.visualization.charts.length}개</p>
            <p>인사이트 {result.insights.summary_points.length}개</p>
          </article>
        </div>
      ) : (
        <div className="empty-state">데이터 탐색 메뉴에서 파일을 먼저 업로드하세요.</div>
      )}
    </section>
  );
}

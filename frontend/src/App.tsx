import { useEffect, useState } from "react";

import { api, type ExploreResponse } from "./lib/api";
import DataExplorerPage from "./pages/DataExplorerPage";
import EdaPage from "./pages/EdaPage";
import HomePage from "./pages/HomePage";
import InsightPage from "./pages/InsightPage";
import PreprocessPage from "./pages/PreprocessPage";
import SavedResultsPage from "./pages/SavedResultsPage";
import VisualizationPage from "./pages/VisualizationPage";

type TabKey = "home" | "explore" | "preprocess" | "eda" | "visualization" | "insight" | "saved";

export type SavedAnalysis = {
  id: string;
  savedAt: string;
  result: ExploreResponse;
};

const STORAGE_KEY = "data-analysis-automation.saved-results";

const navItems: Array<{ key: TabKey; label: string }> = [
  { key: "home", label: "홈" },
  { key: "explore", label: "데이터 탐색" },
  { key: "preprocess", label: "전처리" },
  { key: "eda", label: "EDA" },
  { key: "visualization", label: "시각화" },
  { key: "insight", label: "인사이트" },
  { key: "saved", label: "저장 결과" },
];

function loadSavedResults(): SavedAnalysis[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as SavedAnalysis[]) : [];
  } catch {
    return [];
  }
}

function persistSavedResults(items: SavedAnalysis[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export default function App() {
  const [backendStatus, setBackendStatus] = useState("unknown");
  const [dbStatus, setDbStatus] = useState("unknown");
  const [activeTab, setActiveTab] = useState<TabKey>("explore");
  const [analysisResult, setAnalysisResult] = useState<ExploreResponse | null>(null);
  const [savedResults, setSavedResults] = useState<SavedAnalysis[]>(() => loadSavedResults());
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    api.health().then((data) => setBackendStatus(data.status)).catch(() => setBackendStatus("error"));
    api.dbHealth().then((data) => setDbStatus(data.status)).catch(() => setDbStatus("error"));
  }, []);

  function saveAnalysisResult(result: ExploreResponse) {
    const item: SavedAnalysis = {
      id: `${Date.now()}-${result.source_name}`,
      savedAt: new Date().toISOString(),
      result,
    };
    const nextItems = [item, ...savedResults].slice(0, 20);

    try {
      persistSavedResults(nextItems);
      setSavedResults(nextItems);
      setSaveError(null);
    } catch {
      setSaveError("브라우저 저장 공간이 부족해 결과를 저장하지 못했습니다.");
    }
  }

  function handleAnalysisComplete(result: ExploreResponse) {
    setAnalysisResult(result);
    saveAnalysisResult(result);
    setActiveTab("explore");
  }

  function handleLoadSavedResult(item: SavedAnalysis) {
    setAnalysisResult(item.result);
    setActiveTab("explore");
  }

  function handleDeleteSavedResult(id: string) {
    const nextItems = savedResults.filter((item) => item.id !== id);
    persistSavedResults(nextItems);
    setSavedResults(nextItems);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <p className="eyebrow">Data Analysis Automation</p>
          <h1>데이터 분석 자동화</h1>
          <p className="muted">파일 업로드 후 상단 메뉴에서 단계별 결과와 저장 결과를 확인합니다.</p>
        </div>

        <nav className="topnav" aria-label="분석 단계 메뉴">
          {navItems.map((item) => (
            <button
              key={item.key}
              type="button"
              className={`topnav-link${activeTab === item.key ? " active" : ""}`}
              onClick={() => setActiveTab(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="status-row">
          <span>
            Backend: <strong>{backendStatus}</strong>
          </span>
          <span>
            Database: <strong>{dbStatus}</strong>
          </span>
          <span>
            Saved: <strong>{savedResults.length}</strong>
          </span>
          {analysisResult ? (
            <span>
              File: <strong>{analysisResult.source_name}</strong>
            </span>
          ) : null}
        </div>
        {saveError ? <p className="error-text">{saveError}</p> : null}
      </header>

      <main className="content">
        {activeTab === "home" ? <HomePage result={analysisResult} /> : null}
        {activeTab === "explore" ? (
          <DataExplorerPage result={analysisResult} onAnalysisComplete={handleAnalysisComplete} />
        ) : null}
        {activeTab === "preprocess" ? <PreprocessPage result={analysisResult} /> : null}
        {activeTab === "eda" ? <EdaPage result={analysisResult} /> : null}
        {activeTab === "visualization" ? <VisualizationPage result={analysisResult} /> : null}
        {activeTab === "insight" ? <InsightPage result={analysisResult} /> : null}
        {activeTab === "saved" ? (
          <SavedResultsPage
            currentResult={analysisResult}
            savedResults={savedResults}
            onDelete={handleDeleteSavedResult}
            onLoad={handleLoadSavedResult}
          />
        ) : null}
      </main>
    </div>
  );
}

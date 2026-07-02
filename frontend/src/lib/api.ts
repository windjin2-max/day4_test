const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export type ExploreQualityIssue = {
  type: string;
  severity: string;
  column?: string;
  message: string;
};

export type ExploreResponse = {
  job_id: number;
  source_name: string;
  file_type: string;
  exploration: {
    summary: {
      rows: number;
      columns: number;
      memory_mb: number;
      duplicate_rows: number;
      numeric_columns: string[];
      categorical_columns: string[];
      datetime_columns: string[];
    };
    column_profile: Array<{
      column: string;
      dtype: string;
      missing_count: number;
      missing_rate: number;
      unique_count: number;
    }>;
    numeric_summary: Array<Record<string, unknown>>;
    categorical_summary: Array<Record<string, unknown>>;
    quality_issues: ExploreQualityIssue[];
    sample_rows: Array<Record<string, unknown>>;
  };
  preprocessing: {
    required: boolean;
    priority: string;
    plan: {
      required: boolean;
      priority: string;
      reasons: string[];
      steps: Array<{
        key: string;
        label: string;
        required: boolean;
        columns?: string[];
      }>;
    };
    actions: string[];
    rows_before: number;
    rows_after: number;
    missing_before: number;
    missing_after: number;
    duplicate_before: number;
    duplicate_after: number;
    improved: boolean;
    summary: {
      removed_duplicates: number;
      filled_missing: number;
    };
  };
  eda: {
    correlation_matrix: Array<Record<string, unknown>>;
    top_correlations: Array<{
      left: string;
      right: string;
      correlation: number;
    }>;
    group_summary: Array<Record<string, unknown>>;
    distribution_summary: Array<Record<string, unknown>>;
  };
  visualization: {
    charts: Array<{
      title: string;
      chart_type: string;
      image_base64: string;
      mime_type: string;
    }>;
    recommendations: Array<Record<string, unknown>>;
  };
  insights: {
    summary_points: string[];
    detailed_findings: Array<{
      title: string;
      description: string;
      evidence: string[];
    }>;
    risk_flags: string[];
    opportunities: string[];
    next_actions: string[];
  };
  report_markdown: string;
};

export const api = {
  health: () => request<{ status: string; service: string }>("/api/health"),
  dbHealth: () => request<{ status: string; database: string }>("/api/db/health"),
  exploreFile: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${BASE_URL}/api/explore`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const detail = await response.json().catch(() => null);
      throw new Error(detail?.detail ?? `Request failed: ${response.status}`);
    }

    return response.json() as Promise<ExploreResponse>;
  },
};

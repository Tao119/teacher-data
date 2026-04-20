const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
  return res.json();
}

export interface ProjectStats {
  total_records: number;
  train_count: number;
  review_count: number;
  avg_similarity: number;
  total_audio_files: number;
  total_cost_usd: number;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  language: string;
  agree_threshold: number;
  review_threshold: number;
  concurrency: number;
  created_at: string;
  updated_at: string;
  stats?: ProjectStats;
}

export interface Record {
  id: string;
  project_id: string;
  audio_file_id: string;
  start_sec: number;
  end_sec: number;
  text: string;
  original_text: string;
  whisper_text: string;
  gemini_text: string;
  strategy: string;
  similarity: number;
  confidence: number;
  cer: number;
  bucket: string;
  reviewed_at: string | null;
  created_at: string;
  audio_file_name?: string;
}

export interface RecordList {
  items: Record[];
  total: number;
  page: number;
  per_page: number;
}

export const api = {
  projects: {
    list: () => req<Project[]>("/projects"),
    get: (id: string) => req<Project>(`/projects/${id}`),
    create: (body: { name: string; description?: string; language?: string }) =>
      req<Project>("/projects", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }),
    delete: (id: string) => fetch(`${BASE}/projects/${id}`, { method: "DELETE" }),
  },
  uploads: {
    upload: (projectId: string, files: File[]) => {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      return req<{ uploaded: number; files: { id: string; name: string }[] }>(
        `/projects/${projectId}/uploads`,
        { method: "POST", body: form }
      );
    },
    deleteFile: (audioFileId: string) =>
      fetch(`${BASE}/audio-files/${audioFileId}`, { method: "DELETE" }),
  },
  jobs: {
    create: (projectId: string, audioFileIds?: string[]) =>
      req<{ job_id: string; total_files: number }>(`/projects/${projectId}/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audio_file_ids: audioFileIds ?? null }),
      }),
    get: (jobId: string) => req<{ id: string; status: string; processed: number; total_files: number; written: number }>(`/jobs/${jobId}`),
  },
  records: {
    list: (projectId: string, bucket?: string, page = 1) =>
      req<RecordList>(`/projects/${projectId}/records?${bucket ? `bucket=${bucket}&` : ""}page=${page}&per_page=30`),
    update: (id: string, text: string) =>
      req<Record>(`/records/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) }),
    approve: (id: string) => req<Record>(`/records/${id}/approve`, { method: "POST" }),
    reject: (id: string) => req<Record>(`/records/${id}/reject`, { method: "POST" }),
    reset: (id: string) => req<Record>(`/records/${id}/reset`, { method: "POST" }),
    audioUrl: (id: string) => `${BASE}/records/${id}/audio`,
  },
  exports: {
    trainUrl: (projectId: string) => `${BASE}/projects/${projectId}/export/train.jsonl`,
    reviewUrl: (projectId: string) => `${BASE}/projects/${projectId}/export/review.jsonl`,
    zipUrl: (projectId: string) => `${BASE}/projects/${projectId}/export.zip`,
  },
};

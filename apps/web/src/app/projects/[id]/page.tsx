"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, Project } from "@/lib/api";
import { Upload, Download, ClipboardList, ChevronLeft, Loader2, CheckCircle2, AlertCircle, FileAudio, Database, Trash2 } from "lucide-react";

interface AudioFile { id: string; name: string; status: string; size_bytes: number; error?: string }

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const STATUS_STYLE: Record<string, { bg: string; text: string; label: string }> = {
  pending:    { bg: "#f3f4f6", text: "#6b7280", label: "待機中" },
  processing: { bg: "#eff6ff", text: "#2563eb", label: "処理中" },
  done:       { bg: "#f0fdf4", text: "#16a34a", label: "完了" },
  failed:     { bg: "#fef2f2", text: "#dc2626", label: "失敗" },
};

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [audioFiles, setAudioFiles] = useState<AudioFile[]>([]);
  const [jobStatus, setJobStatus] = useState<{ status: string; processed: number; total: number } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const esRef = useRef<EventSource | null>(null);

  const loadProject = useCallback(() => api.projects.get(id).then(setProject).catch(console.error), [id]);
  const loadFiles = useCallback(() =>
    fetch(`${BASE}/projects/${id}/audio-files`).then(r => r.json()).then(setAudioFiles).catch(console.error), [id]);

  useEffect(() => { loadProject(); loadFiles(); }, [loadProject, loadFiles]);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const arr = Array.from(files);
    await api.uploads.upload(id, arr);
    await loadFiles();
    const { job_id, total_files } = await api.jobs.create(id);
    setJobStatus({ status: "running", processed: 0, total: total_files });
    if (esRef.current) esRef.current.close();
    const es = new EventSource(`${BASE}/jobs/${job_id}/events`);
    esRef.current = es;
    es.addEventListener("file_done", e => {
      const d = JSON.parse(e.data);
      setJobStatus(prev => prev ? { ...prev, processed: d.processed, total: d.total } : prev);
      loadFiles();
    });
    es.addEventListener("completed", () => {
      es.close();
      setJobStatus(prev => prev ? { ...prev, status: "completed" } : prev);
      loadProject(); loadFiles();
    });
    es.addEventListener("failed", () => { es.close(); setJobStatus(prev => prev ? { ...prev, status: "failed" } : prev); loadFiles(); });
  };

  if (!project) return (
    <div className="h-screen flex items-center justify-center" style={{ background: "var(--bg)" }}>
      <Loader2 size={20} className="animate-spin" style={{ color: "var(--text-muted)" }} />
    </div>
  );

  const stats = project.stats;
  const pct = jobStatus && jobStatus.total > 0 ? (jobStatus.processed / jobStatus.total) * 100 : 0;

  return (
    <div className="min-h-screen" style={{ background: "var(--bg)" }}>
      {/* Top bar */}
      <header style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)" }}
        className="sticky top-0 z-10">
        <div className="px-4 h-12 flex items-center gap-2 min-w-0">
          <Database size={16} className="shrink-0" style={{ color: "var(--accent)" }} />
          <Link href="/" className="text-sm font-semibold shrink-0" style={{ color: "var(--text-primary)" }}>Teacher Data</Link>
          <span className="shrink-0" style={{ color: "var(--text-muted)" }}>/</span>
          <span className="text-sm truncate min-w-0" style={{ color: "var(--text-secondary)" }}>{project.name}</span>
          <div className="ml-auto shrink-0 flex items-center gap-2">
            <Link href={`/projects/${id}/review`}
              className="flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-md transition-colors whitespace-nowrap"
              style={{ background: "var(--accent)", color: "#fff" }}>
              <ClipboardList size={14} /> レビュー
              {(stats?.review_count ?? 0) > 0 && (
                <span className="ml-0.5 px-1.5 py-0.5 text-xs rounded-full font-medium"
                  style={{ background: "rgba(255,255,255,0.25)" }}>{stats!.review_count}</span>
              )}
            </Link>
            <Link href={`/projects/${id}/review?filter=all`}
              className="flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-md border transition-colors whitespace-nowrap"
              style={{ color: "var(--text-secondary)", borderColor: "var(--border)", background: "var(--surface)" }}>
              全件
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-6 space-y-4">
        {/* Stats row */}
        <div className="grid grid-cols-5 gap-3">
          {[
            { label: "音声ファイル", value: stats?.total_audio_files ?? 0, unit: "件", accent: "#2563eb" },
            { label: "train", value: stats?.train_count ?? 0, unit: "件", accent: "#16a34a" },
            { label: "review", value: stats?.review_count ?? 0, unit: "件", accent: "#d97706" },
            { label: "平均類似度", value: stats ? `${Math.round(stats.avg_similarity * 100)}%` : "—", unit: "", accent: "#111827" },
            { label: "推定コスト", value: stats ? `¥${Math.round(stats.total_cost_usd * 150)}` : "—", unit: "", accent: "#6b7280" },
          ].map(s => (
            <div key={s.label} className="rounded-lg border px-4 py-3"
              style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
              <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>{s.label}</p>
              <p className="text-2xl font-semibold font-mono" style={{ color: s.accent }}>
                {s.value}<span className="text-sm font-normal ml-0.5" style={{ color: "var(--text-muted)" }}>{s.unit}</span>
              </p>
            </div>
          ))}
        </div>

        {/* Upload */}
        <div className="rounded-lg border" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
          <div className="px-4 py-2.5 border-b flex items-center gap-2"
            style={{ borderColor: "var(--border)" }}>
            <Upload size={14} style={{ color: "var(--text-muted)" }} />
            <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>音声ファイルを追加</span>
          </div>
          <div className="p-4">
            <div
              className="border-2 border-dashed rounded-md p-6 text-center cursor-pointer transition-colors"
              style={{ borderColor: "var(--border-strong)" }}
              onClick={() => fileRef.current?.click()}
              onDrop={e => { e.preventDefault(); handleFiles(e.dataTransfer.files); }}
              onDragOver={e => e.preventDefault()}
              onDragEnter={e => (e.currentTarget.style.borderColor = "var(--accent)")}
              onDragLeave={e => (e.currentTarget.style.borderColor = "var(--border-strong)")}>
              <input ref={fileRef} type="file" multiple accept=".mp3,.wav,.m4a,.mp4,.flac,.ogg,.webm"
                className="hidden" onChange={e => handleFiles(e.target.files)} />
              <FileAudio size={24} className="mx-auto mb-2" style={{ color: "var(--text-muted)" }} />
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                ドロップ または <span style={{ color: "var(--accent)" }}>クリックして選択</span>
              </p>
              <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>MP3, WAV, M4A, FLAC, OGG</p>
            </div>

            {/* Job progress */}
            {jobStatus && (
              <div className="mt-3 rounded-md px-3 py-2.5"
                style={{ background: "var(--bg)", border: "1px solid var(--border)" }}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 text-xs" style={{ color: "var(--text-secondary)" }}>
                    {jobStatus.status === "running" && <Loader2 size={12} className="animate-spin" style={{ color: "var(--accent)" }} />}
                    {jobStatus.status === "completed" && <CheckCircle2 size={12} style={{ color: "var(--success)" }} />}
                    {jobStatus.status === "failed" && <AlertCircle size={12} style={{ color: "var(--danger)" }} />}
                    {jobStatus.status === "running" && "文字起こし処理中..."}
                    {jobStatus.status === "completed" && "処理完了"}
                    {jobStatus.status === "failed" && "処理に失敗しました"}
                  </div>
                  <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                    {jobStatus.processed} / {jobStatus.total}
                  </span>
                </div>
                <div className="h-1 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
                  <div className="h-1 rounded-full transition-all duration-500"
                    style={{ width: `${pct}%`, background: jobStatus.status === "completed" ? "var(--success)" : "var(--accent)" }} />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* File list */}
        {audioFiles.length > 0 && (
          <div className="rounded-lg border overflow-hidden"
            style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
            <div className="px-4 py-2.5 border-b"
              style={{ borderColor: "var(--border)" }}>
              <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                ファイル一覧 ({audioFiles.length})
              </span>
            </div>
            <div className="divide-y max-h-56 overflow-y-auto" style={{ borderColor: "var(--border)" }}>
              {audioFiles.map(af => {
                const s = STATUS_STYLE[af.status] ?? STATUS_STYLE.pending;
                return (
                  <div key={af.id} className="flex items-center gap-3 px-4 py-2 group">
                    <span className="text-xs px-2 py-0.5 rounded font-medium shrink-0"
                      style={{ background: s.bg, color: s.text }}>
                      {af.status === "processing" && <Loader2 size={10} className="inline animate-spin mr-1" />}
                      {s.label}
                    </span>
                    <span className="text-sm flex-1 truncate" style={{ color: "var(--text-primary)" }}>{af.name}</span>
                    <span className="text-xs font-mono shrink-0" style={{ color: "var(--text-muted)" }}>
                      {(af.size_bytes / 1024 / 1024).toFixed(1)} MB
                    </span>
                    {af.error && (
                      <span className="text-xs truncate max-w-40" style={{ color: "var(--danger)" }}
                        title={af.error}>{af.error}</span>
                    )}
                    <button
                      className="opacity-0 group-hover:opacity-100 p-1 rounded transition-opacity shrink-0"
                      style={{ color: "var(--text-muted)" }}
                      onMouseEnter={e => (e.currentTarget.style.color = "var(--danger)")}
                      onMouseLeave={e => (e.currentTarget.style.color = "var(--text-muted)")}
                      onClick={async () => {
                        if (!confirm(`"${af.name}" を削除しますか？関連するレコードも削除されます。`)) return;
                        await api.uploads.deleteFile(af.id);
                        await Promise.all([loadFiles(), loadProject()]);
                      }}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Export */}
        <div className="rounded-lg border" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
          <div className="px-4 py-2.5 border-b flex items-center gap-2"
            style={{ borderColor: "var(--border)" }}>
            <Download size={14} style={{ color: "var(--text-muted)" }} />
            <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>エクスポート</span>
          </div>
          <div className="px-4 py-3 flex gap-2 flex-wrap">
            {[
              { href: api.exports.trainUrl(id), label: "train.jsonl", count: stats?.train_count ?? 0, color: "var(--success)", bg: "var(--success-light)" },
              { href: api.exports.reviewUrl(id), label: "review.jsonl", count: stats?.review_count ?? 0, color: "var(--warning)", bg: "var(--warning-light)" },
              { href: api.exports.zipUrl(id), label: "dataset.zip", count: null, color: "var(--text-secondary)", bg: "var(--bg)" },
            ].map(e => (
              <a key={e.label} href={e.href} download
                className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium border transition-opacity hover:opacity-80"
                style={{ color: e.color, background: e.bg, borderColor: "var(--border)" }}>
                {e.label}
                {e.count !== null && (
                  <span className="text-xs font-mono" style={{ opacity: 0.7 }}>{e.count}件</span>
                )}
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

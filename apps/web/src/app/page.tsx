"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Project } from "@/lib/api";
import { Plus, Trash2, ChevronRight, Database, FileAudio } from "lucide-react";

export default function Home() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [lang, setLang] = useState("ja");

  const load = () => api.projects.list().then(setProjects).catch(console.error);
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!name.trim()) return;
    await api.projects.create({ name: name.trim(), language: lang });
    setName(""); setCreating(false); load();
  };

  const remove = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    if (!confirm("プロジェクトを削除しますか？")) return;
    await api.projects.delete(id); load();
  };

  return (
    <div className="min-h-screen" style={{ background: "var(--bg)" }}>
      {/* Top bar */}
      <header style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)" }}
        className="sticky top-0 z-10">
        <div className="px-6 h-12 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database size={16} style={{ color: "var(--accent)" }} />
            <span className="font-semibold text-sm" style={{ color: "var(--text-primary)" }}>Teacher Data</span>
          </div>
          <button onClick={() => setCreating(true)}
            className="flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-md transition-colors hover:opacity-90"
            style={{ background: "#2563eb", color: "#fff" }}>
            <Plus size={14} /> 新規プロジェクト
          </button>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* Create form */}
        {creating && (
          <div className="mb-6 rounded-lg border p-4"
            style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
            <p className="text-xs font-medium mb-3" style={{ color: "var(--text-secondary)" }}>新規プロジェクト</p>
            <div className="flex gap-2">
              <input autoFocus value={name} onChange={e => setName(e.target.value)}
                onKeyDown={e => e.key === "Enter" && create()}
                placeholder="プロジェクト名"
                className="flex-1 px-3 py-1.5 text-sm rounded-md border outline-none"
                style={{ borderColor: "var(--border-strong)", background: "var(--surface)" }}
                onFocus={e => (e.target.style.borderColor = "var(--accent)")}
                onBlur={e => (e.target.style.borderColor = "var(--border-strong)")} />
              <select value={lang} onChange={e => setLang(e.target.value)}
                className="px-3 py-1.5 text-sm rounded-md border"
                style={{ borderColor: "var(--border-strong)", background: "var(--surface)" }}>
                <option value="ja">日本語</option>
                <option value="en">English</option>
                <option value="zh">中文</option>
              </select>
              <button onClick={create}
                className="px-3 py-1.5 text-sm font-medium rounded-md hover:opacity-90"
                style={{ background: "#2563eb", color: "#fff" }}>作成</button>
              <button onClick={() => setCreating(false)}
                className="px-3 py-1.5 text-sm rounded-md"
                style={{ color: "var(--text-secondary)", background: "var(--bg)", border: "1px solid var(--border)" }}>
                キャンセル</button>
            </div>
          </div>
        )}

        {/* Project table */}
        <div className="rounded-lg border overflow-hidden"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
          {/* Table header */}
          <div className="grid text-xs font-medium px-4 py-2.5 border-b"
            style={{ gridTemplateColumns: "1fr 60px 80px 80px 90px 80px 80px", color: "var(--text-muted)", borderColor: "var(--border)" }}>
            <span>プロジェクト名</span>
            <span className="text-center">言語</span>
            <span className="text-right">音声</span>
            <span className="text-right" style={{ color: "var(--success)" }}>train</span>
            <span className="text-right" style={{ color: "var(--warning)" }}>review</span>
            <span className="text-right">類似度</span>
            <span></span>
          </div>

          {projects.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3"
              style={{ color: "var(--text-muted)" }}>
              <FileAudio size={32} strokeWidth={1} />
              <p className="text-sm">プロジェクトがありません</p>
            </div>
          ) : projects.map((p, i) => (
            <Link key={p.id} href={`/projects/${p.id}`}
              className="grid items-center px-4 py-3 border-b transition-colors group"
              style={{
                gridTemplateColumns: "1fr 60px 80px 80px 90px 80px 80px",
                borderColor: i === projects.length - 1 ? "transparent" : "var(--border)",
              }}
              onMouseEnter={e => (e.currentTarget.style.background = "var(--bg)")}
              onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
              <div className="flex items-center gap-2">
                <ChevronRight size={14} style={{ color: "var(--text-muted)" }} />
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>{p.name}</span>
              </div>
              <span className="text-center text-xs rounded px-1.5 py-0.5 font-mono"
                style={{ background: "var(--bg)", color: "var(--text-secondary)" }}>{p.language}</span>
              <span className="text-right text-sm" style={{ color: "var(--text-secondary)" }}>
                {p.stats?.total_audio_files ?? 0}
              </span>
              <span className="text-right text-sm font-medium" style={{ color: "var(--success)" }}>
                {p.stats?.train_count ?? 0}
              </span>
              <span className="text-right text-sm font-medium"
                style={{ color: (p.stats?.review_count ?? 0) > 0 ? "var(--warning)" : "var(--text-muted)" }}>
                {p.stats?.review_count ?? 0}
              </span>
              <span className="text-right text-sm font-mono" style={{ color: "var(--text-secondary)" }}>
                {p.stats?.avg_similarity.toFixed(2) ?? "—"}
              </span>
              <div className="flex justify-end">
                <button onClick={e => remove(e, p.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded transition-opacity"
                  style={{ color: "var(--text-muted)" }}
                  onMouseEnter={e => (e.currentTarget.style.color = "var(--danger)")}
                  onMouseLeave={e => (e.currentTarget.style.color = "var(--text-muted)")}>
                  <Trash2 size={14} />
                </button>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

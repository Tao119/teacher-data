"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api, Record } from "@/lib/api";
import { CheckCircle2, XCircle, RotateCcw, ChevronLeft, ChevronRight, Save, Database, ChevronLeftIcon } from "lucide-react";

function diffChars(a: string, b: string): { text: string; type: "same" | "add" | "del" }[] {
  if (a === b) return [{ text: a, type: "same" }];
  const res: { text: string; type: "same" | "add" | "del" }[] = [];
  let i = 0;
  const max = Math.max(a.length, b.length);
  while (i < max) {
    if (a[i] === b[i]) {
      let j = i;
      while (j < max && a[j] === b[j]) j++;
      res.push({ text: a.slice(i, j), type: "same" });
      i = j;
    } else {
      let j = i;
      while (j < max && a[j] !== b[j]) j++;
      if (i < a.length) res.push({ text: a.slice(i, j), type: "del" });
      if (i < b.length) res.push({ text: b.slice(i, j), type: "add" });
      i = j;
    }
  }
  return res;
}

function DiffText({ base, target }: { base: string; target: string }) {
  const parts = diffChars(base, target);
  return (
    <p className="text-sm leading-relaxed whitespace-pre-wrap" style={{ fontFamily: "var(--font-mono, monospace)" }}>
      {parts.map((p, i) =>
        p.type === "same" ? <span key={i} style={{ color: "var(--text-primary)" }}>{p.text}</span> :
        p.type === "add" ? <mark key={i} style={{ background: "#bbf7d0", color: "#15803d", borderRadius: 2 }}>{p.text}</mark> :
        <del key={i} style={{ background: "#fee2e2", color: "#b91c1c", borderRadius: 2, textDecoration: "line-through" }}>{p.text}</del>
      )}
    </p>
  );
}

const STRATEGY_COLOR: Record<string, string> = {
  agree: "var(--success)", fallback: "var(--warning)", prefer: "var(--accent)", diverged: "var(--danger)"
};

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const [records, setRecords] = useState<Record[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Record | null>(null);
  const [editText, setEditText] = useState("");
  const [saving, setSaving] = useState(false);
  const [filter, setFilter] = useState<"review" | "all">(
    searchParams.get("filter") === "all" ? "all" : "review"
  );
  const audioRef = useRef<HTMLAudioElement>(null);

  const load = useCallback(async () => {
    const res = await api.records.list(id, filter === "review" ? "review" : undefined, page);
    setRecords(res.items);
    setTotal(res.total);
  }, [id, page, filter]);

  useEffect(() => { load(); }, [load]);

  const select = (r: Record) => {
    setSelected(r); setEditText(r.text);
    if (audioRef.current) audioRef.current.src = api.records.audioUrl(r.id);
  };
  useEffect(() => { if (records.length > 0 && !selected) select(records[0]); }, [records]);

  const save = async () => {
    if (!selected || editText === selected.text) return;
    setSaving(true);
    const updated = await api.records.update(selected.id, editText);
    setSaving(false);
    setSelected(updated);
    setRecords(prev => prev.map(r => r.id === updated.id ? updated : r));
  };

  const approve = async () => {
    if (!selected) return;
    if (editText !== selected.text) await save();
    const updated = await api.records.approve(selected.id);
    const remaining = records.filter(r => r.id !== updated.id);
    if (filter === "review") {
      setRecords(remaining);
      if (remaining.length > 0) select(remaining[0]); else setSelected(null);
    } else {
      setRecords(prev => prev.map(r => r.id === updated.id ? updated : r));
    }
  };

  const reject = async () => {
    if (!selected) return;
    if (editText !== selected.text) await save();
    const updated = await api.records.reject(selected.id);
    setRecords(prev => prev.map(r => r.id === updated.id ? updated : r));
    const idx = records.findIndex(r => r.id === selected.id);
    const next = records[idx + 1] ?? records[idx - 1];
    if (next) select(next);
  };

  const reset = async () => {
    if (!selected) return;
    const updated = await api.records.reset(selected.id);
    setSelected(updated); setEditText(updated.text);
    setRecords(prev => prev.map(r => r.id === updated.id ? updated : r));
  };

  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") { e.preventDefault(); approve(); }
      if ((e.metaKey || e.ctrlKey) && e.key === "s") { e.preventDefault(); save(); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [selected, editText]);

  return (
    <div className="h-screen flex flex-col" style={{ background: "var(--bg)" }}>
      {/* Header */}
      <header style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)" }} className="shrink-0">
        <div className="px-4 h-12 flex items-center gap-2 min-w-0">
          <Database size={16} className="shrink-0" style={{ color: "var(--accent)" }} />
          <Link href="/" className="text-sm font-semibold shrink-0" style={{ color: "var(--text-primary)" }}>Teacher Data</Link>
          <span className="shrink-0" style={{ color: "var(--text-muted)" }}>/</span>
          <Link href={`/projects/${id}`} className="text-sm shrink-0" style={{ color: "var(--text-secondary)" }}>プロジェクト</Link>
          <span className="shrink-0" style={{ color: "var(--text-muted)" }}>/</span>
          <span className="text-sm shrink-0" style={{ color: "var(--text-secondary)" }}>レビュー</span>

          <div className="shrink-0 flex items-center gap-1 ml-4 rounded-md overflow-hidden border"
            style={{ borderColor: "var(--border)" }}>
            {(["review", "all"] as const).map(f => (
              <button key={f} onClick={() => { setFilter(f); setPage(1); setSelected(null); }}
                className="px-3 py-1 text-xs font-medium transition-colors whitespace-nowrap"
                style={{
                  background: filter === f ? "var(--accent)" : "transparent",
                  color: filter === f ? "#fff" : "var(--text-secondary)",
                }}>
                {f === "review" ? `要レビュー (${total})` : "全件"}
              </button>
            ))}
          </div>

          <div className="ml-auto shrink-0 text-xs hidden md:block" style={{ color: "var(--text-muted)" }}>
            ⌘+Enter: train統合　⌘+S: 保存
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 shrink-0 border-r overflow-y-auto"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
          {records.map(r => {
            const isSelected = selected?.id === r.id;
            return (
              <button key={r.id} onClick={() => select(r)} className="w-full text-left px-3 py-2.5 border-b transition-colors"
                style={{
                  borderColor: "var(--border)",
                  background: isSelected ? "var(--accent-light)" : "transparent",
                  borderLeft: isSelected ? "2px solid var(--accent)" : "2px solid transparent",
                }}>
                <p className="text-xs mb-0.5 truncate" style={{ color: "var(--text-muted)" }}>{r.audio_file_name}</p>
                <p className="text-xs leading-relaxed line-clamp-2" style={{ color: "var(--text-primary)" }}>{r.text}</p>
                <div className="flex gap-2 mt-1.5 items-center">
                  <span className="text-xs font-medium"
                    style={{ color: STRATEGY_COLOR[r.strategy] ?? "var(--text-muted)" }}>{r.strategy}</span>
                  {r.strategy !== "fallback" && (
                    <div className="flex items-center gap-1 flex-1 min-w-0">
                      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "#e5e7eb" }}>
                        <div className="h-1.5 rounded-full" style={{
                          width: `${r.similarity * 100}%`,
                          background: r.similarity >= 0.95 ? "#16a34a" : r.similarity >= 0.80 ? "#d97706" : "#dc2626"
                        }} />
                      </div>
                      <span className="text-xs font-mono shrink-0" style={{
                        color: r.similarity >= 0.95 ? "#16a34a" : r.similarity >= 0.80 ? "#d97706" : "#dc2626"
                      }}>
                        {Math.round(r.similarity * 100)}%
                      </span>
                    </div>
                  )}
                  {r.bucket === "train" && (
                    <span className="text-xs ml-auto" style={{ color: "var(--success)" }}>✓</span>
                  )}
                </div>
              </button>
            );
          })}

          {total > 30 && (
            <div className="flex items-center justify-between px-3 py-2 border-t"
              style={{ borderColor: "var(--border)" }}>
              <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
                className="p-1 rounded disabled:opacity-30"
                style={{ color: "var(--text-secondary)" }}><ChevronLeft size={14} /></button>
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>{page} / {Math.ceil(total / 30)}</span>
              <button disabled={page >= Math.ceil(total / 30)} onClick={() => setPage(p => p + 1)}
                className="p-1 rounded disabled:opacity-30"
                style={{ color: "var(--text-secondary)" }}><ChevronRight size={14} /></button>
            </div>
          )}
        </aside>

        {/* Main panel */}
        <main className="flex-1 overflow-y-auto p-5" style={{ background: "var(--bg)" }}>
          {selected ? (
            <div className="max-w-2xl mx-auto space-y-4">
              {/* Audio */}
              <div className="rounded-lg border" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
                <div className="px-4 py-2.5 border-b flex items-center justify-between"
                  style={{ borderColor: "var(--border)" }}>
                  <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>
                    {selected.audio_file_name}
                  </span>
                  <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                    {selected.start_sec.toFixed(1)}s – {selected.end_sec.toFixed(1)}s
                  </span>
                </div>
                <div className="px-4 py-3">
                  <audio ref={audioRef} controls className="w-full h-8"
                    src={api.records.audioUrl(selected.id)}
                    onLoadedMetadata={() => { if (audioRef.current) audioRef.current.currentTime = selected.start_sec; }} />
                </div>
              </div>

              {/* Diff */}
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: "Whisper", base: selected.whisper_text, target: selected.gemini_text, color: "#2563eb" },
                  { label: "Gemini", base: selected.gemini_text, target: selected.whisper_text, color: "#7c3aed" },
                ].map(col => (
                  <div key={col.label} className="rounded-lg border"
                    style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
                    <div className="px-3 py-2 border-b"
                      style={{ borderColor: "var(--border)" }}>
                      <span className="text-xs font-semibold tracking-wide" style={{ color: col.color }}>{col.label}</span>
                    </div>
                    <div className="px-3 py-2.5">
                      <DiffText base={col.base} target={col.target} />
                    </div>
                  </div>
                ))}
              </div>

              {/* Editor */}
              <div className="rounded-lg border" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
                <div className="px-4 py-2.5 border-b flex items-center justify-between"
                  style={{ borderColor: "var(--border)" }}>
                  <span className="text-xs font-medium" style={{ color: "var(--text-secondary)" }}>採用テキスト</span>
                  <div className="flex items-center gap-3 text-xs" style={{ color: "var(--text-muted)" }}>
                    <span className="font-medium" style={{ color: STRATEGY_COLOR[selected.strategy] ?? "var(--text-muted)" }}>
                      {selected.strategy}
                    </span>
                    {selected.strategy === "fallback" ? (
                      <span>片方のみ</span>
                    ) : (
                      <div className="flex items-center gap-1.5">
                        <div className="w-24 h-1.5 rounded-full overflow-hidden" style={{ background: "#e5e7eb" }}>
                          <div className="h-1.5 rounded-full transition-all" style={{
                            width: `${selected.similarity * 100}%`,
                            background: selected.similarity >= 0.95 ? "#16a34a" : selected.similarity >= 0.80 ? "#d97706" : "#dc2626"
                          }} />
                        </div>
                        <span className="font-mono font-medium" style={{
                          color: selected.similarity >= 0.95 ? "#16a34a" : selected.similarity >= 0.80 ? "#d97706" : "#dc2626"
                        }}>
                          {Math.round(selected.similarity * 100)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                <div className="p-3">
                  <textarea value={editText} onChange={e => setEditText(e.target.value)} rows={5}
                    className="w-full text-sm resize-none outline-none rounded border px-3 py-2"
                    style={{
                      fontFamily: "monospace",
                      borderColor: "var(--border-strong)",
                      background: "var(--bg)",
                      color: "var(--text-primary)",
                    }}
                    onFocus={e => (e.target.style.borderColor = "var(--accent)")}
                    onBlur={e => (e.target.style.borderColor = "var(--border-strong)")} />
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <button onClick={approve}
                  className="flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition-opacity hover:opacity-90"
                  style={{ background: "var(--success)", color: "#fff" }}>
                  <CheckCircle2 size={15} /> OK → train
                </button>
                <button onClick={reject}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-md text-sm transition-colors border"
                  style={{ color: "var(--text-secondary)", borderColor: "var(--border)", background: "var(--surface)" }}>
                  <XCircle size={14} /> スキップ
                </button>
                <button onClick={reset} title="原文に戻す"
                  className="px-3 py-2 rounded-md border transition-colors"
                  style={{ color: "var(--text-muted)", borderColor: "var(--border)", background: "var(--surface)" }}>
                  <RotateCcw size={14} />
                </button>
                <button onClick={save} disabled={saving || editText === selected.text}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-md text-sm font-medium border transition-colors disabled:opacity-40"
                  style={{ color: "var(--accent)", borderColor: "var(--accent)", background: "var(--accent-light)" }}>
                  <Save size={14} /> 保存
                </button>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center gap-3"
              style={{ color: "var(--text-muted)" }}>
              <CheckCircle2 size={36} strokeWidth={1} />
              <p className="text-sm">
                {filter === "review" ? "要レビューのレコードはありません" : "レコードがありません"}
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

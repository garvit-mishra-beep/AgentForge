"use client";

import React, { useState, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";

const EXAMPLES: { label: string; code: string }[] = [
  {
    label: "JWT middleware",
    code: `import jwt
from functools import wraps

SECRET = "my-dev-secret"
USERS_DB = {"admin": "password123"}

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        user = USERS_DB.get(payload["sub"])
        return f(user, *args, **kwargs)
    return wrapper`,
  },
  {
    label: "REST endpoint",
    code: `@app.get("/api/search")
def search(q: str, page: int = 1):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM items WHERE name LIKE '%{q}%'")
    results = cursor.fetchall()
    return {"results": results, "page": page}`,
  },
  {
    label: "React component",
    code: `function DataGrid({ columns, dataUrl }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(dataUrl).then(r => r.json()).then(setRows);
  });

  return loading ? <Spinner /> : (
    <table>
      <thead><tr>{columns.map(c => <th key={c.key}>{c.label}</th>)}</tr></thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>{columns.map(c => <td>{row[c.key]}</td>)}</tr>
        ))}
      </tbody>
    </table>
  );
}`,
  },
];

interface QuickReviewTextareaProps {
  onReview: (code: string) => void;
  busy: boolean;
}

export function QuickReviewTextarea({ onReview, busy }: QuickReviewTextareaProps) {
  const [code, setCode] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleExample = useCallback((code: string) => {
    setCode(code);
    textareaRef.current?.focus();
  }, []);

  const handleSubmit = useCallback(() => {
    if (!code.trim() || busy) return;
    onReview(code.trim());
  }, [code, busy, onReview]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  return (
    <div className="w-full space-y-4">
      <textarea
        ref={textareaRef}
        value={code}
        onChange={(e) => setCode(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Paste your AI-generated code here..."
        rows={8}
        className="w-full rounded-xl border border-border bg-surface px-4 py-3 font-mono text-sm text-foreground transition-colors placeholder:text-muted-foreground/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary resize-y min-h-[160px]"
      />

      <div className="flex items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1.5">
          <span className="text-[11px] text-muted-foreground self-center mr-1">
            Examples:
          </span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex.label}
              type="button"
              onClick={() => handleExample(ex.code)}
              className="rounded-md border border-border px-2.5 py-1 text-[11px] text-muted-foreground hover:text-foreground hover:border-border-hover transition-colors cursor-pointer"
            >
              {ex.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-muted-foreground hidden sm:inline">
            Ctrl+Enter to submit
          </span>
          <Button
            size="lg"
            onClick={handleSubmit}
            disabled={!code.trim() || busy}
            className="shrink-0"
          >
            {busy ? "Reviewing..." : "Review My Code"}
          </Button>
        </div>
      </div>
    </div>
  );
}

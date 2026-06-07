import { useState } from "react"

export default function IngestForm({ onIngest, loading, error }) {
  const [ytUrl, setYtUrl]   = useState("")
  const [igUrl, setIgUrl]   = useState("")

  const handleSubmit = () => {
    if (!ytUrl.trim() || !igUrl.trim()) return
    onIngest(ytUrl.trim(), igUrl.trim())
  }

  return (
    <div style={{
      padding: "1.25rem 2rem",
      background: "var(--surface)",
      borderBottom: "1px solid var(--border)",
      display: "flex", gap: "0.75rem", alignItems: "flex-start",
      flexWrap: "wrap",
    }}>
      <input
        value={ytUrl}
        onChange={e => setYtUrl(e.target.value)}
        placeholder="YouTube URL (Video A)"
        style={inputStyle("#7c6af7")}
      />
      <input
        value={igUrl}
        onChange={e => setIgUrl(e.target.value)}
        placeholder="Instagram Reel URL (Video B)"
        style={inputStyle("#f7716a")}
      />
      <button
        onClick={handleSubmit}
        disabled={loading || !ytUrl || !igUrl}
        style={{
          padding: "0.65rem 1.5rem",
          background: loading
            ? "var(--border)"
            : "linear-gradient(135deg, var(--accent), var(--accent2))",
          border: "none", borderRadius: 8,
          color: "#fff", fontFamily: "'Syne', sans-serif",
          fontWeight: 700, fontSize: "0.85rem",
          cursor: loading ? "not-allowed" : "pointer",
          letterSpacing: "0.05em", whiteSpace: "nowrap",
          transition: "opacity 0.2s",
        }}
      >
        {loading ? "⏳ Analyzing..." : "⚡ Analyze Videos"}
      </button>

      {error && (
        <div style={{
          width: "100%", padding: "0.5rem 1rem",
          background: "#3d1515", border: "1px solid var(--accent2)",
          borderRadius: 6, color: "var(--accent2)", fontSize: "0.8rem",
        }}>❌ {error}
        </div>
      )}
    </div>
  )
}

const inputStyle = (accentColor) => ({
  flex: 1, minWidth: 240,
  padding: "0.65rem 1rem",
  background: "var(--card-bg)",
  border: `1px solid var(--border)`,
  borderRadius: 8, color: "var(--text)",
  fontFamily: "'DM Mono', monospace",
  fontSize: "0.8rem", outline: "none",
  transition: "border-color 0.2s",
  onFocus: { borderColor: accentColor },
})
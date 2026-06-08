import { useState } from "react"
import VideoCard from "./components/VideoCard"
import ChatPanel from "./components/ChatPanel"
import IngestForm from "./components/IngestForm"
import "./index.css"
const API = import.meta.env.VITE_API_URL

export default function App() {
  const [videoData, setVideoData] = useState(null)
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState("")
  const [threadId]                = useState(() => `thread-${Date.now()}`)

  const handleIngest = async (youtubeUrl, instagramUrl) => {
    setLoading(true)
    setError("")
    setVideoData(null)
    try {
      const res = await fetch(`${API}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          youtube_url: youtubeUrl,
          instagram_url: instagramUrl,
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || "Ingest failed")
      }
      const data = await res.json()
      setVideoData(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <header style={{
        padding: "1.5rem 2rem",
        borderBottom: "1px solid var(--border)",
        display: "flex",
        alignItems: "center",
        gap: "1rem",
        background: "var(--surface)",
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: 8,
          background: "linear-gradient(135deg, var(--accent), var(--accent2))",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 18,
        }}>⚡</div>
        <div>
          <h1 style={{
            fontFamily: "'Syne', sans-serif",
            fontWeight: 800, fontSize: "1.3rem",
            background: "linear-gradient(90deg, var(--accent), var(--accent2))",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          }}>VideoRAG</h1>
          <p style={{ fontSize: "0.7rem", color: "var(--muted)", letterSpacing: "0.1em" }}>
            AI-POWERED VIDEO ANALYTICS
          </p>
        </div>
      </header>

      {/* Ingest Form */}
      <IngestForm onIngest={handleIngest} loading={loading} error={error} />

      {/* Main Content */}
      {videoData && (
        <div style={{
          flex: 1, display: "grid",
          gridTemplateColumns: "1fr 1fr 420px",
          gap: "1px",
          background: "var(--border)",
          minHeight: "calc(100vh - 200px)",
        }}>
          <VideoCard
            label="A"
            data={videoData.video_a}
            source="youtube"
          />
          <VideoCard
            label="B"
            data={videoData.video_b}
            source="instagram"
          />
          <ChatPanel threadId={threadId} />
        </div>
      )}

      {/* Empty state */}
      {!videoData && !loading && (
        <div style={{
          flex: 1, display: "flex", alignItems: "center",
          justifyContent: "center", flexDirection: "column", gap: "1rem",
          color: "var(--muted)",
        }}>
          <div style={{ fontSize: "3rem" }}>🎬</div>
          <p style={{ fontFamily: "'Syne', sans-serif", fontSize: "1.1rem" }}>
            Paste two video URLs above to begin
          </p>
        </div>
      )}
    </div>
  )
}
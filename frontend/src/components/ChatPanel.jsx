import { useState, useRef, useEffect } from "react"

export default function ChatPanel({ threadId }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hey! I've analyzed both videos. Ask me anything — engagement rates, hook comparisons, improvement suggestions.",
      sources: [],
    }
  ])
  const [input, setInput]     = useState("")
  const [streaming, setStreaming] = useState(false)
  const bottomRef             = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || streaming) return

    const query = input.trim()
    setInput("")
    setMessages(prev => [...prev, { role: "user", content: query, sources: [] }])
    setStreaming(true)

    // Add empty assistant message to stream into
    setMessages(prev => [...prev, { role: "assistant", content: "", sources: [] }])

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, thread_id: threadId }),
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() // keep incomplete line

        for (const line of lines) {
          if (line.startsWith("data:")) {
            const raw = line.slice(5).trim()
            if (!raw) continue
            try {
              const parsed = JSON.parse(raw)

              if (parsed.token !== undefined) {
                // Stream token into last message
                setMessages(prev => {
                  const updated = [...prev]
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    content: updated[updated.length - 1].content + parsed.token,
                  }
                  return updated
                })
              }

              if (parsed.sources !== undefined) {
                // Attach sources to last message
                setMessages(prev => {
                  const updated = [...prev]
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    sources: parsed.sources,
                  }
                  return updated
                })
              }

            } catch (_) { /* skip malformed lines */ }
          }
        }
      }
    } catch (e) {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1].content = `Error: ${e.message}`
        return updated
      })
    } finally {
      setStreaming(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const SUGGESTED = [
    "What's the engagement rate of each video?",
    "Why did one video outperform the other?",
    "Compare the hooks in the first 5 seconds",
    "Suggest improvements for Video B",
  ]

  return (
    <div style={{
      background: "var(--surface)",
      display: "flex", flexDirection: "column",
      height: "100%",
    }}>
      {/* Chat header */}
      <div style={{
        padding: "0.75rem 1rem",
        borderBottom: "1px solid var(--border)",
        fontFamily: "'Syne', sans-serif",
        fontWeight: 700, fontSize: "0.8rem",
        letterSpacing: "0.05em",
        display: "flex", alignItems: "center", gap: "0.5rem",
      }}>
        <span style={{
          width: 8, height: 8, borderRadius: "50%",
          background: "var(--success)",
          boxShadow: "0 0 6px var(--success)",
        }} />
        RAG CHAT
      </div>

      {/* Messages */}
      <div style={{
        flex: 1, overflowY: "auto",
        padding: "1rem", display: "flex",
        flexDirection: "column", gap: "1rem",
      }}>
        {messages.map((msg, i) => (
          <div key={i}>
            <div style={{
              display: "flex",
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
            }}>
              <div style={{
                maxWidth: "88%",
                padding: "0.65rem 0.9rem",
                borderRadius: msg.role === "user"
                  ? "12px 12px 2px 12px"
                  : "12px 12px 12px 2px",
                background: msg.role === "user"
                  ? "linear-gradient(135deg, var(--accent), #5a4fd1)"
                  : "var(--card-bg)",
                border: msg.role === "assistant"
                  ? "1px solid var(--border)" : "none",
                fontSize: "0.78rem", lineHeight: 1.6,
                whiteSpace: "pre-wrap",
              }}>
                {msg.content}
                {msg.role === "assistant" && streaming && i === messages.length - 1 && (
                  <span style={{
                    display: "inline-block", width: 6, height: 14,
                    background: "var(--accent)", marginLeft: 2,
                    animation: "blink 1s step-end infinite",
                    verticalAlign: "middle",
                  }} />
                )}
              </div>
            </div>

            {/* Sources */}
            {msg.sources?.length > 0 && (
              <div style={{
                marginTop: "0.4rem", display: "flex",
                flexWrap: "wrap", gap: "0.3rem",
              }}>
                {msg.sources.map((s, j) => (
                  <span key={j} style={{
                    fontSize: "0.6rem", padding: "2px 6px",
                    background: s.video_id === "A"
                      ? "rgba(124,106,247,0.15)"
                      : "rgba(247,113,106,0.15)",
                    border: `1px solid ${s.video_id === "A" ? "var(--accent)" : "var(--accent2)"}`,
                    borderRadius: 4,
                    color: s.video_id === "A" ? "var(--accent)" : "var(--accent2)",
                  }}>
                    Video {s.video_id} · Chunk {s.chunk_index} · {s.score}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}

        {/* Suggested questions — show only at start */}
        {messages.length === 1 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {SUGGESTED.map(q => (
              <button key={q} onClick={() => setInput(q)} style={{
                textAlign: "left", padding: "0.5rem 0.75rem",
                background: "var(--card-bg)",
                border: "1px solid var(--border)",
                borderRadius: 6, color: "var(--muted)",
                fontSize: "0.7rem", cursor: "pointer",
                fontFamily: "'DM Mono', monospace",
                transition: "border-color 0.2s, color 0.2s",
              }}>
                → {q}
              </button>
            ))}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{
        padding: "0.75rem",
        borderTop: "1px solid var(--border)",
        display: "flex", gap: "0.5rem",
      }}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask about the videos... (Enter to send)"
          rows={2}
          style={{
            flex: 1, background: "var(--card-bg)",
            border: "1px solid var(--border)",
            borderRadius: 8, color: "var(--text)",
            padding: "0.6rem 0.8rem",
            fontFamily: "'DM Mono', monospace",
            fontSize: "0.75rem", resize: "none",
            outline: "none", lineHeight: 1.5,
          }}
        />
        <button
          onClick={sendMessage}
          disabled={streaming || !input.trim()}
          style={{
            padding: "0 1rem",
            background: streaming
              ? "var(--border)"
              : "linear-gradient(135deg, var(--accent), var(--accent2))",
            border: "none", borderRadius: 8,
            color: "#fff", cursor: streaming ? "not-allowed" : "pointer",
            fontFamily: "'Syne', sans-serif",
            fontWeight: 700, fontSize: "1.1rem",
          }}
        >
          {streaming ? "..." : "↑"}
        </button>
      </div>

      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </div>
  )
}
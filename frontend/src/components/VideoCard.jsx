const fmt = (n) => {
  if (n === "unavailable" || n === undefined || n === null) return "N/A"
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M"
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K"
  return n.toString()
}

export default function VideoCard({ label, data, source }) {
  const meta = data?.metadata || {}
  const isYT = source === "youtube"

  const embedUrl = isYT
    ? `https://www.youtube.com/embed/${data?.yt_video_id || ""}`
    : null

  const labelColor = label === "A" ? "#7c6af7" : "#f7716a"

  return (
    <div style={{
      background: "var(--card-bg)",
      display: "flex", flexDirection: "column",
      overflow: "hidden",
    }}>
      {/* Label bar */}
      <div style={{
        padding: "0.75rem 1rem",
        borderBottom: "1px solid var(--border)",
        display: "flex", alignItems: "center", gap: "0.5rem",
      }}>
        <span style={{
          background: labelColor, color: "#fff",
          fontFamily: "'Syne', sans-serif", fontWeight: 800,
          fontSize: "0.7rem", padding: "2px 8px", borderRadius: 4,
          letterSpacing: "0.1em",
        }}>VIDEO {label}</span>
        <span style={{ fontSize: "0.7rem", color: "var(--muted)" }}>
          {isYT ? "▶ YouTube" : "📸 Instagram"}
        </span>
        <span style={{
          marginLeft: "auto", fontSize: "0.7rem",
          color: "var(--success)", fontWeight: 600,
        }}>
          {meta.engagement_rate?.toFixed(2)}% engagement
        </span>
      </div>

      {/* Video embed or thumbnail */}
      <div style={{ position: "relative", paddingTop: "56.25%", background: "#000" }}>
        {isYT && data?.yt_video_id ? (
          <iframe
            src={embedUrl}
            style={{
              position: "absolute", top: 0, left: 0,
              width: "100%", height: "100%", border: "none",
            }}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope"
            allowFullScreen
          />
        ) : (
          <div style={{
            position: "absolute", top: 0, left: 0,
            width: "100%", height: "100%",
            background: "var(--surface)",
            display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center",
            gap: "0.5rem",
          }}>
            {meta.thumbnail ? (
              <img
                src={meta.thumbnail}
                alt="thumbnail"
                crossOrigin="anonymous"
                onError={(e) => {
                    e.target.style.display = "none"
                    e.target.nextSibling.style.display = "flex"
                }}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
             />
            ) : null} 
            <div style={{
              display: meta.thumbnail ? "none" : "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.5rem",
            }}>
              <span style={{ fontSize: "3rem" }}>📸</span>
              <span style={{ fontSize: "0.7rem", color: "var(--muted)" }}>
                Instagram
              </span>
            </div>
            <a
              href={data?.url}
              target="_blank"
              rel="noreferrer"
              style={{
                position: "absolute", bottom: 8,
                background: "rgba(0,0,0,0.7)",
                color: labelColor, fontSize: "0.7rem",
                padding: "4px 10px", borderRadius: 4,
                textDecoration: "none", fontWeight: 600,
              }}
            >
              Open Video ↗
            </a>
          </div>
        )}
      </div>

      {/* Metadata grid */}
      <div style={{ padding: "1rem", flex: 1, overflowY: "auto" }}>
        <p style={{
          fontFamily: "'Syne', sans-serif", fontWeight: 700,
          fontSize: "0.9rem", marginBottom: "0.75rem",
          lineHeight: 1.3,
        }}>{meta.title || "Untitled"}</p>

        <p style={{ fontSize: "0.75rem", color: "var(--muted)", marginBottom: "1rem" }}>
          by {meta.creator || "Unknown"}
        </p>

        {/* Stats row */}
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(3, 1fr)",
          gap: "0.5rem", marginBottom: "1rem",
        }}>
          {[
            { label: "Views", value: fmt(meta.views) },
            { label: "Likes", value: fmt(meta.likes) },
            { label: "Comments", value: fmt(meta.comments) },
          ].map(stat => (
            <div key={stat.label} style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 6, padding: "0.5rem",
              textAlign: "center",
            }}>
              <div style={{
                fontFamily: "'Syne', sans-serif",
                fontWeight: 700, fontSize: "1rem",
                color: labelColor,
              }}>{stat.value}</div>
              <div style={{ fontSize: "0.65rem", color: "var(--muted)" }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>

        {/* Engagement bar */}
        <div style={{ marginBottom: "1rem" }}>
          <div style={{
            display: "flex", justifyContent: "space-between",
            fontSize: "0.7rem", color: "var(--muted)", marginBottom: 4,
          }}>
            <span>Engagement Rate</span>
            <span style={{ color: "var(--success)" }}>
              {meta.engagement_rate?.toFixed(4)}%
            </span>
          </div>
          <div style={{
            height: 4, background: "var(--border)", borderRadius: 2,
          }}>
            <div style={{
              height: "100%",
              width: `${Math.min((meta.engagement_rate || 0) * 5, 100)}%`,
              background: `linear-gradient(90deg, ${labelColor}, var(--success))`,
              borderRadius: 2, transition: "width 1s ease",
            }} />
          </div>
        </div>

        {/* Hashtags */}
        {meta.hashtags?.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem" }}>
            {meta.hashtags.slice(0, 8).map(tag => (
              <span key={tag} style={{
                fontSize: "0.65rem", padding: "2px 6px",
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: 4, color: "var(--muted)",
              }}>#{tag}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
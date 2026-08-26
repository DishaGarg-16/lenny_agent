import React from "react";
import { MessageSquare, Plus, Trash2, Sparkles } from "lucide-react";

export default function Sidebar({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  health,
}) {
  const isOnline = health?.status === "healthy" || health?.status === "degraded";

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <Sparkles size={18} style={{ color: "var(--accent)" }} />
        <span>Lenny Assistant</span>
      </div>

      <button className="btn-new-chat" onClick={onNewChat}>
        <Plus size={16} />
        <span>New Chat</span>
      </button>

      <div className="session-list-section">
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`session-item ${s.id === currentSessionId ? "active" : ""}`}
            onClick={() => onSelectSession(s.id)}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", overflow: "hidden" }}>
              <MessageSquare size={14} style={{ flexShrink: 0 }} />
              <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {s.title}
              </span>
            </div>
            <button
              style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
              title="Delete Chat"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteSession(s.id);
              }}
            >
              <Trash2 size={13} />
            </button>
          </div>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="status-dot" style={{ background: isOnline ? "#10b981" : "#f59e0b" }} />
        <span>{isOnline ? "Ollama Connected" : "Ollama Offline"}</span>
      </div>
    </aside>
  );
}

import React from "react";
import { Cpu, Layout, Moon, Sun } from "lucide-react";

export default function Header({
  sessionTitle,
  models,
  activeModel,
  onSelectModel,
  theme,
  onToggleTheme,
  hasActiveArtifact,
  isArtifactOpen,
  onToggleArtifact,
}) {
  const modelList = models.length > 0 ? models : [
    { id: "ollama/llama3.2", name: "Llama 3.2 (Local)", is_available: true },
    { id: "anthropic/claude-3-5-sonnet", name: "Claude 3.5 Sonnet (Cloud)", is_available: false }
  ];

  return (
    <header className="top-header">
      <div style={{ fontWeight: 600, fontSize: 14 }}>
        {sessionTitle || "The Lenny Growth Assistant"}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        {/* Model Selector Pill */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px", background: "var(--bg-card)", padding: "4px 10px", borderRadius: "999px", border: "1px solid var(--border)", fontSize: "12px" }}>
          <Cpu size={13} style={{ color: "var(--accent)" }} />
          <select
            value={activeModel}
            onChange={(e) => onSelectModel(e.target.value)}
            style={{ background: "transparent", border: "none", color: "inherit", outline: "none", cursor: "pointer", fontSize: "12px" }}
          >
            {modelList.map((m) => (
              <option key={m.id} value={m.id} style={{ background: "var(--bg-card)", color: "var(--text-main)" }}>
                {m.name} {m.is_available ? "" : "(Offline)"}
              </option>
            ))}
          </select>
        </div>

        {/* Artifact Toggle */}
        {hasActiveArtifact && (
          <button className="btn-open-artifact" onClick={onToggleArtifact} style={{ padding: "5px 10px", fontSize: "11px" }}>
            <Layout size={13} />
            <span>{isArtifactOpen ? "Hide Artifact" : "View Artifact"}</span>
          </button>
        )}

        {/* Theme Toggle */}
        <button className="btn-icon" onClick={onToggleTheme} title="Toggle Dark/Light Mode">
          {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
        </button>
      </div>
    </header>
  );
}

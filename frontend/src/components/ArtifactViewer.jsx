import React, { useState } from "react";
import { Copy, Check, Download, Maximize2, Minimize2, X, Eye, Code } from "lucide-react";
import { marked } from "marked";

export default function ArtifactViewer({ artifact, onClose }) {
  const [tab, setTab] = useState("preview");
  const [copied, setCopied] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);

  if (!artifact) return null;
  const isHtml = artifact.artifact_type === "html";

  const handleCopy = () => {
    navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const ext = isHtml ? "html" : "md";
    const blob = new Blob([artifact.content], { type: isHtml ? "text/html" : "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${artifact.title.toLowerCase().replace(/[^a-z0-9]/g, "_")}.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`artifact-drawer ${fullscreen ? "fullscreen" : ""}`} style={fullscreen ? { position: "fixed", inset: 0, width: "100vw", height: "100vh", zIndex: 60 } : {}}>
      <div className="artifact-header">
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ padding: "2px 6px", background: "var(--accent)", color: "white", borderRadius: "4px", fontSize: "10px", fontWeight: 700, textTransform: "uppercase" }}>
            {artifact.artifact_type}
          </span>
          <span style={{ fontWeight: 600, fontSize: "13px" }}>{artifact.title}</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <div style={{ display: "flex", background: "var(--bg-card)", borderRadius: "4px", padding: "2px", border: "1px solid var(--border)" }}>
            <button style={{ padding: "3px 8px", fontSize: "11px", border: "none", borderRadius: "3px", background: tab === "preview" ? "var(--accent)" : "transparent", color: tab === "preview" ? "white" : "var(--text-sub)", cursor: "pointer" }} onClick={() => setTab("preview")}>Preview</button>
            <button style={{ padding: "3px 8px", fontSize: "11px", border: "none", borderRadius: "3px", background: tab === "code" ? "var(--accent)" : "transparent", color: tab === "code" ? "white" : "var(--text-sub)", cursor: "pointer" }} onClick={() => setTab("code")}>Code</button>
          </div>

          <button className="btn-icon" onClick={handleCopy} title="Copy Code">
            {copied ? <Check size={13} style={{ color: "#10b981" }} /> : <Copy size={13} />}
          </button>
          <button className="btn-icon" onClick={handleDownload} title="Download File"><Download size={13} /></button>
          <button className="btn-icon" onClick={() => setFullscreen(!fullscreen)} title="Maximize View">{fullscreen ? <Minimize2 size={13} /> : <Maximize2 size={13} />}</button>
          <button className="btn-icon" onClick={onClose} title="Close"><X size={14} /></button>
        </div>
      </div>

      <div className="artifact-body">
        {tab === "preview" ? (
          isHtml ? (
            <iframe title="Artifact Preview" className="artifact-iframe" sandbox="allow-scripts" srcDoc={artifact.content} />
          ) : (
            <div className="artifact-markdown-view markdown-body" dangerouslySetInnerHTML={{ __html: marked.parse(artifact.content) }} />
          )
        ) : (
          <pre className="artifact-code-view"><code>{artifact.content}</code></pre>
        )}
      </div>
    </div>
  );
}

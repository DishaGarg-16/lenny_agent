import React from "react";
import { X, Award, Clock } from "lucide-react";

export default function CitationModal({ citation, onClose }) {
  if (!citation) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="citation-modal" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--accent)", fontWeight: 700, fontSize: "14px" }}>
            <Award size={16} />
            <span>{citation.guest}</span>
          </div>
          <button className="btn-icon" onClick={onClose}><X size={14} /></button>
        </div>

        <div style={{ background: "var(--bg-card)", padding: "14px", borderRadius: "8px", border: "1px solid var(--border)", fontSize: "13px", lineHeight: 1.6, color: "var(--text-sub)", fontStyle: "italic", marginBottom: "12px" }}>
          "{citation.snippet}"
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "12px", color: "var(--text-muted)" }}>
          <div>
            <div style={{ fontWeight: 600, color: "var(--text-main)" }}>{citation.episode_title}</div>
            <div style={{ display: "flex", alignItems: "center", gap: "4px", marginTop: "2px" }}><Clock size={11} /><span>Timestamp: {citation.timestamp_str}</span></div>
          </div>
          <div style={{ padding: "2px 6px", borderRadius: "4px", background: "rgba(99, 102, 241, 0.15)", color: "var(--accent)", fontWeight: 600, fontSize: "11px" }}>
            {Math.round(citation.similarity_score * 100)}% Match
          </div>
        </div>
      </div>
    </div>
  );
}

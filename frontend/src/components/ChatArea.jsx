import React, { useState, useRef, useEffect } from "react";
import { Send, Sparkles, BookOpen, Layers, Zap } from "lucide-react";
import { marked } from "marked";

const STARTERS = [
  { title: "Founder-Led PM", desc: "Brian Chesky on Figma prototypes & weekly reviews", prompt: "How does Brian Chesky run founder-led product reviews at Airbnb?" },
  { title: "B2B PLG Loops", desc: "Elena Verna's 3 non-obvious laws of monetization", prompt: "Explain Elena Verna's 3 non-obvious laws of B2B Product-Led Growth." },
  { title: "LNO Prioritization", desc: "Shreyas Doshi's framework for high-leverage work", prompt: "How should a Product Manager apply Shreyas Doshi's LNO framework?" },
  { title: "Ship 30 Essay", desc: "Generate a ~1,250-word digital essay with Casey Winters", prompt: "Write a Ship 30 for 30 essay on why compounding growth loops beat linear funnels.", skill: "ship30" }
];

export default function ChatArea({ messages, isLoading, onSendMessage, onOpenCitation, onOpenArtifact }) {
  const [input, setInput] = useState("");
  const [isShip30, setIsShip30] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim(), isShip30 ? "ship30" : "default");
    setInput("");
  };

  return (
    <div className="chat-pane">
      <div className="chat-messages-container">
        {messages.length === 0 ? (
          <div className="welcome-hero">
            <h1 style={{ fontSize: "24px", fontWeight: 700, marginBottom: "8px" }}>The Lenny Growth Assistant</h1>
            <p style={{ fontSize: "14px", color: "var(--text-sub)", lineHeight: 1.6 }}>
              Ask anything about Product Management, Growth Loops, or Strategy. Grounded in 200+ hours of podcast transcripts.
            </p>
            <div className="starter-grid">
              {STARTERS.map((s, i) => (
                <div key={i} className="starter-card" onClick={() => { if (s.skill) setIsShip30(true); onSendMessage(s.prompt, s.skill || "default"); }}>
                  <div className="starter-card-title"><Sparkles size={14} style={{ color: "var(--accent)" }} /><span>{s.title}</span></div>
                  <div className="starter-card-desc">{s.desc}</div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={m.id || i} className={`message-row ${m.role}`}>
              <div className="message-bubble">
                <div className="markdown-body" dangerouslySetInnerHTML={{ __html: marked.parse(m.content || "") }} />
                {m.artifact && (
                  <div className="artifact-action-card">
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <Layers size={16} style={{ color: "var(--accent)" }} />
                      <span style={{ fontWeight: 600, fontSize: "13px" }}>{m.artifact.title}</span>
                    </div>
                    <button className="btn-open-artifact" onClick={() => onOpenArtifact(m.artifact)}>View Artifact</button>
                  </div>
                )}
                {m.citations && m.citations.length > 0 && (
                  <div className="citations-bar">
                    <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-muted)", marginRight: "4px" }}>Sources:</span>
                    {m.citations.map((c, ci) => (
                      <button key={ci} className="citation-pill" onClick={() => onOpenCitation(c)}>
                        <BookOpen size={11} />
                        <span>{c.guest} ({c.timestamp_str})</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="message-row assistant">
            <div className="message-bubble" style={{ color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "6px" }}>
              <Zap size={14} style={{ color: "var(--accent)" }} />
              <span>Consulting Lenny's transcript knowledge base...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-wrapper">
        <form onSubmit={handleSubmit} className="input-pill-container">
          <textarea
            rows={1}
            className="chat-textarea"
            placeholder={isShip30 ? "Enter topic for 1,250-word Ship 30 essay..." : "Ask about product strategy, growth loops, pricing..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit(); } }}
          />
          <div className="input-controls">
            <button type="button" className={`skill-toggle-btn ${isShip30 ? "active" : ""}`} onClick={() => setIsShip30(!isShip30)}>
              <Sparkles size={11} />
              <span>Ship 30 Mode: {isShip30 ? "ON" : "OFF"}</span>
            </button>
            <button type="submit" className="btn-send" disabled={!input.trim() || isLoading}>
              <Send size={14} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

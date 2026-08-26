import React, { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import ChatArea from "./components/ChatArea";
import ArtifactViewer from "./components/ArtifactViewer";
import CitationModal from "./components/CitationModal";
import {
  fetchHealth, fetchModels, fetchSessions, fetchSessionDetail,
  createSession, deleteSession, sendChatMessage, generateShip30Essay
} from "./services/api";

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [currentTitle, setCurrentTitle] = useState("New Conversation");
  const [messages, setMessages] = useState([]);
  const [generatingSessionId, setGeneratingSessionId] = useState(null);

  const [models, setModels] = useState([]);
  const [activeModel, setActiveModel] = useState("ollama/llama3.2");
  const [health, setHealth] = useState(null);

  const [activeArtifact, setActiveArtifact] = useState(null);
  const [isArtifactOpen, setIsArtifactOpen] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState(null);
  const [theme, setTheme] = useState("dark");

  useEffect(() => { document.body.className = theme === "dark" ? "dark-theme" : "light-theme"; }, [theme]);

  useEffect(() => {
    const init = async () => {
      try {
        const [h, m, s] = await Promise.all([
          fetchHealth().catch(() => null),
          fetchModels().catch(() => ({ models: [], active_model: "ollama/llama3.2" })),
          fetchSessions().catch(() => [])
        ]);
        if (h) setHealth(h);
        if (m?.models) { setModels(m.models); setActiveModel(m.active_model); }
        if (s?.length > 0) { setSessions(s); handleSelectSession(s[0].id); }
      } catch (err) { console.error(err); }
    };
    init();
  }, []);

  const handleSelectSession = async (id) => {
    try {
      setCurrentSessionId(id);
      const detail = await fetchSessionDetail(id);
      setCurrentTitle(detail.title);
      setMessages(detail.messages || []);
      if (detail.artifacts?.length > 0) {
        setActiveArtifact(detail.artifacts[detail.artifacts.length - 1]);
        setIsArtifactOpen(true);
      } else {
        setIsArtifactOpen(false);
      }
    } catch (err) { console.error(err); }
  };

  const handleNewChat = async () => {
    try {
      const s = await createSession("New Conversation");
      setSessions((prev) => [s, ...prev]);
      setCurrentSessionId(s.id);
      setCurrentTitle(s.title);
      setMessages([]);
      setActiveArtifact(null);
      setIsArtifactOpen(false);
    } catch (err) { console.error(err); }
  };

  const handleDeleteSession = async (id) => {
    try {
      await deleteSession(id);
      const remaining = sessions.filter((s) => s.id !== id);
      setSessions(remaining);
      if (currentSessionId === id) {
        remaining.length > 0 ? handleSelectSession(remaining[0].id) : handleNewChat();
      }
    } catch (err) { console.error(err); }
  };

  const handleSendMessage = async (userText, skill = "default") => {
    const activeId = currentSessionId;
    const userMsg = { id: `u-${Date.now()}`, role: "user", content: userText, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setGeneratingSessionId(activeId || "pending");

    const formattedTitle = userText.slice(0, 32) + (userText.length > 32 ? "..." : "");
    if (currentTitle === "New Conversation") {
      setCurrentTitle(formattedTitle);
      setSessions((prev) => prev.map((s) => (s.id === currentSessionId ? { ...s, title: formattedTitle } : s)));
    }

    try {
      const res = skill === "ship30"
        ? await generateShip30Essay(currentSessionId, userText, null, activeModel)
        : await sendChatMessage(currentSessionId, userText, activeModel, skill);

      if (!currentSessionId && res.session_id) {
        setCurrentSessionId(res.session_id);
        setSessions((prev) => [{ id: res.session_id, title: formattedTitle }, ...prev]);
      }
      setMessages((prev) => [...prev, { id: res.message_id, role: "assistant", content: res.content, citations: res.citations || [], artifact: res.artifact || null }]);
      if (res.artifact) { setActiveArtifact(res.artifact); setIsArtifactOpen(true); }
    } catch (err) {
      setMessages((prev) => [...prev, { id: `err-${Date.now()}`, role: "assistant", content: `⚠️ Error: ${err.message}` }]);
    } finally {
      setGeneratingSessionId(null);
    }
  };

  return (
    <div className="app-layout">
      <Sidebar sessions={sessions} currentSessionId={currentSessionId} onSelectSession={handleSelectSession} onNewChat={handleNewChat} onDeleteSession={handleDeleteSession} health={health} />
      <div className="main-stage">
        <Header sessionTitle={currentTitle} models={models} activeModel={activeModel} onSelectModel={setActiveModel} theme={theme} onToggleTheme={() => setTheme(theme === "dark" ? "light" : "dark")} hasActiveArtifact={Boolean(activeArtifact)} isArtifactOpen={isArtifactOpen} onToggleArtifact={() => setIsArtifactOpen(!isArtifactOpen)} />
        <div className="split-workspace">
          <ChatArea
            messages={messages}
            isLoading={generatingSessionId !== null && (generatingSessionId === currentSessionId || generatingSessionId === "pending")}
            onSendMessage={handleSendMessage}
            onOpenCitation={setSelectedCitation}
            onOpenArtifact={(art) => { setActiveArtifact(art); setIsArtifactOpen(true); }}
          />
          {isArtifactOpen && activeArtifact && <ArtifactViewer artifact={activeArtifact} onClose={() => setIsArtifactOpen(false)} />}
        </div>
      </div>
      {selectedCitation && <CitationModal citation={selectedCitation} onClose={() => setSelectedCitation(null)} />}
    </div>
  );
}

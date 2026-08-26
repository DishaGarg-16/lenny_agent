const API_BASE = "";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function fetchModels() {
  const res = await fetch(`${API_BASE}/api/models`);
  if (!res.ok) throw new Error("Failed to fetch models");
  return res.json();
}

export async function fetchSessions() {
  const res = await fetch(`${API_BASE}/api/sessions`);
  if (!res.ok) throw new Error("Failed to fetch sessions");
  return res.json();
}

export async function fetchSessionDetail(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
  if (!res.ok) throw new Error("Failed to fetch session detail");
  return res.json();
}

export async function createSession(title = "New Conversation") {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function deleteSession(sessionId) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: "DELETE" });
  return res.ok;
}

export async function sendChatMessage(sessionId, message, modelOverride = null, skill = "default") {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message, model_override: modelOverride, skill }),
  });
  if (!res.ok) throw new Error("Failed to send chat message");
  return res.json();
}

export async function generateShip30Essay(sessionId, topic, guestFilter = null, modelOverride = null) {
  const res = await fetch(`${API_BASE}/api/skills/ship30`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, topic, guest_filter: guestFilter, model_override: modelOverride }),
  });
  if (!res.ok) throw new Error("Failed to generate Ship 30 essay");
  return res.json();
}

export async function fetchArtifact(artifactId) {
  const res = await fetch(`${API_BASE}/api/artifacts/${artifactId}`);
  if (!res.ok) throw new Error("Failed to fetch artifact");
  return res.json();
}

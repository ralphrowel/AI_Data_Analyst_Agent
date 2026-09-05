const BASE = "http://localhost:8000";

export async function fetchDatasets() {
  const res = await fetch(`${BASE}/api/datasets`);
  if (!res.ok) throw new Error("Failed to fetch datasets");
  return res.json();
}

export async function uploadDataset(filename, content) {
  const res = await fetch(`${BASE}/api/upload`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename, content }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Failed to upload dataset");
  }
  return res.json();
}

export async function fetchSessions() {
  const res = await fetch(`${BASE}/api/sessions`);
  if (!res.ok) throw new Error("Failed to fetch sessions");
  return res.json();
}

export async function createSession(datasetName, title) {
  const res = await fetch(`${BASE}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_name: datasetName, title: title }),
  });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function fetchSessionDetails(sessionId) {
  const res = await fetch(`${BASE}/api/sessions/${sessionId}`);
  if (!res.ok) throw new Error("Failed to fetch session details");
  return res.json();
}

export async function deleteSession(sessionId) {
  const res = await fetch(`${BASE}/api/sessions/${sessionId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete session");
  return res.json();
}

export async function fetchSuggestions(sessionId, provider) {
  const url = new URL(`${BASE}/api/suggestions`);
  if (sessionId) url.searchParams.append("session_id", sessionId);
  if (provider) url.searchParams.append("provider", provider);
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Failed to fetch suggestions");
  return res.json();
}

export async function askQuestion(question, chartType, chartTheme, provider, sessionId) {
  const res = await fetch(`${BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      chart_type: chartType,
      chart_theme: chartTheme,
      provider: provider || "groq",
      session_id: sessionId || null,
    }),
  });
  if (!res.ok) throw new Error("Failed to get answer");
  return res.json();
}

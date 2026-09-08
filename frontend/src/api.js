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

export async function fetchRecentGraphs(limit = 8) {
  const res = await fetch(`${BASE}/api/recent-graphs?limit=${limit}`);
  if (!res.ok) return [];
  return res.json();
}

export async function fetchDatasetChanges() {
  const res = await fetch(`${BASE}/api/dataset-changes`);
  if (!res.ok) return [];
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

export async function fetchDatasetRows(datasetName, page = 1, pageSize = 50, search = "", sortBy = "", sortOrder = "asc") {
  const url = new URL(`${BASE}/api/datasets/${encodeURIComponent(datasetName)}/rows`);
  url.searchParams.append("page", page);
  url.searchParams.append("page_size", pageSize);
  if (search) url.searchParams.append("search", search);
  if (sortBy) {
    url.searchParams.append("sort_by", sortBy);
    url.searchParams.append("sort_order", sortOrder);
  }
  const res = await fetch(url.toString());
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to load rows" }));
    throw new Error(err.detail || "Failed to load rows");
  }
  return res.json();
}

export async function updateDatasetCells(datasetName, updates) {
  const res = await fetch(`${BASE}/api/datasets/${encodeURIComponent(datasetName)}/update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ updates }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to save changes" }));
    throw new Error(err.detail || "Failed to save changes");
  }
  return res.json();
}

export async function addDatasetRow(datasetName, rowData) {
  const res = await fetch(`${BASE}/api/datasets/${encodeURIComponent(datasetName)}/rows/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ row_data: rowData }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to add row" }));
    throw new Error(err.detail || "Failed to add row");
  }
  return res.json();
}

export async function deleteDatasetRow(datasetName, rowIndex) {
  const res = await fetch(`${BASE}/api/datasets/${encodeURIComponent(datasetName)}/rows/${rowIndex}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to delete row" }));
    throw new Error(err.detail || "Failed to delete row");
  }
  return res.json();
}

export async function fetchSessionWidgets(sessionId) {
  const res = await fetch(`${BASE}/api/sessions/${encodeURIComponent(sessionId)}/widgets`);
  if (!res.ok) throw new Error("Failed to fetch widgets");
  return res.json();
}

export async function createSessionWidget(sessionId, prompt, chartType, chartTheme, provider) {
  const res = await fetch(`${BASE}/api/sessions/${encodeURIComponent(sessionId)}/widgets`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      chart_type: chartType || null,
      chart_theme: chartTheme || "light",
      provider: provider || "groq",
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to create widget" }));
    throw new Error(err.detail || "Failed to create widget");
  }
  return res.json();
}

export async function pinWidgetToSession(sessionId, widgetData) {
  const res = await fetch(`${BASE}/api/sessions/${encodeURIComponent(sessionId)}/widgets/pin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(widgetData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to pin widget" }));
    throw new Error(err.detail || "Failed to pin widget");
  }
  return res.json();
}

export async function recomputeSessionWidgets(sessionId, chartTheme = "light") {
  const res = await fetch(`${BASE}/api/sessions/${encodeURIComponent(sessionId)}/widgets/recompute?chart_theme=${chartTheme}`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to sync widgets" }));
    throw new Error(err.detail || "Failed to sync widgets");
  }
  return res.json();
}

export async function deleteSessionWidget(sessionId, widgetId) {
  const res = await fetch(`${BASE}/api/sessions/${encodeURIComponent(sessionId)}/widgets/${encodeURIComponent(widgetId)}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to delete widget" }));
    throw new Error(err.detail || "Failed to delete widget");
  }
  return res.json();
}



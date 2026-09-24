import { DEMO_NETFLIX_COLUMNS, DEMO_NETFLIX_ROWS } from "./netflix_demo_data";
import { executeDemoAnalysis } from "./demo_analyst";

function getApiBaseUrl() {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (typeof window !== "undefined") {
    const isLocalhost = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
    if (!isLocalhost && envUrl && (envUrl.includes("localhost") || envUrl.includes("127.0.0.1"))) {
      console.warn("VITE_API_BASE_URL points to localhost in a production deployment; falling back to origin.");
      return window.location.origin.replace(/\/$/, "");
    }
  }
  return (envUrl || (typeof window !== "undefined" ? window.location.origin : "")).replace(/\/$/, "");
}

const BASE = getApiBaseUrl();

let currentAuthToken = localStorage.getItem("visiq_auth_token") || null;

export function setAuthToken(token) {
  currentAuthToken = token;
  if (token) {
    localStorage.setItem("visiq_auth_token", token);
  } else {
    localStorage.removeItem("visiq_auth_token");
  }
}

export function getAuthToken() {
  return currentAuthToken;
}

function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (currentAuthToken) {
    headers["Authorization"] = `Bearer ${currentAuthToken}`;
  }
  return headers;
}

/**
 * Safely parse JSON from a fetch Response, preventing
 * SyntaxError: Unexpected token '<', "<!doctype "... is not valid JSON
 */
async function safeJson(res, defaultError = "Request failed") {
  const contentType = res.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}: ${res.statusText || defaultError}`);
    }
    throw new Error(
      "Received HTML instead of JSON from API. Ensure your backend server is running and VITE_API_BASE_URL is configured."
    );
  }
  return res.json();
}

export async function fetchCurrentUser() {
  try {
    const res = await fetch(`${BASE}/api/auth/me`, {
      headers: authHeaders(),
    });
    if (!res.ok) return null;
    return await safeJson(res);
  } catch {
    return null;
  }
}

export async function fetchUserQuota() {
  try {
    const res = await fetch(`${BASE}/api/user/quota`, {
      headers: authHeaders(),
    });
    if (!res.ok) return null;
    return await safeJson(res);
  } catch {
    return null;
  }
}

export async function fetchDatasets() {
  try {
    const res = await fetch(`${BASE}/api/datasets`, {
      headers: authHeaders(),
    });
    if (!res.ok) {
      const err = await safeJson(res, "Failed to fetch datasets").catch(() => ({ detail: "Failed to fetch datasets" }));
      throw new Error(err.detail || "Failed to fetch datasets");
    }
    return await safeJson(res, "Failed to fetch datasets");
  } catch (err) {
    throw err;
  }
}

export async function uploadDataset(filename, content) {
  const res = await fetch(`${BASE}/api/upload`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ filename, content }),
  });
  if (!res.ok) {
    const err = await safeJson(res, "Upload failed").catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Failed to upload dataset");
  }
  return safeJson(res, "Upload failed");
}

export async function fetchSessions() {
  const res = await fetch(`${BASE}/api/sessions`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await safeJson(res, "Failed to fetch sessions").catch(() => ({ detail: "Failed to fetch sessions" }));
    throw new Error(err.detail || "Failed to fetch sessions");
  }
  return safeJson(res, "Failed to fetch sessions");
}

export async function fetchRecentGraphs(limit = 8) {
  try {
    const res = await fetch(`${BASE}/api/recent-graphs?limit=${limit}`, {
      headers: authHeaders(),
    });
    if (!res.ok) return [];
    return await safeJson(res);
  } catch {
    return [];
  }
}

export async function fetchDatasetChanges() {
  try {
    const res = await fetch(`${BASE}/api/dataset-changes`, {
      headers: authHeaders(),
    });
    if (!res.ok) return [];
    return await safeJson(res);
  } catch {
    return [];
  }
}

export async function createSession(datasetName, title) {
  const res = await fetch(`${BASE}/api/sessions`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ dataset_name: datasetName, title: title }),
  });
  if (!res.ok) {
    const err = await safeJson(res, "Failed to create session").catch(() => ({ detail: "Failed to create session" }));
    throw new Error(err.detail || "Failed to create session");
  }
  return safeJson(res, "Failed to create session");
}

export async function fetchSessionDetails(sessionId) {
  const res = await fetch(`${BASE}/api/sessions/${sessionId}`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await safeJson(res, "Failed to fetch session details").catch(() => ({ detail: "Failed to fetch session details" }));
    throw new Error(err.detail || "Failed to fetch session details");
  }
  return safeJson(res, "Failed to fetch session details");
}

export async function deleteSession(sessionId) {
  const res = await fetch(`${BASE}/api/sessions/${sessionId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await safeJson(res, "Failed to delete session").catch(() => ({ detail: "Failed to delete session" }));
    throw new Error(err.detail || "Failed to delete session");
  }
  return safeJson(res, "Failed to delete session");
}

export async function fetchSuggestions(sessionId, provider) {
  const params = new URLSearchParams();
  if (sessionId) params.append("session_id", sessionId);
  if (provider) params.append("provider", provider);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`${BASE}/api/suggestions${qs}`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await safeJson(res, "Failed to fetch suggestions").catch(() => ({ detail: "Failed to fetch suggestions" }));
    throw new Error(err.detail || "Failed to fetch suggestions");
  }
  return safeJson(res, "Failed to fetch suggestions");
}

export async function askQuestion(question, chartType, chartTheme, provider, sessionId) {
  try {
    const res = await fetch(`${BASE}/api/ask`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        question,
        chart_type: chartType,
        chart_theme: chartTheme,
        provider: provider || "groq",
        session_id: sessionId || null,
      }),
    });

    if (!res.ok) {
      let errorDetail = "";
      try {
        const err = await safeJson(res, "Failed to get answer");
        errorDetail = err.detail || err.message || "";
      } catch {}

      if (res.status === 429) {
        throw new Error(
          errorDetail || "You have reached the maximum limit of 10 queries. This AI data analyst is built for internal company use and is not intended for public access."
        );
      }

      // If in guest mode and backend is offline / returned error, fall back to instant client-side demo analysis
      const currentUser = JSON.parse(localStorage.getItem("visiq_current_user") || "null");
      if (currentUser?.isGuest || sessionId === "demo_guest_netflix") {
        console.warn(`Backend returned HTTP ${res.status}. Falling back to instant client-side demo analysis.`);
        return executeDemoAnalysis(question, chartType, chartTheme, provider);
      }

      if (!errorDetail) {
        if (res.status === 404 || res.status === 405) {
          errorDetail = `Backend API endpoint unreachable (HTTP ${res.status} at ${BASE}). Please ensure VITE_API_BASE_URL is set in your Vercel deployment settings.`;
        } else if (res.status === 502 || res.status === 503) {
          errorDetail = `Backend server is waking up or temporarily unavailable (HTTP ${res.status}). Please try again in a few moments.`;
        } else {
          errorDetail = `Server returned HTTP ${res.status}: ${res.statusText || "Request failed"}`;
        }
      }
      throw new Error(errorDetail);
    }

    return await safeJson(res, "Failed to get answer");
  } catch (err) {
    // If network error (e.g. Failed to fetch / offline / CORS)
    const currentUser = JSON.parse(localStorage.getItem("visiq_current_user") || "null");
    if (currentUser?.isGuest || sessionId === "demo_guest_netflix") {
      console.warn("Backend network error. Serving instant demo response:", err.message);
      return executeDemoAnalysis(question, chartType, chartTheme, provider);
    }
    throw err;
  }
}

// In-memory demo fallback for netflix titles when backend is offline or disconnected
function getFallbackNetflixRows(page = 1, pageSize = 50, search = "", sortBy = "", sortOrder = "asc") {
  let list = [...DEMO_NETFLIX_ROWS];
  if (search && search.trim()) {
    const q = search.trim().toLowerCase();
    list = list.filter((row) =>
      Object.values(row).some((val) => val && String(val).toLowerCase().includes(q))
    );
  }
  if (sortBy) {
    list.sort((a, b) => {
      const valA = a[sortBy];
      const valB = b[sortBy];
      if (valA === valB) return 0;
      if (valA == null) return 1;
      if (valB == null) return -1;
      const cmp = valA < valB ? -1 : 1;
      return sortOrder === "desc" ? -cmp : cmp;
    });
  }
  const totalRows = list.length;
  const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));
  const start = (page - 1) * pageSize;
  const slice = list.slice(start, start + pageSize);
  return {
    rows: slice,
    columns: DEMO_NETFLIX_COLUMNS,
    total_rows: totalRows,
    total_pages: totalPages,
    page: Number(page),
    page_size: Number(pageSize),
  };
}

export async function fetchDatasetRows(datasetName, page = 1, pageSize = 50, search = "", sortBy = "", sortOrder = "asc") {
  const safeName = encodeURIComponent(datasetName || "netflix_titles.csv");
  const params = new URLSearchParams();
  params.append("page", page);
  params.append("page_size", pageSize);
  if (search) params.append("search", search);
  if (sortBy) {
    params.append("sort_by", sortBy);
    params.append("sort_order", sortOrder || "asc");
  }
  const qs = params.toString() ? `?${params.toString()}` : "";
  try {
    const res = await fetch(`${BASE}/api/datasets/${safeName}/rows${qs}`, {
      headers: authHeaders(),
    });
    if (!res.ok) {
      const err = await safeJson(res, "Failed to load rows").catch(() => ({ detail: "Failed to load rows" }));
      throw new Error(err.detail || "Failed to load rows");
    }
    return await safeJson(res, "Failed to load rows");
  } catch (err) {
    // If exploring the demo netflix dataset and backend is disconnected or returned HTML
    if (safeName.includes("netflix") || !datasetName) {
      console.warn("Backend dataset rows unavailable; using bundled demo dataset:", err.message);
      return getFallbackNetflixRows(page, pageSize, search, sortBy, sortOrder);
    }
    throw err;
  }
}

export async function updateDatasetCells(datasetName, updates) {
  try {
    const res = await fetch(`${BASE}/api/datasets/${encodeURIComponent(datasetName)}/update`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ updates }),
    });
    if (!res.ok) {
      const err = await safeJson(res, "Failed to save changes").catch(() => ({ detail: "Failed to save changes" }));
      throw new Error(err.detail || "Failed to save changes");
    }
    return await safeJson(res, "Failed to save changes");
  } catch (err) {
    if (datasetName?.includes("netflix")) {
      return { success: true, updated: updates.length, demo: true };
    }
    throw err;
  }
}

export async function addDatasetRow(datasetName, rowData) {
  try {
    const res = await fetch(`${BASE}/api/datasets/${encodeURIComponent(datasetName)}/rows/add`, {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ row_data: rowData }),
    });
    if (!res.ok) {
      const err = await safeJson(res, "Failed to add row").catch(() => ({ detail: "Failed to add row" }));
      throw new Error(err.detail || "Failed to add row");
    }
    return await safeJson(res, "Failed to add row");
  } catch (err) {
    if (datasetName?.includes("netflix")) {
      return { success: true, row: rowData, demo: true };
    }
    throw err;
  }
}

export async function deleteDatasetRow(datasetName, rowIndex) {
  try {
    const res = await fetch(`${BASE}/api/datasets/${encodeURIComponent(datasetName)}/rows/${rowIndex}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    if (!res.ok) {
      const err = await safeJson(res, "Failed to delete row").catch(() => ({ detail: "Failed to delete row" }));
      throw new Error(err.detail || "Failed to delete row");
    }
    return await safeJson(res, "Failed to delete row");
  } catch (err) {
    if (datasetName?.includes("netflix")) {
      return { success: true, deleted: rowIndex, demo: true };
    }
    throw err;
  }
}

export async function fetchSessionWidgets(sessionId) {
  const res = await fetch(`${BASE}/api/sessions/${encodeURIComponent(sessionId)}/widgets`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await safeJson(res, "Failed to fetch widgets").catch(() => ({ detail: "Failed to fetch widgets" }));
    throw new Error(err.detail || "Failed to fetch widgets");
  }
  return safeJson(res, "Failed to fetch widgets");
}

export async function createSessionWidget(sessionId, prompt, chartType, chartTheme, provider) {
  const res = await fetch(`${BASE}/api/sessions/${encodeURIComponent(sessionId)}/widgets`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      prompt,
      chart_type: chartType || null,
      chart_theme: chartTheme || "light",
      provider: provider || "groq",
    }),
  });
  if (!res.ok) {
    const err = await safeJson(res, "Failed to create widget").catch(() => ({ detail: "Failed to create widget" }));
    throw new Error(err.detail || "Failed to create widget");
  }
  return safeJson(res, "Failed to create widget");
}

export async function pinWidgetToSession(sessionId, widgetData) {
  const res = await fetch(`${BASE}/api/sessions/${encodeURIComponent(sessionId)}/widgets/pin`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(widgetData),
  });
  if (!res.ok) {
    const err = await safeJson(res, "Failed to pin widget").catch(() => ({ detail: "Failed to pin widget" }));
    throw new Error(err.detail || "Failed to pin widget");
  }
  return safeJson(res, "Failed to pin widget");
}

export async function recomputeSessionWidgets(sessionId, chartTheme = "light") {
  const res = await fetch(`${BASE}/api/sessions/${encodeURIComponent(sessionId)}/widgets/recompute?chart_theme=${chartTheme}`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await safeJson(res, "Failed to sync widgets").catch(() => ({ detail: "Failed to sync widgets" }));
    throw new Error(err.detail || "Failed to sync widgets");
  }
  return safeJson(res, "Failed to sync widgets");
}

export async function deleteSessionWidget(sessionId, widgetId) {
  const res = await fetch(`${BASE}/api/sessions/${encodeURIComponent(sessionId)}/widgets/${encodeURIComponent(widgetId)}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await safeJson(res, "Failed to delete widget").catch(() => ({ detail: "Failed to delete widget" }));
    throw new Error(err.detail || "Failed to delete widget");
  }
  return safeJson(res, "Failed to delete widget");
}

export async function loginWithPassword(username, password) {
  const res = await fetch(`${BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await safeJson(res, "Invalid username or password").catch(() => ({ detail: "Invalid username or password" }));
    throw new Error(err.detail || "Invalid username or password");
  }
  return safeJson(res, "Login failed");
}

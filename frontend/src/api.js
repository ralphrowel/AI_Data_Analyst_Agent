const BASE = "http://localhost:8000";

export async function fetchSuggestions() {
  const res = await fetch(`${BASE}/api/suggestions`);
  if (!res.ok) throw new Error("Failed to fetch suggestions");
  return res.json();
}

export async function askQuestion(question, chartType) {
  const res = await fetch(`${BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, chart_type: chartType }),
  });
  if (!res.ok) throw new Error("Failed to get answer");
  return res.json();
}

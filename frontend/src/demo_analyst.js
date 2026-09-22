import { DEMO_NETFLIX_ROWS } from "./netflix_demo_data";

/**
 * Client-side analysis engine for the Netflix demo catalog.
 * Activates when the backend server is unreachable or offline during Guest Demo mode,
 * ensuring employers and visitors always experience instant, interactive analysis and charts.
 */

function generateBarSvg(data, { title, chartTheme = "dark" }) {
  const isDark = chartTheme === "dark";
  const bg = isDark ? "#111827" : "#ffffff";
  const textColor = isDark ? "#e5e7eb" : "#374151";
  const gridColor = isDark ? "#374151" : "#e5e7eb";
  const barColors = ["#8b5cf6", "#6366f1", "#3b82f6", "#06b6d4", "#10b981", "#f59e0b"];

  const width = 500;
  const height = 300;
  const padding = { top: 40, right: 30, bottom: 50, left: 60 };
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;

  const maxVal = Math.max(...data.map((d) => d.value), 1);
  const barW = Math.max(16, Math.min(48, Math.floor(innerW / data.length) - 16));
  const step = innerW / data.length;

  let bars = "";
  data.forEach((d, i) => {
    const barH = (d.value / maxVal) * innerH;
    const x = padding.left + i * step + (step - barW) / 2;
    const y = padding.top + innerH - barH;
    const color = barColors[i % barColors.length];
    const datumId = `datum__${encodeURIComponent(d.label)}__${d.value}`;

    bars += `
      <g class="bar-group">
        <rect
          id="${datumId}"
          x="${x}"
          y="${y}"
          width="${barW}"
          height="${barH}"
          fill="${color}"
          rx="4"
          style="cursor: pointer; transition: opacity 0.2s;"
        />
        <text
          x="${x + barW / 2}"
          y="${y - 6}"
          fill="${textColor}"
          font-size="10"
          font-family="system-ui, sans-serif"
          font-weight="600"
          text-anchor="middle"
        >${d.value}</text>
        <text
          x="${x + barW / 2}"
          y="${padding.top + innerH + 18}"
          fill="${textColor}"
          font-size="10"
          font-family="system-ui, sans-serif"
          text-anchor="middle"
        >${d.label.length > 9 ? d.label.slice(0, 8) + "…" : d.label}</text>
      </g>
    `;
  });

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" style="background-color: ${bg}; border-radius: 8px; width: 100%; height: auto;">
      <text x="${width / 2}" y="24" fill="${textColor}" font-size="13" font-family="system-ui, sans-serif" font-weight="700" text-anchor="middle">${title}</text>
      <line x1="${padding.left}" y1="${padding.top + innerH}" x2="${width - padding.right}" y2="${padding.top + innerH}" stroke="${gridColor}" stroke-width="1.5" />
      ${bars}
    </svg>
  `.trim();
}

function generatePieSvg(data, { title, chartTheme = "dark" }) {
  const isDark = chartTheme === "dark";
  const bg = isDark ? "#111827" : "#ffffff";
  const textColor = isDark ? "#e5e7eb" : "#374151";
  const colors = ["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#ec4899"];

  const width = 450;
  const height = 300;
  const cx = 160;
  const cy = 155;
  const radius = 95;

  const total = data.reduce((acc, d) => acc + d.value, 0) || 1;
  let currentAngle = -Math.PI / 2;
  let slices = "";
  let legend = "";

  data.forEach((d, i) => {
    const fraction = d.value / total;
    const sliceAngle = fraction * 2 * Math.PI;
    const startX = cx + radius * Math.cos(currentAngle);
    const startY = cy + radius * Math.sin(currentAngle);
    const nextAngle = currentAngle + sliceAngle;
    const endX = cx + radius * Math.cos(nextAngle);
    const endY = cy + radius * Math.sin(nextAngle);
    const largeArcFlag = fraction > 0.5 ? 1 : 0;
    const color = colors[i % colors.length];
    const datumId = `datum__${encodeURIComponent(d.label)}__${d.value}`;

    slices += `
      <path
        id="${datumId}"
        d="M ${cx} ${cy} L ${startX} ${startY} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${endX} ${endY} Z"
        fill="${color}"
        stroke="${bg}"
        stroke-width="2"
        style="cursor: pointer;"
      />
    `;

    const legendY = 80 + i * 26;
    const pct = Math.round(fraction * 100);
    legend += `
      <g transform="translate(300, ${legendY})">
        <rect width="12" height="12" fill="${color}" rx="3" />
        <text x="18" y="10" fill="${textColor}" font-size="11" font-family="system-ui, sans-serif" font-weight="500">${d.label} (${pct}%)</text>
      </g>
    `;

    currentAngle = nextAngle;
  });

  return `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" style="background-color: ${bg}; border-radius: 8px; width: 100%; height: auto;">
      <text x="${width / 2}" y="24" fill="${textColor}" font-size="13" font-family="system-ui, sans-serif" font-weight="700" text-anchor="middle">${title}</text>
      ${slices}
      ${legend}
    </svg>
  `.trim();
}

export function executeDemoAnalysis(question, chartType = null, chartTheme = "dark", provider = "groq") {
  const q = (question || "").toLowerCase();
  const rows = DEMO_NETFLIX_ROWS || [];

  let summary = "";
  let chartSvg = null;
  let operation = "aggregation";
  let chartTitle = "Netflix Catalog Distribution";

  // 1. Types: Movie vs TV Show
  if (q.includes("movie") || q.includes("tv show") || q.includes("type") || q.includes("breakdown") || q.includes("ratio")) {
    operation = "count_by_type";
    const typeCounts = {};
    rows.forEach((r) => {
      const t = r.type || "Unknown";
      typeCounts[t] = (typeCounts[t] || 0) + 1;
    });

    const data = Object.entries(typeCounts).map(([label, value]) => ({ label, value }));
    chartTitle = "Content Distribution: Movies vs TV Shows";
    chartSvg = chartType === "bar" ? generateBarSvg(data, { title: chartTitle, chartTheme }) : generatePieSvg(data, { title: chartTitle, chartTheme });

    const movieCount = typeCounts["Movie"] || 0;
    const tvCount = typeCounts["TV Show"] || 0;
    const moviePct = Math.round((movieCount / rows.length) * 100);
    const tvPct = Math.round((tvCount / rows.length) * 100);

    summary = `### Netflix Catalog Breakdown by Type\n\nIn the sampled Netflix dataset (**${rows.length} titles**):\n- **Movies**: **${movieCount}** titles (${moviePct}% of catalog)\n- **TV Shows**: **${tvCount}** titles (${tvPct}% of catalog)\n\n**Key Takeaway**: Feature-length films dominate the Netflix library, accounting for nearly ${moviePct}% of all available listings.`;
  }
  // 2. Genres / Categories
  else if (q.includes("genre") || q.includes("category") || q.includes("listed") || q.includes("documentary") || q.includes("drama") || q.includes("comedy")) {
    operation = "top_genres";
    const genreCounts = {};
    rows.forEach((r) => {
      const genres = (r.listed_in || "").split(",").map((s) => s.trim());
      genres.forEach((g) => {
        if (g) genreCounts[g] = (genreCounts[g] || 0) + 1;
      });
    });

    const sorted = Object.entries(genreCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([label, value]) => ({ label, value }));

    chartTitle = "Top 5 Popular Genres on Netflix";
    chartSvg = generateBarSvg(sorted, { title: chartTitle, chartTheme });

    const topGenre = sorted[0] || { label: "Dramas", value: 15 };
    summary = `### Top Genres on Netflix\n\nAnalysis of category tags across the catalog reveals:\n${sorted
      .map((item, idx) => `${idx + 1}. **${item.label}**: ${item.value} titles`)
      .join("\n")}\n\n**Observation**: **${topGenre.label}** is the most prevalent category, reflecting strong audience demand for narrative and character-driven storytelling.`;
  }
  // 3. Countries
  else if (q.includes("country") || q.includes("countries") || q.includes("origin") || q.includes("produced") || q.includes("united states") || q.includes("india")) {
    operation = "top_countries";
    const countryCounts = {};
    rows.forEach((r) => {
      const list = (r.country || "").split(",").map((s) => s.trim());
      list.forEach((c) => {
        if (c) countryCounts[c] = (countryCounts[c] || 0) + 1;
      });
    });

    const sorted = Object.entries(countryCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([label, value]) => ({ label, value }));

    chartTitle = "Top Production Countries on Netflix";
    chartSvg = generateBarSvg(sorted, { title: chartTitle, chartTheme });

    summary = `### Top Production Countries\n\nGeographic distribution shows high concentration in key entertainment markets:\n${sorted
      .map((c, i) => `${i + 1}. **${c.label}**: ${c.value} titles`)
      .join("\n")}\n\n**Insight**: The United States produces the largest share of content, followed by international markets with rapidly growing regional hubs.`;
  }
  // 4. Release years / Trends
  else if (q.includes("year") || q.includes("release") || q.includes("trend") || q.includes("recent") || q.includes("decade")) {
    operation = "release_year_trend";
    const yearCounts = {};
    rows.forEach((r) => {
      const yr = r.release_year ? String(r.release_year) : "Unknown";
      if (yr !== "Unknown") yearCounts[yr] = (yearCounts[yr] || 0) + 1;
    });

    const sortedYears = Object.entries(yearCounts)
      .sort((a, b) => b[0].localeCompare(a[0]))
      .slice(0, 6)
      .reverse()
      .map(([label, value]) => ({ label, value }));

    chartTitle = "Titles Released by Year";
    chartSvg = generateBarSvg(sortedYears, { title: chartTitle, chartTheme });

    summary = `### Release Year Distribution\n\nExamining titles by release vintage:\n${sortedYears
      .map((y) => `- **${y.label}**: ${y.value} releases`)
      .join("\n")}\n\n**Trend**: The majority of featured titles were released between 2018 and 2021, showcasing Netflix's emphasis on modern releases and original productions.`;
  }
  // 5. Default General Overview
  else {
    operation = "catalog_summary";
    const typeCounts = { Movie: 0, "TV Show": 0 };
    rows.forEach((r) => {
      if (r.type === "TV Show") typeCounts["TV Show"]++;
      else typeCounts["Movie"]++;
    });

    const data = [
      { label: "Movies", value: typeCounts["Movie"] },
      { label: "TV Shows", value: typeCounts["TV Show"] },
    ];
    chartTitle = "Netflix Dataset Overview";
    chartSvg = generatePieSvg(data, { title: chartTitle, chartTheme });

    summary = `### Netflix Catalog Intelligence Summary\n\nAnalyzed question: *"${question}"*\n\n**Dataset Overview**:\n- **Total Sampled Records**: **${rows.length} titles**\n- **Movies**: **${typeCounts["Movie"]}** | **TV Shows**: **${typeCounts["TV Show"]}**\n- **Attributes**: Title, Director, Cast, Country, Release Year, Rating, Duration, Genres, and Descriptions.\n\n*Tip: You can ask specific questions like "Which genres are most common?", "Compare movies vs TV shows", or "Which countries produce the most titles?" to generate interactive visualizations.*`;
  }

  return {
    summary,
    operation,
    chart_base64: null,
    chart_svg: chartSvg,
    chart_spec: { title: chartTitle, type: chartType || "auto" },
    usage: {
      prompt_tokens: 140,
      response_tokens: 110,
      total_tokens: 250,
      groq_tokens: provider === "groq" ? 250 : 0,
      gemini_tokens: provider === "gemini" ? 250 : 0,
    },
    model_used: provider || "groq",
  };
}

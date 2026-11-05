"""Generates a high-resolution, publication-grade architecture flowchart image for Visiq."""
import os
import shutil
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

def create_flowchart():
    # Sizing and styling
    fig, ax = plt.subplots(figsize=(20, 28), dpi=200)
    fig.patch.set_facecolor('#0b0f19')  # Deep dark slate background
    ax.set_facecolor('#0b0f19')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 140)
    ax.axis('off')

    # Color Palette
    TEXT_MAIN = '#f8fafc'
    TEXT_MUTED = '#94a3b8'
    BORDER_COLOR = '#334155'
    
    C_INDIGO = {'bg': '#1e1b4b', 'border': '#6366f1', 'pill': '#4338ca', 'text': '#818cf8'}
    C_EMERALD = {'bg': '#064e3b', 'border': '#10b981', 'pill': '#047857', 'text': '#34d399'}
    C_AMBER = {'bg': '#451a03', 'border': '#f59e0b', 'pill': '#b45309', 'text': '#fbbf24'}
    C_CYAN = {'bg': '#083344', 'border': '#06b6d4', 'pill': '#0e7490', 'text': '#38bdf8'}
    C_PURPLE = {'bg': '#3b0764', 'border': '#a855f7', 'pill': '#7e22ce', 'text': '#c084fc'}
    C_NODE = {'bg': '#131b2e', 'border': '#1e293b'}

    def draw_box(x, y, w, h, bg, border, radius=0.8, lw=1.5):
        box = FancyBboxPatch((x, y), w, h,
                             boxstyle=f"round,pad=0.2,rounding_size={radius}",
                             facecolor=bg, edgecolor=border, linewidth=lw, zorder=2)
        ax.add_patch(box)
        return box

    def draw_pill(x, y, w, h, text, bg, fg, fontsize=9):
        pill = FancyBboxPatch((x, y), w, h,
                              boxstyle="round,pad=0.1,rounding_size=0.4",
                              facecolor=bg, edgecolor='none', zorder=4)
        ax.add_patch(pill)
        ax.text(x + w/2, y + h/2, text, color=fg, fontsize=fontsize,
                fontweight='bold', ha='center', va='center', zorder=5, family='sans-serif')

    def draw_arrow(x1, y1, x2, y2, color='#64748b', lw=2.0, style='->'):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                    shrinkA=4, shrinkB=4, zorder=3,
                                    mutation_scale=16))

    # --- TITLE HEADER ---
    draw_box(4, 128, 92, 9, '#111827', '#374151', radius=1.0, lw=2.0)
    ax.text(50, 134, "VISIQ — END-TO-END SYSTEM ARCHITECTURE & ROUTE FLOW",
            color='#ffffff', fontsize=18, fontweight='bold', ha='center', va='center', family='sans-serif')
    ax.text(50, 130.5, "Unified Execution Topology: Ingestion -> 6-Dimension Quality Assessment -> Deterministic Remediation -> Quality-Aware Agent Analytics",
            color='#94a3b8', fontsize=10.5, ha='center', va='center', family='sans-serif')

    # =========================================================================
    # STAGE 1: INGESTION & WORKSPACE (y: 104 to 124)
    # =========================================================================
    draw_box(4, 104, 92, 21, C_INDIGO['bg'], C_INDIGO['border'], radius=1.2, lw=2)
    draw_pill(6, 121.5, 20, 2.2, "STAGE 1: INGESTION", C_INDIGO['pill'], '#ffffff', fontsize=9.5)
    ax.text(28, 122.6, "Workspace Initialization & Multi-Tenant Boundary Guard", color=TEXT_MUTED, fontsize=10, va='center')

    # Nodes in Stage 1
    # 1.1 Upload
    draw_box(6, 106, 26, 13.5, C_NODE['bg'], C_NODE['border'])
    draw_pill(7.5, 116.5, 14, 1.8, "POST /api/upload", '#312e81', '#a5b4fc', 8.5)
    ax.text(7.5, 113.8, "User CSV / Doc Ingestion", color=TEXT_MAIN, fontsize=10, fontweight='bold')
    ax.text(7.5, 109.5, "- 5 MB Size Guard (HTTP 413)\n- FileStore: Supabase Bucket\n  or Local data/uploads/{user_id}/\n- RAG Doc Indexing (.md/.txt)",
            color=TEXT_MUTED, fontsize=8.5, va='top')

    draw_arrow(32, 113, 38, 113, color=C_INDIGO['border'])

    # 1.2 Session Creation
    draw_box(38, 106, 26, 13.5, C_NODE['bg'], C_NODE['border'])
    draw_pill(39.5, 116.5, 15, 1.8, "POST /api/sessions", '#312e81', '#a5b4fc', 8.5)
    ax.text(39.5, 113.8, "Workspace Mounting", color=TEXT_MAIN, fontsize=10, fontweight='bold')
    ax.text(39.5, 109.5, "- Scopes Workspace to User ID\n- Mounts in-memory DataFrame\n- Initial session state & metadata\n- Local SQLite / Postgres DB",
            color=TEXT_MUTED, fontsize=8.5, va='top')

    draw_arrow(64, 113, 70, 113, color=C_INDIGO['border'])

    # 1.3 Active Workspace State
    draw_box(70, 106, 24, 13.5, C_NODE['bg'], C_NODE['border'])
    draw_pill(71.5, 116.5, 15, 1.8, "WORKSPACE READY", '#065f46', '#6ee7b7', 8.5)
    ax.text(71.5, 113.8, "Active Dataset Mounted", color=TEXT_MAIN, fontsize=10, fontweight='bold')
    ax.text(71.5, 109.5, "- Raw df active in session\n- Triggers automated quality\n  profiling & health audit\n- Ready for query execution",
            color=TEXT_MUTED, fontsize=8.5, va='top')

    # Arrow Down to Stage 2
    draw_arrow(82, 106, 82, 100, color='#64748b', lw=2.5)

    # =========================================================================
    # STAGE 2: DATA QUALITY & PROFILING (y: 77 to 100)
    # =========================================================================
    draw_box(4, 77, 92, 23, C_EMERALD['bg'], C_EMERALD['border'], radius=1.2, lw=2)
    draw_pill(6, 96.5, 23, 2.2, "STAGE 2: QUALITY AUDIT", C_EMERALD['pill'], '#ffffff', fontsize=9.5)
    ax.text(31, 97.6, "6-Dimension Statistical Profiling & Health Assessment", color=TEXT_MUTED, fontsize=10, va='center')

    # 2.1 Quality Request
    draw_box(6, 79, 25, 15.5, C_NODE['bg'], C_NODE['border'])
    draw_pill(7.5, 91.5, 18, 1.8, "GET /api/datasets/{name}/quality", '#064e3b', '#6ee7b7', 8)
    ax.text(7.5, 88.8, "Trigger Quality Audit", color=TEXT_MAIN, fontsize=10, fontweight='bold')
    ax.text(7.5, 84.8, "- Computes SHA-256 fingerprint\n- Checks cached audit in DB\n- Zero-lag instant cache hits\n- Parameter: refresh=true",
            color=TEXT_MUTED, fontsize=8.5, va='top')

    draw_arrow(31, 87, 37, 87, color=C_EMERALD['border'])

    # 2.2 Six Quality Dimensions
    draw_box(37, 79, 31, 15.5, C_NODE['bg'], C_NODE['border'])
    draw_pill(38.5, 91.5, 19, 1.8, "DataQualityEngine (6-Dim)", '#065f46', '#6ee7b7', 8)
    ax.text(38.5, 88.8, "Rule Checks & Profiling", color=TEXT_MAIN, fontsize=10, fontweight='bold')
    ax.text(38.5, 84.8, "- Completeness: null & empty cell counts\n- Uniqueness: duplicate rows & key collisions\n- Validity: date formats & regex patterns\n- Consistency: categorical casing drift\n- Accuracy: negative totals & IQR outliers\n- Integrity: foreign key relational checks",
            color=TEXT_MUTED, fontsize=8.5, va='top')

    draw_arrow(68, 87, 74, 87, color=C_EMERALD['border'])

    # 2.3 Score & Plan Generation
    draw_box(74, 79, 20, 15.5, C_NODE['bg'], C_NODE['border'])
    draw_pill(75.5, 91.5, 16, 1.8, "DataQualityScorer", '#065f46', '#6ee7b7', 8)
    ax.text(75.5, 88.8, "Health Score & Plan", color=TEXT_MAIN, fontsize=10, fontweight='bold')
    ax.text(75.5, 84.8, "- Overall Score (0-100)\n- Health Grade (A to F)\n- Auto Suggested Plan\n- Issue inventory by severity\n- Cached in app_records",
            color=TEXT_MUTED, fontsize=8.5, va='top')

    # Arrow Down to Stage 3
    draw_arrow(84, 77, 84, 73, color='#64748b', lw=2.5)

    # =========================================================================
    # STAGE 3: DETERMINISTIC CLEANING & QUARANTINE (y: 49 to 73)
    # =========================================================================
    draw_box(4, 49, 92, 24, C_AMBER['bg'], C_AMBER['border'], radius=1.2, lw=2)
    draw_pill(6, 69.5, 26, 2.2, "STAGE 3: CLEAN & QUARANTINE", C_AMBER['pill'], '#ffffff', fontsize=9.5)
    ax.text(34, 70.6, "Deterministic Remediation, Isolated Quarantine & Lineage", color=TEXT_MUTED, fontsize=10, va='center')

    # 3.1 Preview Dry-run
    draw_box(6, 51, 23, 16.5, C_NODE['bg'], C_NODE['border'])
    draw_pill(7.5, 64.5, 18, 1.8, "POST /clean/preview", '#78350f', '#fde68a', 8)
    ax.text(7.5, 62, "Stateless Dry-Run", color=TEXT_MAIN, fontsize=10, fontweight='bold')
    ax.text(7.5, 58.5, "- Pure in-memory trial run\n- Cell diffs & changed values\n- Predicted score delta (+pts)\n- Zero disk mutation",
            color=TEXT_MUTED, fontsize=8.5, va='top')

    draw_arrow(29, 59, 35, 59, color=C_AMBER['border'])

    # 3.2 Cleaning Pipeline
    draw_box(35, 51, 33, 16.5, C_NODE['bg'], C_NODE['border'])
    draw_pill(36.5, 64.5, 14, 1.8, "POST /clean", '#78350f', '#fde68a', 8)
    ax.text(36.5, 62, "10-Stage Deterministic Pipeline", color=TEXT_MAIN, fontsize=10, fontweight='bold')
    ax.text(36.5, 58.5, "1. Normalize column names & trim whitespace\n2. Standardize categorical casing & aliases\n3. Convert mixed dates to ISO-8601\n4. Strip currency symbols (PHP, $, commas, k)\n5. Remove duplicates & impute missing\n6. Quarantine unrecoverable fatal outliers",
            color=TEXT_MUTED, fontsize=8.5, va='top')

    draw_arrow(68, 59, 74, 59, color=C_AMBER['border'])

    # 3.3 Snapshots & Lineage
    draw_box(74, 51, 20, 16.5, C_NODE['bg'], C_NODE['border'])
    draw_pill(75.5, 64.5, 16, 1.8, "PATCH /sessions/.../dataset", '#78350f', '#fde68a', 7.5)
    ax.text(75.5, 62, "Immutable Snapshots", color=TEXT_MAIN, fontsize=10, fontweight='bold')
    ax.text(75.5, 58.5, "- Derived: {stem}__clean_v1\n- Quarantined: ...__quarantine\n- Records CleaningJob & Lineage\n- Hot-swaps session DataFrame\n- Zero prompt contamination",
            color=TEXT_MUTED, fontsize=8.5, va='top')

    # Arrow Down to Stage 4
    draw_arrow(84, 49, 84, 45, color='#64748b', lw=2.5)

    # =========================================================================
    # STAGE 4: QUALITY-AWARE AGENT ANALYTICS (y: 20 to 45)
    # =========================================================================
    draw_box(4, 20, 92, 25, C_CYAN['bg'], C_CYAN['border'], radius=1.2, lw=2)
    draw_pill(6, 41.5, 26, 2.2, "STAGE 4: AI AGENT ANALYTICS", C_CYAN['pill'], '#ffffff', fontsize=9.5)
    ax.text(34, 42.6, "Quality-Aware Agent Pipeline (Zero eval, Deterministic Badge)", color=TEXT_MUTED, fontsize=10, va='center')

    # 4.1 Ask Endpoint
    draw_box(6, 22, 20, 17.5, C_NODE['bg'], C_NODE['border'])
    draw_pill(7.5, 36.5, 12, 1.8, "POST /api/ask", '#0e7490', '#a5f3fc', 8.5)
    ax.text(7.5, 34, "User Query", color=TEXT_MAIN, fontsize=10, fontweight='bold')
    ax.text(7.5, 30.5, "- Daily Quota Guard:\n  50k tokens / 10 queries\n- Session verification\n- Rate limit: 15 req/min\n- Provider: Groq or Gemini",
            color=TEXT_MUTED, fontsize=8.5, va='top')

    draw_arrow(26, 30.5, 31, 30.5, color=C_CYAN['border'])

    # 4.2 Query Router
    draw_box(31, 22, 19, 17.5, C_NODE['bg'], C_NODE['border'])
    draw_pill(32.5, 36.5, 14, 1.8, "QueryRouter", '#0e7490', '#a5f3fc', 8.5)
    ax.text(32.5, 34, "Intent Classifier", color=TEXT_MAIN, fontsize=10, fontweight='bold')
    ax.text(32.5, 30.5, "- Classifies Query:\n  * Structured (Pandas)\n  * RAG (Vector docs)\n  * Hybrid (Both)\n- Zero-cost heuristic fallback",
            color=TEXT_MUTED, fontsize=8.5, va='top')

    draw_arrow(50, 30.5, 55, 30.5, color=C_CYAN['border'])

    # 4.3 Structured Tools
    draw_box(55, 22, 21, 17.5, C_NODE['bg'], C_NODE['border'])
    draw_pill(56.5, 36.5, 16, 1.8, "ToolRegistry (Zero eval)", '#0e7490', '#a5f3fc', 8)
    ax.text(56.5, 34, "Pandas Tools", color=TEXT_MAIN, fontsize=10, fontweight='bold')
    ax.text(56.5, 30.5, "- aggregate_data (sum, avg)\n- filter_rows (eq, contains)\n- group_data (group & agg)\n- sort_data (top N, order)\n- get_dataset_schema\n- get_quality_report",
            color=TEXT_MUTED, fontsize=8.5, va='top')

    draw_arrow(76, 30.5, 80, 30.5, color=C_CYAN['border'])

    # 4.4 Synthesis & Badge
    draw_box(80, 22, 15, 17.5, C_NODE['bg'], C_NODE['border'])
    draw_pill(81, 36.5, 12, 1.8, "Response Synthesis", '#0e7490', '#a5f3fc', 7.5)
    ax.text(81, 34, "Chart + Badge", color=TEXT_MAIN, fontsize=10, fontweight='bold')
    ax.text(81, 30.5, "- Matplotlib SVG\n- Summary text\n- Quality Badge:\n  Calculated OUTSIDE\n  LLM prompt\n  Zero contamination",
            color=TEXT_MUTED, fontsize=8.5, va='top')

    # Arrow Down to Stage 5
    draw_arrow(87, 20, 87, 16, color='#64748b', lw=2.5)

    # =========================================================================
    # STAGE 5: DASHBOARD & ZERO-AI RECOMPUTE (y: 2 to 16)
    # =========================================================================
    draw_box(4, 2, 92, 14, C_PURPLE['bg'], C_PURPLE['border'], radius=1.2, lw=2)
    draw_pill(6, 12.5, 26, 2.0, "STAGE 5: DASHBOARD WIDGETS", C_PURPLE['pill'], '#ffffff', fontsize=9.5)
    ax.text(34, 13.5, "Live Visual Insight Widgets & 0-AI Token Recomputation", color=TEXT_MUTED, fontsize=10, va='center')

    # 5.1 Pin
    draw_box(6, 3.5, 27, 8, C_NODE['bg'], C_NODE['border'])
    draw_pill(7.5, 8.5, 16, 1.8, "POST /widgets/pin", '#581c87', '#e9d5ff', 8.5)
    ax.text(7.5, 6.2, "Pin Visual Insight from Chat -> Session Dashboard", color=TEXT_MAIN, fontsize=9)

    draw_arrow(33, 7.5, 39, 7.5, color=C_PURPLE['border'])

    # 5.2 Mutate Trigger
    draw_box(39, 3.5, 24, 8, C_NODE['bg'], C_NODE['border'])
    draw_pill(40.5, 8.5, 14, 1.8, "Dataset Mutation", '#581c87', '#e9d5ff', 8.5)
    ax.text(40.5, 6.2, "Cell Edit, Row Add, or Clean Snapshot Switch", color=TEXT_MAIN, fontsize=9)

    draw_arrow(63, 7.5, 69, 7.5, color=C_PURPLE['border'])

    # 5.3 Recompute
    draw_box(69, 3.5, 25, 8, C_NODE['bg'], C_NODE['border'])
    draw_pill(70.5, 8.5, 20, 1.8, "POST /widgets/recompute", '#581c87', '#e9d5ff', 8)
    ax.text(70.5, 6.2, "0-AI Token Recompute: Instant Matplotlib Refresh", color=TEXT_MAIN, fontsize=9)

    # Save outputs
    output_dir = Path("docs/images")
    output_dir.mkdir(parents=True, exist_ok=True)
    img_path = output_dir / "visiq_architecture_flowchart.png"
    plt.savefig(img_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight', pad_inches=0.3)
    plt.close()

    print(f"Image successfully generated at: {img_path}")

    # Copy to artifact directory for rendering in conversation
    artifact_dir = Path(r"C:\Users\ralph\.gemini\antigravity\brain\a43d1d3c-96c5-4926-a3ae-b70ce1df1beb")
    if artifact_dir.exists():
        target_art = artifact_dir / "visiq_architecture_flowchart.png"
        shutil.copyfile(img_path, target_art)
        print(f"Copied to artifact directory at: {target_art}")

if __name__ == "__main__":
    create_flowchart()

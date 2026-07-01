import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


def _has_year_like_keys(data: dict) -> bool:
    keys = list(data.keys())[:5]
    try:
        return all(1000 <= abs(int(k)) <= 2100 for k in keys if k)
    except (ValueError, TypeError):
        return False


def generate_chart(result: dict, output_path: str = "chart.png"):
    op = result.get("operation")
    id_cols = set(result.get("id_columns", []))

    if op in ("unsupported", "filter"):
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    if op in ("value_counts",):
        counts = result.get("counts", {})
        if not counts:
            return
        labels = list(counts.keys())
        values = list(counts.values())
        top_n = result.get("limit", 20)
        labels = labels[:top_n]
        values = values[:top_n]
        colors = [plt.cm.viridis(i / max(len(labels), 1)) for i in range(len(labels))]
        bars = ax.barh(range(len(labels)), values, color=colors)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel("Count")
        ax.set_title(f"Top {len(labels)} values in '{result.get('target_column', '')}'")
        for bar, v in zip(bars, values):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                    str(v), va="center", fontsize=8)
        ax.invert_yaxis()

    elif op in ("group_by_agg",):
        results = result.get("results", {})
        if not results:
            return
        labels = list(results.keys())
        values = list(results.values())
        agg_func = result.get("agg_func", "count")

        if _has_year_like_keys(results):
            ax.plot(labels, values, marker="o", linestyle="-", color="#2c7fb8")
            ax.tick_params(axis="x", rotation=45)
            ax.set_xlabel(result.get("target_column", ""))
        else:
            colors = [plt.cm.viridis(i / max(len(labels), 1)) for i in range(len(labels))]
            bars = ax.bar(range(len(labels)), values, color=colors)
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
            for bar, v in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.01,
                        f"{v:.1f}" if isinstance(v, float) else str(v),
                        ha="center", fontsize=8)

        ax.set_ylabel(agg_func.capitalize())
        ax.set_title(f"{agg_func.capitalize()} of '{result.get('agg_column', '')}' by '{result.get('target_column', '')}'")

    elif op in ("sort_limit",):
        results = result.get("results", [])
        if not results:
            return
        target = result.get("target_column", list(results[0].keys())[0])
        labels = [r.get(target, "") for r in results]
        if _has_year_like_keys({str(k): 1 for k in labels}):
            other_cols = [c for c in results[0].keys() if c != target and c not in id_cols]
            value_col = other_cols[0] if other_cols else None
            if value_col:
                values = [r.get(value_col, 0) for r in results]
                ax.plot([str(l) for l in labels], values, marker="o", color="#2c7fb8")
                ax.set_ylabel(value_col)
                ax.set_title(f"{target} vs {value_col}")
            else:
                return
        else:
            return

    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

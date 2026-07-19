import base64
import io

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt


def _has_year_like_keys(data: dict) -> bool:
    keys = list(data.keys())[:5]
    try:
        return all(1000 <= abs(int(k)) <= 2100 for k in keys if k)
    except (ValueError, TypeError):
        return False


YEAR_LIKE_COLUMNS = {"release_year", "year", "date_added"}
COMPOSITIONAL_COLUMNS = {"type"}


def _resolve_chart_type(chart_type: str | None, chart_data: dict, target_column: str | None) -> str:
    if chart_type and chart_type != "auto":
        return chart_type

    if target_column and target_column in YEAR_LIKE_COLUMNS or _has_year_like_keys(chart_data):
        return "line"

    if target_column and target_column in COMPOSITIONAL_COLUMNS:
        return "pie"

    return "bar"


def _draw_pie(ax, labels, values, target_column):
    colors = [plt.cm.viridis(i / max(len(labels), 1)) for i in range(len(labels))]
    ax.pie(values, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
    ax.set_title(f"Distribution of '{target_column}'")


def _draw_line(ax, labels, values, xlabel, ylabel, title):
    ax.plot(labels, values, marker="o", linestyle="-", color="#2c7fb8")
    ax.tick_params(axis="x", rotation=45)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.4)


def _draw_bar(ax, labels, values, xlabel, ylabel, title):
    colors = [plt.cm.viridis(i / max(len(labels), 1)) for i in range(len(labels))]
    bars = ax.bar(range(len(labels)), values, color=colors)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.01,
                f"{v:.1f}" if isinstance(v, float) else str(v),
                ha="center", fontsize=8)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)


def generate_chart(result: dict, chart_type: str | None = None, chart_theme: str = "light") -> str | None:
    op = result.get("operation")
    id_cols = set(result.get("id_columns", []))

    if op == "unsupported":
        return None

    style = "dark_background" if chart_theme == "dark" else "default"
    with plt.style.context(style):
        fig, ax = plt.subplots(figsize=(10, 6))

        if chart_theme == "dark":
            bg = "#1f2937"
            fig.patch.set_facecolor(bg)
            ax.set_facecolor(bg)

        if op == "filter":
            chart_counts = result.get("chart_counts")
            chart_target = result.get("chart_target_column")
            if not chart_counts or not chart_target:
                plt.close(fig)
                return None
            labels = list(chart_counts.keys())
            values = list(chart_counts.values())
            resolved = _resolve_chart_type(chart_type, chart_counts, chart_target)

            if resolved == "pie":
                _draw_pie(ax, labels, values, chart_target)
            elif resolved == "line":
                _draw_line(ax, labels, values, chart_target, "Count",
                           f"Breakdown of '{chart_target}'")
            else:
                colors = [plt.cm.viridis(i / max(len(labels), 1)) for i in range(len(labels))]
                bars = ax.barh(range(len(labels)), values, color=colors)
                ax.set_yticks(range(len(labels)))
                ax.set_yticklabels(labels, fontsize=9)
                ax.set_xlabel("Count")
                ax.set_title(f"Breakdown of '{chart_target}'")
                for bar, v in zip(bars, values):
                    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                            str(v), va="center", fontsize=8)
                ax.grid(True, axis="x", linestyle="--", alpha=0.4)
                ax.invert_yaxis()

        elif op in ("value_counts",):
            counts = result.get("counts", {})
            if not counts:
                plt.close(fig)
                return None
            labels = list(counts.keys())
            values = list(counts.values())
            target = result.get("target_column", "")
            resolved = _resolve_chart_type(chart_type, counts, target)

            if resolved == "pie":
                _draw_pie(ax, labels, values, target)
            elif resolved == "line":
                _draw_line(ax, labels, values, target, "Count",
                           f"Top {len(labels)} values in '{target}'")
            else:
                colors = [plt.cm.viridis(i / max(len(labels), 1)) for i in range(len(labels))]
                bars = ax.barh(range(len(labels)), values, color=colors)
                ax.set_yticks(range(len(labels)))
                ax.set_yticklabels(labels, fontsize=9)
                ax.set_xlabel("Count")
                ax.set_title(f"Top {len(labels)} values in '{target}'")
                for bar, v in zip(bars, values):
                    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                            str(v), va="center", fontsize=8)
                ax.grid(True, axis="x", linestyle="--", alpha=0.4)
                ax.invert_yaxis()

        elif op in ("group_by_agg",):
            chart_data = result.get("chart_results") or result.get("results", {})
            if not chart_data:
                plt.close(fig)
                return None
            labels = list(chart_data.keys())
            values = list(chart_data.values())
            target = result.get("target_column", "")
            agg_col = result.get("agg_column", "")
            agg_func = result.get("agg_func", "count")
            resolved = _resolve_chart_type(chart_type, chart_data, target)

            ylabel = agg_func.capitalize()
            title = f"{agg_func.capitalize()} of '{agg_col}' by '{target}'"

            if resolved == "pie":
                _draw_pie(ax, labels, values, target)
            elif resolved == "line":
                _draw_line(ax, labels, values, target, ylabel, title)
            else:
                _draw_bar(ax, labels, values, target, ylabel, title)

        elif op in ("sort_limit",):
            results = result.get("results", [])
            if not results:
                plt.close(fig)
                return None
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
                    ax.grid(True, linestyle="--", alpha=0.4)
                else:
                    plt.close(fig)
                    return None
            else:
                plt.close(fig)
                return None

        else:
            plt.close(fig)
            return None

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

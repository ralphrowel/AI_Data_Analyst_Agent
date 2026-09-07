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
    wedges, texts, autotexts = ax.pie(values, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
    for w, l, v in zip(wedges, labels, values):
        safe_l = str(l).replace("__", " ")
        w.set_gid(f"datum__{safe_l}__{v}")
    ax.set_title(f"Distribution of '{target_column}'")


def _draw_line(ax, labels, values, xlabel, ylabel, title):
    ax.plot(labels, values, marker="o", linestyle="-", color="#2c7fb8")
    for l, v in zip(labels, values):
        pt = ax.plot(l, v, marker="o", markersize=9, color="#2c7fb8")[0]
        safe_l = str(l).replace("__", " ")
        pt.set_gid(f"datum__{safe_l}__{v}")
    ax.tick_params(axis="x", rotation=45)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.4)


def _draw_bar(ax, labels, values, xlabel, ylabel, title):
    colors = [plt.cm.viridis(i / max(len(labels), 1)) for i in range(len(labels))]
    bars = ax.bar(range(len(labels)), values, color=colors)
    for bar, l, v in zip(bars, labels, values):
        safe_l = str(l).replace("__", " ")
        bar.set_gid(f"datum__{safe_l}__{v}")
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


def generate_chart(result: dict, chart_type: str | None = None, chart_theme: str = "light") -> tuple[str | None, str | None]:
    op = result.get("operation")
    id_cols = set(result.get("id_columns", []))

    if op == "unsupported":
        return None, None

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
                return None, None
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
                for bar, l, v in zip(bars, labels, values):
                    safe_l = str(l).replace("__", " ")
                    bar.set_gid(f"datum__{safe_l}__{v}")
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
                return None, None
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
                for bar, l, v in zip(bars, labels, values):
                    safe_l = str(l).replace("__", " ")
                    bar.set_gid(f"datum__{safe_l}__{v}")
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
                return None, None
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
                return None, None
            target = result.get("target_column", list(results[0].keys())[0])
            label_col = "title" if "title" in results[0] else list(results[0].keys())[0]
            labels = [str(r.get(label_col, ""))[:25] for r in results]
            other_cols = [c for c in results[0].keys() if c != label_col and c not in id_cols]
            value_col = target if target in other_cols else (other_cols[0] if other_cols else None)
            if value_col:
                try:
                    values = [float(r.get(value_col, 0)) for r in results]
                    if _has_year_like_keys({str(k): 1 for k in labels}):
                        ax.plot([str(l) for l in labels], values, marker="o", color="#2c7fb8")
                        for l, v in zip(labels, values):
                            pt = ax.plot(str(l), v, marker="o", markersize=9, color="#2c7fb8")[0]
                            safe_l = str(l).replace("__", " ")
                            pt.set_gid(f"datum__{safe_l}__{v}")
                        ax.set_ylabel(value_col)
                        ax.set_title(f"{label_col} vs {value_col}")
                        ax.grid(True, linestyle="--", alpha=0.4)
                    else:
                        colors = [plt.cm.viridis(i / max(len(labels), 1)) for i in range(len(labels))]
                        bars = ax.barh(range(len(labels)), values, color=colors)
                        for bar, l, v in zip(bars, labels, values):
                            safe_l = str(l).replace("__", " ")
                            bar.set_gid(f"datum__{safe_l}__{v}")
                        ax.set_yticks(range(len(labels)))
                        ax.set_yticklabels(labels, fontsize=8)
                        ax.set_xlabel(value_col)
                        ax.set_title(f"Top {len(labels)} by '{value_col}'")
                        for bar, v in zip(bars, values):
                            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                                    f"{v:.1f}" if isinstance(v, float) else str(v), va="center", fontsize=8)
                        ax.grid(True, axis="x", linestyle="--", alpha=0.4)
                        ax.invert_yaxis()
                except Exception:
                    plt.close(fig)
                    return None, None
            else:
                plt.close(fig)
                return None, None

        else:
            plt.close(fig)
            return None, None

        buf_png = io.BytesIO()
        fig.savefig(buf_png, format="png", dpi=150, bbox_inches="tight")
        chart_base64 = base64.b64encode(buf_png.getvalue()).decode("utf-8")

        buf_svg = io.StringIO()
        fig.savefig(buf_svg, format="svg", bbox_inches="tight")
        svg_raw = buf_svg.getvalue()

        import re
        chart_svg = re.sub(
            r'(<g id="datum__([^_]+)__([^"]+)">)',
            r'\1<title>\2: \3</title>',
            svg_raw,
        )

        plt.close(fig)
        return chart_base64, chart_svg


def extract_chart_spec(result: dict, chart_type: str | None = None) -> dict | None:
    """Extract structured data series and metadata for interactive frontend vector charts with hover tooltips."""
    if not isinstance(result, dict):
        return None
    op = result.get("operation")
    if op == "unsupported":
        return None

    id_cols = set(result.get("id_columns", []))

    if op == "filter":
        chart_counts = result.get("chart_counts")
        chart_target = result.get("chart_target_column")
        if not chart_counts or not chart_target:
            return None
        labels = [str(k) for k in chart_counts.keys()]
        values = list(chart_counts.values())
        resolved = _resolve_chart_type(chart_type, chart_counts, chart_target)
        title = f"Breakdown of '{chart_target}'"
        return {
            "type": resolved,
            "orientation": "horizontal" if resolved == "bar" else "vertical",
            "title": title,
            "xlabel": "Count",
            "ylabel": str(chart_target),
            "series": [{"label": l, "value": v} for l, v in zip(labels, values)],
            "total": sum(v for v in values if isinstance(v, (int, float))),
        }

    elif op in ("value_counts",):
        counts = result.get("counts", {})
        if not counts:
            return None
        labels = [str(k) for k in counts.keys()]
        values = list(counts.values())
        target = str(result.get("target_column", ""))
        resolved = _resolve_chart_type(chart_type, counts, target)
        title = f"Top {len(labels)} values in '{target}'" if target else f"Top {len(labels)} values"
        return {
            "type": resolved,
            "orientation": "horizontal" if resolved == "bar" else "vertical",
            "title": title,
            "xlabel": "Count",
            "ylabel": target,
            "series": [{"label": l, "value": v} for l, v in zip(labels, values)],
            "total": sum(v for v in values if isinstance(v, (int, float))),
        }

    elif op in ("group_by_agg",):
        chart_data = result.get("chart_results") or result.get("results", {})
        if not chart_data:
            return None
        labels = [str(k) for k in chart_data.keys()]
        values = list(chart_data.values())
        target = str(result.get("target_column", ""))
        agg_col = str(result.get("agg_column", ""))
        agg_func = str(result.get("agg_func", "count"))
        resolved = _resolve_chart_type(chart_type, chart_data, target)
        ylabel = agg_func.capitalize()
        title = f"{agg_func.capitalize()} of '{agg_col}' by '{target}'"
        return {
            "type": resolved,
            "orientation": "vertical",
            "title": title,
            "xlabel": target,
            "ylabel": ylabel,
            "series": [{"label": l, "value": v} for l, v in zip(labels, values)],
            "total": sum(v for v in values if isinstance(v, (int, float))),
        }

    elif op in ("sort_limit",):
        results = result.get("results", [])
        if not results or not isinstance(results, list):
            return None
        target = result.get("target_column", list(results[0].keys())[0])
        label_col = "title" if "title" in results[0] else list(results[0].keys())[0]
        labels = [str(r.get(label_col, ""))[:30] for r in results]
        other_cols = [c for c in results[0].keys() if c != label_col and c not in id_cols]
        value_col = target if target in other_cols else (other_cols[0] if other_cols else None)
        if not value_col:
            return None
        try:
            values = [float(r.get(value_col, 0)) for r in results]
            is_line = _has_year_like_keys({str(k): 1 for k in labels})
            return {
                "type": "line" if is_line else "bar",
                "orientation": "vertical" if is_line else "horizontal",
                "title": f"Top {len(labels)} by '{value_col}'",
                "xlabel": str(value_col) if not is_line else str(label_col),
                "ylabel": str(label_col) if not is_line else str(value_col),
                "series": [{"label": l, "value": v} for l, v in zip(labels, values)],
                "total": sum(values),
            }
        except Exception:
            return None

    return None


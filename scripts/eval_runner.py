"""Headless evaluation runner for Visiq Benchmark Suite.

Evaluates tool execution and accuracy against deterministic ground truth.
Includes local response caching to prevent token exhaustion and rate limits.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 stdout on Windows
try:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from backend.app.agent.coordinator import _extract_json
from backend.app.agent.prompts import build_tool_selection_prompt
from backend.app.config import DEFAULT_LLM_PROVIDER, GROQ_MODEL, GEMINI_MODEL
from backend.app.llm.client import call_llm
from backend.app.tools.base import default_registry
from backend.app.tools.structured_tools import aggregate_data, filter_rows, get_dataset_schema, group_data, sort_data

CACHE_DIR = PROJECT_ROOT / "data" / "benchmarks" / "cache"
RESULTS_DIR = PROJECT_ROOT / "benchmarks" / "results"
QUESTIONS_PATH = PROJECT_ROOT / "data" / "benchmarks" / "questions_benchmark.json"


def _hash_query(model: str, question: str) -> str:
    key = f"{model}:{question.strip().lower()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def get_cached_tool_plan(model: str, question: str) -> Optional[Dict[str, Any]]:
    h = _hash_query(model, question)
    cache_file = CACHE_DIR / f"{model.replace('/', '_')}_{h}.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_cached_tool_plan(model: str, question: str, plan: Dict[str, Any]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    h = _hash_query(model, question)
    cache_file = CACHE_DIR / f"{model.replace('/', '_')}_{h}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)


def plan_query(
    question: str,
    df: pd.DataFrame,
    provider: str = "groq",
    model_override: Optional[str] = None,
    use_cache: bool = True,
) -> Tuple[Dict[str, Any], bool]:
    """Generates a structured tool plan for a user question with local caching."""
    model_name = model_override or (GROQ_MODEL if provider == "groq" else GEMINI_MODEL)

    if use_cache:
        cached = get_cached_tool_plan(model_name, question)
        if cached:
            return cached, True

    # Generate schema description from DataFrame
    schema_info = get_dataset_schema(df)
    schema_desc = (
        f"Columns: {', '.join([c['name'] + ' (' + c['dtype'] + ')' for c in schema_info['columns']])}. "
        f"Total rows: {schema_info['row_count']}."
    )

    tools_schemas = default_registry.get_schemas()
    prompt = build_tool_selection_prompt(
        question=question,
        data_description=schema_desc,
        tools_schemas=tools_schemas,
        history=[],
    )

    resp, prov = call_llm(prompt, provider=provider)
    raw_text = resp.text.strip() if prov == "gemini" else resp.choices[0].message.content.strip()

    plan = _extract_json(raw_text)
    if not plan or "tool" not in plan:
        plan = {"tool": "unsupported", "parameters": {"reason": "Could not parse JSON tool decision."}}

    save_cached_tool_plan(model_name, question, plan)
    return plan, False


def execute_tool_plan(df: pd.DataFrame, tool_name: str, params: Dict[str, Any]) -> Tuple[Any, bool, Optional[str]]:
    """Executes a tool plan deterministically against the DataFrame.

    Returns:
        (raw_result, success_boolean, error_message_if_any)
    """
    tool_fn = default_registry.get(tool_name)
    if not tool_fn:
        return None, False, f"Unregistered tool: '{tool_name}'"

    try:
        if tool_name == "search_documents":
            result = tool_fn(**params)
        else:
            result = tool_fn(df=df, **params)
        return result, True, None
    except Exception as err:
        return None, False, str(err)


def extract_scalar_result(raw_result: Any, question_meta: Dict[str, Any]) -> Any:
    """Extracts a comparable scalar number or string from a raw tool output."""
    if raw_result is None:
        return None

    result_type = question_meta.get("result_type", "number")

    # If already a number
    if isinstance(raw_result, (int, float)):
        return raw_result

    # If string
    if isinstance(raw_result, str):
        if result_type == "number":
            # Attempt to parse
            cleaned = raw_result.replace("₱", "").replace("PHP", "").replace(",", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return raw_result
        return raw_result.strip()

    # If DataFrame (from filter_rows)
    if isinstance(raw_result, pd.DataFrame):
        q_text = question_meta["question"].lower()
        # If count question
        if any(w in q_text for w in ["how many", "count", "number of"]):
            return len(raw_result)
        # If asks for sum or revenue
        if any(w in q_text for w in ["total", "sum", "revenue", "amount"]):
            for col in ["total_amount_php", "gross_revenue_php", "sales_amount_php"]:
                if col in raw_result.columns:
                    num_s = pd.to_numeric(raw_result[col], errors="coerce")
                    return round(float(num_s.sum()), 2)
        return len(raw_result)

    # If dict (from group_data)
    if isinstance(raw_result, dict):
        if not raw_result:
            return None
        q_text = question_meta["question"].lower()
        # If looking for top category/region (string)
        if result_type == "string":
            if any(w in q_text for w in ["least", "lowest", "bottom", "min"]):
                return list(raw_result.keys())[-1]
            return list(raw_result.keys())[0]
        # If looking for a specific group value
        gt_val = question_meta.get("ground_truth_value")
        # Check if any key matches question context
        for k, v in raw_result.items():
            if k.lower() in q_text:
                return v
        return list(raw_result.values())[0]

    return None


def evaluate_match(extracted: Any, ground_truth: Any, question_meta: Dict[str, Any]) -> bool:
    """Evaluates whether extracted scalar matches ground truth within relative tolerance."""
    if extracted is None:
        return False

    result_type = question_meta.get("result_type", "number")
    tol = question_meta.get("tolerance_pct", 0.001)

    if result_type == "number":
        try:
            val = float(extracted)
            gt = float(ground_truth)
            if gt == 0:
                return abs(val) <= 0.001
            rel_error = abs(val - gt) / abs(gt)
            return rel_error <= tol
        except (ValueError, TypeError):
            return False
    else:
        # String match
        s_val = str(extracted).strip().lower()
        s_gt = str(ground_truth).strip().lower()
        return s_val == s_gt or s_gt in s_val


def run_benchmark(
    dataset_path: Path,
    questions_path: Path = QUESTIONS_PATH,
    provider: str = "groq",
    model_override: Optional[str] = None,
    use_cache: bool = True,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Executes the full evaluation suite and returns structured benchmark metrics."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    if not questions_path.exists():
        raise FileNotFoundError(f"Questions benchmark not found: {questions_path}")

    df = pd.read_csv(dataset_path)
    with open(questions_path, "r", encoding="utf-8") as f:
        questions: List[Dict[str, Any]] = json.load(f)

    if limit:
        questions = questions[:limit]

    total_q = len(questions)
    crashes = 0
    exact_matches = 0
    cache_hits = 0

    category_stats: Dict[str, Dict[str, int]] = {}
    detailed_results: List[Dict[str, Any]] = []

    model_label = model_override or (GROQ_MODEL if provider == "groq" else GEMINI_MODEL)
    print(f"\n================================================================================")
    print(f"BENCHMARK RUN: {dataset_path.name}")
    print(f"Model: {model_label} (Provider: {provider}) | Queries: {total_q}")
    print(f"================================================================================\n")

    for i, q in enumerate(questions, 1):
        q_id = q["id"]
        cat = q["category"]
        question_text = q["question"]
        gt_value = q["ground_truth_value"]

        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "crashes": 0, "correct": 0}
        category_stats[cat]["total"] += 1

        # 1. Get or generate query plan
        plan, was_cached = plan_query(
            question=question_text,
            df=df,
            provider=provider,
            model_override=model_override,
            use_cache=use_cache,
        )
        if was_cached:
            cache_hits += 1

        tool_name = plan.get("tool", "unsupported")
        params = plan.get("parameters", {})

        # 2. Execute plan against DataFrame
        raw_res, exec_ok, err_msg = execute_tool_plan(df, tool_name, params)

        if not exec_ok:
            crashes += 1
            category_stats[cat]["crashes"] += 1
            extracted = None
            is_correct = False
            status_str = f"[CRASH] {err_msg[:35]}"
        else:
            # 3. Extract and score outcome
            extracted = extract_scalar_result(raw_res, q)
            is_correct = evaluate_match(extracted, gt_value, q)
            if is_correct:
                exact_matches += 1
                category_stats[cat]["correct"] += 1
                status_str = "[PASS]"
            else:
                status_str = f"[FAIL] (Got: {extracted}, Expected: {gt_value})"

        print(f"[{i:02d}/{total_q:02d}] {status_str:40s} | {q_id}")

        detailed_results.append(
            {
                "id": q_id,
                "category": cat,
                "question": question_text,
                "tool_planned": tool_name,
                "tool_params": params,
                "execution_success": exec_ok,
                "execution_error": err_msg,
                "extracted_value": extracted,
                "ground_truth_value": gt_value,
                "is_correct": is_correct,
                "vulnerability": q.get("error_vulnerability"),
            }
        )

    accuracy_pct = round((exact_matches / total_q) * 100, 2) if total_q > 0 else 0.0
    crash_rate_pct = round((crashes / total_q) * 100, 2) if total_q > 0 else 0.0

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    summary = {
        "timestamp": timestamp,
        "dataset_name": dataset_path.name,
        "model": model_label,
        "provider": provider,
        "total_queries": total_q,
        "cache_hits": cache_hits,
        "execution_crashes": crashes,
        "crash_rate_pct": crash_rate_pct,
        "exact_matches": exact_matches,
        "accuracy_pct": accuracy_pct,
        "category_breakdown": {
            k: {
                "total": v["total"],
                "crashes": v["crashes"],
                "correct": v["correct"],
                "accuracy_pct": round((v["correct"] / v["total"]) * 100, 2) if v["total"] > 0 else 0.0,
            }
            for k, v in category_stats.items()
        },
        "results": detailed_results,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = RESULTS_DIR / f"eval_{dataset_path.stem}_{timestamp}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Print summary table
    print(f"\n================================================================================")
    print(f"BENCHMARK RESULTS SUMMARY: {dataset_path.name}")
    print(f"================================================================================")
    print(f"Accuracy Rate    : {accuracy_pct}% ({exact_matches}/{total_q})")
    print(f"Crash Rate       : {crash_rate_pct}% ({crashes}/{total_q})")
    print(f"Cache Hit Ratio  : {cache_hits}/{total_q}")
    print("\nCategory Breakdown:")
    for cat, stats in summary["category_breakdown"].items():
        print(f"  - {cat:20s}: {stats['accuracy_pct']:5.1f}% correct ({stats['correct']}/{stats['total']}), {stats['crashes']} crashes")
    print(f"\nDetailed log saved: {out_file}\n")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Run Visiq Data Analyst Benchmark Suite.")
    parser.add_argument("--dataset", type=str, required=True, help="Path to CSV dataset to evaluate")
    parser.add_argument("--questions", type=str, default=str(QUESTIONS_PATH), help="Path to benchmark questions JSON")
    parser.add_argument("--provider", type=str, default=DEFAULT_LLM_PROVIDER, choices=["groq", "gemini"])
    parser.add_argument("--model", type=str, default=None, help="Optional model name override")
    parser.add_argument("--no-cache", action="store_true", help="Disable plan caching")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions (for quick smoke tests)")

    args = parser.parse_args()

    run_benchmark(
        dataset_path=Path(args.dataset),
        questions_path=Path(args.questions),
        provider=args.provider,
        model_override=args.model,
        use_cache=not args.no_cache,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()

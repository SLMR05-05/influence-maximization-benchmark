#!/usr/bin/env python3
"""
Statistics & Benchmark Data Engine for IM-Benchmark-Lab.

All values shown by the Statistics page are read from real experiment
outputs stored under ``runs/EXP_*/summary.json`` (or ``runs/latest_results.json``
when no per-experiment directory exists). Nothing is generated, simulated or
hardcoded: when no experiment data is available the getters return empty
results and the GUI renders an empty state instead.
"""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = PROJECT_ROOT / "runs"

# Presentation only (algorithm identity is derived from the run files).
ALGORITHM_COLORS = {
    "iga": "#ef4444",
    "ga": "#3b82f6",
    "celf": "#10b981",
    "degree": "#8b5cf6",
    "degree_discount": "#8b5cf6",
    "pagerank": "#f59e0b",
}
FALLBACK_COLORS = ["#06b6d4", "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#84cc16"]


# ─────────────────────────────────────────────────────────────────────────────
#  Loading real experiment records
# ─────────────────────────────────────────────────────────────────────────────

_CACHE: Dict[str, Any] = {"stamp": None, "records": []}


def _read_record(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("summary"), list):
        return None
    data["_path"] = str(path)
    data["_mtime"] = path.stat().st_mtime
    return data


def _load_experiments() -> List[Dict[str, Any]]:
    """Loads every real experiment record, newest last. Cached by file mtimes."""
    run_files = sorted(RUNS_DIR.glob("EXP_*/summary.json"))
    latest_file = RUNS_DIR / "latest_results.json"
    files = list(run_files)
    if not files and latest_file.exists():
        files = [latest_file]

    stamp = tuple((str(p), p.stat().st_mtime_ns) for p in files if p.exists())
    if _CACHE["stamp"] == stamp:
        return _CACHE["records"]

    records = []
    for path in files:
        if not path.exists():
            continue
        record = _read_record(path)
        if record is not None:
            records.append(record)

    records.sort(key=lambda r: (str(r.get("timestamp") or ""), float(r.get("_mtime") or 0)))
    _CACHE["stamp"] = stamp
    _CACHE["records"] = records
    return records


def _matches(record: Dict[str, Any], dataset: str, model: str, k: Optional[int]) -> bool:
    if str(record.get("dataset", "")) != dataset:
        return False
    if model and str(record.get("model") or "IC") != model:
        return False
    if k is not None:
        try:
            if int(record.get("k", 0)) != int(k):
                return False
        except (TypeError, ValueError):
            return False
    return True


def _matching_experiments(dataset: Optional[str], model: str = "IC",
                          k: Optional[int] = None) -> List[Dict[str, Any]]:
    return [
        r for r in _load_experiments()
        if (dataset is None or _matches(r, dataset, model, k))
    ]


def _latest_experiment(dataset: Optional[str], model: str = "IC",
                       k: Optional[int] = None) -> Optional[Dict[str, Any]]:
    matches = _matching_experiments(dataset, model, k)
    return matches[-1] if matches else None


def _format_seconds(value: float) -> str:
    if value >= 1.0:
        return f"{value:.3f}s"
    if value >= 0.001:
        return f"{value:.4f}s"
    return f"{value * 1000:.3f}ms"


def _color_for(code: str, index: int = 0) -> str:
    if code in ALGORITHM_COLORS:
        return ALGORITHM_COLORS[code]
    return FALLBACK_COLORS[index % len(FALLBACK_COLORS)]


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(values: Sequence[float]) -> float:
    return float(statistics.fmean(values)) if values else 0.0


def _pstd(values: Sequence[float]) -> float:
    return float(statistics.pstdev(values)) if len(values) > 1 else 0.0


def _detail_for(record: Dict[str, Any], row: Dict[str, Any]) -> Dict[str, Any]:
    details = record.get("details") or {}
    name = row.get("algorithm")
    detail = details.get(name)
    if isinstance(detail, dict):
        return detail
    # Fall back to matching by algorithm code.
    for value in details.values():
        if isinstance(value, dict) and value.get("code") == row.get("code"):
            return value
    return {}


def _spreads_of(detail: Dict[str, Any]) -> List[float]:
    spreads = detail.get("spreads") or []
    if not spreads:
        runs_detail = detail.get("runs_detail") or []
        spreads = [run.get("spread") for run in runs_detail if isinstance(run, dict)]
    return [_as_float(value) for value in spreads if value is not None]


def _times_of(detail: Dict[str, Any]) -> List[float]:
    times = detail.get("times") or []
    if not times:
        runs_detail = detail.get("runs_detail") or []
        times = [run.get("wall_time") for run in runs_detail if isinstance(run, dict)]
    return [_as_float(value) for value in times if value is not None]


def _seed_sets_of(detail: Dict[str, Any]) -> List[List[int]]:
    seeds = detail.get("seeds") or []
    if not seeds:
        runs_detail = detail.get("runs_detail") or []
        seeds = [run.get("seed_set") for run in runs_detail if isinstance(run, dict)]
    result = []
    for seed_set in seeds:
        if isinstance(seed_set, (list, tuple, set)):
            result.append(sorted(int(node) for node in seed_set))
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  Available filters (derived from real runs)
# ─────────────────────────────────────────────────────────────────────────────

def get_available_datasets(model: str = "IC") -> List[str]:
    return sorted({str(r.get("dataset")) for r in _load_experiments()
                   if str(r.get("model", "IC")) == model and r.get("dataset")})


def get_available_k_values(dataset: str, model: str = "IC") -> List[int]:
    values = set()
    for record in _matching_experiments(dataset, model):
        try:
            values.add(int(record.get("k")))
        except (TypeError, ValueError):
            continue
    return sorted(values)


def get_available_models(dataset: Optional[str] = None) -> List[str]:
    return sorted({str(r.get("model", "IC")) for r in _load_experiments()
                   if dataset is None or str(r.get("dataset")) == dataset})


def get_latest_run_selection(model: str = "IC") -> Optional[Dict[str, Any]]:
    """Returns the filters of the most recent real run (used for initial UI state)."""
    records = [r for r in _load_experiments() if str(r.get("model", "IC")) == model]
    if not records:
        return None
    record = records[-1]
    try:
        k_value = int(record.get("k"))
    except (TypeError, ValueError):
        k_value = None
    return {
        "dataset": record.get("dataset"),
        "k": k_value,
        "model": record.get("model", "IC"),
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Tab A — Performance overview
# ─────────────────────────────────────────────────────────────────────────────

def get_performance_summary(
    dataset_name: str = "",
    k: Optional[int] = None,
    model: str = "IC",
) -> List[Dict[str, Any]]:
    """Returns per-algorithm metrics computed from the latest matching run."""
    record = _latest_experiment(dataset_name, model, k)
    if record is None:
        return []

    rows = []
    for index, row in enumerate(record.get("summary") or []):
        code = str(row.get("code") or "").lower()
        detail = _detail_for(record, row)
        spreads = _spreads_of(detail)
        times = _times_of(detail)

        mean = _mean(spreads) if spreads else _as_float(row.get("mean_spread"))
        std = _pstd(spreads) if spreads else _as_float(row.get("std_spread"))
        median = float(statistics.median(spreads)) if spreads else mean
        best = max(spreads) if spreads else _as_float(row.get("best_spread"), mean)
        run_count = len(spreads) or int(_as_float(record.get("runs"), 1) or 1)
        total_time = _mean(times) if times else _as_float(row.get("mean_time"))
        ci_95 = 1.96 * std / math.sqrt(run_count) if run_count > 1 else 0.0

        rows.append({
            "code": code,
            "algorithm": row.get("algorithm") or code,
            "color": _color_for(code, index),
            "best_spread": round(best, 2),
            "mean_spread": round(mean, 2),
            "median_spread": round(median, 2),
            "std_spread": round(std, 2),
            "ci_95": f"± {ci_95:.2f}" if run_count > 1 else "—",
            "runs": run_count,
            "time_total_num": total_time,
            "time_total": _format_seconds(total_time),
            # The runner does not record a stage breakdown.
            "time_prep": "—",
            "time_search": "—",
            "time_eval": "—",
        })

    rows.sort(key=lambda r: r["mean_spread"], reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows


# ─────────────────────────────────────────────────────────────────────────────
#  Tab B — Spread vs k
# ─────────────────────────────────────────────────────────────────────────────

def get_spread_vs_k_data(
    dataset_name: str = "",
    model: str = "IC",
    k: Optional[int] = None,
) -> Dict[str, Any]:
    """Builds spread curves from every real experiment of the selected dataset."""
    experiments = _matching_experiments(dataset_name, model)
    empty = {"dataset": dataset_name, "k_list": [], "curves": {}, "box_data": {}, "box_k": k}
    if not experiments:
        return empty

    by_k: Dict[int, Dict[str, Dict[str, List[float]]]] = {}
    meta: Dict[str, Dict[str, Any]] = {}

    for record in experiments:
        try:
            record_k = int(record.get("k"))
        except (TypeError, ValueError):
            continue
        for index, row in enumerate(record.get("summary") or []):
            code = str(row.get("code") or "").lower()
            detail = _detail_for(record, row)
            spreads = _spreads_of(detail)
            mean = _mean(spreads) if spreads else _as_float(row.get("mean_spread"))
            median = float(statistics.median(spreads)) if spreads else mean

            slot = by_k.setdefault(record_k, {}).setdefault(code, {"means": [], "medians": []})
            slot["means"].append(mean)
            slot["medians"].append(median)
            meta.setdefault(code, {
                "name": row.get("algorithm") or code,
                "color": _color_for(code, index),
            })

    if not by_k:
        return empty

    k_list = sorted(by_k)
    curves: Dict[str, Dict[str, Any]] = {}
    for code, info in meta.items():
        curve_k, means, medians, errors = [], [], [], []
        for value_k in k_list:
            means_at_k = by_k.get(value_k, {}).get(code, {}).get("means", [])
            medians_at_k = by_k.get(value_k, {}).get(code, {}).get("medians", [])
            if not means_at_k:
                continue
            curve_k.append(value_k)
            means.append(round(_mean(means_at_k), 2))
            medians.append(round(_mean(medians_at_k), 2))
            errors.append(round(_pstd(means_at_k), 2))
        if means:
            curves[code] = {
                "name": info["name"],
                "color": info["color"],
                "k_list": curve_k,
                "means": means,
                "medians": medians,
                "errors": errors,
            }

    box_k = k if k in by_k else k_list[-1]
    box_record = _latest_experiment(dataset_name, model, box_k)
    box_data: Dict[str, List[float]] = {}
    if box_record is not None:
        for row in box_record.get("summary") or []:
            code = str(row.get("code") or "").lower()
            spreads = _spreads_of(_detail_for(box_record, row))
            if spreads:
                box_data[code] = spreads

    return {
        "dataset": dataset_name,
        "k_list": k_list,
        "curves": curves,
        "box_data": box_data,
        "box_k": box_k,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Tab C — Runtime analysis
# ─────────────────────────────────────────────────────────────────────────────

def get_runtime_analysis_data(
    dataset_name: str = "",
    model: str = "IC",
    k: Optional[int] = None,
) -> Dict[str, Any]:
    """Returns measured execution times (total only; no fabricated stage split)."""
    experiments = _matching_experiments(dataset_name, model)
    empty = {"dataset": dataset_name, "stages": [], "k_vals": [], "runtime_vs_k": {}}
    if not experiments:
        return empty

    record = _latest_experiment(dataset_name, model, k)
    if record is None:
        return empty
    stages = []
    for index, row in enumerate(record.get("summary") or []):
        code = str(row.get("code") or "").lower()
        detail = _detail_for(record, row)
        times = _times_of(detail)
        total = _mean(times) if times else _as_float(row.get("mean_time"))
        stages.append({
            "code": code,
            "algorithm": row.get("algorithm") or code,
            "color": _color_for(code, index),
            "prep": None,
            "search": None,
            "eval": None,
            "total": total,
            "runs": len(times) or int(_as_float(record.get("runs"), 1) or 1),
        })

    by_k: Dict[int, Dict[str, List[float]]] = {}
    meta: Dict[str, str] = {}
    for exp in experiments:
        try:
            exp_k = int(exp.get("k"))
        except (TypeError, ValueError):
            continue
        for row in exp.get("summary") or []:
            code = str(row.get("code") or "").lower()
            times = _times_of(_detail_for(exp, row))
            total = _mean(times) if times else _as_float(row.get("mean_time"))
            by_k.setdefault(exp_k, {}).setdefault(code, []).append(total)
            meta.setdefault(code, row.get("algorithm") or code)

    k_vals = sorted(by_k)
    runtime_vs_k = {}
    for code in meta:
        points = [(value_k, _mean(values)) for value_k, values in
                  ((value_k, by_k[value_k].get(code, [])) for value_k in k_vals) if values]
        runtime_vs_k[code] = {
            "k_list": [point[0] for point in points],
            "times": [round(point[1], 4) for point in points],
        }

    return {
        "dataset": dataset_name,
        "stages": stages,
        "k_vals": k_vals,
        "runtime_vs_k": runtime_vs_k,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Tab D — Convergence analysis (only for runs that recorded a history)
# ─────────────────────────────────────────────────────────────────────────────

def _aggregate_history(runs: Sequence[Sequence[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    histories = [h for h in runs if h]
    if not histories:
        return None
    length = min(len(h) for h in histories)
    if length == 0:
        return None

    generations, evaluations, best, avg = [], [], [], []
    for i in range(length):
        entries = [h[i] for h in histories]
        generations.append(int(_as_float(
            entries[0].get("generation", entries[0].get("iteration")), i)))
        evaluations.append(int(_as_float(
            entries[0].get("evaluations", entries[0].get("evaluations_so_far")), 0)))
        best.append(round(_mean([
            _as_float(e.get("best_fitness", e.get("cumulative_spread"))) for e in entries
        ]), 4))
        avg.append(round(_mean([
            _as_float(e.get("mean_fitness", e.get("cumulative_spread"))) for e in entries
        ]), 4))

    return {"generations": generations, "evaluations": evaluations, "best": best, "avg": avg}


def get_convergence_data(
    dataset_name: str = "",
    k: Optional[int] = None,
    model: str = "IC",
) -> Optional[Dict[str, Any]]:
    """Returns real convergence histories, or None when the run has none."""
    record = _latest_experiment(dataset_name, model, k)
    if record is None:
        return None

    details = record.get("details") or {}
    series: Dict[str, Dict[str, Any]] = {}
    for index, row in enumerate(record.get("summary") or []):
        code = str(row.get("code") or "").lower()
        detail = _detail_for(record, row)
        runs = [run.get("convergence") or [] for run in detail.get("runs_detail") or []
                if isinstance(run, dict)]
        aggregated = _aggregate_history(runs)
        if aggregated is None:
            continue

        final = round(_as_float(row.get("mean_spread")), 2)
        best_curve = aggregated["best"]
        peak = max(best_curve) if best_curve else final

        def first_generation(ratio: float) -> Optional[int]:
            if peak <= 0:
                return None
            threshold = ratio * peak
            for generation, value in zip(aggregated["generations"], best_curve):
                if value >= threshold:
                    return generation
            return None

        series[code] = {
            **aggregated,
            "name": row.get("algorithm") or code,
            "color": _color_for(code, index),
            "final": final,
            "gen_90": first_generation(0.90),
            "gen_98": first_generation(0.98),
            "total_evaluations": int(_as_float(
                (detail.get("runs_detail") or [{}])[0].get("evaluations"), 0)),
        }

    if not series:
        return None
    return {"dataset": dataset_name, "k": record.get("k"), "series": series}


# ─────────────────────────────────────────────────────────────────────────────
#  Tab E — Seed set analysis
# ─────────────────────────────────────────────────────────────────────────────

def _jaccard(a: Sequence[int], b: Sequence[int]) -> float:
    set_a, set_b = set(a), set(b)
    union = set_a | set_b
    return len(set_a & set_b) / len(union) if union else 0.0


def get_seed_set_analysis_data(
    dataset_name: str = "",
    k: Optional[int] = None,
    model: str = "IC",
) -> Optional[Dict[str, Any]]:
    """Compares the seed sets actually returned by two algorithms."""
    record = _latest_experiment(dataset_name, model, k)
    if record is None:
        return None

    rows = record.get("summary") or []
    candidates = []
    for row in rows:
        detail = _detail_for(record, row)
        seeds = _seed_sets_of(detail)
        if seeds:
            candidates.append((row, seeds))
    if not candidates:
        return None

    def find(code: str):
        return next((item for item in candidates if str(item[0].get("code", "")).lower() == code), None)

    pair = (find("iga"), find("ga"))
    if not all(pair):
        pair = tuple(candidates[:2]) if len(candidates) >= 2 else (candidates[0], None)

    row_a, seeds_a = pair[0]
    row_b, seeds_b = pair[1] if pair[1] else (None, [])

    paired = min(len(seeds_a), len(seeds_b)) if seeds_b else 0
    jaccard_scores = [_jaccard(seeds_a[i], seeds_b[i]) for i in range(paired)]
    shared_counts = [len(set(seeds_a[i]) & set(seeds_b[i])) for i in range(paired)]
    unique_a = [len(set(seeds_a[i]) - set(seeds_b[i])) for i in range(paired)]
    unique_b = [len(set(seeds_b[i]) - set(seeds_a[i])) for i in range(paired)]

    jaccard = _mean(jaccard_scores) if jaccard_scores else 0.0
    shared = _mean(shared_counts) if shared_counts else 0.0
    only_a = _mean(unique_a) if unique_a else float(len(set(seeds_a[0]))) if seeds_a else 0.0
    only_b = _mean(unique_b) if unique_b else float(len(set(seeds_b[0]))) if seeds_b else 0.0

    union_b = set().union(*(set(s) for s in seeds_b)) if seeds_b else set()

    def node_rows(seed_sets: Sequence[Sequence[int]], other_union: set) -> List[Dict[str, Any]]:
        counts: Dict[int, int] = {}
        for seed_set in seed_sets:
            for node in set(seed_set):
                counts[node] = counts.get(node, 0) + 1
        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return [
            {
                "node_id": node,
                "frequency": count,
                "runs": len(seed_sets),
                "is_shared": node in other_union,
            }
            for node, count in ordered
        ]

    name_a = row_a.get("algorithm") or "Thuật toán A"
    name_b = (row_b or {}).get("algorithm") or "—"
    nodes_iga = node_rows(seeds_a, union_b or set())
    nodes_ga = node_rows(seeds_b, set().union(*(set(s) for s in seeds_a)) if seeds_a else set())

    if paired:
        insight = (
            f"{name_a} và {name_b} chia sẻ trung bình {shared:.1f}/{int(_as_float(record.get('k'), 0))} "
            f"đỉnh hạt giống qua {paired} cặp lần chạy (Jaccard trung bình = {jaccard * 100:.1f}%). "
            f"Số đỉnh riêng trung bình: {name_a} = {only_a:.1f}, {name_b} = {only_b:.1f}."
        )
    else:
        insight = (
            f"Chỉ có dữ liệu tập hạt giống của {name_a} ({len(seeds_a)} lần chạy); "
            f"không đủ hai thuật toán để tính Jaccard."
        )

    return {
        "dataset": dataset_name,
        "k": int(_as_float(record.get("k"), 0)),
        "algorithm_a": name_a,
        "algorithm_b": name_b,
        "jaccard_similarity": jaccard,
        "jaccard_pct": f"{jaccard * 100:.1f}%",
        "shared_count": shared,
        "paired_runs": paired,
        "unique_iga_count": only_a,
        "unique_ga_count": only_b,
        "nodes_iga": nodes_iga,
        "nodes_ga": nodes_ga,
        "insight": insight,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  CSV export (real data only)
# ─────────────────────────────────────────────────────────────────────────────

def export_statistics_csv(
    tab_name: str,
    dataset_name: str = "",
    k: Optional[int] = None,
    model: str = "IC",
) -> str:
    """Builds a CSV for the selected tab from the same real data as the UI."""
    lines: List[str] = []

    if tab_name == "overview":
        summary = get_performance_summary(dataset_name, k=k, model=model)
        if not summary:
            return ""
        lines.append("Algorithm,Best Spread,Mean Spread,Median Spread,Std Dev,95% CI,Runs,Total Time (s),Rank")
        for row in summary:
            lines.append(
                f'"{row["algorithm"]}",{row["best_spread"]},{row["mean_spread"]},'
                f'{row["median_spread"]},{row["std_spread"]},"{row["ci_95"]}",'
                f'{row["runs"]},{row["time_total_num"]:.4f},{row["rank"]}'
            )

    elif tab_name == "spread":
        data = get_spread_vs_k_data(dataset_name, model=model, k=k)
        if not data["curves"]:
            return ""
        lines.append("Algorithm," + ",".join(f"k={value}" for value in data["k_list"]))
        for curve in data["curves"].values():
            lines.append(f'"{curve["name"]}",' + ",".join(str(v) for v in curve["means"]))

    elif tab_name == "runtime":
        data = get_runtime_analysis_data(dataset_name, model=model, k=k)
        if not data["stages"]:
            return ""
        lines.append("Algorithm,Total Runtime (s),Runs")
        for stage in data["stages"]:
            lines.append(f'"{stage["algorithm"]}",{stage["total"]:.4f},{stage["runs"]}')

    elif tab_name == "convergence":
        convergence = get_convergence_data(dataset_name, k=k, model=model)
        if not convergence:
            return ""
        for code, series in convergence["series"].items():
            lines.append("")
            lines.append(f'# {series["name"]} ({code})')
            lines.append("Generation,Evaluations,Best Fitness,Average Fitness")
            for gen, ev, best, avg in zip(
                series["generations"], series["evaluations"], series["best"], series["avg"]
            ):
                lines.append(f"{gen},{ev},{best},{avg}")
        if lines and not lines[0]:
            lines.pop(0)

    elif tab_name == "seed_set":
        data = get_seed_set_analysis_data(dataset_name, k=k, model=model)
        if not data:
            return ""
        lines.append("Algorithm,Node ID,Selected Runs,Total Runs,Shared")
        for node in data["nodes_iga"]:
            lines.append(
                f'"{data["algorithm_a"]}",{node["node_id"]},'
                f'{node["frequency"]},{node["runs"]},{node["is_shared"]}'
            )
        for node in data["nodes_ga"]:
            lines.append(
                f'"{data["algorithm_b"]}",{node["node_id"]},'
                f'{node["frequency"]},{node["runs"]},{node["is_shared"]}'
            )

    return "\n".join(lines)

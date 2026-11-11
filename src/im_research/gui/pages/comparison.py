#!/usr/bin/env python3
"""Comparison Page — Relative Performance Across Selected Algorithms."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk

from im_research.gui.core.theme import *
from im_research.gui.core.ui_helpers import section_header, create_empty_state
from im_research.gui.core.results_store import load_runs

WEIGHTS = {
    "spread": 0.45,
    "time": 0.30,
    "std": 0.15,
    "convergence": 0.10,
}


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _min_max_normalize(values):
    if not values:
        return [0.0 for _ in values]
    lo = min(values)
    hi = max(values)
    if hi - lo < 1e-12:
        return [1.0 for _ in values]
    return [(value - lo) / (hi - lo) for value in values]


class PageComparison(ctk.CTkScrollableFrame):
    def __init__(self, master, on_switch_tab=None, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self.on_switch_tab = on_switch_tab
        self._build()

    def on_show(self):
        self._refresh()

    def _refresh(self):
        for child in self.winfo_children():
            child.destroy()
        self._build()
        self.after(50, self._scroll_to_top)

    def _load_runs(self):
        try:
            return load_runs()
        except Exception:
            return []

    def _scroll_to_top(self):
        try:
            self._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass

    def _collect_rows(self, runs):
        collected = []
        for run_index, run in enumerate(runs):
            selected = run.get("summary", []) or []
            baseline = run.get("baseline", []) or []
            rows = [dict(row, _baseline=False, _run=run_index) for row in selected]
            if (
                len(selected) == 1
                and str(selected[0].get("code", "")).lower() != "celf"
            ):
                rows.extend(dict(row, _baseline=True, _run=run_index) for row in baseline)
            collected.extend(rows)
        return collected

    def _prepare_rows(self, rows):
        if not rows:
            return []

        spreads = [_safe_float(row.get("mean_spread", 0)) for row in rows]
        times = [_safe_float(row.get("mean_time", 0)) for row in rows]
        stds = [_safe_float(row.get("std_spread", 0)) for row in rows]
        generations = [
            max(1.0, _safe_float(row.get("generations", 1), 1.0)) for row in rows
        ]

        max_spread = max(spreads) if spreads else 0.0
        positive_times = [value for value in times if value > 0]
        fastest_time = min(positive_times) if positive_times else 0.0
        max_std = max(stds) if stds else 0.0
        max_gen = max(generations) if generations else 1.0

        spread_norms = _min_max_normalize(spreads)
        speed_norms = [
            1.0 if time_value <= 0 else (fastest_time / time_value if fastest_time > 0 else 0.0)
            for time_value in times
        ]
        std_norms = _min_max_normalize(stds)
        conv_norms = [
            1.0 - (gen / max_gen if max_gen > 0 else 0.0) for gen in generations
        ]

        prepared = []
        for index, row in enumerate(rows):
            spread_norm = spread_norms[index]
            speed_norm = speed_norms[index]
            std_norm = std_norms[index]
            conv_norm = conv_norms[index]
            composite = (
                WEIGHTS["spread"] * spread_norm
                + WEIGHTS["time"] * speed_norm
                + WEIGHTS["std"] * (1.0 - std_norm)
                + WEIGHTS["convergence"] * conv_norm
            )
            generations_value = generations[index]
            time_value = times[index]
            spread_value = spreads[index]
            std_value = stds[index]
            cpi = 0.0
            if time_value > 0 and generations_value > 0:
                cpi = spread_value * (1.0 - std_norm) / (time_value * generations_value)

            prepared.append({
                "algorithm": row.get("algorithm", row.get("name", "N/A")),
                "code": str(row.get("code", "")).lower(),
                "run": row.get("_run", 0),
                "baseline": bool(row.get("_baseline", False)),
                "spread": spread_value,
                "time": time_value,
                "std": std_value,
                "generations": generations_value,
                "spread_norm": spread_norm,
                "speed_norm": speed_norm,
                "std_norm": std_norm,
                "conv_norm": conv_norm,
                "composite": composite,
                "cpi": cpi,
                "online_bound": row.get("online_bound"),
            })

        # Pareto frontier: maximize spread, minimize time.
        for item in prepared:
            item["pareto"] = not any(
                other is not item
                and other["spread"] >= item["spread"]
                and other["time"] <= item["time"]
                and (
                    other["spread"] > item["spread"]
                    or other["time"] < item["time"]
                )
                for other in prepared
            )

        prepared.sort(key=lambda item: (item["spread"], item["composite"]), reverse=True)
        for rank, item in enumerate(prepared, start=1):
            item["rank"] = rank
        return prepared

    def _friedman_ranks(self, runs):
        ranks_by_algorithm = {}
        counts = {}
        for run in runs:
            selected = run.get("summary", []) or []
            baseline = run.get("baseline", []) or []
            rows = [dict(row, _baseline=False) for row in selected]
            if (
                len(selected) == 1
                and str(selected[0].get("code", "")).lower() != "celf"
            ):
                rows.extend(dict(row, _baseline=True) for row in baseline)
            if not rows:
                continue
            ordered = sorted(rows, key=lambda row: _safe_float(row.get("mean_spread", 0)), reverse=True)
            for position, row in enumerate(ordered, start=1):
                code = str(row.get("code", "")).lower()
                name = row.get("algorithm", row.get("name", "N/A"))
                key = code or name
                ranks_by_algorithm.setdefault(key, []).append(position)
                counts[key] = name
        result = []
        for key, values in ranks_by_algorithm.items():
            result.append({
                "key": key,
                "algorithm": counts[key],
                "average_rank": sum(values) / len(values),
                "runs": len(values),
            })
        result.sort(key=lambda item: item["average_rank"])
        return result

    def _aggregate(self, rows):
        groups = {}
        for row in rows:
            key = row["code"] or row["algorithm"]
            groups.setdefault(key, []).append(row)

        aggregated = []
        for key, values in groups.items():
            spreads = [item["spread"] for item in values]
            times = [item["time"] for item in values]
            stds = [item["std"] for item in values]
            generations = [item["generations"] for item in values]
            composites = [item["composite"] for item in values]
            cpis = [item["cpi"] for item in values]
            aggregated.append({
                "key": key,
                "algorithm": values[0]["algorithm"],
                "runs": len(values),
                "mean_spread": sum(spreads) / len(spreads),
                "mean_time": sum(times) / len(times),
                "mean_std": sum(stds) / len(stds),
                "mean_generations": sum(generations) / len(generations),
                "mean_composite": sum(composites) / len(composites),
                "mean_cpi": sum(cpis) / len(cpis),
                "pareto_count": sum(1 for item in values if item["pareto"]),
            })
        return aggregated

    def _build(self):
        runs = self._load_runs()
        subtitle = "So sánh hiệu năng, Pareto, điểm tổng hợp, Friedman rank và CPI"
        if runs:
            subtitle += f" · Tổng số lần chạy: {len(runs)}"
        section_header(self, "So sánh thuật toán", subtitle)

        if not runs:
            card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                                border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=(0, 16), padx=2)
            cmd = (lambda: self.on_switch_tab("experiments")) if self.on_switch_tab else None
            create_empty_state(
                parent=card,
                title="Chưa có dữ liệu so sánh",
                subtitle="Hãy chạy thí nghiệm để có dữ liệu so sánh.",
                action_text="Mở trang Thí nghiệm" if cmd else None,
                action_command=cmd,
                pady=28,
            )
            return

        rows = self._collect_rows(runs)
        prepared = self._prepare_rows(rows)
        friedman = self._friedman_ranks(runs)

        self._build_run_cards(runs, prepared)
        self._build_global_section(prepared, friedman)
        self._build_verdict_section(prepared, friedman)

        self.after(50, self._scroll_to_top)

    def _build_run_cards(self, runs, prepared):
        for index, run in enumerate(runs):
            card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                                border_width=1, border_color=BORDER_COLOR)
            card.pack(fill="x", pady=(0, 14), padx=2)

            run_rows = [item for item in prepared if item["run"] == index]
            ctk.CTkLabel(
                card, text=f"Lần chạy #{index + 1}",
                font=("Segoe UI", 12, "bold"), text_color=HEADER_FG,
            ).pack(anchor="w", padx=16, pady=(12, 2))

            meta_parts = [
                str(run.get("dataset", "—")),
                f"k={run.get('k', '—')}",
                str(run.get("model", "—")),
                f"R={run.get('mc', run.get('mc_val', '—'))}",
            ]
            if run.get("timestamp"):
                meta_parts.append(str(run.get("timestamp")))
            ctk.CTkLabel(
                card, text=" · ".join(meta_parts),
                font=FONT_SMALL, text_color=SUBTEXT_FG,
            ).pack(anchor="w", padx=16, pady=(0, 8))

            if not run_rows:
                ctk.CTkLabel(
                    card, text="Không có dữ liệu thuật toán cho lần chạy này.",
                    font=FONT_SMALL, text_color=SUBTEXT_FG, anchor="w",
                ).pack(fill="x", padx=16, pady=(0, 12))
                continue

            table = ctk.CTkFrame(card, fg_color="transparent")
            table.pack(fill="x", padx=12, pady=(0, 10))

            headers = [
                "Hạng", "Thuật toán", "Spread", "Time", "Std", "Gen",
                "Composite", "CPI", "Pareto",
            ]
            for column, header in enumerate(headers):
                table.grid_columnconfigure(column, weight=2 if column == 1 else 1)
                ctk.CTkLabel(
                    table, text=header, font=("Segoe UI", 9, "bold"),
                    text_color=SUBTEXT_FG,
                ).grid(row=0, column=column, padx=6, pady=(0, 6), sticky="w")

            for row_index, item in enumerate(run_rows, start=1):
                code = item["code"]
                color = RED if "iga" in code else (
                    BLUE if "celf" in code else (
                        ORANGE if "ga" in code else PURPLE
                    )
                )
                name = item["algorithm"]
                if item["baseline"]:
                    name += " (tham chiếu)"
                values = [
                    f"#{item['rank']}",
                    name,
                    f"{item['spread']:.2f}",
                    f"{item['time']:.3f}s",
                    f"{item['std']:.2f}",
                    f"{item['generations']:.0f}",
                    f"{item['composite'] * 100:.1f}%",
                    f"{item['cpi']:.2f}",
                    "Yes" if item["pareto"] else "No",
                ]
                for column, value in enumerate(values):
                    text_color = color if column == 1 else HEADER_FG
                    font = ("Segoe UI", 9, "bold") if column in (0, 1, 6) else ("Segoe UI", 9)
                    ctk.CTkLabel(
                        table, text=value, font=font,
                        text_color=text_color, anchor="w",
                    ).grid(row=row_index, column=column, padx=6, pady=4, sticky="w")

    def _build_global_section(self, prepared, friedman):
        section = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                               border_width=1, border_color=BORDER_COLOR)
        section.pack(fill="x", pady=(0, 14), padx=2)

        ctk.CTkLabel(
            section, text="Tổng hợp toàn cục",
            font=("Segoe UI", 12, "bold"), text_color=HEADER_FG,
        ).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(
            section,
            text="Trung bình theo thuật toán trên mọi lần chạy. Composite = 45% Spread + 30% Tốc độ + 15% (1-Std) + 10% Hội tụ.",
            font=FONT_SMALL, text_color=SUBTEXT_FG,
        ).pack(anchor="w", padx=16, pady=(0, 8))

        aggregated = self._aggregate(prepared)
        # Normalize aggregated metrics for a global composite score.
        if aggregated:
            spreads = [item["mean_spread"] for item in aggregated]
            times = [item["mean_time"] for item in aggregated]
            stds = [item["mean_std"] for item in aggregated]
            gens = [item["mean_generations"] for item in aggregated]
            spread_norms = _min_max_normalize(spreads)
            positive_times = [value for value in times if value > 0]
            fastest = min(positive_times) if positive_times else 0.0
            speed_norms = [
                1.0 if time_value <= 0 else (fastest / time_value if fastest > 0 else 0.0)
                for time_value in times
            ]
            std_norms = _min_max_normalize(stds)
            max_gen = max(gens) if gens else 1.0
            conv_norms = [1.0 - (gen / max_gen if max_gen > 0 else 0.0) for gen in gens]
            for index, item in enumerate(aggregated):
                item["global_composite"] = (
                    WEIGHTS["spread"] * spread_norms[index]
                    + WEIGHTS["time"] * speed_norms[index]
                    + WEIGHTS["std"] * (1.0 - std_norms[index])
                    + WEIGHTS["convergence"] * conv_norms[index]
                )
                item["global_cpi"] = 0.0
                if item["mean_time"] > 0 and item["mean_generations"] > 0:
                    item["global_cpi"] = (
                        item["mean_spread"] * (1.0 - std_norms[index])
                        / (item["mean_time"] * item["mean_generations"])
                    )
            # Pareto on aggregated means.
            for item in aggregated:
                item["pareto"] = not any(
                    other is not item
                    and other["mean_spread"] >= item["mean_spread"]
                    and other["mean_time"] <= item["mean_time"]
                    and (
                        other["mean_spread"] > item["mean_spread"]
                        or other["mean_time"] < item["mean_time"]
                    )
                    for other in aggregated
                )

        rank_map = {item["key"]: item["average_rank"] for item in friedman}

        table = ctk.CTkFrame(section, fg_color="transparent")
        table.pack(fill="x", padx=16, pady=(0, 10))

        headers = [
            "Thuật toán", "Runs", "Spread TB", "Time TB", "Std TB", "Gen TB",
            "Friedman Rank", "Composite", "CPI", "Pareto",
        ]
        for column, header in enumerate(headers):
            table.grid_columnconfigure(column, weight=2 if column == 0 else 1)
            ctk.CTkLabel(
                table, text=header, font=("Segoe UI", 9, "bold"),
                text_color=SUBTEXT_FG,
            ).grid(row=0, column=column, padx=6, pady=(0, 6), sticky="w")

        for row_index, item in enumerate(sorted(aggregated, key=lambda value: value["global_composite"], reverse=True), start=1):
            key = item["key"]
            color = RED if "iga" in key else (
                BLUE if "celf" in key else (
                    ORANGE if "ga" in key else PURPLE
                )
            )
            values = [
                item["algorithm"],
                str(item["runs"]),
                f"{item['mean_spread']:.2f}",
                f"{item['mean_time']:.3f}s",
                f"{item['mean_std']:.2f}",
                f"{item['mean_generations']:.1f}",
                f"{rank_map.get(key, 0):.2f}",
                f"{item['global_composite'] * 100:.1f}%",
                f"{item['global_cpi']:.2f}",
                "Yes" if item["pareto"] else "No",
            ]
            for column, value in enumerate(values):
                text_color = color if column == 0 else HEADER_FG
                font = ("Segoe UI", 9, "bold") if column in (0, 7) else ("Segoe UI", 9)
                ctk.CTkLabel(
                    table, text=value, font=font,
                    text_color=text_color, anchor="w",
                ).grid(row=row_index, column=column, padx=6, pady=4, sticky="w")

    def _build_verdict_section(self, prepared, friedman):
        section = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                               border_width=1, border_color=BORDER_COLOR)
        section.pack(fill="x", pady=(0, 14), padx=2)

        ctk.CTkLabel(
            section, text="Kết luận & Kiến nghị",
            font=("Segoe UI", 12, "bold"), text_color=HEADER_FG,
        ).pack(anchor="w", padx=16, pady=(12, 2))

        aggregated = self._aggregate(prepared)
        if not aggregated:
            return
        # Recompute global composite quickly.
        spreads = [item["mean_spread"] for item in aggregated]
        times = [item["mean_time"] for item in aggregated]
        stds = [item["mean_std"] for item in aggregated]
        gens = [item["mean_generations"] for item in aggregated]
        spread_norms = _min_max_normalize(spreads)
        positive_times = [value for value in times if value > 0]
        fastest = min(positive_times) if positive_times else 0.0
        speed_norms = [
            1.0 if time_value <= 0 else (fastest / time_value if fastest > 0 else 0.0)
            for time_value in times
        ]
        std_norms = _min_max_normalize(stds)
        max_gen = max(gens) if gens else 1.0
        conv_norms = [1.0 - (gen / max_gen if max_gen > 0 else 0.0) for gen in gens]
        for index, item in enumerate(aggregated):
            item["global_composite"] = (
                WEIGHTS["spread"] * spread_norms[index]
                + WEIGHTS["time"] * speed_norms[index]
                + WEIGHTS["std"] * (1.0 - std_norms[index])
                + WEIGHTS["convergence"] * conv_norms[index]
            )

        best_practical = max(aggregated, key=lambda item: item["global_composite"])
        best_academic_key = friedman[0]["key"] if friedman else best_practical["key"]
        best_academic = next(
            (item for item in aggregated if item["key"] == best_academic_key),
            best_practical,
        )

        pareto_names = ", ".join(item["algorithm"] for item in aggregated if item.get("pareto"))
        text = (
            f"Thực tế: {best_practical['algorithm']} dung hòa tốt nhất giữa tốc độ và chất lượng "
            f"(Composite {best_practical['global_composite'] * 100:.1f}%). "
            f"Hàn lâm: {best_academic['algorithm']} đạt thứ hạng thống kê tốt nhất "
            f"(Friedman rank {friedman[0]['average_rank']:.2f} nếu có). "
            f"Biên Pareto: {pareto_names or '—'}."
        )
        ctk.CTkLabel(
            section, text=text, font=FONT_SMALL,
            text_color=HEADER_FG, anchor="w", justify="left", wraplength=1100,
        ).pack(fill="x", padx=16, pady=(0, 12))

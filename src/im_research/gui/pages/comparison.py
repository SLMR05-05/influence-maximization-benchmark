#!/usr/bin/env python3
"""Comparison Page — Relative Performance Across Selected Algorithms."""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk

from im_research.gui.core.theme import *
from im_research.gui.core.ui_helpers import section_header, create_empty_state


class PageComparison(ctk.CTkScrollableFrame):
    def __init__(self, master, on_switch_tab=None, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self.on_switch_tab = on_switch_tab
        self._build()

    def _load_runs(self):
        runs_dir = PROJECT_ROOT / "runs"
        history_path = runs_dir / "results_history.json"
        latest_path = runs_dir / "latest_results.json"

        runs = []
        if history_path.exists():
            try:
                with open(history_path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                if isinstance(data, list):
                    runs = [run for run in data if isinstance(run, dict)]
            except Exception:
                runs = []

        if latest_path.exists():
            try:
                with open(latest_path, "r", encoding="utf-8") as handle:
                    latest = json.load(handle)
                if isinstance(latest, dict):
                    timestamp = latest.get("timestamp")
                    if not any(run.get("timestamp") == timestamp for run in runs):
                        runs.append(latest)
            except Exception:
                pass

        runs.sort(key=lambda run: str(run.get("timestamp", "")), reverse=True)
        return runs

    def _scroll_to_top(self):
        try:
            self._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass

    def _prepare_rows(self, rows):
        if not rows:
            return []

        spreads = [float(row.get("mean_spread", 0) or 0) for row in rows]
        times = [float(row.get("mean_time", 0) or 0) for row in rows]
        best_spread = max(spreads) if spreads else 0.0
        positive_times = [value for value in times if value > 0]
        fastest_time = min(positive_times) if positive_times else 0.0

        prepared = []
        for row, spread, mean_time in zip(rows, spreads, times):
            spread_norm = spread / best_spread if best_spread > 0 else 0.0
            if mean_time <= 0:
                speed_norm = 1.0
            elif fastest_time > 0:
                speed_norm = fastest_time / mean_time
            else:
                speed_norm = 0.0
            score = 0.7 * spread_norm + 0.3 * speed_norm
            prepared.append({
                "algorithm": row.get("algorithm", row.get("name", "N/A")),
                "code": str(row.get("code", "")).lower(),
                "spread": spread,
                "time": mean_time,
                "spread_norm": spread_norm,
                "speed_norm": speed_norm,
                "score": score,
                "baseline": bool(row.get("_baseline", False)),
            })

        prepared.sort(
            key=lambda item: (item["spread"], item["score"]),
            reverse=True,
        )
        for rank, item in enumerate(prepared, start=1):
            item["rank"] = rank
        return prepared

    def _build(self):
        runs = self._load_runs()
        subtitle = (
            "Lịch sử so sánh các thuật toán được chọn · Nếu chỉ chọn một thuật toán, "
            "Greedy / CELF được dùng làm mốc tham chiếu"
        )
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
                subtitle="Hãy chạy thí nghiệm để so sánh các thuật toán được chọn.",
                action_text="Mở trang Thí nghiệm ▶" if cmd else None,
                action_command=cmd,
                pady=28,
            )
            return

        for index, run in enumerate(runs, start=1):
            self._build_run_card(run, index)

        self.after(50, self._scroll_to_top)

    def _build_run_card(self, run, index):
        card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_COLOR)
        card.pack(fill="x", pady=(0, 14), padx=2)

        selected = run.get("summary", [])
        baseline = run.get("baseline", [])
        rows = [dict(row, _baseline=False) for row in selected]
        if (
            len(selected) == 1
            and str(selected[0].get("code", "")).lower() != "celf"
        ):
            rows.extend(dict(row, _baseline=True) for row in baseline)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            header, text=f"Lần chạy #{index}",
            font=("Segoe UI", 12, "bold"), text_color=HEADER_FG,
        ).pack(side="left")

        meta_parts = [
            str(run.get("dataset", "—")),
            f"k={run.get('k', '—')}",
            str(run.get("model", "—")),
            f"R={run.get('mc', run.get('mc_val', '—'))}",
        ]
        timestamp = run.get("timestamp")
        if timestamp:
            meta_parts.append(str(timestamp))
        ctk.CTkLabel(
            header, text=" · ".join(meta_parts),
            font=FONT_SMALL, text_color=SUBTEXT_FG,
        ).pack(side="left", padx=(12, 0))

        ctk.CTkLabel(
            header, text=f"{len(rows)} thuật toán",
            font=FONT_SMALL, text_color=SUBTEXT_FG,
        ).pack(side="right")

        if not rows:
            ctk.CTkLabel(
                card, text="Không có dữ liệu thuật toán cho lần chạy này.",
                font=FONT_SMALL, text_color=SUBTEXT_FG, anchor="w",
            ).pack(fill="x", padx=16, pady=(0, 12))
            return

        prepared = self._prepare_rows(rows)
        self._build_table_section(card, prepared, selected, baseline)
        self._build_score_section(card, prepared)

    def _build_table_section(self, parent, prepared, selected, baseline):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            section, text="Bảng so sánh trực tiếp",
            font=("Segoe UI", 11, "bold"), text_color=HEADER_FG,
        ).pack(anchor="w")
        ctk.CTkLabel(
            section,
            text="Hạng theo Spread TB. Điểm tổng hợp = 70% Spread% + 30% Tốc độ%; "
                 "Tốc độ% chuẩn hóa theo thuật toán nhanh nhất trong nhóm.",
            font=FONT_SMALL, text_color=SUBTEXT_FG,
        ).pack(anchor="w", pady=(0, 6))

        table = ctk.CTkFrame(section, fg_color="transparent")
        table.pack(fill="x")

        headers = [
            "Hạng Spread", "Thuật toán", "Spread TB", "Thời gian",
            "Spread %", "Tốc độ %", "Điểm 70/30",
        ]
        for column, header in enumerate(headers):
            table.grid_columnconfigure(
                column, weight=2 if column == 1 else 1,
            )
            ctk.CTkLabel(
                table, text=header, font=("Segoe UI", 9, "bold"),
                text_color=SUBTEXT_FG,
            ).grid(row=0, column=column, padx=8, pady=(0, 6), sticky="w")

        for index, item in enumerate(prepared, start=1):
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
                f"{item['spread_norm'] * 100:.1f}%",
                f"{item['speed_norm'] * 100:.1f}%",
                f"{item['score'] * 100:.1f}%",
            ]
            for column, value in enumerate(values):
                text_color = color if column == 1 else HEADER_FG
                font = (
                    ("Segoe UI", 10, "bold")
                    if column in (0, 1, 6)
                    else ("Segoe UI", 10)
                )
                ctk.CTkLabel(
                    table, text=value, font=font,
                    text_color=text_color, anchor="w",
                ).grid(row=index, column=column, padx=8, pady=5, sticky="w")

        note = None
        if len(selected) == 1 and str(selected[0].get("code", "")).lower() == "celf":
            note = (
                "Chỉ có Greedy / CELF được chọn; không có thuật toán khác "
                "để so sánh trong lần chạy này."
            )
        elif len(selected) == 1 and not baseline:
            note = (
                "Chưa có dữ liệu Greedy / CELF cho lần chạy này. "
                "Hãy chạy lại thí nghiệm để hệ thống tự thêm mốc tham chiếu."
            )
        elif len(selected) == 1:
            note = (
                "Chỉ chọn 1 thuật toán, nên Greedy / CELF được thêm vào "
                "làm mốc tham chiếu."
            )

        if note:
            ctk.CTkLabel(
                section, text=note, font=FONT_SMALL,
                text_color=SUBTEXT_FG, anchor="w", justify="left",
            ).pack(fill="x", pady=(6, 0))

    def _build_score_section(self, parent, prepared):
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(
            section, text="Điểm tổng hợp tham khảo (70% Spread + 30% Tốc độ)",
            font=("Segoe UI", 11, "bold"), text_color=HEADER_FG,
        ).pack(anchor="w", pady=(0, 6))

        container = ctk.CTkFrame(section, fg_color="transparent")
        container.pack(fill="x")

        for item in sorted(prepared, key=lambda value: value["score"], reverse=True):
            code = item["code"]
            color = RED if "iga" in code else (
                BLUE if "celf" in code else (
                    ORANGE if "ga" in code else PURPLE
                )
            )
            row = ctk.CTkFrame(container, fg_color="transparent")
            row.pack(fill="x", pady=4)

            name = item["algorithm"]
            if item["baseline"]:
                name += " (tham chiếu)"

            ctk.CTkLabel(
                row, text=name, width=180,
                font=("Segoe UI", 10, "bold"),
                text_color=color, anchor="w",
            ).pack(side="left")

            progress = ctk.CTkProgressBar(
                row, width=420, height=14, progress_color=color,
            )
            progress.set(max(0.0, min(1.0, item["score"])))
            progress.pack(side="left", padx=8)

            ctk.CTkLabel(
                row, text=f"{item['score'] * 100:.1f}%",
                font=("Segoe UI", 10), text_color=HEADER_FG,
            ).pack(side="left")

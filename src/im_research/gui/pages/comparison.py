#!/usr/bin/env python3
"""Comparison Page — Relative Performance & Statistical Validation."""
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

    def _build(self):
        section_header(
            self,
            "So sánh thuật toán & Kiểm định thống kê",
            "Đo lường hiệu quả tương đối và kiểm định Wilcoxon Signed-Rank Test (mức ý nghĩa α = 0.05)"
        )

        cmd = (lambda: self.on_switch_tab("experiments")) if self.on_switch_tab else None

        # ── 1. Relative Performance Bar Chart Card ─────────────────────────────
        bar_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                                border_width=1, border_color=BORDER_COLOR)
        bar_card.pack(fill="x", pady=(0, 16), padx=2)
        ctk.CTkLabel(bar_card, text="Hiệu quả lan truyền chuẩn hóa (% so với thuật toán tốt nhất)",
                     font=("Segoe UI", 12, "bold"), text_color=HEADER_FG).pack(anchor="w", padx=16, pady=(14, 6))

        results_file = PROJECT_ROOT / "runs" / "latest_results.json"
        bars = []
        if results_file.exists():
            try:
                import json
                with open(results_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                summary = data.get("summary", [])
                if summary:
                    best_spread = max(r.get("mean_spread", 1.0) for r in summary)
                    for r in summary:
                        ratio = r.get("mean_spread", 0.0) / best_spread if best_spread > 0 else 1.0
                        code = r.get("code", "").lower()
                        col = RED if "iga" in code else (BLUE if "celf" in code else (ORANGE if "ga" in code else PURPLE))
                        bars.append((r.get("algorithm", r.get("name", "N/A")), ratio, col))
            except Exception:
                bars = []

        if bars:
            chart_container = ctk.CTkFrame(bar_card, fg_color="transparent")
            chart_container.pack(fill="x", padx=16, pady=8)
            for algo, ratio, col in bars:
                row = ctk.CTkFrame(chart_container, fg_color="transparent")
                row.pack(fill="x", pady=4)
                ctk.CTkLabel(row, text=algo, width=160, font=("Segoe UI", 11, "bold"), text_color=col, anchor="w").pack(side="left")
                p_bar = ctk.CTkProgressBar(row, width=420, height=14, progress_color=col)
                p_bar.set(ratio)
                p_bar.pack(side="left", padx=8)
                ctk.CTkLabel(row, text=f"{ratio * 100:.1f}%", font=("Segoe UI", 11), text_color=HEADER_FG).pack(side="left")
            ctk.CTkFrame(bar_card, height=12, fg_color="transparent").pack()
        else:
            create_empty_state(
                parent=bar_card,
                title="Chưa có dữ liệu so sánh hiệu quả",
                subtitle="Biểu đồ so sánh phần trăm độ bao phủ giữa IGA và các thuật toán cơ sở sẽ hiển thị sau khi chạy thí nghiệm.",
                action_text="Khởi chạy thí nghiệm ▶",
                action_command=cmd,
                pady=28
            )

        # ── 2. Wilcoxon Test Summary Table Card ────────────────────────────────
        w_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER_COLOR)
        w_card.pack(fill="x", pady=(0, 16), padx=2)
        ctk.CTkLabel(w_card, text="Kiểm định cặp Wilcoxon Signed-Rank (IGA vs Baselines, α = 0.05)",
                     font=("Segoe UI", 12, "bold"), text_color=HEADER_FG).pack(anchor="w", padx=16, pady=(14, 6))

        stat_rows, stat_reason = self._wilcoxon_rows(results_file)
        if stat_rows:
            n_pairs = stat_rows[0]["n"]
            ctk.CTkLabel(
                w_card,
                text=f"Số cặp lần chạy dùng cho kiểm định: n = {n_pairs} (lấy từ details.spreads của lần chạy gần nhất)",
                font=FONT_MAIN, text_color=SUBTEXT_FG
            ).pack(anchor="w", padx=16, pady=(0, 6))

            th = ctk.CTkFrame(w_card, fg_color=("#f1f5f9", "#1e293b"), corner_radius=6)
            th.pack(fill="x", padx=12, pady=(4, 4))
            for text, width in [("Baseline", 180), ("n cặp", 70), ("W statistic", 110),
                                ("p-value", 100), ("Kết luận (α = 0.05)", 220)]:
                ctk.CTkLabel(th, text=text, font=("Segoe UI", 9, "bold"), text_color=HEADER_FG,
                             width=width, anchor="w").pack(side="left", padx=6, pady=6)

            for idx, row in enumerate(stat_rows):
                rf = ctk.CTkFrame(w_card, fg_color="transparent" if idx % 2 == 0 else ("#f8fafc", "#0d1424"),
                                  corner_radius=4)
                rf.pack(fill="x", padx=12, pady=2)
                values = [
                    (row["name"], 180, row["color"]),
                    (str(row["n"]), 70, HEADER_FG),
                    (row["stat"], 110, HEADER_FG),
                    (row["p"], 100, HEADER_FG),
                    (row["conclusion"], 220, row["conclusion_color"]),
                ]
                for value, width, color in values:
                    ctk.CTkLabel(rf, text=value, font=("Segoe UI", 9), text_color=color,
                                 width=width, anchor="w").pack(side="left", padx=6, pady=5)
            ctk.CTkFrame(w_card, height=10, fg_color="transparent").pack()
        else:
            create_empty_state(
                parent=w_card,
                title="Chưa có dữ liệu kiểm định thống kê",
                subtitle=stat_reason,
                action_text=None,
                action_command=None,
                pady=24
            )

    @staticmethod
    def _wilcoxon_rows(results_file: Path):
        """Computes a real paired Wilcoxon test from the latest run's per-run spreads."""
        if not results_file.exists():
            return [], "Chưa có runs/latest_results.json. Hãy chạy thí nghiệm để thu thập dữ liệu."

        try:
            import json
            with open(results_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return [], "Không đọc được tệp kết quả thực nghiệm."

        details = data.get("details") or {}

        def spreads_for(code: str):
            for detail in details.values():
                if str(detail.get("code", "")).lower() == code:
                    return [float(value) for value in detail.get("spreads") or []]
            return []

        iga = spreads_for("iga")
        if len(iga) < 2:
            return [], "Cần ít nhất 2 lần chạy IGA để thực hiện kiểm định cặp."

        try:
            from scipy.stats import wilcoxon
        except Exception:
            return [], "Chưa cài đặt SciPy nên không thể thực hiện kiểm định Wilcoxon."

        rows = []
        for detail in details.values():
            code = str(detail.get("code", "")).lower()
            if code == "iga":
                continue
            baseline = [float(value) for value in detail.get("spreads") or []]
            n = min(len(iga), len(baseline))
            if n < 2:
                continue

            pairs_a, pairs_b = iga[:n], baseline[:n]
            diffs = [a - b for a, b in zip(pairs_a, pairs_b)]
            if all(abs(diff) < 1e-12 for diff in diffs):
                stat_text, p_text = "—", "—"
                conclusion, color = "Không có khác biệt", SUBTEXT_FG
            else:
                try:
                    result = wilcoxon(pairs_a, pairs_b, alternative="two-sided")
                    statistic = float(result.statistic)
                    p_value = float(result.pvalue)
                    stat_text = f"{statistic:.2f}"
                    p_text = f"{p_value:.4f}"
                    if p_value < 0.05:
                        conclusion, color = "Khác biệt có ý nghĩa", GREEN
                    else:
                        conclusion, color = "Chưa đủ ý nghĩa thống kê", ORANGE
                except Exception:
                    stat_text, p_text = "—", "—"
                    conclusion, color = "Không thể kiểm định", SUBTEXT_FG

            name = next(
                (row.get("algorithm") for row in data.get("summary", [])
                 if str(row.get("code", "")).lower() == code),
                code,
            )
            rows.append({
                "name": name,
                "n": n,
                "stat": stat_text,
                "p": p_text,
                "conclusion": conclusion,
                "conclusion_color": color,
                "color": RED if code == "celf" else BLUE,
            })

        if not rows:
            return [], "Không có baseline nào đủ số lần chạy để ghép cặp với IGA."
        return rows, ""

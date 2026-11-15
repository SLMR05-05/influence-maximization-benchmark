#!/usr/bin/env python3
"""Reports Page — Export Academic Reports (LaTeX, CSV, High-DPI Charts)."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
from tkinter import messagebox, filedialog

from im_research.gui.core.theme import *
from im_research.gui.core.ui_helpers import section_header, create_empty_state


class PageReports(ctk.CTkScrollableFrame):
    def __init__(self, master, on_switch_tab=None, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self.on_switch_tab = on_switch_tab
        self._build()

    def _has_results(self) -> bool:
        runs_dir = PROJECT_ROOT / "runs"
        if not runs_dir.exists():
            return False
        return (runs_dir / "latest_results.json").exists() or bool(list(runs_dir.glob("EXP_*")))

    def _build(self):
        section_header(
            self,
            "Xuất báo cáo & Tài liệu luận văn",
            "Xuất kết quả sang các định dạng chuẩn học thuật (LaTeX, CSV, PNG biểu đồ độ phân giải cao)"
        )

        has_data = self._has_results()

        # If no experiment data, display informative empty state card
        if not has_data:
            notice_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                                       border_width=1, border_color=BORDER_COLOR)
            notice_card.pack(fill="x", pady=(0, 16))

            cmd = (lambda: self.on_switch_tab("experiments")) if self.on_switch_tab else None
            create_empty_state(
                parent=notice_card,
                title="Chưa có dữ liệu thực nghiệm để xuất báo cáo",
                subtitle="Thư mục runs/ hiện chưa có kết quả. Các chức năng xuất LaTeX, CSV và đồ thị 300 DPI sẽ sẵn sàng ngay sau khi chạy thí nghiệm.",
                action_text="Khởi chạy thí nghiệm ▶",
                action_command=cmd,
                pady=28
            )

        cards = [
            ("Bảng LaTeX chuẩn cho Luận văn", "Tạo mã nguồn LaTeX từ bảng summary thật của lần chạy gần nhất", self._export_latex),
            ("Dữ liệu kết quả thô (CSV)", "Xuất chi tiết từng lần chạy: spread, thời gian, số đánh giá và seed set", self._export_csv),
            ("Bộ biểu đồ nghiên cứu (PNG 300 DPI)", "Biểu đồ Mean Spread ± Std từ kết quả thực nghiệm", self._export_chart),
        ]

        for title, desc, fn in cards:
            c = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                             border_width=1, border_color=BORDER_COLOR)
            c.pack(fill="x", pady=6)
            inner = ctk.CTkFrame(c, fg_color="transparent")
            inner.pack(fill="x", padx=18, pady=16)
            ctk.CTkLabel(inner, text=title, font=("Segoe UI", 12, "bold"),
                         text_color=HEADER_FG).pack(side="left")
            ctk.CTkLabel(inner, text=desc, font=FONT_MAIN,
                         text_color=SUBTEXT_FG).pack(side="left", padx=16)
            ctk.CTkButton(inner, text="Xuất dữ liệu", width=120, height=32,
                          fg_color=BLUE, hover_color="#1557b0", corner_radius=6,
                          command=fn).pack(side="right")

    def _load_results(self):
        results_file = PROJECT_ROOT / "runs" / "latest_results.json"
        if not results_file.exists():
            return None
        try:
            import json
            with open(results_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    @staticmethod
    def _latex_escape(value: str) -> str:
        replacements = {
            "\\": r"\textbackslash{}",
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
        }
        return "".join(replacements.get(char, char) for char in str(value))

    def _export_latex(self):
        data = self._load_results()
        if not data:
            messagebox.showwarning("Chưa có dữ liệu", "Hệ thống chưa có kết quả thực nghiệm để xuất LaTeX!\nVui lòng thực hiện thí nghiệm trước.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".tex", filetypes=[("LaTeX File", "*.tex")])
        if not path:
            return

        summary = data.get("summary") or []
        caption = (
            f"Kết quả lan truyền trên {data.get('dataset', '—')} "
            f"với k = {data.get('k', '—')} (MC = {data.get('mc_val', '—')})"
        )
        lines = [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\caption{" + self._latex_escape(caption) + "}",
            r"\label{tab:influence_spread_results}",
            r"\begin{tabular}{lrrrr}",
            r"\toprule",
            r"Thuật toán & Mean Spread & Std & Thời gian (s) & Hạng \\",
            r"\midrule",
        ]
        for row in summary:
            lines.append(
                f"{self._latex_escape(row.get('algorithm', '—'))} & "
                f"{row.get('mean_spread', 0.0):.2f} & "
                f"{row.get('std_spread', 0.0):.2f} & "
                f"{row.get('mean_time', 0.0):.3f} & "
                f"{self._latex_escape(row.get('rank', '—'))} \\\\"
            )
        lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        messagebox.showinfo("Xuất LaTeX", f"Đã xuất bảng LaTeX thành công:\n{path}")

    def _export_csv(self):
        data = self._load_results()
        if not data:
            messagebox.showwarning("Chưa có dữ liệu", "Hệ thống chưa có kết quả thực nghiệm để xuất CSV!\nVui lòng thực hiện thí nghiệm trước.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV File", "*.csv")])
        if not path:
            return

        import csv
        details = data.get("details") or {}
        rows = []
        for algorithm, detail in details.items():
            for run in detail.get("runs_detail") or []:
                rows.append([
                    algorithm,
                    detail.get("code", ""),
                    data.get("dataset", ""),
                    data.get("k", ""),
                    data.get("mc_val", ""),
                    run.get("run", ""),
                    run.get("seed", ""),
                    run.get("spread", ""),
                    run.get("wall_time", ""),
                    run.get("search_time", ""),
                    run.get("evaluations", ""),
                    " ".join(str(node) for node in (run.get("seed_set") or [])),
                ])

        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            if rows:
                writer.writerow([
                    "algorithm", "code", "dataset", "k", "mc_val", "run", "seed",
                    "spread", "wall_time_s", "search_time_s", "evaluations", "seed_set",
                ])
                writer.writerows(rows)
            else:
                writer.writerow([
                    "algorithm", "code", "dataset", "k", "mc_val",
                    "mean_spread", "std_spread", "mean_time_s", "rank",
                ])
                for row in data.get("summary") or []:
                    writer.writerow([
                        row.get("algorithm", ""), row.get("code", ""),
                        data.get("dataset", ""), data.get("k", ""), data.get("mc_val", ""),
                        row.get("mean_spread", ""), row.get("std_spread", ""),
                        row.get("mean_time", ""), row.get("rank", ""),
                    ])
        messagebox.showinfo("Xuất CSV", f"Đã xuất tệp dữ liệu CSV thành công:\n{path}")

    def _export_chart(self):
        data = self._load_results()
        if not data:
            messagebox.showwarning("Chưa có dữ liệu", "Hệ thống chưa có kết quả thực nghiệm để tạo biểu đồ!\nVui lòng thực hiện thí nghiệm trước.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png")])
        if not path:
            return

        summary = data.get("summary") or []
        if not summary:
            messagebox.showwarning("Chưa có dữ liệu", "Tệp kết quả không chứa bảng summary.")
            return

        import matplotlib
        matplotlib.use("Agg")
        from matplotlib.figure import Figure

        names = [row.get("algorithm", "—") for row in summary]
        means = [float(row.get("mean_spread", 0.0)) for row in summary]
        stds = [float(row.get("std_spread", 0.0)) for row in summary]
        colors = ["#ef4444", "#3b82f6", "#f59e0b", "#10b981", "#8b5cf6", "#64748b"]

        fig = Figure(figsize=(8.0, 4.5), dpi=300)
        ax = fig.add_subplot(111)
        bars = ax.bar(range(len(names)), means, yerr=stds, capsize=4,
                      color=[colors[index % len(colors)] for index in range(len(names))],
                      alpha=0.85)
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=20, ha="right", fontsize=8)
        ax.set_ylabel("Mean Influence Spread")
        ax.set_title(
            f"Mean Spread trên {data.get('dataset', '—')} "
            f"(k = {data.get('k', '—')}, MC = {data.get('mc_val', '—')})",
            fontsize=10, fontweight="bold",
        )
        ax.grid(True, axis="y", linestyle="--", linewidth=0.6, alpha=0.5)
        for bar, value in zip(bars, means):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{value:.2f}", ha="center", va="bottom", fontsize=7)
        fig.tight_layout()
        fig.savefig(path, dpi=300)
        messagebox.showinfo("Xuất biểu đồ", f"Đã lưu biểu đồ PNG 300 DPI:\n{path}")

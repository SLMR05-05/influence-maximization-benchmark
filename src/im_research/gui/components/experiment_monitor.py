"""Experiment Monitor — Hiển thị kết quả thật từ runs/latest_results.json."""
import json
from pathlib import Path

import customtkinter as ctk
from tkinter import ttk

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class ExperimentMonitor(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10)
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(
            self, text="Experiment Monitor",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)

        self.table = ttk.Treeview(
            self, columns=("Algorithm", "Mean Spread", "Std", "Runs", "Time", "Rank"),
            show="headings", height=10,
        )
        for column, width in [
            ("Algorithm", 140), ("Mean Spread", 100), ("Std", 80),
            ("Runs", 70), ("Time", 90), ("Rank", 70),
        ]:
            self.table.heading(column, text=column)
            self.table.column(column, width=width)
        self.table.pack(padx=20, pady=10, fill="both", expand=True)

        self.status = ctk.CTkLabel(self, text="", text_color="gray")
        self.status.pack(pady=(0, 6))
        ctk.CTkButton(
            self, text="Làm mới từ runs/", fg_color="#2563eb", command=self.refresh
        ).pack(pady=(0, 10))
        self.refresh()

    def refresh(self):
        for item in self.table.get_children():
            self.table.delete(item)

        results_file = PROJECT_ROOT / "runs" / "latest_results.json"
        if not results_file.exists():
            self.status.configure(text="Chưa có kết quả thực nghiệm trong runs/.")
            return
        try:
            with open(results_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            self.status.configure(text="Không đọc được runs/latest_results.json.")
            return

        rows = data.get("summary") or []
        if not rows:
            self.status.configure(text="Tệp kết quả không chứa bảng summary.")
            return
        for row in rows:
            self.table.insert("", "end", values=(
                row.get("algorithm", "—"),
                f"{row.get('mean_spread', 0.0):.2f}",
                f"{row.get('std_spread', 0.0):.2f}",
                data.get("runs", "—"),
                f"{row.get('mean_time', 0.0):.3f}s",
                row.get("rank", "—"),
            ))
        self.status.configure(
            text=f"{data.get('dataset', '—')} · k = {data.get('k', '—')} · "
                 f"MC = {data.get('mc_val', '—')} · {data.get('runs', '—')} lần chạy"
        )

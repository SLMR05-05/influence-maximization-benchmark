"""Experiment Setup — Khung thiết lập thí nghiệm (CustomTkinter)."""
from pathlib import Path

import customtkinter as ctk
from tkinter import messagebox

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class ExperimentSetup(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10)
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(
            self, text="Experiment Setup — Wizard 6 Bước",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)

        steps = ["1. Dataset", "2. Diffusion", "3. Algorithms", "4. Parameters", "5. Budget", "6. Review"]
        step_bar = ctk.CTkFrame(self, fg_color="transparent")
        step_bar.pack(pady=5)
        for step in steps:
            ctk.CTkLabel(
                step_bar, text=step, font=ctk.CTkFont(size=10), fg_color="#2563eb",
                text_color="white", corner_radius=6, width=90,
            ).pack(side="left", padx=3)

        ctk.CTkLabel(
            self, text="Bước 1 — Chọn Dataset:", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 2))

        config_dir = PROJECT_ROOT / "configs" / "datasets"
        dataset_names = sorted(path.stem for path in config_dir.glob("*.yaml")) if config_dir.exists() else []
        if dataset_names:
            for name in dataset_names:
                ctk.CTkCheckBox(self, text=name).pack(anchor="w", padx=40)
        else:
            ctk.CTkLabel(self, text="Chưa tìm thấy cấu hình dataset.", text_color="gray").pack(anchor="w", padx=40)

        ctk.CTkLabel(
            self,
            text="Bước 5 — Ngân sách (k, số lần chạy, MC) được cấu hình trong trang Thí nghiệm.",
        ).pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(
            self,
            text="Bước 6 — Kiểm tra: dataset, diffusion, thuật toán, k, evaluator và seed.",
            text_color="#D97706",
        ).pack(anchor="w", padx=20, pady=5)
        ctk.CTkButton(
            self, text="Mở trang Thí nghiệm", fg_color="#16A34A",
            command=lambda: messagebox.showinfo(
                "Experiment", "Vui lòng sử dụng trang Thí nghiệm để cấu hình và khởi chạy."
            ),
        ).pack(pady=15)

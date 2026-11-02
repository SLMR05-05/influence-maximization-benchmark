"""Experiment Setup — Thiết lập thí nghiệm (CustomTkinter)"""
import customtkinter as ctk
from tkinter import messagebox

class ExperimentSetup(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10)
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self, text="Experiment Setup — Wizard 6 Bước", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        steps = ["1. Dataset", "2. Diffusion", "3. Algorithms", "4. Parameters", "5. Budget", "6. Review"]
        step_bar = ctk.CTkFrame(self, fg_color="transparent")
        step_bar.pack(pady=5)
        for s in steps:
            ctk.CTkLabel(step_bar, text=s, font=ctk.CTkFont(size=10), fg_color="#2563eb", text_color="white", corner_radius=6, width=90).pack(side="left", padx=3)
        ctk.CTkLabel(self, text="Bước 1 — Chọn Dataset:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(10,2))
        for ds in ["Karate Club", "ego-Facebook", "Email-Enron"]:
            ctk.CTkCheckBox(self, text=ds).pack(anchor="w", padx=40)
        ctk.CTkLabel(self, text="Bước 5 — Ngân Sách: k = [5,10,15,20,25,30,40,50] | Reps = 30 | R_search=200 | R_val=10,000").pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(self, text="Bước 6 — Kiểm Tra Công Bằng: ✓ Dataset ✓ Diffusion ✓ k ✓ Evaluator ⚠ Budget ✓ Seeds", text_color="#D97706").pack(anchor="w", padx=20, pady=5)
        ctk.CTkButton(self, text="Khởi Chạy Thí Nghiệm", fg_color="#16A34A", command=lambda: messagebox.showinfo("Experiment", "Experiment started.")).pack(pady=15)

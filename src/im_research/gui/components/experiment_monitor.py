"""Experiment Monitor — Theo dõi thực nghiệm (CustomTkinter)"""
import customtkinter as ctk
from tkinter import ttk

class ExperimentMonitor(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10)
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self, text="Experiment Monitor", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        table = ttk.Treeview(self, columns=("Algorithm", "Progress", "Completed", "Status", "Time"), show="headings", height=10)
        for c, w in [("Algorithm", 120), ("Progress", 80), ("Completed", 80), ("Status", 80), ("Time", 100)]:
            table.heading(c, text=c); table.column(c, width=w)
        for row in [("Degree","100%","30/30","Completed","12s"),("CELF","100%","30/30","Completed","45s"),("GA","70%","21/30","Running","210s"),("IGA","45%","13/30","Running","180s"),("PSO","0%","0/30","Queued","—")]:
            table.insert("", "end", values=row)
        table.pack(padx=20, pady=10, fill="both", expand=True)
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=10)
        ctk.CTkButton(btns, text="Retry Failed", fg_color="#D97706").pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Cancel / Halt", fg_color="#DC2626").pack(side="left", padx=5)
        ctk.CTkButton(btns, text="Resume (Checkpoint)", fg_color="#2563eb").pack(side="left", padx=5)
        ctk.CTkLabel(self, text="Checkpoints: Lưu quần thể GA/IGA, trạng thái RNG, lịch sử hội tụ.", text_color="gray").pack(pady=5)

"""Dataset Manager — Quản lý dữ liệu đồ thị (CustomTkinter)"""
import customtkinter as ctk
from tkinter import messagebox

DATASETS = [
    ("Wiki-Vote", 7115, 103689, "Directed", "Ready"),
    ("Email-Eu", 1005, 25571, "Directed", "Ready"),
    ("CA-GrQc", 5242, 14496, "Undirected", "Ready"),
    ("Karate Club", 34, 78, "Undirected", "Ready"),
    ("Dolphins", 62, 159, "Undirected", "Ready"),
]

class DatasetManager(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10)
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self, text="Dataset Manager", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="Load Dataset File", command=self.load_dataset).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Preprocess & Validate", command=self.validate).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Export CSV", command=lambda: messagebox.showinfo("Export", "File saved to runs/processed/")).pack(side="left", padx=5)

        # Table (using tkinter Treeview with customtkinter frame)
        import tkinter as tk
        from tkinter import ttk
        table = ttk.Treeview(self, columns=("Dataset", "Nodes", "Edges", "Type", "Status"), show="headings", height=12)
        for c, w in [("Dataset", 150), ("Nodes", 80), ("Edges", 80), ("Type", 100), ("Status", 80)]:
            table.heading(c, text=c); table.column(c, width=w)
        for row in DATASETS:
            table.insert("", "end", values=row)
        table.pack(padx=20, pady=10, fill="both", expand=True)

        ctk.CTkLabel(self, text="Each dataset has its own metadata file with hash, preprocessing history, and used experiments.").pack(pady=5)

    def load_dataset(self):
        messagebox.showinfo("Import", f"{len(DATASETS)} datasets available. Select one or multiple for experiment.")

    def validate(self):
        messagebox.showinfo("Validation", "Check duplicate edges, self-loops, node ID range, and directedness.")

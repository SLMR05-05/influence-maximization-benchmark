"""Data Preview & Column Mapping — Xem trước và ánh xạ cột dữ liệu"""
import customtkinter as ctk
from tkinter import ttk, messagebox
import os

class DataPreviewMapping(ctk.CTkFrame):
    def __init__(self, parent, file_path=None):
        super().__init__(parent, corner_radius=10)
        self.file_path = file_path
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self, text="Data Preview & Column Mapping", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

        # File Info Section
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(info_frame, text="File Info", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")

        info_data = [
            ("File Name", "wiki-vote.txt"),
            ("File Format", "Edge List (Text)"),
            ("Total Rows", "103,689"),
            ("Detected Columns", "3"),
            ("Encoding", "UTF-8"),
            ("Delimiter", "Tab / Space"),
        ]
        for k, v in info_data:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"{k}:", width=150, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=v, anchor="w").pack(side="left")

        # Column Mapping Section
        ctk.CTkLabel(self, text="Column Mapping", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(10,5))
        map_frame = ctk.CTkFrame(self, fg_color="transparent")
        map_frame.pack(fill="x", padx=20, pady=5)

        columns = ["Column 1", "Column 2", "Column 3"]
        mapping_options = ["Ignore", "Source Node", "Target Node", "Edge Weight", "Edge ID"]

        for i, col in enumerate(columns):
            row = ctk.CTkFrame(map_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=col, width=120, anchor="w").pack(side="left")
            combo = ctk.CTkComboBox(row, values=mapping_options, width=150)
            combo.set(mapping_options[0] if i == 0 else mapping_options[i+1] if i < len(mapping_options)-1 else "Ignore")
            combo.pack(side="left", padx=10)

        # Sample Data Preview
        ctk.CTkLabel(self, text="Sample Data (first 5 rows)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(10,5))
        table = ttk.Treeview(self, columns=("Col1", "Col2", "Col3"), show="headings", height=6)
        for c, w in [("Col1", 120), ("Col2", 120), ("Col3", 120)]:
            table.heading(c, text=c); table.column(c, width=w)
        sample = [("3", "5", "1.0"), ("5", "7", "0.5"), ("7", "9", "0.8"), ("9", "11", "0.3"), ("11", "3", "1.2")]
        for row in sample:
            table.insert("", "end", values=row)
        table.pack(padx=20, pady=5)

        # Graph Interpretation Preview
        ctk.CTkLabel(self, text="Graph Interpretation Preview", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(10,5))
        interp = [
            ("Estimated Nodes", "7,115"),
            ("Estimated Edges", "103,689"),
            ("Graph Direction", "Directed"),
            ("Weight Availability", "Yes (float)"),
        ]
        for k, v in interp:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=1)
            ctk.CTkLabel(row, text=f"{k}:", width=180, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=v, anchor="w").pack(side="left")

        # Mapping Validation
        ctk.CTkLabel(self, text="Mapping Validation", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=20, pady=(10,5))
        checks = [
            ("Source and Target mapped", True),
            ("Source/Target not same column", True),
            ("Weight data type valid", True),
            ("Required values present", True),
            ("File not empty", True),
        ]
        for label, ok in checks:
            state = "✓" if ok else "✗"
            color = "#16A34A" if ok else "#DC2626"
            ctk.CTkLabel(self, text=f"{state} {label}", text_color=color).pack(anchor="w", padx=40)

        # Actions
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=15)
        ctk.CTkButton(btn_frame, text="Save Mapping", fg_color="#2563eb").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Reset Mapping", fg_color="#64748b").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Back", fg_color="#64748b").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Continue to Validation", fg_color="#16A34A").pack(side="left", padx=5)

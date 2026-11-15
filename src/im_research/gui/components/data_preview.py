"""Data Preview & Column Mapping — Xem trước tệp dữ liệu thực do người dùng chọn."""
from pathlib import Path

import customtkinter as ctk
from tkinter import ttk


class DataPreviewMapping(ctk.CTkFrame):
    def __init__(self, parent, file_path=None):
        super().__init__(parent, corner_radius=10)
        self.file_path = file_path
        self.build_ui()

    def _read_preview(self):
        """Returns (line_count, sample_rows, column_count) for the selected file."""
        if not self.file_path:
            return 0, [], 0
        path = Path(self.file_path)
        if not path.exists() or not path.is_file():
            return 0, [], 0

        sample_rows = []
        line_count = 0
        max_columns = 0
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#") or stripped.startswith("%"):
                        continue
                    line_count += 1
                    parts = stripped.split()
                    max_columns = max(max_columns, len(parts))
                    if len(sample_rows) < 5:
                        sample_rows.append(parts)
        except Exception:
            return 0, [], 0
        return line_count, sample_rows, max_columns

    def build_ui(self):
        ctk.CTkLabel(
            self, text="Data Preview & Column Mapping",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)

        line_count, sample_rows, column_count = self._read_preview()
        path = Path(self.file_path) if self.file_path else None

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(info_frame, text="File Info", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")

        info_data = [
            ("File Name", path.name if path and path.exists() else "Chưa chọn tệp"),
            ("File Format", "Edge List (Text)" if sample_rows else "—"),
            ("Total Rows", f"{line_count:,}".replace(",", ".") if line_count else "—"),
            ("Detected Columns", str(column_count) if column_count else "—"),
            ("Encoding", "UTF-8" if sample_rows else "—"),
            ("Delimiter", "Tab / Space" if sample_rows else "—"),
        ]
        for key, value in info_data:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"{key}:", width=150, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, anchor="w").pack(side="left")

        ctk.CTkLabel(
            self, text="Column Mapping", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        map_frame = ctk.CTkFrame(self, fg_color="transparent")
        map_frame.pack(fill="x", padx=20, pady=5)

        mapping_options = ["Ignore", "Source Node", "Target Node", "Edge Weight", "Edge ID"]
        for index in range(max(column_count, 1)):
            row = ctk.CTkFrame(map_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"Column {index + 1}", width=120, anchor="w").pack(side="left")
            combo = ctk.CTkComboBox(row, values=mapping_options, width=150)
            default = "Source Node" if index == 0 else ("Target Node" if index == 1 else "Ignore")
            combo.set(default)
            combo.pack(side="left", padx=10)

        ctk.CTkLabel(
            self, text="Sample Data (first 5 rows)", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))

        columns = [f"Col{index + 1}" for index in range(max(column_count, 1))]
        table = ttk.Treeview(self, columns=columns, show="headings", height=6)
        for column in columns:
            table.heading(column, text=column)
            table.column(column, width=120)
        for row_values in sample_rows:
            padded = list(row_values[:len(columns)]) + [""] * (len(columns) - len(row_values))
            table.insert("", "end", values=padded)
        table.pack(padx=20, pady=5)

        ctk.CTkLabel(
            self, text="Graph Interpretation Preview",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        interp = [
            ("Estimated Nodes", "—"),
            ("Estimated Edges", f"{line_count:,}".replace(",", ".") if line_count else "—"),
            ("Graph Direction", "—"),
            ("Weight Availability", "—"),
        ]
        for key, value in interp:
            row = ctk.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=1)
            ctk.CTkLabel(row, text=f"{key}:", width=180, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, anchor="w").pack(side="left")

        ctk.CTkLabel(
            self, text="Mapping Validation", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        checks = [
            ("Source and Target mapped", column_count >= 2),
            ("Source/Target not same column", column_count >= 2),
            ("Weight data type valid", False if column_count == 0 else True),
            ("Required values present", bool(sample_rows)),
            ("File not empty", line_count > 0),
        ]
        for label, ok in checks:
            state = "✓" if ok else "—"
            color = "#16A34A" if ok else "#64748b"
            ctk.CTkLabel(self, text=f"{state} {label}", text_color=color).pack(anchor="w", padx=40)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=15)
        ctk.CTkLabel(
            btn_frame,
            text="Ánh xạ cột chỉ mang tính xem trước; loader dùng quy ước edge list hiện có.",
            text_color="#64748b",
        ).pack()

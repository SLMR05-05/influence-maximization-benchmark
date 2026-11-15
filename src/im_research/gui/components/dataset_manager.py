"""Dataset Manager — Kiểm tra 5 bộ dữ liệu đồ thị chuẩn có trong data/raw."""
from pathlib import Path

import customtkinter as ctk
from tkinter import messagebox

RAW_DIR = Path(__file__).resolve().parents[4] / "data" / "raw"

DATASETS = [
    ("Karate Club", 34, 78, "Vô hướng (Mạng xã hội nhỏ)", "Zachary (1977)", "karate.txt"),
    ("Dolphins", 62, 159, "Vô hướng (Mạng quan hệ xã hội)", "Lusseau (2003)", "dolphins.txt"),
    ("ego-Facebook", 4039, 88234, "Vô hướng (Mạng xã hội trực tuyến)", "SNAP [8]", "facebook.txt"),
    ("NetHEPT", 15233, 58891, "Vô hướng (Mạng đồng tác giả học thuật)", "arXiv / SNAP [15]", "nethept.txt"),
    ("Email-Enron", 36692, 183831, "Vô hướng (Mạng truyền thông email)", "SNAP [8]", "enron.txt"),
]


class DatasetManager(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10)
        self.build_ui()

    def _available_count(self) -> int:
        return sum(1 for *_, filename in DATASETS if (RAW_DIR / filename).exists())

    def build_ui(self):
        ctk.CTkLabel(
            self, text="Quản lý 5 Bộ Dữ liệu Chuẩn (Benchmark Datasets)",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=10)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_frame, text="Kiểm tra Tệp Dữ liệu Thật", command=self.load_dataset).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Xác thực Tệp (dòng/đỉnh)", command=self.validate).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Mở Thư mục data/raw", command=self.open_raw_folder).pack(side="left", padx=5)

        from tkinter import ttk
        table = ttk.Treeview(
            self, columns=("Dataset", "Nodes", "Edges", "Type", "Source", "Status"),
            show="headings", height=12,
        )
        for column, width in [
            ("Dataset", 130), ("Nodes", 70), ("Edges", 70),
            ("Type", 180), ("Source", 140), ("Status", 220),
        ]:
            table.heading(column, text=column)
            table.column(column, width=width)

        for name, nodes, edges, graph_type, source, filename in DATASETS:
            exists = (RAW_DIR / filename).exists()
            status = f"Sẵn sàng ({filename})" if exists else f"Thiếu ({filename})"
            table.insert("", "end", values=(name, nodes, edges, graph_type, source, status))
        table.pack(padx=20, pady=10, fill="both", expand=True)

        available = self._available_count()
        ctk.CTkLabel(
            self,
            text=f"{available}/{len(DATASETS)} tệp dữ liệu gốc hiện có trong data/raw.",
        ).pack(pady=5)

    def open_raw_folder(self):
        import os
        if RAW_DIR.exists():
            os.startfile(str(RAW_DIR))
        else:
            messagebox.showinfo("Thư mục", f"Đường dẫn: {RAW_DIR}")

    def load_dataset(self):
        found = [name for name, *_, filename in DATASETS if (RAW_DIR / filename).exists()]
        missing = [name for name, *_, filename in DATASETS if not (RAW_DIR / filename).exists()]
        message = f"Phát hiện {len(found)}/{len(DATASETS)} bộ dữ liệu trong {RAW_DIR}:"
        if found:
            message += "\n• " + "\n• ".join(found)
        if missing:
            message += "\n\nCòn thiếu:\n• " + "\n• ".join(missing)
        messagebox.showinfo("Dữ liệu thực nghiệm", message)

    def validate(self):
        results = []
        for name, *_, filename in DATASETS:
            path = RAW_DIR / filename
            if not path.exists():
                results.append(f"{name}: thiếu tệp")
                continue
            try:
                nodes = set()
                edges = 0
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        stripped = line.strip()
                        if not stripped or stripped.startswith("#") or stripped.startswith("%"):
                            continue
                        parts = stripped.split()
                        if len(parts) < 2:
                            continue
                        nodes.add(parts[0])
                        nodes.add(parts[1])
                        edges += 1
                results.append(f"{name}: {len(nodes)} đỉnh, {edges} cạnh")
            except Exception as exc:
                results.append(f"{name}: lỗi đọc ({exc})")
        messagebox.showinfo("Xác thực tệp dữ liệu", "\n".join(results))

#!/usr/bin/env python3
"""Page module."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.ui_helpers import section_header, metric_card
class PageExperiments(ctk.CTkScrollableFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self._log_text = None
        self._build()

    def _build(self):
        section_header(
            self,
            "Thiết lập & Khởi chạy thí nghiệm",
            "Cấu hình các tham số môi trường, chọn thuật toán và khởi chạy qua WSL2 C++ Engine"
        )

        form = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12,
                            border_width=1, border_color=BORDER_COLOR)
        form.pack(fill="x", pady=(0, 14))
        form.columnconfigure(1, weight=1)

        def make_row(lbl, r):
            ctk.CTkLabel(form, text=lbl, font=FONT_MAIN, text_color=SUBTEXT_FG,
                         anchor="w").grid(row=r, column=0, padx=16, pady=8, sticky="w")

        # Dataset Select
        make_row("Bộ dữ liệu (Graph):", 0)
        self.ds_var = ctk.StringVar(value="Karate Club")
        ctk.CTkOptionMenu(
            form, variable=self.ds_var, width=240,
            values=["Karate Club", "Dolphins", "ego-Facebook", "NetHEPT", "Email-Enron"]
        ).grid(row=0, column=1, padx=16, pady=8, sticky="w")

        # Model Select
        make_row("Mô hình lan truyền:", 1)
        self.model_var = ctk.StringVar(value="IC (Independent Cascade, p=0.1)")
        ctk.CTkOptionMenu(
            form, variable=self.model_var, width=240,
            values=["IC (Independent Cascade, p=0.1)", "LT (Linear Threshold)"]
        ).grid(row=1, column=1, padx=16, pady=8, sticky="w")

        # Seed set size k
        make_row("Kích thước tập hạt giống (k):", 2)
        self.k_var = ctk.StringVar(value="10")
        ctk.CTkEntry(form, textvariable=self.k_var, width=120).grid(
            row=2, column=1, padx=16, pady=8, sticky="w")

        # MC repetitions (Search phase)
        make_row("Số lần mô phỏng MC (Search):", 3)
        self.mc_var = ctk.StringVar(value="200")
        ctk.CTkEntry(form, textvariable=self.mc_var, width=120).grid(
            row=3, column=1, padx=16, pady=8, sticky="w")

        # Repetitions / Independent runs
        make_row("Số lần lặp độc lập (Runs):", 4)
        self.runs_var = ctk.StringVar(value="30")
        ctk.CTkEntry(form, textvariable=self.runs_var, width=120).grid(
            row=4, column=1, padx=16, pady=8, sticky="w")

        # Algorithm selection checklist
        make_row("Thuật toán thực thi:", 5)
        algo_box = ctk.CTkFrame(form, fg_color="transparent")
        algo_box.grid(row=5, column=1, padx=16, pady=8, sticky="w")

        self.algo_checks = {}
        algos = [
            ("celf", "CELF (Greedy)", True),
            ("ga", "Baseline GA", True),
            ("degree_discount", "Degree Discount", True),
            ("pagerank", "PageRank", True),
            ("degree", "Degree Centrality", True),
        ]
        for idx, (code, name, def_val) in enumerate(algos):
            var = ctk.BooleanVar(value=def_val)
            self.algo_checks[code] = var
            ctk.CTkCheckBox(algo_box, text=name, variable=var, font=FONT_MAIN,
                            text_color=HEADER_FG, checkmark_color=BLUE).grid(
                                row=idx // 3, column=idx % 3, padx=8, pady=4, sticky="w")

        # Run Button
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", pady=(4, 12))

        ctk.CTkButton(
            btn_row, text="▶  Khởi chạy thí nghiệm (Execute in WSL2)",
            font=("Segoe UI", 12, "bold"),
            fg_color=GREEN, hover_color="#137333",
            height=40, corner_radius=8,
            command=self._execute_experiment
        ).pack(side="left")

        # Execution Log Box
        section_header(self, "Nhật ký thực thi (Execution Log)", "Theo dõi tiến trình trực tiếp từ C++ OpenMP Batch Evaluator")
        self._log_text = ctk.CTkTextbox(
            self, height=220, font=FONT_MONO,
            fg_color="#1e1e24", text_color="#a6e3a1",
            border_width=1, border_color=BORDER_COLOR, corner_radius=8
        )
        self._log_text.pack(fill="x", pady=(0, 16))
        self._log("Hệ thống đã sẵn sàng. Chọn tham số và nhấn Khởi chạy thí nghiệm.")

    def _log(self, text: str):
        def _do():
            if self._log_text:
                ts = datetime.now().strftime("%H:%M:%S")
                self._log_text.configure(state="normal")
                self._log_text.insert("end", f"[{ts}] {text}\n")
                self._log_text.see("end")
                self._log_text.configure(state="disabled")
        self.after(0, _do)

    def _execute_experiment(self):
        import shutil
        wsl_bin = (
            shutil.which("wsl")
            or shutil.which("wsl.exe")
            or r"C:\Windows\System32\wsl.exe"
            or r"C:\Users\LENOVO\AppData\Local\Microsoft\WindowsApps\wsl.exe"
        )
        if not os.path.exists(wsl_bin) and not shutil.which("wsl"):
            self._log(f"❌ Không tìm thấy trình thực thi WSL tại: {wsl_bin}")
            return

        ds = self.ds_var.get()
        model_str = self.model_var.get()
        model_code = "IC" if "IC" in model_str else "LT"
        k = self.k_var.get().strip() or "10"
        mc = self.mc_var.get().strip() or "200"
        runs = self.runs_var.get().strip() or "1"
        selected = [k_algo for k_algo, v in self.algo_checks.items() if v.get()]

        clean_ds = ds.split()[0]
        self._log(f"Bắt đầu thí nghiệm: Dataset={ds}, Model={model_code}, k={k}, MC={mc}, Runs={runs}")
        self._log(f"Thuật toán tham gia: {', '.join(selected)}")
        self._log("Đang kích hoạt môi trường WSL2 & C++ OpenMP Batch Evaluator...")

        # Run in thread so GUI doesn't freeze
        import threading
        def worker():
            algo_args = " ".join(f"--algo {a}" for a in selected)
            bash_script = (
                "cd '/mnt/d/Khanh/Đồ án chuyên ngành' && "
                "source .venv/bin/activate && "
                f"python -m im_research.experiments.runner --dataset '{clean_ds}' --model {model_code} --k {k} --mc {mc} --runs {runs} {algo_args}"
            )
            cmd = [wsl_bin, "-d", "Ubuntu", "--", "bash", "-c", bash_script]
            try:
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, encoding="utf-8", errors="replace"
                )
                for line in proc.stdout:
                    text_line = line.strip()
                    if text_line:
                        self._log(text_line)
                proc.wait()
                if proc.returncode == 0:
                    self._log("✓ Thí nghiệm hoàn tất thành công! Đã lưu kết quả vào thư mục runs/")
                else:
                    self._log(f"⚠ Quá trình kết thúc với mã thoát: {proc.returncode}")
            except Exception as e:
                self._log(f"❌ Lỗi khi khởi chạy: {e}")

        threading.Thread(target=worker, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE 6: REPORTS & EXPORT

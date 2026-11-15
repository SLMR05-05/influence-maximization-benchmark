#!/usr/bin/env python3
"""Page module."""
import os
import queue
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
from im_research.gui.core.theme import *
from im_research.gui.core.tooltip import Tooltip
from im_research.gui.core.ui_helpers import section_header, metric_card
from im_research.core.diffusion_config import get_ic_config


def _to_wsl_path(windows_path: Path) -> str:
    """Converts a Windows path (e.g. D:\\Khanh\\project) to its WSL mount path (/mnt/d/Khanh/project)."""
    p = Path(windows_path).resolve()
    drive = p.drive.rstrip(":").lower()
    if not drive:
        return p.as_posix()
    rest = str(p)[len(p.drive):].replace("\\", "/")
    return f"/mnt/{drive}{rest}"


class PageExperiments(ctk.CTkScrollableFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=BG_APP, **kw)
        self._log_text = None
        self._log_queue = queue.Queue()
        self._build()
        self.after(150, self._poll_log_queue)

    def _build(self):
        self._ic_config = get_ic_config()
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
        try:
            from im_research.data.config_loader import load_all_dataset_configs
            ds_cfgs = load_all_dataset_configs()
            ds_values = [d["name"] for d in ds_cfgs] if ds_cfgs else ["Karate Club", "Dolphins", "ego-Facebook", "NetHEPT", "Email-Enron"]
        except Exception:
            ds_values = ["Karate Club", "Dolphins", "ego-Facebook", "NetHEPT", "Email-Enron"]
        self.ds_var = ctk.StringVar(value=ds_values[0] if ds_values else "Karate Club")
        self.opt_dataset = ctk.CTkOptionMenu(
            form, variable=self.ds_var, width=240,
            values=ds_values
        )
        self.opt_dataset.grid(row=0, column=1, padx=16, pady=8, sticky="w")

        # Model selector (IC or WC)
        make_row("Mô hình lan truyền:", 1)
        model_box = ctk.CTkFrame(form, fg_color="transparent")
        model_box.grid(row=1, column=1, padx=16, pady=8, sticky="w")
        curr_model = self._ic_config.get("model", "IC")
        self.model_var = ctk.StringVar(value="WC (Weighted Cascade)" if curr_model == "WC" else "IC (Independent Cascade)")
        self.opt_model = ctk.CTkOptionMenu(
            model_box,
            variable=self.model_var,
            width=240,
            values=["IC (Independent Cascade)", "WC (Weighted Cascade)"],
            command=self._on_model_change
        )
        self.opt_model.pack(anchor="w")

        self.lbl_model_info = ctk.CTkLabel(
            model_box,
            text=(
                f"p = {self._ic_config['edge_probability']:g}   ·   "
                f"R_search = {self._ic_config['mc_search']:,}   ·   "
                f"R_val = {self._ic_config['mc_validation']:,}   ·   "
                f"seed = {self._ic_config['seed_search']}/{self._ic_config['seed_validation']}"
            ),
            font=FONT_SMALL,
            text_color=SUBTEXT_FG,
            anchor="w",
        )
        self.lbl_model_info.pack(anchor="w", pady=(2, 0))

        # Seed set size k
        make_row("Kích thước tập hạt giống (k):", 2)
        self.k_var = ctk.StringVar(value="10")
        ctk.CTkEntry(form, textvariable=self.k_var, width=120).grid(
            row=2, column=1, padx=16, pady=8, sticky="w")

        # MC repetitions (Search phase)
        make_row("Số lần mô phỏng MC (Search):", 3)
        self.mc_var = ctk.StringVar(value=str(self._ic_config["mc_search"]))
        ctk.CTkEntry(form, textvariable=self.mc_var, width=120).grid(
            row=3, column=1, padx=16, pady=8, sticky="w")

        # MC repetitions (Validation phase)
        make_row("Số lần mô phỏng MC (Validation):", 4)
        self.mc_val_var = ctk.StringVar(value=str(self._ic_config["mc_validation"]))
        ctk.CTkEntry(form, textvariable=self.mc_val_var, width=120).grid(
            row=4, column=1, padx=16, pady=8, sticky="w")

        # Repetitions / Independent runs
        make_row("Số lần lặp độc lập (Runs):", 5)
        self.runs_var = ctk.StringVar(value="30")
        ctk.CTkEntry(form, textvariable=self.runs_var, width=120).grid(
            row=5, column=1, padx=16, pady=8, sticky="w")

        # Algorithm selection checklist
        make_row("Thuật toán thực thi:", 6)
        algo_box = ctk.CTkFrame(form, fg_color="transparent")
        algo_box.grid(row=6, column=1, padx=16, pady=8, sticky="w")

        self.algo_checks = {}
        algos = [
            ("iga", "IGA (Đề xuất)", True),
            ("ga", "Baseline GA", True),
            ("celf", "CELF (Greedy)", True),
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

    def _on_model_change(self, val: str):
        chosen = "WC" if "WC" in val else "IC"
        if chosen == "WC":
            self.lbl_model_info.configure(
                text=f"Xác suất cạnh: p(u->v) = 1/d_in(v)   ·   R_search = {self._ic_config['mc_search']:,}   ·   R_val = {self._ic_config['mc_validation']:,}"
            )
        else:
            self.lbl_model_info.configure(
                text=(
                    f"p = {self._ic_config['edge_probability']:g}   ·   "
                    f"R_search = {self._ic_config['mc_search']:,}   ·   "
                    f"R_val = {self._ic_config['mc_validation']:,}   ·   "
                    f"seed = {self._ic_config['seed_search']}/{self._ic_config['seed_validation']}"
                )
            )

    def _log(self, text: str):
        """Thread-safe: any thread (e.g. the WSL worker) can enqueue a log line."""
        self._log_queue.put(text)

    def _poll_log_queue(self):
        """Drains queued log lines on the Tk main thread (scheduled via after())."""
        try:
            while True:
                self._write_log(self._log_queue.get_nowait())
        except queue.Empty:
            pass
        try:
            self.after(100, self._poll_log_queue)
        except tk.TclError:
            pass

    def _write_log(self, text: str):
        if not self._log_text:
            return
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_text.configure(state="normal")
        self._log_text.insert("end", f"[{ts}] {text}\n")
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    def _execute_experiment(self):
        wsl_bin = (
            shutil.which("wsl")
            or shutil.which("wsl.exe")
            or r"C:\Windows\System32\wsl.exe"
            or r"C:\Users\LENOVO\AppData\Local\Microsoft\WindowsApps\wsl.exe"
        )
        if not wsl_bin or not os.path.exists(wsl_bin):
            self._log(f"❌ Không tìm thấy trình thực thi WSL tại: {wsl_bin}")
            return

        ds = self.ds_var.get()
        model_choice = "WC" if "WC" in self.model_var.get() else "IC"
        ic = get_ic_config()
        p = ic["edge_probability"]
        seed = ic["seed_search"]
        seed_val = ic["seed_validation"]
        k = self.k_var.get().strip() or "10"
        mc = self.mc_var.get().strip() or str(ic["mc_search"])
        mc_val = self.mc_val_var.get().strip() or str(ic["mc_validation"])
        runs = self.runs_var.get().strip() or "1"
        selected = [k_algo for k_algo, v in self.algo_checks.items() if v.get()]

        try:
            k, mc, mc_val, runs = int(k), int(mc), int(mc_val), int(runs)
        except ValueError:
            self._log("❌ k, số lần MC và số lần lặp phải là số nguyên. Kiểm tra lại cấu hình.")
            return
        if k < 1 or mc < 1 or mc_val < 1 or runs < 1:
            self._log("❌ k, số lần MC và số lần lặp phải lớn hơn 0.")
            return
        if not selected:
            self._log("❌ Chưa chọn thuật toán nào để thực thi.")
            return

        self._log(
            f"Bắt đầu thí nghiệm: Dataset={ds}, Model={model_choice}, p={p:g}, "
            f"k={k}, MC_search={mc}, MC_val={mc_val}, Runs={runs}"
        )
        self._log(f"Seed evaluator: search={seed}, validation={seed_val}")
        self._log(f"Thuật toán tham gia: {', '.join(selected)}")
        self._log("Đang kích hoạt môi trường WSL2 & C++ OpenMP Batch Evaluator...")

        # Run in thread so GUI doesn't freeze
        import threading
        project_wsl = _to_wsl_path(PROJECT_ROOT)

        def worker():
            algo_args = " ".join(f"--algo {a}" for a in selected)
            bash_script = (
                f"cd {shlex.quote(project_wsl)} && "
                "if [ -f .venv/bin/activate ]; then source .venv/bin/activate; "
                "else source ~/im_env/bin/activate; fi && "
                "export PYTHONUNBUFFERED=1 && "
                f"python -u -m im_research.experiments.runner "
                f"--dataset {shlex.quote(ds)} --model {model_choice} --p {p:g} "
                f"--k {k} --mc {mc} --mc_val {mc_val} --runs {runs} "
                f"--seed {seed} --seed_val {seed_val} {algo_args}"
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

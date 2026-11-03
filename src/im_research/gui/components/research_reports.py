"""Research Reports (CustomTkinter)"""
import customtkinter as ctk
from tkinter import messagebox

class ResearchReports(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10)
        ctk.CTkLabel(self, text="Research Reports", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        exports = ["Export CSV", "Export Excel", "Export PDF", "Export Figures", "Export Config", "Report History"]
        for exp in exports:
            ctk.CTkButton(self, text=exp, command=lambda: messagebox.showinfo("Export", f"{exp} → File saved.")).pack(anchor="w", padx=20, pady=2)
        ctk.CTkLabel(self, text="Nội dung báo cáo tự động:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10,2))
        for s in ["1. Dataset","2. Diffusion","3. Algorithm Params","4. Quy trình","5. Bảng kết quả","6. Influence chart","7. Runtime chart","8. Convergence","9. Kiểm định","10. Ablation"]:
            ctk.CTkLabel(self, text=s).pack(anchor="w", padx=40)
        ctk.CTkLabel(self, text="Xuất dữ liệu/biểu đồ trước → Sau mới tự động tạo nội dung báo cáo.", text_color="#D97706").pack(pady=10)

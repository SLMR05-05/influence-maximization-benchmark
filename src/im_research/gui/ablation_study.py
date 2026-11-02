"""Ablation Study (CustomTkinter)"""
import customtkinter as ctk
from tkinter import ttk, messagebox

class AblationStudy(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10)
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self, text="Ablation Study — Đánh Giá Thành Phần IGA", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        tree = ttk.Treeview(self, columns=("Version","Init","Mut","Div","Status"), show="headings", height=5)
        for c, w in [("Version",120),("Init",60),("Mut",60),("Div",60),("Status",80)]:
            tree.heading(c,text=c); tree.column(c,width=w)
        for v,i,m,d in [("GA (Baseline)",False,False,False),("IGA-A (+Init)",True,False,False),("IGA-B (+Mut)",False,True,False),("IGA-C (+Diversity)",False,False,True),("IGA-Full",True,True,True)]:
            tree.insert("","end",values=(v,"Yes" if i else "No","Yes" if m else "No","Yes" if d else "No","Configured"))
        tree.pack(padx=20,pady=10)
        ctk.CTkLabel(self, text="Nguyên tắc: Các phiên bản chỉ khác ở thành phần được kiểm tra;\nđiều kiện còn lại phải nhất quán.").pack(pady=10)
        ctk.CTkButton(self, text="Run Ablation Experiment", fg_color="#2563eb", command=lambda: messagebox.showinfo("Ablation","Started.")).pack(pady=10)

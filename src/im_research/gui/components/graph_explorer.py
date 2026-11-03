"""Graph Explorer (CustomTkinter)"""
import customtkinter as ctk
from tkinter import messagebox

class GraphExplorer(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10)
        ctk.CTkLabel(self, text="Graph Explorer — Khám Phá Mạng Lưới", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        ctk.CTkLabel(self, text="Phóng to / thu nhỏ / di chuyển đồ thị. Tìm kiếm node theo ID. Hiển thị degree, neighbors.").pack()
        ctk.CTkLabel(self, text="Cảnh báo: Không render toàn bộ đồ thị lớn trực tiếp.\nSử dụng sampling / subgraph / vùng lân cận.", text_color="#D97706").pack(pady=10)
        ctk.CTkButton(self, text="Load Subgraph (Sample)", command=lambda: messagebox.showinfo("Explorer","Showing sampled subgraph with selected seed nodes marked.")).pack(pady=10)

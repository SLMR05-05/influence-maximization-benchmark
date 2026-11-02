"""Dashboard — Tổng quan nghiên cứu (CustomTkinter)"""
import customtkinter as ctk

class Dashboard(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10)
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self, text="Tổng Quan Nghiên Cứu", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        cards = ["Total Experiments", "Completed Runs", "Avg Runtime", "Best Spread", "Active Experiments", "Last Experiment"]
        for c in cards:
            ctk.CTkLabel(self, text=f"{c}: 0", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=2)

        # Recent experiments
        ctk.CTkLabel(self, text="Recent Experiments", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10,2))
        ctk.CTkLabel(self, text="  Mới nhất sẽ hiển thị ở đây...").pack(anchor="w", padx=20)

        # Best Results
        ctk.CTkLabel(self, text="Best Results", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10,2))
        ctk.CTkLabel(self, text="  Chọn experiment để xem kết quả tốt nhất").pack(anchor="w", padx=20)

        # Execution Status
        ctk.CTkLabel(self, text="Execution Status", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10,2))
        ctk.CTkLabel(self, text="  S (running: 0 | completed: 0 | failed: 0)").pack(anchor="w", padx=20)

        # System Resources
        ctk.CTkLabel(self, text="System Resources", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=20, pady=(10,2))
        ctk.CTkLabel(self, text="  CPU: Ready | RAM: Active | C++ Engine: Ready").pack(anchor="w", padx=20)

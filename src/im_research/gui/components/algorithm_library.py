"""Algorithm Library — Danh sách thuật toán thực có trong dự án (CustomTkinter)"""
import customtkinter as ctk

ALGORITHMS = {
    "Heuristic": ["Degree Centrality", "Degree Discount", "PageRank"],
    "Greedy": ["CELF"],
    "Evolutionary": ["Baseline GA", "IGA"],
}


class AlgorithmLibrary(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10)
        self.build_ui()

    def build_ui(self):
        ctk.CTkLabel(self, text="Algorithm Library", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        self.group_var = ctk.StringVar(value="Heuristic")
        group_frame = ctk.CTkFrame(self, fg_color="transparent")
        group_frame.pack(fill="x", padx=20, pady=5)
        for group in ALGORITHMS:
            ctk.CTkRadioButton(
                group_frame, text=group, variable=self.group_var, value=group
            ).pack(side="left", padx=8)

        ctk.CTkLabel(
            self, text="IGA Configurable Components",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))
        components = [
            "Population Init", "Selection", "Crossover", "Mutation",
            "Diversity", "Elitism", "Termination",
        ]
        for comp in components:
            ctk.CTkLabel(self, text=f"  • {comp}", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=30)

        ctk.CTkLabel(
            self,
            text="Công cụ: Không chỉnh sửa mã nguồn trực tiếp trong giao diện này.\n"
                 "Phát triển mã nguồn vẫn thuộc workspace lập trình.",
            text_color="gray",
        ).pack(pady=10)

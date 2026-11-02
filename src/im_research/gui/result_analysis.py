"""Result Analysis — 5 tabs (CustomTkinter)"""
import customtkinter as ctk
from tkinter import ttk, messagebox

class ResultAnalysis(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=10)
        self.build_tabs()

    def build_tabs(self):
        ctk.CTkLabel(self, text="Result Analysis — 5 Tab", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab A
        a = ctk.CTkFrame(nb)
        nb.add(a, text="A. Performance Overview")
        tree = ttk.Treeview(a, columns=("Algorithm","Best","Mean","Std","Runtime"), show="headings", height=6)
        for c, w in [("Algorithm",120),("Best",80),("Mean",80),("Std",60),("Runtime",100)]:
            tree.heading(c,text=c); tree.column(c,width=w)
        for row in [("Degree","—","—","—","—"),("CELF","—","—","—","—"),("GA","—","—","—","—"),("IGA","—","—","—","—")]:
            tree.insert("","end",values=row)
        tree.pack(padx=10,pady=10)

        # Tab B
        b = ctk.CTkFrame(nb)
        nb.add(b, text="B. Influence Comparison")
        ctk.CTkLabel(b, text="Influence Spread theo k — Chọn dataset + diffusion + thuật toán").pack()
        ctk.CTkButton(b, text="Generate Chart", command=lambda: messagebox.showinfo("Chart","Generated.")).pack(pady=10)

        # Tab C
        c = ctk.CTkFrame(nb)
        nb.add(c, text="C. Runtime Comparison")
        ctk.CTkLabel(c, text="Total / Search / Evaluation Runtime + #Fitness Evaluations + #Diffusion Sims").pack()

        # Tab D
        d = ctk.CTkFrame(nb)
        nb.add(d, text="D. Convergence")
        ctk.CTkLabel(d, text="Trục X: Iterations / Evaluations / Time | Trục Y: Best-so-far Influence Spread").pack()
        ctk.CTkLabel(d, text="Cho phép đánh giá IGA hội tụ nhanh hơn GA.").pack(pady=5)

        # Tab E
        e = ctk.CTkFrame(nb)
        nb.add(e, text="E. Statistical")
        ctk.CTkLabel(e, text="Wilcoxon / Friedman / Holm / Effect Size / CI / Ranking").pack()
        ctk.CTkLabel(e, text="Kết quả phải từ quan sát thực nghiệm ghép cặp — không lấy Mean trực tiếp.").pack(pady=5)

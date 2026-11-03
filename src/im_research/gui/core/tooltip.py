#!/usr/bin/env python3
"""Tooltip helper."""
import tkinter as tk
import customtkinter as ctk
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tw:
            return
        x = self.widget.winfo_rootx() + 68
        y = self.widget.winfo_rooty() + 8
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        self.tw.attributes("-topmost", True)
        frame = tk.Frame(self.tw, bg="#202124", padx=10, pady=5)
        frame.pack()
        lbl = tk.Label(
            frame, text=self.text, bg="#202124", fg="#ffffff",
            font=("Segoe UI", 9, "bold"), relief="flat"
        )
        lbl.pack()

    def hide(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None


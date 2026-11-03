#!/usr/bin/env python3
"""
Tooltip helper with debounce delay and anti-flicker coordinate positioning.
Prevents tooltip window from spawning under cursor and causing enter/leave loops.
"""

import tkinter as tk
import customtkinter as ctk


class Tooltip:
    def __init__(self, widget, text: str, delay_ms: int = 400):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.tw = None
        self._timer_id = None

        # Use add="+" to preserve existing CustomTkinter hover bindings
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, event=None):
        self._cancel_timer()
        # Debounce: only show after cursor pauses on widget
        self._timer_id = self.widget.after(self.delay_ms, self.show)

    def _on_leave(self, event=None):
        self._cancel_timer()
        self.hide()

    def _cancel_timer(self):
        if self._timer_id is not None:
            try:
                self.widget.after_cancel(self._timer_id)
            except Exception:
                pass
            self._timer_id = None

    def show(self):
        if self.tw or not self.widget.winfo_exists():
            return

        try:
            wx = self.widget.winfo_rootx()
            wy = self.widget.winfo_rooty()
            ww = self.widget.winfo_width()
            wh = self.widget.winfo_height()
        except Exception:
            return

        # Position safely outside the widget bounds so the mouse cursor never touches it
        screen_w = self.widget.winfo_screenwidth()
        screen_h = self.widget.winfo_screenheight()

        # If widget is part of a sidebar (tall, on the left): position 10px to the right
        if wx < 300 and ww < 350:
            x = wx + ww + 10
            y = wy + max(0, (wh - 26) // 2)
        else:
            # Place below widget
            x = wx + 8
            y = wy + wh + 6

        # Boundary checks
        if x + 180 > screen_w:
            x = max(10, screen_w - 200)
        if y + 40 > screen_h:
            y = max(10, wy - 30)

        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        self.tw.attributes("-topmost", True)

        frame = tk.Frame(
            self.tw,
            bg="#0f172a",
            padx=8,
            pady=4,
            highlightthickness=1,
            highlightbackground="#334155"
        )
        frame.pack()

        lbl = tk.Label(
            frame,
            text=self.text,
            bg="#0f172a",
            fg="#f8fafc",
            font=("Segoe UI", 8, "bold"),
            relief="flat"
        )
        lbl.pack()

    def hide(self, event=None):
        self._cancel_timer()
        if self.tw:
            try:
                self.tw.destroy()
            except Exception:
                pass
            self.tw = None

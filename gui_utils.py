"""
gui_utils.py
------------
Übergreifende Hilfsklassen und Funktionen für die grafische Oberfläche.
"""
import tkinter as tk

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)

    def enter(self, event=None):
        self.id = self.widget.after(500, self.showtip)

    def leave(self, event=None):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

    def showtip(self, event=None):
        if self.tipwindow: return
        
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tipwindow = tk.Toplevel(self.widget)
        self.tipwindow.wm_overrideredirect(True)
        self.tipwindow.wm_geometry(f"+{x}+{y}")
        self.tipwindow.attributes("-topmost", True)
        
        label = tk.Label(self.tipwindow, text=self.text, justify="left",
                         background="#2b2b2b", foreground="white", 
                         relief="solid", borderwidth=1,
                         font=("Helvetica", 10), padx=8, pady=5)
        label.pack()

def create_tooltip(widget, text):
    ToolTip(widget, text)
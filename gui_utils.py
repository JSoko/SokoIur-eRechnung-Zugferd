"""
gui_utils.py
------------
Übergreifende Hilfsklassen und Funktionen für die grafische Oberfläche.
"""
import tkinter as tk


class ToolTip:
    def __init__(self, widget, text, font=("Helvetica", 10)):
        self.widget = widget
        self.text = text
        self.font = font
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
        if self.tipwindow:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tipwindow = tk.Toplevel(self.widget)
        self.tipwindow.wm_overrideredirect(True)
        self.tipwindow.wm_geometry(f"+{x}+{y}")
        self.tipwindow.attributes("-topmost", True)

        label = tk.Label(
            self.tipwindow,
            text=self.text,
            justify="left",
            background="#2b2b2b",
            foreground="white",
            relief="solid",
            borderwidth=1,
            font=self.font,
            padx=10,
            pady=7,
        )
        label.pack()


def create_tooltip(widget, text, font=("Helvetica", 10)):
    ToolTip(widget, text, font=font)

def update_scrollable_visibility(scroll_frame):
    """Blendet die vertikale Scrollbar eines CTkScrollableFrame nur bei echtem Scrollbedarf ein."""
    if not scroll_frame or not hasattr(scroll_frame, "_parent_canvas") or not hasattr(scroll_frame, "_scrollbar"):
        return
    try:
        if not scroll_frame.winfo_exists():
            return
        scroll_frame.update_idletasks()
        canvas = scroll_frame._parent_canvas
        scrollbar = scroll_frame._scrollbar

        bbox = canvas.bbox("all")
        if not bbox:
            if scrollbar.winfo_ismapped():
                scrollbar.grid_remove()
            return

        content_height = bbox[3] - bbox[1]
        visible_height = canvas.winfo_height()

        if visible_height <= 1:
            return

        if content_height > visible_height + 2:
            if not scrollbar.winfo_ismapped():
                scrollbar.grid()
        else:
            if scrollbar.winfo_ismapped():
                scrollbar.grid_remove()
    except Exception:
        pass


def setup_auto_scrollbar(scroll_frame):
    """Bindet Größenänderungen von Container und Inhalt an die automatische Scrollbar-Sichtbarkeit."""
    if not scroll_frame:
        return

    def _schedule(_event=None):
        try:
            if scroll_frame.winfo_exists():
                scroll_frame.after_idle(lambda: update_scrollable_visibility(scroll_frame))
        except Exception:
            pass

    scroll_frame.bind("<Configure>", _schedule, add="+")
    if hasattr(scroll_frame, "_parent_frame"):
        scroll_frame._parent_frame.bind("<Configure>", _schedule, add="+")
    _schedule()
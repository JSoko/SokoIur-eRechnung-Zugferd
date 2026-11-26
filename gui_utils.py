"""
gui_utils.py
------------
Übergreifende Hilfsklassen und Funktionen für die grafische Oberfläche.
"""
import tkinter as tk

_updating_scrollbars = set()


class ToolTip:
    def __init__(self, widget, text, font=("Helvetica", 10)):
        self.widget = widget
        self.text = text
        self.font = font
        self.tipwindow = None
        self.id = None
        self.widget.bind(chr(60) + "Enter" + chr(62), self.enter)
        self.widget.bind(chr(60) + "Leave" + chr(62), self.leave)
        self.widget.bind(chr(60) + "ButtonPress" + chr(62), self.leave)

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


def _hide_scrollbar(scrollbar):
    try:
        if scrollbar and scrollbar.winfo_exists() and scrollbar.winfo_ismapped():
            scrollbar.grid_remove()
    except Exception:
        pass


def _place_scrollbar_right(scroll_frame, scrollbar):
    try:
        if not scrollbar or not scrollbar.winfo_exists():
            return
        scroll_frame.grid_columnconfigure(0, weight=1)
        scroll_frame.grid_columnconfigure(1, weight=0)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(2, 0), pady=0)
        scrollbar.lift()
    except Exception:
        pass


def _get_real_content_height(scroll_frame, canvas) -> int:
    parent_frame = getattr(scroll_frame, "_parent_frame", None)
    if not parent_frame or not parent_frame.winfo_exists():
        return 0

    children = [
        w for w in parent_frame.winfo_children()
        if w.winfo_exists() and w.winfo_manager()
    ]
    if not children:
        return 0

    max_bottom = 0
    for w in children:
        try:
            y = int(w.winfo_y() or 0)
            h = int(w.winfo_reqheight() or w.winfo_height() or 0)
            if y + h > max_bottom:
                max_bottom = y + h
        except Exception:
            pass

    if max_bottom > 0:
        return max_bottom

    try:
        bbox = canvas.bbox("all")
        if bbox:
            return max(0, int(bbox[3] - bbox[1]))
    except Exception:
        pass
    return 0


def update_scrollable_visibility(scroll_frame, buffer_px: int = 8):
    if (
        not scroll_frame
        or not hasattr(scroll_frame, "_parent_canvas")
        or not hasattr(scroll_frame, "_scrollbar")
    ):
        return

    frame_id = id(scroll_frame)
    if frame_id in _updating_scrollbars:
        return

    _updating_scrollbars.add(frame_id)
    try:
        if not scroll_frame.winfo_exists():
            return

        canvas = scroll_frame._parent_canvas
        scrollbar = scroll_frame._scrollbar

        if not canvas.winfo_exists() or not scrollbar.winfo_exists():
            return

        if not scroll_frame.winfo_ismapped() or not canvas.winfo_ismapped():
            _hide_scrollbar(scrollbar)
            return

        parent_frame = getattr(scroll_frame, "_parent_frame", None)
        children = (
            [w for w in parent_frame.winfo_children() if w.winfo_exists() and w.winfo_manager()]
            if parent_frame and parent_frame.winfo_exists()
            else []
        )
        if not children:
            _hide_scrollbar(scrollbar)
            return

        visible_height = int(canvas.winfo_height() or 0)
        if visible_height <= 2:
            _hide_scrollbar(scrollbar)
            return

        content_height = _get_real_content_height(scroll_frame, canvas)
        if content_height <= 0:
            _hide_scrollbar(scrollbar)
            return

        if content_height > visible_height + buffer_px:
            _place_scrollbar_right(scroll_frame, scrollbar)
        else:
            _hide_scrollbar(scrollbar)
    except Exception:
        pass
    finally:
        _updating_scrollbars.discard(frame_id)


def setup_auto_scrollbar(scroll_frame, buffer_px: int = 8):
    if (
        not scroll_frame
        or not hasattr(scroll_frame, "_parent_canvas")
        or not hasattr(scroll_frame, "_scrollbar")
    ):
        return

    timer_id = {"after": None}

    def _run_debounced():
        timer_id["after"] = None
        if scroll_frame.winfo_exists():
            update_scrollable_visibility(scroll_frame, buffer_px=buffer_px)

    def _schedule(_event=None):
        if id(scroll_frame) in _updating_scrollbars:
            return
        try:
            if not scroll_frame.winfo_exists():
                return
            if timer_id["after"] is not None:
                scroll_frame.after_cancel(timer_id["after"])
            timer_id["after"] = scroll_frame.after(40, _run_debounced)
        except Exception:
            pass

    ev_configure = chr(60) + "Configure" + chr(62)
    ev_visibility = chr(60) + "Visibility" + chr(62)
    ev_map = chr(60) + "Map" + chr(62)

    scroll_frame.bind(ev_configure, _schedule, add="+")
    scroll_frame.bind(ev_visibility, _schedule, add="+")
    scroll_frame.bind(ev_map, _schedule, add="+")

    if hasattr(scroll_frame, "_parent_frame") and scroll_frame._parent_frame:
        scroll_frame._parent_frame.bind(ev_configure, _schedule, add="+")

    if hasattr(scroll_frame, "_parent_canvas") and scroll_frame._parent_canvas:
        scroll_frame._parent_canvas.bind(ev_configure, _schedule, add="+")

    scroll_frame.after(80, _run_debounced)

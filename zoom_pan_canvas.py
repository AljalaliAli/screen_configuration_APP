# zoom_pan_canvas.py  – complete updated file
import tkinter as tk
from PIL import Image, ImageTk


class ZoomPanCanvas(tk.Canvas):
    """
    Canvas with
        • wheel zoom (bitmap + overlays),
        • pan with middle / right button,
        • OR Space-bar + left-drag,
        • automatic scroll-region update.
    """

    # ───────────────────────────── init ─────────────────────────────
    def __init__(self, master, **kw):
        super().__init__(master, **kw)

        # public
        self.scale_factor  = 1.0
        self.img_on_canvas = None           # canvas image handle

        # private
        self._img_orig     = None           # pristine PIL.Image
        self._img_tk       = None           # PhotoImage actually shown
        self._dragging     = False
        self._space_down   = False          # <space> pressed?

        # wheel-zoom bindings (cross-platform)
        self.bind("<Control-MouseWheel>", self._on_zoom)    # Win / X11
        self.bind("<MouseWheel>",          self._on_zoom)    # macOS
        self.bind("<Button-4>",            self._on_zoom)    # X11 ↑
        self.bind("<Button-5>",            self._on_zoom)    # X11 ↓

        # middle- / right-button panning
        for b in (2, 3):
            self.bind(f"<ButtonPress-{b}>",  self._pan_start)
            self.bind(f"<B{b}-Motion>",      self._pan_move)
            self.bind(f"<ButtonRelease-{b}>",self._pan_end)

        # space + left-button panning  (common in image editors)
        self.bind_all("<KeyPress-space>",        self._space_press)
        self.bind_all("<KeyRelease-space>",      self._space_release)
        self.bind("<ButtonPress-1>",             self._maybe_pan_start)
        self.bind("<B1-Motion>",                 self._maybe_pan_move)
        self.bind("<ButtonRelease-1>",           self._maybe_pan_end)

    # ─────────────────────── public API ────────────────────────────
    def show_pil_image(self, pil_img):
        """Display PIL.Image and reset zoom/pan."""
        self.delete("all")
        self.scale_factor  = 1.0
        self._img_orig     = pil_img.copy()
        self._rebuild_tk_image()
        self.img_on_canvas = self.create_image(
            0, 0, image=self._img_tk, anchor="nw", tags=("bg",)
        )
        self._update_scroll_region()

    def clear_all(self):
        self.delete("all")
        self.scale_factor  = 1.0
        self._img_orig     = None
        self._img_tk       = None
        self.img_on_canvas = None
        self.config(scrollregion=(0, 0, 0, 0))

    # ────────────────────── wheel ZOOM ─────────────────────────────
    def _on_zoom(self, event):
        if self._img_orig is None:
            return

        # normalise wheel delta
        delta = 120 if (getattr(event, 'num', 0) == 4) else \
               -120 if (getattr(event, 'num', 0) == 5) else event.delta
        if delta == 0:
            return

        zoom       = 1.1 if delta > 0 else 1 / 1.1
        new_scale  = self.scale_factor * zoom
        if not (0.1 <= new_scale <= 10):
            return                                    # clamp

        cx, cy = self.canvasx(event.x), self.canvasy(event.y)

        # 1) scale vector overlays
        self.scale("overlay", cx, cy, zoom, zoom)

        # 2) rebuild raster at new resolution
        self.scale_factor = new_scale
        self._rebuild_tk_image()
        self.itemconfigure(self.img_on_canvas, image=self._img_tk)

        # move bitmap anchor to keep cursor fixed
        self.scale("bg", cx, cy, zoom, zoom)

        # optional: keep rectangle borders readable
        for rid in self.find_withtag("rect_border"):
            self.itemconfig(rid, width=max(1, 2 / self.scale_factor))

        self._update_scroll_region()

    def _rebuild_tk_image(self):
        w = int(self._img_orig.width  * self.scale_factor)
        h = int(self._img_orig.height * self.scale_factor)
        if w < 1 or h < 1:
            return
        self._img_tk = ImageTk.PhotoImage(self._img_orig.resize((w, h),
                                                                Image.LANCZOS))

    # ──────────────────────── panning ──────────────────────────────
    # middle / right buttons
    def _pan_start(self, ev):
        self.scan_mark(ev.x, ev.y)
        self._dragging = True
        self.config(cursor="fleur")

    def _pan_move(self, ev):
        if self._dragging:
            self.scan_dragto(ev.x, ev.y, gain=1)

    def _pan_end(self, _):
        self._dragging = False
        self.config(cursor="")

    # space + left button
    def _space_press(self, *_):
        self._space_down = True

    def _space_release(self, *_):
        self._space_down = False
        if not self._dragging:
            self.config(cursor="")

    def _maybe_pan_start(self, ev):
        if self._space_down:
            self._pan_start(ev)

    def _maybe_pan_move(self, ev):
        if self._dragging:
            self._pan_move(ev)

    def _maybe_pan_end(self, ev):
        if self._dragging:
            self._pan_end(ev)

    # ─────────────────────── helpers ───────────────────────────────
    def _update_scroll_region(self):
        bbox = self.bbox("all")
        if bbox:
            self.config(scrollregion=bbox)

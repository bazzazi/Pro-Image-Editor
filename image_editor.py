# -*- coding: utf-8 -*-
# =============================================================================
#  ____             ___                            _____    _ _ _
# |  _ \ _ __ ___  |_ _|_ __ ___   __ _  __ _  __| ____|__| (_) |_ ___  _ __
# | |_) | '__/ _ \  | || '_ ` _ \ / _` |/ _` |/ _ \  _| / _` | | __/ _ \| '__|
# |  __/| | | (_) | | || | | | | | (_| | (_| |  __/ |__| (_| | | || (_) | |
# |_|   |_|  \___/ |___|_| |_| |_|\__,_|\__, |\___|_____\__,_|_|\__\___/|_|
#                                       |___/
# -----------------------------------------------------------------------------
#  Pro Image Editor  v3.0 — a modern, professional desktop image editor
#  Windows-first, cross-platform (Python 3.10+, Tkinter + Pillow)
# -----------------------------------------------------------------------------
#
#  Developer / توسعه دهنده : Mohammad Ali Bazzazi  ·  محمدعلی بزازی
#  Website  / وب‌سایت        : https://mohammadalibazzazi.ir
#
#  © 2026 Mohammad Ali Bazzazi — All rights reserved.
# =============================================================================
"""
Pro Image Editor v3.0
=====================
Major new features over v2:
  • Object system for TEXT and SHAPES (rect / ellipse / line / arrow):
      – Click-drag to move
      – 8 handles to resize, dedicated handle to rotate
      – Double-click text to edit its content
      – Live property panel: font family, size, color, bold / italic,
        outline, shadow, opacity, rotation, alignment
      – Delete / Duplicate / Bring-to-front / Send-to-back
      – Arrow keys nudge selected object (Shift = 10px)
  • Selection tool with marquee, per-object handles, snapping to grid
  • Filters: Gaussian Blur, Box Blur, Sharpen, Emboss, Contour, Find Edges,
    Smooth, Sepia, Vignette, Posterize, Solarize, Auto-Contrast, Equalize
  • Adjustments: Hue shift, Temperature/Tint, Gamma, plus v2 ones
  • Eraser tool (transparent) and Eyedropper (pick color) and Bucket fill
  • Histogram viewer  ·  Grid + Rulers overlay  ·  Zoom-under-cursor
  • New blank image  ·  Add border  ·  Watermark (text/tile)
  • Crop presets 1:1 / 4:3 / 16:9 / 3:2 / 9:16 + rule-of-thirds overlay
  • Clipboard: copy image, paste image (from OS clipboard) as new layer
  • Drag-and-drop files onto the window
  • Recent files menu (persisted between sessions)
  • Export to PDF; smart compression to a target file size (KB)
  • Auto-save option (every N minutes into user data dir)
  • Rich keyboard shortcuts and status bar hints

Run:
    python image_editor.py
"""

from __future__ import annotations

import io
import json
import math
import os
import platform
import time
import uuid
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox, simpledialog
from typing import Optional, Any

from PIL import (
    Image, ImageTk, ImageDraw, ImageFont, ImageOps, ImageEnhance,
    ImageChops, ImageFilter, ImageGrab,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
APP_NAME       = "Pro Image Editor"
APP_VERSION    = "1.0"
APP_AUTHOR     = "Mohammad Ali Bazzazi"
APP_AUTHOR_FA  = "محمدعلی بزازی"
APP_WEBSITE    = "https://mohammadalibazzazi.ir"
APP_GITHUB     = "https://github.com/bazzazi"
APP_LINKEDIN   = "https://www.linkedin.com/in/bazzazi/"
APP_COPYRIGHT  = "© 2026 Mohammad Ali Bazzazi — All rights reserved."


SUPPORTED_OPEN = [
    ("All images", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp *.ico"),
    ("PNG",  "*.png"),
    ("JPEG", "*.jpg *.jpeg"),
    ("BMP",  "*.bmp"),
    ("GIF",  "*.gif"),
    ("TIFF", "*.tif *.tiff"),
    ("WEBP", "*.webp"),
    ("ICO",  "*.ico"),
    ("All files", "*.*"),
]

EXT_TO_FMT = {
    ".png":  "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".bmp": "BMP",
    ".gif":  "GIF", ".tif": "TIFF", ".tiff": "TIFF", ".webp": "WEBP",
    ".ico":  "ICO", ".pdf": "PDF",
}

SAVE_FILETYPES = [
    ("PNG  (lossless)",                "*.png"),
    ("JPEG (visually lossless q=100)", "*.jpg"),
    ("WEBP (lossless)",                "*.webp"),
    ("TIFF (LZW lossless)",            "*.tiff"),
    ("BMP  (uncompressed)",            "*.bmp"),
    ("GIF",                            "*.gif"),
    ("ICO (Windows icon)",             "*.ico"),
    ("PDF",                            "*.pdf"),
]

# UI theme
BG           = "#15161c"
BG_PANEL     = "#1e1f27"
BG_PANEL_ALT = "#262832"
FG           = "#e8eaf0"
FG_MUTED     = "#8b8fa3"
ACCENT       = "#4f8cff"
ACCENT_HOVER = "#3a75e6"
DANGER       = "#ff4f6a"
HANDLE_FILL  = "#ffffff"
HANDLE_OUT   = "#4f8cff"

RECENT_MAX = 10

# App data dir (settings + autosave)
if platform.system() == "Windows":
    APP_DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                                "ProImageEditor")
elif platform.system() == "Darwin":
    APP_DATA_DIR = os.path.expanduser("~/Library/Application Support/ProImageEditor")
else:
    APP_DATA_DIR = os.path.join(
        os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")),
        "ProImageEditor")
os.makedirs(APP_DATA_DIR, exist_ok=True)
SETTINGS_PATH = os.path.join(APP_DATA_DIR, "settings.json")
AUTOSAVE_DIR  = os.path.join(APP_DATA_DIR, "autosave")
os.makedirs(AUTOSAVE_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def hex_to_rgba(hx: str, alpha: int = 255) -> tuple[int, int, int, int]:
    hx = hx.lstrip("#")
    if len(hx) == 3:
        hx = "".join(c * 2 for c in hx)
    r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
    return (r, g, b, alpha)


def rgba_to_hex(rgba) -> str:
    return "#{:02x}{:02x}{:02x}".format(int(rgba[0]), int(rgba[1]), int(rgba[2]))


def load_settings() -> dict:
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(data: dict) -> None:
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Objects (vector overlay layer)
# ---------------------------------------------------------------------------
class BaseObject:
    """Base class for editable overlay objects."""
    kind = "base"

    def __init__(self) -> None:
        self.id: str = uuid.uuid4().hex[:8]
        self.x: float = 0.0        # top-left of bounding box (image coords)
        self.y: float = 0.0
        self.w: float = 100.0
        self.h: float = 100.0
        self.rotation: float = 0.0  # degrees
        self.opacity: int = 255     # 0..255
        self.visible: bool = True
        self.locked: bool = False
        self.name: str = self.kind

    # ---- geometry ----
    def center(self) -> tuple[float, float]:
        return (self.x + self.w / 2, self.y + self.h / 2)

    def bbox(self) -> tuple[float, float, float, float]:
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    def move(self, dx: float, dy: float) -> None:
        self.x += dx
        self.y += dy

    def hit_test(self, px: float, py: float, margin: float = 0.0) -> bool:
        """Point-in-oriented-bbox test."""
        cx, cy = self.center()
        ang = -math.radians(self.rotation)
        cos_a, sin_a = math.cos(ang), math.sin(ang)
        lx = (px - cx) * cos_a - (py - cy) * sin_a + self.w / 2
        ly = (px - cx) * sin_a + (py - cy) * cos_a + self.h / 2
        return (-margin <= lx <= self.w + margin and
                -margin <= ly <= self.h + margin)

    def corners(self) -> list[tuple[float, float]]:
        """Return 4 rotated corners in image coords, TL, TR, BR, BL."""
        cx, cy = self.center()
        ang = math.radians(self.rotation)
        cos_a, sin_a = math.cos(ang), math.sin(ang)
        half_w, half_h = self.w / 2, self.h / 2
        pts_local = [(-half_w, -half_h), (half_w, -half_h),
                     (half_w, half_h), (-half_w, half_h)]
        return [(cx + x * cos_a - y * sin_a, cy + x * sin_a + y * cos_a)
                for x, y in pts_local]

    # ---- rendering ----
    def render(self, base: Image.Image) -> None:
        raise NotImplementedError

    def clone(self) -> "BaseObject":
        raise NotImplementedError


class TextObject(BaseObject):
    kind = "text"

    def __init__(self) -> None:
        super().__init__()
        self.text: str = "Sample text"
        self.font_family: str = ""
        self.font_path: Optional[str] = None
        self.font_size: int = 48
        self.color: str = "#ffffff"
        self.stroke_color: str = "#000000"
        self.stroke_width: int = 0
        self.bold: bool = False
        self.italic: bool = False
        self.align: str = "left"   # left / center / right
        self.line_spacing: float = 1.15
        self.shadow: bool = False
        self.shadow_offset: tuple[int, int] = (3, 3)
        self.shadow_color: str = "#000000"
        self.shadow_blur: int = 3
        self.name = "Text"

    def _resolve_font(self, discover_fn) -> Optional[str]:
        """Pick a matching font path taking bold/italic into account."""
        if not self.font_family and not self.font_path:
            return None
        candidates = discover_fn() if discover_fn else []
        wanted_variants = []
        fam = (self.font_family or "").lower()
        if self.bold and self.italic:
            wanted_variants = ["bold italic", "bold oblique", "bolditalic"]
        elif self.bold:
            wanted_variants = ["bold"]
        elif self.italic:
            wanted_variants = ["italic", "oblique"]
        for name, path in candidates:
            nl = name.lower()
            if fam and fam not in nl:
                continue
            if wanted_variants and not any(v in nl for v in wanted_variants):
                continue
            return path
        # fallback: any matching family, no style
        for name, path in candidates:
            if fam and fam in name.lower():
                return path
        return self.font_path

    def make_font(self, size: int, discover_fn=None) -> ImageFont.ImageFont:
        path = self._resolve_font(discover_fn)
        if path:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
        # try known fallbacks
        for c in ("arial.ttf", "C:/Windows/Fonts/segoeui.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                  "DejaVuSans.ttf"):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
        return ImageFont.load_default()

    def _measure(self, discover_fn=None) -> tuple[int, int, ImageFont.ImageFont]:
        font = self.make_font(self.font_size, discover_fn)
        dummy = Image.new("RGBA", (1, 1))
        d = ImageDraw.Draw(dummy)
        lines = self.text.split("\n") or [""]
        widths, heights = [], []
        line_h = 0
        for ln in lines:
            try:
                bbox = d.textbbox((0, 0), ln, font=font,
                                  stroke_width=self.stroke_width)
                w = bbox[2] - bbox[0]; h = bbox[3] - bbox[1]
            except Exception:
                w, h = d.textsize(ln, font=font)
            widths.append(w); heights.append(h)
            line_h = max(line_h, h)
        total_h = int(len(lines) * line_h * self.line_spacing)
        total_w = max(widths) if widths else 0
        return total_w, total_h, font

    def refresh_size(self, discover_fn=None) -> None:
        w, h, _ = self._measure(discover_fn)
        pad = max(4, self.stroke_width * 2 + 2)
        self.w = max(1, w + pad * 2)
        self.h = max(1, h + pad * 2)

    def _render_layer(self, discover_fn=None) -> Image.Image:
        """Render the text into a transparent RGBA image sized to (w,h)."""
        w, h, font = self._measure(discover_fn)
        pad = max(4, self.stroke_width * 2 + 2)
        layer_w = max(1, int(self.w))
        layer_h = max(1, int(self.h))
        layer = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        # Shadow
        if self.shadow:
            shadow_layer = Image.new("RGBA", (layer_w, layer_h), (0, 0, 0, 0))
            sd = ImageDraw.Draw(shadow_layer)
            self._draw_text_block(sd, pad + self.shadow_offset[0],
                                  pad + self.shadow_offset[1],
                                  font, hex_to_rgba(self.shadow_color, 255),
                                  None, 0)
            if self.shadow_blur > 0:
                shadow_layer = shadow_layer.filter(
                    ImageFilter.GaussianBlur(self.shadow_blur))
            layer = Image.alpha_composite(layer, shadow_layer)
            draw = ImageDraw.Draw(layer)
        self._draw_text_block(
            draw, pad, pad, font,
            hex_to_rgba(self.color, 255),
            hex_to_rgba(self.stroke_color, 255) if self.stroke_width > 0 else None,
            self.stroke_width)
        # opacity
        if self.opacity < 255:
            a = layer.split()[3].point(lambda v: v * self.opacity // 255)
            layer.putalpha(a)
        return layer

    def _draw_text_block(self, draw, x, y, font, fill,
                         stroke_fill, stroke_width):
        lines = self.text.split("\n") or [""]
        # measure line height uniformly
        try:
            bbox = draw.textbbox((0, 0), "Ag", font=font)
            base_h = bbox[3] - bbox[1]
        except Exception:
            _, base_h = draw.textsize("Ag", font=font)
        line_step = int(base_h * self.line_spacing)
        for i, ln in enumerate(lines):
            try:
                bb = draw.textbbox((0, 0), ln, font=font,
                                   stroke_width=stroke_width or 0)
                lw = bb[2] - bb[0]
            except Exception:
                lw, _ = draw.textsize(ln, font=font)
            if self.align == "center":
                lx = x + (int(self.w) - 2 * x - lw) // 2
            elif self.align == "right":
                lx = int(self.w) - x - lw
            else:
                lx = x
            ly = y + i * line_step
            if stroke_fill is not None and stroke_width > 0:
                draw.text((lx, ly), ln, font=font, fill=fill,
                          stroke_width=stroke_width, stroke_fill=stroke_fill)
            else:
                draw.text((lx, ly), ln, font=font, fill=fill)

    def render(self, base: Image.Image, discover_fn=None) -> None:
        if not self.visible:
            return
        layer = self._render_layer(discover_fn)
        if abs(self.rotation) > 0.01:
            layer = layer.rotate(self.rotation, resample=Image.BICUBIC,
                                 expand=True)
        cx, cy = self.center()
        px = int(cx - layer.width / 2)
        py = int(cy - layer.height / 2)
        base.alpha_composite(layer, dest=(px, py))

    def clone(self) -> "TextObject":
        o = TextObject()
        o.__dict__.update(self.__dict__)
        o.id = uuid.uuid4().hex[:8]
        o.x += 20; o.y += 20
        return o


class ShapeObject(BaseObject):
    kind = "shape"

    def __init__(self, shape: str = "rect") -> None:
        super().__init__()
        self.shape = shape           # rect / ellipse / line / arrow
        self.fill_color: Optional[str] = "#4f8cff"
        self.stroke_color: Optional[str] = "#ffffff"
        self.stroke_width: int = 3
        self.name = shape.capitalize()

    def _render_layer(self) -> Image.Image:
        lw = max(1, int(self.w)); lh = max(1, int(self.h))
        layer = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        sw = max(0, int(self.stroke_width))
        fill = hex_to_rgba(self.fill_color, 255) if self.fill_color else None
        outline = (hex_to_rgba(self.stroke_color, 255)
                   if self.stroke_color and sw > 0 else None)
        inset = sw // 2
        if self.shape == "rect":
            d.rectangle([inset, inset, lw - 1 - inset, lh - 1 - inset],
                        fill=fill, outline=outline, width=sw)
        elif self.shape == "ellipse":
            d.ellipse([inset, inset, lw - 1 - inset, lh - 1 - inset],
                      fill=fill, outline=outline, width=sw)
        elif self.shape == "line":
            color = outline or fill or (255, 255, 255, 255)
            d.line([(inset, lh // 2), (lw - 1 - inset, lh // 2)],
                   fill=color, width=max(1, sw))
        elif self.shape == "arrow":
            color = outline or fill or (255, 255, 255, 255)
            width = max(1, sw)
            y0 = lh // 2
            head = min(lw // 3, max(10, lh // 2))
            d.line([(inset, y0), (lw - 1 - inset - head, y0)],
                   fill=color, width=width)
            d.polygon([(lw - 1 - inset, y0),
                       (lw - 1 - inset - head, y0 - head // 2),
                       (lw - 1 - inset - head, y0 + head // 2)],
                      fill=color)
        if self.opacity < 255:
            a = layer.split()[3].point(lambda v: v * self.opacity // 255)
            layer.putalpha(a)
        return layer

    def render(self, base: Image.Image, discover_fn=None) -> None:
        if not self.visible:
            return
        layer = self._render_layer()
        if abs(self.rotation) > 0.01:
            layer = layer.rotate(self.rotation, resample=Image.BICUBIC,
                                 expand=True)
        cx, cy = self.center()
        px = int(cx - layer.width / 2)
        py = int(cy - layer.height / 2)
        base.alpha_composite(layer, dest=(px, py))

    def clone(self) -> "ShapeObject":
        o = ShapeObject(self.shape)
        o.__dict__.update(self.__dict__)
        o.id = uuid.uuid4().hex[:8]
        o.x += 20; o.y += 20
        return o


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------
class ImageEditor(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1400x880")
        self.minsize(1100, 700)
        self.configure(bg=BG)

        # ---- Settings ----
        self.settings = load_settings()
        self.recent_files: list[str] = [
            p for p in self.settings.get("recent_files", []) if os.path.isfile(p)
        ]

        # ---- State ----
        self.original_image: Optional[Image.Image] = None
        self.image: Optional[Image.Image]          = None  # base RGBA raster
        self.current_path: Optional[str]           = None
        self.modified: bool                        = False

        self.objects: list[BaseObject] = []
        self.selected: Optional[BaseObject] = None

        self.display_image: Optional[ImageTk.PhotoImage] = None
        self.display_scale: float = 1.0
        self.zoom_mode: str       = "fit"

        # history stores snapshots of (image, objects)
        self.history:    list[tuple[Image.Image, list[BaseObject]]] = []
        self.redo_stack: list[tuple[Image.Image, list[BaseObject]]] = []
        self.HISTORY_MAX = 60

        # Tool state
        self.tool        = tk.StringVar(value="select")
        self.brush_color = self.settings.get("brush_color", "#ff2d55")
        self.brush_size  = tk.IntVar(value=self.settings.get("brush_size", 8))
        self.text_color  = self.settings.get("text_color", "#ffffff")
        self.text_size   = tk.IntVar(value=self.settings.get("text_size", 48))
        self.text_family = tk.StringVar(value=self.settings.get("text_family", ""))
        self.text_bold   = tk.BooleanVar(value=False)
        self.text_italic = tk.BooleanVar(value=False)
        self.shape_fill  = tk.BooleanVar(value=True)
        self.shape_stroke_w = tk.IntVar(value=3)
        self.show_grid   = tk.BooleanVar(value=False)
        self.show_rulers = tk.BooleanVar(value=False)
        self.snap_to_grid = tk.BooleanVar(value=False)
        self.grid_size   = tk.IntVar(value=32)
        self.autosave_min = tk.IntVar(value=int(self.settings.get("autosave_min", 0)))

        # Drag state
        self.drag_mode: Optional[str] = None   # move | resize-<h> | rotate | draw-shape | brush | crop | pan | marquee
        self.drag_start_img: Optional[tuple[float, float]] = None
        self.drag_start_obj: Optional[dict] = None
        self.last_point:    Optional[tuple[float, float]] = None
        self.crop_start:    Optional[tuple[int, int]]     = None
        self.crop_rect_id:  Optional[int]                 = None
        self.brush_cursor_id: Optional[int]               = None
        self.pan_anchor:   Optional[tuple[int, int]]      = None
        self.new_shape_kind: Optional[str] = None
        self.crop_ratio: Optional[float] = None  # None = free
        self.crop_thirds: bool = True

        # UI hooks that need late binding
        self._prop_widgets: dict[str, Any] = {}
        self._font_choices: list[tuple[str, str]] = []
        self._suppress_prop_update = False

        # ---- Build UI ----
        self._build_style()
        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()
        self._update_title()
        self._refresh_recent_menu()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(60_000, self._autosave_tick)

        # Try to enable drag & drop (best-effort; needs tkdnd; silently skip)
        self._try_enable_dnd()

        # Show welcome / about splash on startup
        self.after(250, self._show_splash)

    # ------------------------------------------------------------------
    # Style
    # ------------------------------------------------------------------
    def _build_style(self) -> None:
        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass

        st.configure(".", background=BG, foreground=FG,
                     fieldbackground=BG_PANEL_ALT, borderwidth=0, focuscolor=BG)
        st.configure("TFrame",  background=BG)
        st.configure("Panel.TFrame",  background=BG_PANEL)
        st.configure("TLabel",  background=BG, foreground=FG)
        st.configure("Panel.TLabel", background=BG_PANEL, foreground=FG)
        st.configure("Muted.TLabel", background=BG_PANEL, foreground=FG_MUTED)
        st.configure("Title.TLabel", background=BG_PANEL, foreground=FG_MUTED,
                     font=("Segoe UI Semibold", 9))
        st.configure("TButton", padding=(10, 6), background=BG_PANEL_ALT,
                     foreground=FG, borderwidth=0, relief="flat")
        st.map("TButton",
               background=[("active", "#33364a"), ("pressed", "#2a2d3e")],
               foreground=[("active", "#ffffff")])
        st.configure("Accent.TButton", background=ACCENT, foreground="#ffffff",
                     padding=(12, 6))
        st.map("Accent.TButton",
               background=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER)])
        st.configure("Danger.TButton", background=DANGER, foreground="#ffffff",
                     padding=(10, 6))
        st.configure("Tool.TRadiobutton", background=BG_PANEL, foreground=FG,
                     indicatorcolor=BG_PANEL_ALT, padding=(4, 4))
        st.map("Tool.TRadiobutton",
               background=[("active", BG_PANEL_ALT)],
               indicatorcolor=[("selected", ACCENT)])
        st.configure("TLabelframe", background=BG_PANEL, foreground=FG_MUTED,
                     borderwidth=0, relief="flat")
        st.configure("TLabelframe.Label", background=BG_PANEL,
                     foreground=FG_MUTED, font=("Segoe UI Semibold", 9))
        st.configure("Horizontal.TScale", background=BG_PANEL,
                     troughcolor=BG_PANEL_ALT)
        st.configure("TCombobox", fieldbackground=BG_PANEL_ALT,
                     background=BG_PANEL_ALT, foreground=FG, arrowcolor=FG)
        st.configure("TSeparator", background="#2a2c38")
        st.configure("Status.TLabel", background=BG_PANEL, foreground=FG_MUTED,
                     padding=(8, 4))
        st.configure("TCheckbutton", background=BG_PANEL, foreground=FG)
        st.map("TCheckbutton", background=[("active", BG_PANEL_ALT)])
        st.configure("TNotebook", background=BG_PANEL, borderwidth=0)
        st.configure("TNotebook.Tab", background=BG_PANEL_ALT, foreground=FG,
                     padding=(10, 6))
        st.map("TNotebook.Tab",
               background=[("selected", ACCENT)],
               foreground=[("selected", "#ffffff")])

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------
    def _build_menu(self) -> None:
        menubar = tk.Menu(self, tearoff=0, bg=BG_PANEL, fg=FG,
                          activebackground=ACCENT, activeforeground="#ffffff",
                          borderwidth=0)
        self.config(menu=menubar)

        m_file = tk.Menu(menubar, tearoff=0, bg=BG_PANEL, fg=FG,
                         activebackground=ACCENT, activeforeground="#ffffff")
        m_file.add_command(label="New blank image…", accelerator="Ctrl+N",
                           command=self.new_blank)
        m_file.add_command(label="Open…", accelerator="Ctrl+O",
                           command=self.open_image)
        self.recent_menu = tk.Menu(m_file, tearoff=0, bg=BG_PANEL, fg=FG,
                                   activebackground=ACCENT,
                                   activeforeground="#ffffff")
        m_file.add_cascade(label="Open recent", menu=self.recent_menu)
        m_file.add_separator()
        m_file.add_command(label="Save", accelerator="Ctrl+S", command=self.save)
        m_file.add_command(label="Save As…", accelerator="Ctrl+Shift+S",
                           command=self.save_as)
        m_file.add_command(label="Export to PDF…", command=self.export_pdf)
        m_file.add_command(label="Compress to size…", accelerator="Ctrl+K",
                           command=self.compress_dialog)
        m_file.add_separator()
        m_file.add_command(label="Copy image (clipboard)", accelerator="Ctrl+Shift+C",
                           command=self.copy_image_to_clipboard)
        m_file.add_command(label="Paste from clipboard", accelerator="Ctrl+Shift+V",
                           command=self.paste_from_clipboard)
        m_file.add_separator()
        m_file.add_command(label="Auto-save every… (minutes)",
                           command=self.set_autosave_interval)
        m_file.add_command(label="Open auto-save folder",
                           command=lambda: self._open_folder(AUTOSAVE_DIR))
        m_file.add_separator()
        m_file.add_command(label="Exit", accelerator="Ctrl+Q",
                           command=self._on_close)
        menubar.add_cascade(label="File", menu=m_file)

        m_edit = tk.Menu(menubar, tearoff=0, bg=BG_PANEL, fg=FG,
                         activebackground=ACCENT, activeforeground="#ffffff")
        m_edit.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        m_edit.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo)
        m_edit.add_separator()
        m_edit.add_command(label="Duplicate selection", accelerator="Ctrl+D",
                           command=self.duplicate_selected)
        m_edit.add_command(label="Delete selection", accelerator="Delete",
                           command=self.delete_selected)
        m_edit.add_command(label="Bring to front", accelerator="Ctrl+]",
                           command=lambda: self._reorder_selected("front"))
        m_edit.add_command(label="Send to back", accelerator="Ctrl+[",
                           command=lambda: self._reorder_selected("back"))
        m_edit.add_separator()
        m_edit.add_command(label="Flatten objects into image",
                           command=self.flatten_objects)
        m_edit.add_command(label="Reset to original", command=self.reset_image)
        menubar.add_cascade(label="Edit", menu=m_edit)

        m_img = tk.Menu(menubar, tearoff=0, bg=BG_PANEL, fg=FG,
                        activebackground=ACCENT, activeforeground="#ffffff")
        m_img.add_command(label="Rotate 90° CW",  command=lambda: self.rotate(-90))
        m_img.add_command(label="Rotate 90° CCW", command=lambda: self.rotate(90))
        m_img.add_command(label="Rotate arbitrary…", command=self.rotate_dialog)
        m_img.add_separator()
        m_img.add_command(label="Flip horizontal", command=lambda: self.flip("h"))
        m_img.add_command(label="Flip vertical",   command=lambda: self.flip("v"))
        m_img.add_separator()
        m_img.add_command(label="Resize…", command=self.resize_dialog)
        m_img.add_command(label="Canvas size / border…", command=self.border_dialog)
        m_img.add_command(label="Watermark…", command=self.watermark_dialog)
        m_img.add_separator()
        m_img.add_command(label="Brightness…", command=lambda: self._enhance_dialog("Brightness"))
        m_img.add_command(label="Contrast…",   command=lambda: self._enhance_dialog("Contrast"))
        m_img.add_command(label="Saturation…", command=lambda: self._enhance_dialog("Color"))
        m_img.add_command(label="Sharpness…",  command=lambda: self._enhance_dialog("Sharpness"))
        m_img.add_command(label="Gamma…",      command=self.gamma_dialog)
        m_img.add_command(label="Hue shift…",  command=self.hue_dialog)
        m_img.add_command(label="Temperature / Tint…", command=self.temperature_dialog)
        m_img.add_separator()
        m_img.add_command(label="Grayscale", command=self.to_grayscale)
        m_img.add_command(label="Sepia",     command=self.to_sepia)
        m_img.add_command(label="Invert colors", command=self.invert_colors)
        m_img.add_command(label="Auto-contrast", command=self.auto_contrast)
        m_img.add_command(label="Equalize",  command=self.equalize)
        m_img.add_command(label="Posterize…", command=self.posterize_dialog)
        m_img.add_command(label="Solarize…",  command=self.solarize_dialog)
        menubar.add_cascade(label="Image", menu=m_img)

        m_filt = tk.Menu(menubar, tearoff=0, bg=BG_PANEL, fg=FG,
                         activebackground=ACCENT, activeforeground="#ffffff")
        m_filt.add_command(label="Gaussian blur…", command=self.gaussian_blur_dialog)
        m_filt.add_command(label="Box blur…",     command=self.box_blur_dialog)
        m_filt.add_command(label="Motion blur…",  command=self.motion_blur_dialog)
        m_filt.add_command(label="Sharpen",       command=lambda: self._apply_filter(ImageFilter.SHARPEN))
        m_filt.add_command(label="Smooth",        command=lambda: self._apply_filter(ImageFilter.SMOOTH))
        m_filt.add_command(label="Detail",        command=lambda: self._apply_filter(ImageFilter.DETAIL))
        m_filt.add_command(label="Edge enhance",  command=lambda: self._apply_filter(ImageFilter.EDGE_ENHANCE))
        m_filt.add_command(label="Emboss",        command=lambda: self._apply_filter(ImageFilter.EMBOSS))
        m_filt.add_command(label="Contour",       command=lambda: self._apply_filter(ImageFilter.CONTOUR))
        m_filt.add_command(label="Find edges",    command=lambda: self._apply_filter(ImageFilter.FIND_EDGES))
        m_filt.add_separator()
        m_filt.add_command(label="Vignette…",     command=self.vignette_dialog)
        m_filt.add_command(label="Pixelate…",     command=self.pixelate_dialog)
        menubar.add_cascade(label="Filters", menu=m_filt)

        m_view = tk.Menu(menubar, tearoff=0, bg=BG_PANEL, fg=FG,
                         activebackground=ACCENT, activeforeground="#ffffff")
        m_view.add_command(label="Zoom in",  accelerator="Ctrl++",
                           command=lambda: self.zoom_by(1.25))
        m_view.add_command(label="Zoom out", accelerator="Ctrl+-",
                           command=lambda: self.zoom_by(0.8))
        m_view.add_command(label="Fit to window", accelerator="Ctrl+0",
                           command=self.zoom_fit)
        m_view.add_command(label="Actual pixels 100 %", accelerator="Ctrl+1",
                           command=self.zoom_100)
        m_view.add_separator()
        m_view.add_checkbutton(label="Show grid", variable=self.show_grid,
                               command=self._render)
        m_view.add_checkbutton(label="Snap to grid", variable=self.snap_to_grid)
        m_view.add_checkbutton(label="Show rulers", variable=self.show_rulers,
                               command=self._render)
        m_view.add_command(label="Set grid size…", command=self._set_grid_size)
        m_view.add_separator()
        m_view.add_command(label="Show histogram", command=self.show_histogram)
        m_view.add_command(label="Image info", command=self.show_info)
        menubar.add_cascade(label="View", menu=m_view)

        m_help = tk.Menu(menubar, tearoff=0, bg=BG_PANEL, fg=FG,
                         activebackground=ACCENT, activeforeground="#ffffff")
        m_help.add_command(label="Keyboard shortcuts", command=self._show_shortcuts)
        m_help.add_command(label="Welcome screen…", command=self._show_splash)
        m_help.add_separator()
        m_help.add_command(label="Developer website",
                           command=lambda: webbrowser.open(APP_WEBSITE))
        m_help.add_command(label="GitHub profile",
                           command=lambda: webbrowser.open(APP_GITHUB))
        m_help.add_command(label="LinkedIn profile",
                           command=lambda: webbrowser.open(APP_LINKEDIN))
        m_help.add_separator()
        m_help.add_command(label=f"About {APP_NAME}", command=self._show_about)
        menubar.add_cascade(label="Help", menu=m_help)

    def _refresh_recent_menu(self) -> None:
        self.recent_menu.delete(0, "end")
        if not self.recent_files:
            self.recent_menu.add_command(label="(empty)", state="disabled")
            return
        for p in self.recent_files:
            self.recent_menu.add_command(
                label=os.path.basename(p) + "   " + p,
                command=lambda x=p: self._open_path(x))
        self.recent_menu.add_separator()
        self.recent_menu.add_command(label="Clear list", command=self._clear_recent)

    def _clear_recent(self) -> None:
        self.recent_files = []
        self._persist_settings()
        self._refresh_recent_menu()

    def _push_recent(self, path: str) -> None:
        path = os.path.abspath(path)
        self.recent_files = [p for p in self.recent_files if p != path]
        self.recent_files.insert(0, path)
        self.recent_files = self.recent_files[:RECENT_MAX]
        self._persist_settings()
        self._refresh_recent_menu()

    def _persist_settings(self) -> None:
        self.settings.update({
            "recent_files": self.recent_files,
            "brush_color": self.brush_color,
            "brush_size": int(self.brush_size.get()),
            "text_color": self.text_color,
            "text_size": int(self.text_size.get()),
            "text_family": self.text_family.get(),
            "autosave_min": int(self.autosave_min.get()),
        })
        save_settings(self.settings)

    # ------------------------------------------------------------------
    # UI layout
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        # Header
        header = ttk.Frame(self, style="Panel.TFrame")
        header.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(header, text=f"  {APP_NAME}  v{APP_VERSION}",
                  style="Panel.TLabel",
                  font=("Segoe UI Semibold", 11)).pack(side=tk.LEFT, pady=6)
        ttk.Label(header,
                  text=f"by {APP_AUTHOR} · {APP_AUTHOR_FA} · {APP_WEBSITE}   ",
                  style="Muted.TLabel").pack(side=tk.RIGHT, pady=6)

        # Toolbar
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(side=tk.TOP, fill=tk.X, pady=(1, 0))

        def tb_btn(parent, text, cmd, accent=False):
            style = "Accent.TButton" if accent else "TButton"
            b = ttk.Button(parent, text=text, style=style, command=cmd)
            b.pack(side=tk.LEFT, padx=3, pady=6)
            return b

        tb_btn(top, "  New  ", self.new_blank)
        tb_btn(top, "  Open  ", self.open_image, accent=True)
        tb_btn(top, "  Save  ", self.save)
        tb_btn(top, "Save As", self.save_as)
        tb_btn(top, "Compress…", self.compress_dialog)
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        tb_btn(top, "Undo", self.undo)
        tb_btn(top, "Redo", self.redo)
        tb_btn(top, "Reset", self.reset_image)
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        tb_btn(top, "Rotate ⟳", lambda: self.rotate(-90))
        tb_btn(top, "Rotate ⟲", lambda: self.rotate(90))
        tb_btn(top, "Flip H", lambda: self.flip("h"))
        tb_btn(top, "Flip V", lambda: self.flip("v"))
        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        tb_btn(top, "−", lambda: self.zoom_by(0.8))
        tb_btn(top, "Fit", self.zoom_fit)
        tb_btn(top, "1:1", self.zoom_100)
        tb_btn(top, "+", lambda: self.zoom_by(1.25))

        self.info_var = tk.StringVar(value="No image loaded")
        ttk.Label(top, textvariable=self.info_var,
                  style="Muted.TLabel").pack(side=tk.RIGHT, padx=10)

        # Body
        body = ttk.Frame(self)
        body.pack(fill=tk.BOTH, expand=True)

        # Left tool panel
        side = ttk.Frame(body, style="Panel.TFrame", width=270)
        side.pack(side=tk.LEFT, fill=tk.Y)
        side.pack_propagate(False)
        self._build_tool_panel(side)

        # Canvas + scrollbars
        canvas_wrap = ttk.Frame(body)
        canvas_wrap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas_wrap.rowconfigure(0, weight=1)
        canvas_wrap.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_wrap, bg="#0c0d12",
                                highlightthickness=0, cursor="arrow")
        vbar = ttk.Scrollbar(canvas_wrap, orient="vertical",
                             command=self.canvas.yview)
        hbar = ttk.Scrollbar(canvas_wrap, orient="horizontal",
                             command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")

        self.canvas.bind("<Configure>",       lambda e: self._render())
        self.canvas.bind("<ButtonPress-1>",   self.on_mouse_down)
        self.canvas.bind("<B1-Motion>",       self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Motion>",          self.on_mouse_move)
        self.canvas.bind("<Leave>",           lambda e: self._hide_brush_cursor())
        self.canvas.bind("<Button-3>",        self.on_right_click)

        # MMB pan
        self.canvas.bind("<ButtonPress-2>", self._pan_start)
        self.canvas.bind("<B2-Motion>",     self._pan_move)

        # Ctrl+MouseWheel zoom (anchored at cursor)
        self.canvas.bind("<Control-MouseWheel>", self._wheel_zoom)
        self.canvas.bind("<Control-Button-4>",   lambda e: self._wheel_zoom_at(e, 1.15))
        self.canvas.bind("<Control-Button-5>",   lambda e: self._wheel_zoom_at(e, 1 / 1.15))
        # Plain wheel scrolls
        self.canvas.bind("<MouseWheel>",         self._wheel_scroll)
        self.canvas.bind("<Shift-MouseWheel>",   self._wheel_scroll_h)

        # Right property panel
        right = ttk.Frame(body, style="Panel.TFrame", width=280)
        right.pack(side=tk.LEFT, fill=tk.Y)
        right.pack_propagate(False)
        self._build_property_panel(right)

        # Status bar
        status_bar = ttk.Frame(self, style="Panel.TFrame")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status = tk.StringVar(value="Ready")
        ttk.Label(status_bar, textvariable=self.status,
                  style="Status.TLabel").pack(side=tk.LEFT)
        self.cursor_var = tk.StringVar(value="")
        ttk.Label(status_bar, textvariable=self.cursor_var,
                  style="Status.TLabel").pack(side=tk.RIGHT)

    def _build_tool_panel(self, side: ttk.Frame) -> None:
        # Tools
        tools = ttk.LabelFrame(side, text="  TOOLS  ")
        tools.pack(fill=tk.X, padx=10, pady=(10, 6))
        tools_layout = [
            ("↖  Select / Move",  "select"),
            ("✋ Pan",             "pan"),
            ("✎  Brush",          "draw"),
            ("⌫  Eraser",         "erase"),
            ("💧 Eyedropper",     "eyedropper"),
            ("🪣 Bucket fill",    "bucket"),
            ("T  Text",           "text"),
            ("▭  Rectangle",      "shape-rect"),
            ("◯  Ellipse",        "shape-ellipse"),
            ("─  Line",           "shape-line"),
            ("→  Arrow",          "shape-arrow"),
            ("⛶  Crop",           "crop"),
        ]
        for label, val in tools_layout:
            ttk.Radiobutton(tools, text=label, variable=self.tool,
                            value=val, style="Tool.TRadiobutton",
                            command=self._tool_changed).pack(
                anchor="w", padx=8, pady=1, fill=tk.X)

        # Brush / eraser
        brush_f = ttk.LabelFrame(side, text="  BRUSH / ERASER  ")
        brush_f.pack(fill=tk.X, padx=10, pady=6)
        ttk.Label(brush_f, text="Size", style="Panel.TLabel").pack(
            anchor="w", padx=8, pady=(6, 0))
        row = ttk.Frame(brush_f, style="Panel.TFrame"); row.pack(fill=tk.X, padx=8)
        ttk.Scale(row, from_=1, to=200, variable=self.brush_size,
                  orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(row, textvariable=self.brush_size, width=4,
                  style="Panel.TLabel").pack(side=tk.RIGHT, padx=(6, 0))
        self.brush_swatch = tk.Button(brush_f, text="■   Brush color",
                                      bg=self.brush_color, fg="#ffffff",
                                      relief="flat", bd=0,
                                      activebackground=self.brush_color,
                                      command=self.pick_brush_color)
        self.brush_swatch.pack(fill=tk.X, padx=8, pady=8)

        # Text quick settings (also mirrored in property panel when selected)
        text_f = ttk.LabelFrame(side, text="  TEXT DEFAULTS  ")
        text_f.pack(fill=tk.X, padx=10, pady=6)
        ttk.Label(text_f, text="Font family",
                  style="Panel.TLabel").pack(anchor="w", padx=8, pady=(6, 0))
        self._font_choices = self._discover_fonts()
        family_cb = ttk.Combobox(text_f, textvariable=self.text_family,
                                 values=[name for name, _ in self._font_choices],
                                 state="readonly")
        family_cb.pack(fill=tk.X, padx=8, pady=(0, 6))
        if self._font_choices and not self.text_family.get():
            self.text_family.set(self._font_choices[0][0])
        ttk.Label(text_f, text="Size", style="Panel.TLabel").pack(anchor="w", padx=8)
        row = ttk.Frame(text_f, style="Panel.TFrame"); row.pack(fill=tk.X, padx=8)
        ttk.Scale(row, from_=8, to=400, variable=self.text_size,
                  orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(row, textvariable=self.text_size, width=4,
                  style="Panel.TLabel").pack(side=tk.RIGHT, padx=(6, 0))
        self.text_swatch = tk.Button(text_f, text="■   Text color",
                                     bg=self.text_color, fg="#000000",
                                     relief="flat", bd=0,
                                     activebackground=self.text_color,
                                     command=self.pick_text_color)
        self.text_swatch.pack(fill=tk.X, padx=8, pady=8)

        # Crop presets
        crop_f = ttk.LabelFrame(side, text="  CROP  ")
        crop_f.pack(fill=tk.X, padx=10, pady=6)
        ttk.Label(crop_f, text="Aspect ratio", style="Panel.TLabel").pack(
            anchor="w", padx=8, pady=(6, 0))
        self.crop_ratio_var = tk.StringVar(value="Free")
        cb = ttk.Combobox(
            crop_f, textvariable=self.crop_ratio_var, state="readonly",
            values=["Free", "1:1", "4:3", "3:2", "16:9", "9:16", "3:4"])
        cb.pack(fill=tk.X, padx=8, pady=(0, 6))
        cb.bind("<<ComboboxSelected>>", lambda e: self._crop_ratio_changed())
        ttk.Label(crop_f, text="Drag on the image, then Enter/Apply.",
                  style="Muted.TLabel", justify="left").pack(
            anchor="w", padx=8, pady=6)
        ttk.Button(crop_f, text="Apply crop", style="Accent.TButton",
                   command=self.apply_crop).pack(fill=tk.X, padx=8, pady=(0, 4))
        ttk.Button(crop_f, text="Clear selection",
                   command=self._clear_crop_rect).pack(fill=tk.X, padx=8, pady=(0, 8))

    def _build_property_panel(self, right: ttk.Frame) -> None:
        # Notebook with two tabs: Properties + Layers
        nb = ttk.Notebook(right)
        nb.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # ---- Properties tab ----
        prop_tab = ttk.Frame(nb, style="Panel.TFrame")
        nb.add(prop_tab, text="Properties")
        self.prop_container = ttk.Frame(prop_tab, style="Panel.TFrame")
        self.prop_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self._prop_empty = ttk.Label(
            self.prop_container,
            text="No object selected.\n\n"
                 "Pick the Select tool then click a\n"
                 "text or shape to edit it.\n\n"
                 "Double-click a text object to change\n"
                 "its content.",
            style="Muted.TLabel", justify="left")
        self._prop_empty.pack(padx=8, pady=12, anchor="w")

        # ---- Layers tab ----
        layers_tab = ttk.Frame(nb, style="Panel.TFrame")
        nb.add(layers_tab, text="Layers")
        self.layers_list = tk.Listbox(
            layers_tab, bg=BG_PANEL_ALT, fg=FG,
            selectbackground=ACCENT, selectforeground="#ffffff",
            highlightthickness=0, borderwidth=0, activestyle="none")
        self.layers_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.layers_list.bind("<<ListboxSelect>>", self._on_layer_select)
        btnrow = ttk.Frame(layers_tab, style="Panel.TFrame")
        btnrow.pack(fill=tk.X, padx=6, pady=(0, 6))
        ttk.Button(btnrow, text="↑", width=3,
                   command=lambda: self._layer_move(-1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btnrow, text="↓", width=3,
                   command=lambda: self._layer_move(1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btnrow, text="Dup",
                   command=self.duplicate_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btnrow, text="Del", style="Danger.TButton",
                   command=self.delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btnrow, text="Flatten",
                   command=self.flatten_objects).pack(side=tk.RIGHT, padx=2)

    # ------------------------------------------------------------------
    # Shortcuts
    # ------------------------------------------------------------------
    def _bind_shortcuts(self) -> None:
        b = self.bind_all
        b("<Control-n>",        lambda e: self.new_blank())
        b("<Control-o>",        lambda e: self.open_image())
        b("<Control-s>",        lambda e: self.save())
        b("<Control-S>",        lambda e: self.save_as())
        b("<Control-Shift-S>",  lambda e: self.save_as())
        b("<Control-k>",        lambda e: self.compress_dialog())
        b("<Control-z>",        lambda e: self.undo())
        b("<Control-y>",        lambda e: self.redo())
        b("<Control-Shift-Z>",  lambda e: self.redo())
        b("<Control-d>",        lambda e: self.duplicate_selected())
        b("<Delete>",           lambda e: self.delete_selected())
        b("<BackSpace>",        lambda e: self.delete_selected())
        b("<Control-bracketright>", lambda e: self._reorder_selected("front"))
        b("<Control-bracketleft>",  lambda e: self._reorder_selected("back"))
        b("<Control-q>",        lambda e: self._on_close())
        b("<Control-plus>",     lambda e: self.zoom_by(1.25))
        b("<Control-equal>",    lambda e: self.zoom_by(1.25))
        b("<Control-minus>",    lambda e: self.zoom_by(0.8))
        b("<Control-Key-0>",    lambda e: self.zoom_fit())
        b("<Control-Key-1>",    lambda e: self.zoom_100())
        b("<Control-Shift-C>",  lambda e: self.copy_image_to_clipboard())
        b("<Control-Shift-V>",  lambda e: self.paste_from_clipboard())
        b("<Return>",           lambda e: self.apply_crop() if self.tool.get() == "crop" else None)
        b("<Escape>",           lambda e: self._escape_action())
        b("<Left>",             lambda e: self._nudge(-1, 0))
        b("<Right>",            lambda e: self._nudge(1, 0))
        b("<Up>",               lambda e: self._nudge(0, -1))
        b("<Down>",             lambda e: self._nudge(0, 1))
        b("<Shift-Left>",       lambda e: self._nudge(-10, 0))
        b("<Shift-Right>",      lambda e: self._nudge(10, 0))
        b("<Shift-Up>",         lambda e: self._nudge(0, -10))
        b("<Shift-Down>",       lambda e: self._nudge(0, 10))
        # Tool shortcuts
        b("<v>", lambda e: self._set_tool("select"))
        b("<h>", lambda e: self._set_tool("pan"))
        b("<b>", lambda e: self._set_tool("draw"))
        b("<e>", lambda e: self._set_tool("erase"))
        b("<i>", lambda e: self._set_tool("eyedropper"))
        b("<t>", lambda e: self._set_tool("text"))
        b("<r>", lambda e: self._set_tool("shape-rect"))
        b("<o>", lambda e: self._set_tool("shape-ellipse"))
        b("<l>", lambda e: self._set_tool("shape-line"))
        b("<a>", lambda e: self._set_tool("shape-arrow"))
        b("<c>", lambda e: self._set_tool("crop"))

    def _escape_action(self) -> None:
        if self.crop_rect_id:
            self._clear_crop_rect()
        elif self.selected:
            self.selected = None
            self._render()
            self._refresh_property_panel()

    def _set_tool(self, t: str) -> None:
        # Ignore hotkeys while typing in an Entry
        w = self.focus_get()
        if isinstance(w, (tk.Entry, ttk.Entry, tk.Text)):
            return
        self.tool.set(t)
        self._tool_changed()

    def _nudge(self, dx: int, dy: int) -> None:
        w = self.focus_get()
        if isinstance(w, (tk.Entry, ttk.Entry, tk.Text)):
            return
        if self.selected is None:
            return
        self._push_history()
        self.selected.move(dx, dy)
        self._render()

    # ------------------------------------------------------------------
    # Drag & drop (best-effort)
    # ------------------------------------------------------------------
    def _try_enable_dnd(self) -> None:
        try:
            self.tk.call("package", "require", "tkdnd")
            self.tk.call("tkdnd::drop_target", "register", self._w, ("DND_Files",))
            self.bind("<<Drop>>", self._on_dnd_drop)
        except Exception:
            pass  # tkdnd not installed; silently disable

    def _on_dnd_drop(self, event) -> None:
        data = event.data
        # Split braces or spaces
        paths: list[str] = []
        cur = ""
        in_brace = False
        for ch in data:
            if ch == "{":
                in_brace = True; cur = ""
            elif ch == "}":
                in_brace = False
                if cur: paths.append(cur); cur = ""
            elif ch == " " and not in_brace:
                if cur: paths.append(cur); cur = ""
            else:
                cur += ch
        if cur: paths.append(cur)
        for p in paths:
            if os.path.isfile(p):
                self._open_path(p)
                return

    # ------------------------------------------------------------------
    # Fonts
    # ------------------------------------------------------------------
    def _discover_fonts(self) -> list[tuple[str, str]]:
        if getattr(self, "_font_choices_cache", None):
            return self._font_choices_cache
        results: list[tuple[str, str]] = []
        seen: set[str] = set()
        dirs: list[str] = []
        sysname = platform.system()
        if sysname == "Windows":
            win_dir = os.environ.get("WINDIR", r"C:\Windows")
            dirs.append(os.path.join(win_dir, "Fonts"))
        elif sysname == "Darwin":
            dirs += ["/System/Library/Fonts", "/Library/Fonts",
                     os.path.expanduser("~/Library/Fonts")]
        else:
            dirs += ["/usr/share/fonts", "/usr/local/share/fonts",
                     os.path.expanduser("~/.fonts"),
                     os.path.expanduser("~/.local/share/fonts")]
        for d in dirs:
            if not os.path.isdir(d):
                continue
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith((".ttf", ".otf")):
                        name = os.path.splitext(f)[0]
                        key = name.lower()
                        if key in seen:
                            continue
                        seen.add(key)
                        results.append((name, os.path.join(root, f)))
        results.sort(key=lambda x: x[0].lower())
        preferred = ("segoeui", "arial", "calibri", "verdana",
                     "tahoma", "dejavusans", "helvetica")
        head, tail = [], []
        for item in results:
            (head if item[0].lower() in preferred else tail).append(item)
        self._font_choices_cache = head + tail
        return self._font_choices_cache

    def _discover_fonts_lazy(self):
        return self._discover_fonts()

    # ------------------------------------------------------------------
    # Color pickers
    # ------------------------------------------------------------------
    def pick_brush_color(self) -> None:
        c = colorchooser.askcolor(color=self.brush_color, title="Brush color",
                                  parent=self)
        if c and c[1]:
            self.brush_color = c[1]
            self.brush_swatch.configure(bg=c[1], activebackground=c[1])
            self._persist_settings()

    def pick_text_color(self) -> None:
        c = colorchooser.askcolor(color=self.text_color, title="Text color",
                                  parent=self)
        if c and c[1]:
            self.text_color = c[1]
            self.text_swatch.configure(bg=c[1], activebackground=c[1])
            self._persist_settings()

    # ------------------------------------------------------------------
    # Tool change
    # ------------------------------------------------------------------
    def _tool_changed(self) -> None:
        self._clear_crop_rect()
        self._hide_brush_cursor()
        cursors = {
            "select": "arrow", "pan": "fleur", "draw": "crosshair",
            "erase": "crosshair", "eyedropper": "target",
            "bucket": "spraycan", "text": "xterm",
            "shape-rect": "crosshair", "shape-ellipse": "crosshair",
            "shape-line": "crosshair", "shape-arrow": "crosshair",
            "crop": "tcross",
        }
        self.canvas.configure(cursor=cursors.get(self.tool.get(), "arrow"))
        if not self.tool.get().startswith("shape") and self.tool.get() != "text":
            pass
        if self.tool.get() != "select":
            self.selected = None
            self._render()
            self._refresh_property_panel()

    def _crop_ratio_changed(self) -> None:
        m = {
            "Free": None, "1:1": 1.0, "4:3": 4/3, "3:4": 3/4,
            "3:2": 3/2, "16:9": 16/9, "9:16": 9/16,
        }
        self.crop_ratio = m.get(self.crop_ratio_var.get())

    def _set_grid_size(self) -> None:
        v = simpledialog.askinteger("Grid size", "Grid spacing (px):",
                                    initialvalue=self.grid_size.get(),
                                    minvalue=2, maxvalue=512, parent=self)
        if v:
            self.grid_size.set(v)
            self._render()

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------
    def _snapshot(self) -> tuple[Image.Image, list[BaseObject]]:
        img = self.image.copy() if self.image else None
        objs = [self._deep_clone_object(o) for o in self.objects]
        return (img, objs)

    def _deep_clone_object(self, obj: BaseObject) -> BaseObject:
        if isinstance(obj, TextObject):
            o = TextObject()
        elif isinstance(obj, ShapeObject):
            o = ShapeObject(obj.shape)
        else:
            o = BaseObject()
        o.__dict__.update(obj.__dict__)
        return o

    def _push_history(self) -> None:
        if self.image is None:
            return
        self.history.append(self._snapshot())
        if len(self.history) > self.HISTORY_MAX:
            self.history.pop(0)
        self.redo_stack.clear()
        self._set_modified(True)

    def undo(self) -> None:
        if not self.history or self.image is None:
            return
        self.redo_stack.append(self._snapshot())
        img, objs = self.history.pop()
        self.image = img; self.objects = objs
        # keep selection if id still present
        if self.selected:
            self.selected = next((o for o in self.objects
                                  if o.id == self.selected.id), None)
        self._render()
        self._refresh_property_panel()
        self._refresh_layers_list()
        self.status.set("Undo")

    def redo(self) -> None:
        if not self.redo_stack or self.image is None:
            return
        self.history.append(self._snapshot())
        img, objs = self.redo_stack.pop()
        self.image = img; self.objects = objs
        if self.selected:
            self.selected = next((o for o in self.objects
                                  if o.id == self.selected.id), None)
        self._render()
        self._refresh_property_panel()
        self._refresh_layers_list()
        self.status.set("Redo")

    def reset_image(self) -> None:
        if self.original_image is None:
            return
        if not messagebox.askyesno("Reset",
                                   "Discard all edits and reload the original?"):
            return
        self._push_history()
        self.image = self.original_image.copy()
        self.objects.clear()
        self.selected = None
        self._render()
        self._refresh_layers_list()
        self._refresh_property_panel()
        self.status.set("Reset to original")

    # ------------------------------------------------------------------
    # File ops
    # ------------------------------------------------------------------
    def new_blank(self) -> None:
        if self.modified and not messagebox.askyesno(
                "Unsaved changes",
                "You have unsaved changes. Discard and create a new image?"):
            return
        dlg = _ModalDialog(self, "New blank image")
        vw = tk.IntVar(value=1920); vh = tk.IntVar(value=1080)
        color = tk.StringVar(value="#ffffff")
        ttk.Label(dlg.body, text="Width", style="Panel.TLabel").grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        ttk.Entry(dlg.body, textvariable=vw, width=10).grid(
            row=0, column=1, sticky="w", padx=16, pady=(14, 4))
        ttk.Label(dlg.body, text="Height", style="Panel.TLabel").grid(
            row=1, column=0, sticky="w", padx=16, pady=4)
        ttk.Entry(dlg.body, textvariable=vh, width=10).grid(
            row=1, column=1, sticky="w", padx=16, pady=4)
        color_btn = tk.Button(dlg.body, text="■  Background color", bg="#ffffff",
                              fg="#000000", relief="flat", bd=0)
        def pick():
            c = colorchooser.askcolor(color=color.get(), parent=dlg)
            if c and c[1]:
                color.set(c[1])
                color_btn.configure(bg=c[1], activebackground=c[1])
        color_btn.configure(command=pick)
        color_btn.grid(row=2, column=0, columnspan=2, padx=16, pady=(6, 12),
                       sticky="ew")
        if dlg.run() is None:
            return
        try:
            w = max(1, int(vw.get())); h = max(1, int(vh.get()))
        except Exception:
            return
        img = Image.new("RGBA", (w, h), hex_to_rgba(color.get(), 255))
        self.original_image = img.copy()
        self.image = img
        self.current_path = None
        self.history.clear(); self.redo_stack.clear()
        self.objects.clear(); self.selected = None
        self._set_modified(False)
        self.zoom_mode = "fit"
        self._render()
        self._refresh_layers_list()
        self._refresh_property_panel()
        self.status.set(f"New blank {w}×{h}")

    def open_image(self) -> None:
        if self.modified and not messagebox.askyesno(
                "Unsaved changes",
                "You have unsaved changes. Open another file anyway?"):
            return
        path = filedialog.askopenfilename(title="Open image",
                                          filetypes=SUPPORTED_OPEN)
        if not path:
            return
        self._open_path(path)

    def _open_path(self, path: str) -> None:
        try:
            img = Image.open(path)
            img.load()
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
            if img.mode == "RGB":
                img = img.convert("RGBA")
        except Exception as e:
            messagebox.showerror("Open failed", str(e))
            return
        self.original_image = img.copy()
        self.image          = img
        self.current_path   = path
        self.history.clear(); self.redo_stack.clear()
        self.objects.clear(); self.selected = None
        self._set_modified(False)
        self.zoom_mode = "fit"
        self._render()
        self._refresh_layers_list()
        self._refresh_property_panel()
        self.status.set(f"Loaded  ·  {os.path.basename(path)}")
        self._push_recent(path)

    def _open_folder(self, folder: str) -> None:
        try:
            if platform.system() == "Windows":
                os.startfile(folder)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')
        except Exception:
            messagebox.showinfo("Folder", folder)

    def _flattened(self) -> Optional[Image.Image]:
        if self.image is None:
            return None
        base = self.image.copy()
        if base.mode != "RGBA":
            base = base.convert("RGBA")
        for obj in self.objects:
            try:
                obj.render(base, discover_fn=self._discover_fonts_lazy)
            except Exception as e:
                print("Render failed:", e)
        return base

    def save(self) -> None:
        if self.image is None:
            return
        if not self.current_path:
            self.save_as(); return
        ext = os.path.splitext(self.current_path)[1].lower()
        fmt = EXT_TO_FMT.get(ext, "PNG")
        try:
            self._save_lossless(self._flattened(), self.current_path, fmt)
            self._set_modified(False)
            self.status.set(f"Saved  ·  {os.path.basename(self.current_path)}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def save_as(self) -> None:
        if self.image is None:
            return
        initialfile = ""
        if self.current_path:
            base = os.path.splitext(os.path.basename(self.current_path))[0]
            initialfile = base + "_edited.png"
        path = filedialog.asksaveasfilename(
            title="Save image as", defaultextension=".png",
            initialfile=initialfile, filetypes=SAVE_FILETYPES)
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()
        if ext not in EXT_TO_FMT:
            messagebox.showerror("Save failed",
                                 f"Unsupported extension: {ext}\n"
                                 f"Use one of: {', '.join(EXT_TO_FMT)}")
            return
        fmt = EXT_TO_FMT[ext]
        try:
            self._save_lossless(self._flattened(), path, fmt)
            self.current_path = path
            self._set_modified(False)
            self.status.set(f"Saved  ·  {os.path.basename(path)}")
            self._push_recent(path)
            messagebox.showinfo("Saved", f"File saved:\n{path}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def _save_lossless(self, img: Image.Image, path: str, fmt: str) -> None:
        f = fmt.upper()
        if f == "JPEG":
            img.convert("RGB").save(path, "JPEG", quality=100,
                                    subsampling=0, optimize=True)
        elif f == "PNG":
            img.save(path, "PNG", optimize=True, compress_level=9)
        elif f == "WEBP":
            img.save(path, "WEBP", lossless=True, quality=100, method=6)
        elif f == "BMP":
            img.convert("RGB").save(path, "BMP")
        elif f == "TIFF":
            img.save(path, "TIFF", compression="tiff_lzw")
        elif f == "GIF":
            img.convert("P", palette=Image.ADAPTIVE).save(path, "GIF")
        elif f == "ICO":
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128),
                     (256, 256)]
            img.save(path, "ICO", sizes=sizes)
        elif f == "PDF":
            img.convert("RGB").save(path, "PDF", resolution=100.0)
        else:
            img.save(path)

    def export_pdf(self) -> None:
        if self.image is None:
            return
        path = filedialog.asksaveasfilename(
            title="Export as PDF", defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")])
        if not path:
            return
        try:
            self._flattened().convert("RGB").save(path, "PDF", resolution=150.0)
            self.status.set(f"Exported PDF  ·  {os.path.basename(path)}")
            messagebox.showinfo("Export", f"PDF saved:\n{path}")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    # ---- Clipboard ----
    def copy_image_to_clipboard(self) -> None:
        img = self._flattened()
        if img is None:
            return
        try:
            if platform.system() == "Windows":
                import ctypes
                CF_DIB = 8
                out = io.BytesIO()
                img.convert("RGB").save(out, "BMP")
                data = out.getvalue()[14:]  # strip BMP file header
                ctypes.windll.user32.OpenClipboard(0)
                ctypes.windll.user32.EmptyClipboard()
                h = ctypes.windll.kernel32.GlobalAlloc(0x2000, len(data))
                p = ctypes.windll.kernel32.GlobalLock(h)
                ctypes.memmove(p, data, len(data))
                ctypes.windll.kernel32.GlobalUnlock(h)
                ctypes.windll.user32.SetClipboardData(CF_DIB, h)
                ctypes.windll.user32.CloseClipboard()
                self.status.set("Image copied to clipboard")
            else:
                # Fallback: put a PNG data URI on the Tk clipboard (limited)
                out = io.BytesIO(); img.save(out, "PNG")
                self.clipboard_clear()
                self.clipboard_append("data:image/png;base64," +
                                      __import__("base64").b64encode(out.getvalue()).decode())
                self.status.set("Image copied (as data URI)")
        except Exception as e:
            messagebox.showerror("Copy failed", str(e))

    def paste_from_clipboard(self) -> None:
        try:
            img = ImageGrab.grabclipboard()
        except Exception as e:
            messagebox.showerror("Paste failed", str(e))
            return
        if img is None:
            messagebox.showinfo("Paste", "The clipboard does not contain an image.")
            return
        if isinstance(img, list):
            # list of file paths
            for p in img:
                if os.path.isfile(p):
                    self._open_path(p); return
            messagebox.showinfo("Paste", "Clipboard contains files but none are images.")
            return
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        if self.image is None:
            self.original_image = img.copy()
            self.image = img
            self.current_path = None
            self._render()
            self.status.set("Pasted from clipboard")
            return
        # Paste onto current image, centered
        self._push_history()
        px = (self.image.width - img.width) // 2
        py = (self.image.height - img.height) // 2
        self.image.alpha_composite(img, dest=(max(0, px), max(0, py)))
        self._render()
        self.status.set("Pasted from clipboard (composited)")

    # ------------------------------------------------------------------
    # Auto-save
    # ------------------------------------------------------------------
    def set_autosave_interval(self) -> None:
        v = simpledialog.askinteger(
            "Auto-save", "Auto-save every how many minutes?\n(0 = disabled)",
            initialvalue=int(self.autosave_min.get()),
            minvalue=0, maxvalue=120, parent=self)
        if v is None:
            return
        self.autosave_min.set(v)
        self._persist_settings()
        self.status.set(f"Auto-save: {'off' if v == 0 else f'every {v} min'}")

    def _autosave_tick(self) -> None:
        try:
            m = int(self.autosave_min.get())
            if m > 0 and self.image is not None and self.modified:
                stem = "untitled"
                if self.current_path:
                    stem = os.path.splitext(os.path.basename(self.current_path))[0]
                path = os.path.join(
                    AUTOSAVE_DIR,
                    f"{stem}__{time.strftime('%Y%m%d_%H%M%S')}.png")
                self._flattened().save(path, "PNG", optimize=True)
                self.status.set(f"Auto-saved  ·  {os.path.basename(path)}")
        except Exception as e:
            print("Auto-save error:", e)
        # Reschedule every minute; interval acts as gating (only save if enabled)
        self.after(60_000, self._autosave_tick)

    # ------------------------------------------------------------------
    # Compression
    # ------------------------------------------------------------------
    def compress_dialog(self) -> None:
        if self.image is None:
            messagebox.showinfo("No image", "Open an image first."); return
        target_kb = simpledialog.askinteger(
            "Compress to target size",
            "Target maximum file size (KB):\nOriginal resolution is preserved.\n"
            "Quality is automatically tuned by binary-search.",
            minvalue=5, maxvalue=500000, initialvalue=500, parent=self)
        if target_kb is None:
            return
        fmt = self._ask_compress_format()
        if not fmt:
            return
        ext = "jpg" if fmt == "JPEG" else "webp"
        base = ""
        if self.current_path:
            base = os.path.splitext(os.path.basename(self.current_path))[0] + "_compressed"
        path = filedialog.asksaveasfilename(
            title=f"Save compressed {fmt}",
            defaultextension="." + ext,
            initialfile=(base + "." + ext) if base else "",
            filetypes=[(fmt, f"*.{ext}")])
        if not path:
            return
        try:
            final_bytes, quality = self._compress_to_target(
                self._flattened(), path, fmt, target_kb * 1024)
            messagebox.showinfo(
                "Compression done",
                f"Saved: {path}\nFinal size: {final_bytes/1024:.1f} KB "
                f"(target ≤ {target_kb} KB)\nQuality used: {quality}\n"
                f"Resolution unchanged.")
            self.status.set(f"Compressed  ·  {final_bytes/1024:.1f} KB  ·  q={quality}")
        except Exception as e:
            messagebox.showerror("Compression failed", str(e))

    def _ask_compress_format(self) -> Optional[str]:
        dlg = _ModalDialog(self, "Compression format")
        ttk.Label(dlg.body,
                  text="Choose the codec used to hit the target size.\n"
                       "JPEG is fastest and most compatible.\n"
                       "WEBP compresses better at low sizes.",
                  style="Panel.TLabel",
                  justify="left").pack(padx=18, pady=(14, 8))
        var = tk.StringVar(value="JPEG")
        cb = ttk.Combobox(dlg.body, textvariable=var, values=["JPEG", "WEBP"],
                          state="readonly", width=20)
        cb.pack(padx=18, pady=6)
        return dlg.run(var)

    def _compress_to_target(self, img: Image.Image, path: str,
                            fmt: str, target_bytes: int) -> tuple[int, int]:
        im = img.convert("RGB") if fmt == "JPEG" else img
        lo, hi = 20, 100
        best_bytes: Optional[bytes] = None
        best_q = lo
        while lo <= hi:
            mid = (lo + hi) // 2
            buf = io.BytesIO()
            if fmt == "JPEG":
                im.save(buf, "JPEG", quality=mid, subsampling=0,
                        optimize=True, progressive=True)
            else:
                im.save(buf, "WEBP", quality=mid, method=6)
            size = buf.tell()
            if size <= target_bytes:
                best_bytes = buf.getvalue(); best_q = mid; lo = mid + 1
            else:
                hi = mid - 1
        if best_bytes is None:
            buf = io.BytesIO(); q = 20
            if fmt == "JPEG":
                im.save(buf, "JPEG", quality=q, subsampling=2,
                        optimize=True, progressive=True)
            else:
                im.save(buf, "WEBP", quality=q, method=6)
            best_bytes = buf.getvalue(); best_q = q
        with open(path, "wb") as f:
            f.write(best_bytes)
        return len(best_bytes), best_q

    # ------------------------------------------------------------------
    # Transforms
    # ------------------------------------------------------------------
    def rotate(self, angle: float) -> None:
        if self.image is None:
            return
        self._push_history()
        self.image = self.image.rotate(angle, expand=True, resample=Image.BICUBIC)
        # Objects: rotate around image center too (approx)
        w0, h0 = self.image.size
        for obj in self.objects:
            obj.rotation = (obj.rotation + angle) % 360
        self._render()

    def rotate_dialog(self) -> None:
        if self.image is None:
            return
        deg = simpledialog.askfloat("Rotate", "Rotate by (degrees, CCW positive):",
                                    initialvalue=0.0, parent=self)
        if deg is None:
            return
        self.rotate(deg)

    def flip(self, mode: str) -> None:
        if self.image is None:
            return
        self._push_history()
        self.image = (ImageOps.mirror(self.image) if mode == "h"
                      else ImageOps.flip(self.image))
        self._render()

    def resize_dialog(self) -> None:
        if self.image is None:
            return
        w, h = self.image.size
        dlg = _ModalDialog(self, "Resize image")
        ttk.Label(dlg.body, text=f"Current: {w} × {h} px",
                  style="Muted.TLabel").pack(padx=18, pady=(14, 6))
        vw = tk.IntVar(value=w); vh = tk.IntVar(value=h)
        lock = tk.BooleanVar(value=True)
        aspect = w / h if h else 1.0
        updating = {"flag": False}

        def on_w(*_):
            if updating["flag"] or not lock.get(): return
            try:
                updating["flag"] = True
                vh.set(max(1, round(vw.get() / aspect)))
            finally:
                updating["flag"] = False

        def on_h(*_):
            if updating["flag"] or not lock.get(): return
            try:
                updating["flag"] = True
                vw.set(max(1, round(vh.get() * aspect)))
            finally:
                updating["flag"] = False

        vw.trace_add("write", on_w); vh.trace_add("write", on_h)
        row = ttk.Frame(dlg.body, style="Panel.TFrame"); row.pack(padx=18, pady=6)
        ttk.Label(row, text="Width",  style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(row, textvariable=vw, width=10).grid(row=0, column=1, padx=6, pady=3)
        ttk.Label(row, text="Height", style="Panel.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Entry(row, textvariable=vh, width=10).grid(row=1, column=1, padx=6, pady=3)
        ttk.Checkbutton(dlg.body, text="Lock aspect ratio",
                        variable=lock).pack(padx=18, pady=(4, 6), anchor="w")

        result = dlg.run(vw, extra=vh)
        if result is None:
            return
        try:
            new_w = max(1, int(vw.get())); new_h = max(1, int(vh.get()))
        except Exception:
            return
        # scale objects proportionally
        sx = new_w / w; sy = new_h / h
        self._push_history()
        self.image = self.image.resize((new_w, new_h), Image.LANCZOS)
        for obj in self.objects:
            obj.x *= sx; obj.y *= sy; obj.w *= sx; obj.h *= sy
            if isinstance(obj, TextObject):
                obj.font_size = max(4, int(obj.font_size * ((sx + sy) / 2)))
        self._render()
        self.status.set(f"Resized to {new_w} × {new_h}")

    def border_dialog(self) -> None:
        if self.image is None:
            return
        dlg = _ModalDialog(self, "Border / canvas extend")
        v = tk.IntVar(value=40); color = tk.StringVar(value="#000000")
        ttk.Label(dlg.body, text="Border thickness (px)",
                  style="Panel.TLabel").pack(padx=18, pady=(14, 4))
        ttk.Entry(dlg.body, textvariable=v, width=8).pack(padx=18, pady=4)
        btn = tk.Button(dlg.body, text="■  Border color", bg=color.get(),
                        fg="#ffffff", relief="flat", bd=0)
        def pick():
            c = colorchooser.askcolor(color=color.get(), parent=dlg)
            if c and c[1]:
                color.set(c[1]); btn.configure(bg=c[1], activebackground=c[1])
        btn.configure(command=pick)
        btn.pack(fill=tk.X, padx=18, pady=(6, 12))
        if dlg.run() is None: return
        px = max(0, int(v.get()))
        self._push_history()
        self.image = ImageOps.expand(self.image, border=px,
                                     fill=hex_to_rgba(color.get(), 255))
        for obj in self.objects:
            obj.x += px; obj.y += px
        self._render()

    def watermark_dialog(self) -> None:
        if self.image is None: return
        dlg = _ModalDialog(self, "Watermark (text)")
        text = tk.StringVar(value="© " + (APP_AUTHOR))
        size = tk.IntVar(value=max(24, self.image.width // 30))
        opacity = tk.IntVar(value=90)
        angle = tk.IntVar(value=30)
        tile = tk.BooleanVar(value=True)
        color = tk.StringVar(value="#ffffff")

        def row(label, w):
            r = ttk.Frame(dlg.body, style="Panel.TFrame")
            r.pack(fill=tk.X, padx=16, pady=4)
            ttk.Label(r, text=label, style="Panel.TLabel", width=14).pack(side=tk.LEFT)
            w.pack(side=tk.LEFT, fill=tk.X, expand=True)

        row("Text", ttk.Entry(dlg.body, textvariable=text))
        row("Font size", ttk.Entry(dlg.body, textvariable=size, width=8))
        row("Opacity %", ttk.Scale(dlg.body, from_=5, to=100, variable=opacity,
                                   orient=tk.HORIZONTAL))
        row("Rotation°", ttk.Scale(dlg.body, from_=-90, to=90, variable=angle,
                                   orient=tk.HORIZONTAL))
        ttk.Checkbutton(dlg.body, text="Tile across entire image",
                        variable=tile).pack(padx=16, pady=6, anchor="w")
        btn = tk.Button(dlg.body, text="■  Color", bg=color.get(),
                        fg="#000000", relief="flat", bd=0)
        def pick():
            c = colorchooser.askcolor(color=color.get(), parent=dlg)
            if c and c[1]:
                color.set(c[1]); btn.configure(bg=c[1], activebackground=c[1])
        btn.configure(command=pick)
        btn.pack(fill=tk.X, padx=16, pady=(6, 12))
        if dlg.run() is None: return
        self._push_history()
        self._apply_watermark(text.get(), int(size.get()), int(opacity.get()),
                              int(angle.get()), tile.get(), color.get())
        self._render()

    def _apply_watermark(self, text, size, opacity, angle, tile, color):
        if not text: return
        alpha = max(0, min(255, int(opacity * 255 / 100)))
        # Build one label as a rotated RGBA tile
        try:
            font = ImageFont.truetype("arial.ttf", size)
        except Exception:
            font = ImageFont.load_default()
        tmp = Image.new("RGBA", (1, 1)); d = ImageDraw.Draw(tmp)
        try:
            bb = d.textbbox((0, 0), text, font=font)
            tw = bb[2] - bb[0]; th = bb[3] - bb[1]
        except Exception:
            tw, th = d.textsize(text, font=font)
        label = Image.new("RGBA", (tw + 10, th + 10), (0, 0, 0, 0))
        d2 = ImageDraw.Draw(label)
        d2.text((5, 5), text, font=font, fill=hex_to_rgba(color, alpha))
        label = label.rotate(angle, expand=True, resample=Image.BICUBIC)
        w, h = self.image.size
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        if tile:
            step_x = max(label.width + 40, 100)
            step_y = max(label.height + 60, 100)
            for y in range(-label.height, h + step_y, step_y):
                for x in range(-label.width, w + step_x, step_x):
                    canvas.alpha_composite(label, dest=(x, y))
        else:
            canvas.alpha_composite(
                label,
                dest=(w - label.width - 20, h - label.height - 20))
        self.image = Image.alpha_composite(self.image, canvas)

    # ------- Adjustments -------
    def _enhance_dialog(self, kind: str) -> None:
        if self.image is None: return
        base = self.image.copy()
        preview = tk.DoubleVar(value=1.0)
        dlg = _ModalDialog(self, f"{kind} adjustment")
        ttk.Label(dlg.body, text=f"{kind} factor (1.0 = no change)",
                  style="Panel.TLabel").pack(padx=18, pady=(14, 4))
        ttk.Scale(dlg.body, from_=0.0, to=3.0, variable=preview,
                  orient=tk.HORIZONTAL, length=260).pack(padx=18, pady=4)
        val_lbl = ttk.Label(dlg.body, text="1.00", style="Muted.TLabel")
        val_lbl.pack(pady=(0, 6))
        preview.trace_add("write",
                          lambda *_: val_lbl.configure(text=f"{preview.get():.2f}"))
        r = dlg.run(preview)
        if r is None: return
        try:
            factor = float(preview.get())
            enhancer_cls = getattr(ImageEnhance, kind)
            new_img = enhancer_cls(base).enhance(factor)
        except Exception as e:
            messagebox.showerror("Adjustment failed", str(e)); return
        self._push_history()
        self.image = new_img
        self._render()

    def gamma_dialog(self) -> None:
        if self.image is None: return
        v = simpledialog.askfloat("Gamma", "Gamma value (1.0 = no change,\n"
                                  "< 1 brighter, > 1 darker):",
                                  minvalue=0.1, maxvalue=5.0, initialvalue=1.0,
                                  parent=self)
        if v is None: return
        self._push_history()
        inv = 1.0 / v
        lut = [min(255, int((i / 255.0) ** inv * 255 + 0.5)) for i in range(256)]
        if self.image.mode == "RGBA":
            r, g, b, a = self.image.split()
            r = r.point(lut); g = g.point(lut); b = b.point(lut)
            self.image = Image.merge("RGBA", (r, g, b, a))
        else:
            self.image = self.image.point(lut * len(self.image.getbands()))
        self._render()

    def hue_dialog(self) -> None:
        if self.image is None: return
        v = simpledialog.askinteger("Hue shift", "Shift hue by degrees (-180..180):",
                                    minvalue=-180, maxvalue=180, initialvalue=0,
                                    parent=self)
        if v is None: return
        self._push_history()
        has_alpha = self.image.mode == "RGBA"
        alpha = self.image.split()[3] if has_alpha else None
        hsv = self.image.convert("RGB").convert("HSV")
        h, s, val = hsv.split()
        shift = int(v * 255 / 360)
        h = h.point(lambda x: (x + shift) % 256)
        rgb = Image.merge("HSV", (h, s, val)).convert("RGB")
        if has_alpha:
            self.image = rgb.convert("RGBA"); self.image.putalpha(alpha)
        else:
            self.image = rgb
        self._render()

    def temperature_dialog(self) -> None:
        if self.image is None: return
        dlg = _ModalDialog(self, "Temperature / Tint")
        temp = tk.IntVar(value=0)   # -100..100 (blue..red)
        tint = tk.IntVar(value=0)   # -100..100 (green..magenta)
        ttk.Label(dlg.body, text="Temperature (blue ↔ red)",
                  style="Panel.TLabel").pack(padx=18, pady=(14, 2))
        ttk.Scale(dlg.body, from_=-100, to=100, variable=temp,
                  orient=tk.HORIZONTAL, length=260).pack(padx=18, pady=2)
        ttk.Label(dlg.body, text="Tint (green ↔ magenta)",
                  style="Panel.TLabel").pack(padx=18, pady=(10, 2))
        ttk.Scale(dlg.body, from_=-100, to=100, variable=tint,
                  orient=tk.HORIZONTAL, length=260).pack(padx=18, pady=(2, 12))
        if dlg.run() is None: return
        self._push_history()
        t = int(temp.get()); k = int(tint.get())
        has_alpha = self.image.mode == "RGBA"
        alpha = self.image.split()[3] if has_alpha else None
        rgb = self.image.convert("RGB")
        r, g, b = rgb.split()
        r = r.point(lambda x: max(0, min(255, x + t)))
        b = b.point(lambda x: max(0, min(255, x - t)))
        g = g.point(lambda x: max(0, min(255, x - k)))
        r = r.point(lambda x: max(0, min(255, x + k // 2)))
        b = b.point(lambda x: max(0, min(255, x + k // 2)))
        merged = Image.merge("RGB", (r, g, b))
        if has_alpha:
            self.image = merged.convert("RGBA"); self.image.putalpha(alpha)
        else:
            self.image = merged
        self._render()

    def to_grayscale(self) -> None:
        if self.image is None: return
        self._push_history()
        mode = self.image.mode
        gray = ImageOps.grayscale(self.image)
        self.image = gray.convert(mode) if mode in ("RGB", "RGBA") else gray
        self._render()

    def to_sepia(self) -> None:
        if self.image is None: return
        self._push_history()
        has_alpha = self.image.mode == "RGBA"
        alpha = self.image.split()[3] if has_alpha else None
        gray = ImageOps.grayscale(self.image)
        sepia = ImageOps.colorize(gray, black="#3b1e08", white="#fbe6b6")
        if has_alpha:
            self.image = sepia.convert("RGBA"); self.image.putalpha(alpha)
        else:
            self.image = sepia
        self._render()

    def invert_colors(self) -> None:
        if self.image is None: return
        self._push_history()
        if self.image.mode == "RGBA":
            r, g, b, a = self.image.split()
            rgb = ImageChops.invert(Image.merge("RGB", (r, g, b)))
            self.image = Image.merge("RGBA", (*rgb.split(), a))
        else:
            self.image = ImageChops.invert(self.image.convert("RGB"))
        self._render()

    def auto_contrast(self) -> None:
        if self.image is None: return
        self._push_history()
        has_alpha = self.image.mode == "RGBA"
        alpha = self.image.split()[3] if has_alpha else None
        rgb = ImageOps.autocontrast(self.image.convert("RGB"))
        if has_alpha:
            self.image = rgb.convert("RGBA"); self.image.putalpha(alpha)
        else:
            self.image = rgb
        self._render()

    def equalize(self) -> None:
        if self.image is None: return
        self._push_history()
        has_alpha = self.image.mode == "RGBA"
        alpha = self.image.split()[3] if has_alpha else None
        rgb = ImageOps.equalize(self.image.convert("RGB"))
        if has_alpha:
            self.image = rgb.convert("RGBA"); self.image.putalpha(alpha)
        else:
            self.image = rgb
        self._render()

    def posterize_dialog(self) -> None:
        if self.image is None: return
        v = simpledialog.askinteger("Posterize", "Bits per channel (1..8):",
                                    minvalue=1, maxvalue=8, initialvalue=4,
                                    parent=self)
        if v is None: return
        self._push_history()
        has_alpha = self.image.mode == "RGBA"
        alpha = self.image.split()[3] if has_alpha else None
        rgb = ImageOps.posterize(self.image.convert("RGB"), v)
        if has_alpha:
            self.image = rgb.convert("RGBA"); self.image.putalpha(alpha)
        else:
            self.image = rgb
        self._render()

    def solarize_dialog(self) -> None:
        if self.image is None: return
        v = simpledialog.askinteger("Solarize", "Threshold (0..255):",
                                    minvalue=0, maxvalue=255, initialvalue=128,
                                    parent=self)
        if v is None: return
        self._push_history()
        has_alpha = self.image.mode == "RGBA"
        alpha = self.image.split()[3] if has_alpha else None
        rgb = ImageOps.solarize(self.image.convert("RGB"), v)
        if has_alpha:
            self.image = rgb.convert("RGBA"); self.image.putalpha(alpha)
        else:
            self.image = rgb
        self._render()

    def _apply_filter(self, flt) -> None:
        if self.image is None: return
        self._push_history()
        has_alpha = self.image.mode == "RGBA"
        alpha = self.image.split()[3] if has_alpha else None
        try:
            rgb = self.image.convert("RGB").filter(flt)
        except Exception as e:
            messagebox.showerror("Filter failed", str(e)); return
        if has_alpha:
            self.image = rgb.convert("RGBA"); self.image.putalpha(alpha)
        else:
            self.image = rgb
        self._render()

    def gaussian_blur_dialog(self) -> None:
        if self.image is None: return
        r = simpledialog.askfloat("Gaussian blur", "Radius (px):",
                                  minvalue=0.1, maxvalue=200, initialvalue=2.0,
                                  parent=self)
        if r is None: return
        self._apply_filter(ImageFilter.GaussianBlur(r))

    def box_blur_dialog(self) -> None:
        if self.image is None: return
        r = simpledialog.askfloat("Box blur", "Radius (px):",
                                  minvalue=0.1, maxvalue=200, initialvalue=2.0,
                                  parent=self)
        if r is None: return
        self._apply_filter(ImageFilter.BoxBlur(r))

    def motion_blur_dialog(self) -> None:
        if self.image is None: return
        length = simpledialog.askinteger("Motion blur", "Length (px):",
                                         minvalue=2, maxvalue=200,
                                         initialvalue=15, parent=self)
        if length is None: return
        # Simple motion blur kernel (horizontal)
        size = length
        kernel = [0] * (size * size)
        for i in range(size):
            kernel[i * size + size // 2] = 1
        scale = float(size)
        self._apply_filter(ImageFilter.Kernel((size, size), kernel, scale=scale))

    def vignette_dialog(self) -> None:
        if self.image is None: return
        strength = simpledialog.askinteger("Vignette", "Strength (0..100):",
                                           minvalue=0, maxvalue=100,
                                           initialvalue=60, parent=self)
        if strength is None: return
        self._push_history()
        w, h = self.image.size
        mask = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(mask)
        d.ellipse([-w // 4, -h // 4, w + w // 4, h + h // 4], fill=255)
        mask = mask.filter(ImageFilter.GaussianBlur(max(w, h) / 5))
        dark = Image.new("RGBA", (w, h), (0, 0, 0, 255))
        vignette = Image.composite(self.image.convert("RGBA"), dark, mask)
        # mix with original by strength
        self.image = Image.blend(self.image.convert("RGBA"), vignette,
                                 strength / 100.0)
        self._render()

    def pixelate_dialog(self) -> None:
        if self.image is None: return
        block = simpledialog.askinteger("Pixelate", "Block size (px):",
                                        minvalue=2, maxvalue=200, initialvalue=12,
                                        parent=self)
        if block is None: return
        self._push_history()
        w, h = self.image.size
        small = self.image.resize((max(1, w // block), max(1, h // block)),
                                  Image.NEAREST)
        self.image = small.resize((w, h), Image.NEAREST)
        self._render()

    # ------------------------------------------------------------------
    # Histogram / Info
    # ------------------------------------------------------------------
    def show_histogram(self) -> None:
        if self.image is None: return
        top = tk.Toplevel(self); top.title("Histogram")
        top.configure(bg=BG_PANEL); top.transient(self)
        cw, ch = 520, 260
        c = tk.Canvas(top, width=cw, height=ch, bg="#0c0d12",
                      highlightthickness=0)
        c.pack(padx=10, pady=10)
        rgb = self.image.convert("RGB")
        hists = rgb.histogram()  # 768 values
        channels = [("#ff4f6a", hists[0:256]),
                    ("#5ae388", hists[256:512]),
                    ("#4f8cff", hists[512:768])]
        mx = max(max(h) for _, h in channels) or 1
        for color, h in channels:
            pts = []
            for i, v in enumerate(h):
                x = i * cw / 256
                y = ch - (v / mx) * ch * 0.95
                pts.extend([x, y])
            c.create_line(*pts, fill=color, width=1)
        ttk.Button(top, text="Close",
                   command=top.destroy).pack(pady=(0, 10))

    def show_info(self) -> None:
        if self.image is None: return
        w, h = self.image.size
        # estimate PNG size
        buf = io.BytesIO()
        try:
            self._flattened().save(buf, "PNG", optimize=True)
            png_kb = buf.tell() / 1024
        except Exception:
            png_kb = 0
        messagebox.showinfo(
            "Image info",
            f"Path: {self.current_path or '(unsaved)'}\n"
            f"Dimensions: {w} × {h} px\n"
            f"Mode: {self.image.mode}\n"
            f"Objects: {len(self.objects)}\n"
            f"Estimated PNG size: {png_kb:.1f} KB\n"
            f"Modified: {'yes' if self.modified else 'no'}")

    # ------------------------------------------------------------------
    # Object helpers
    # ------------------------------------------------------------------
    def _refresh_layers_list(self) -> None:
        if not hasattr(self, "layers_list"):
            return
        self.layers_list.delete(0, "end")
        for obj in reversed(self.objects):  # top-most first
            marker = "●" if obj is self.selected else "○"
            vis = "👁" if obj.visible else "·"
            name = obj.name
            if isinstance(obj, TextObject):
                snippet = obj.text.split("\n")[0][:20]
                name = f"T · {snippet or 'text'}"
            self.layers_list.insert("end", f"{marker} {vis}  {name}")

    def _on_layer_select(self, event) -> None:
        sel = self.layers_list.curselection()
        if not sel:
            return
        idx = sel[0]
        obj = list(reversed(self.objects))[idx]
        self.selected = obj
        self.tool.set("select")
        self._tool_changed()
        self._render()
        self._refresh_property_panel()

    def _layer_move(self, delta: int) -> None:
        if self.selected is None: return
        i = self.objects.index(self.selected)
        j = max(0, min(len(self.objects) - 1, i - delta))  # reversed display
        if j == i: return
        self._push_history()
        self.objects.pop(i)
        self.objects.insert(j, self.selected)
        self._render(); self._refresh_layers_list()

    def _reorder_selected(self, where: str) -> None:
        if self.selected is None: return
        self._push_history()
        self.objects.remove(self.selected)
        if where == "front":
            self.objects.append(self.selected)
        else:
            self.objects.insert(0, self.selected)
        self._render(); self._refresh_layers_list()

    def duplicate_selected(self) -> None:
        if self.selected is None: return
        self._push_history()
        clone = self.selected.clone()
        self.objects.append(clone)
        self.selected = clone
        self._render(); self._refresh_layers_list(); self._refresh_property_panel()

    def delete_selected(self) -> None:
        if self.selected is None: return
        self._push_history()
        self.objects.remove(self.selected)
        self.selected = None
        self._render(); self._refresh_layers_list(); self._refresh_property_panel()

    def flatten_objects(self) -> None:
        if self.image is None or not self.objects: return
        if not messagebox.askyesno(
            "Flatten", f"Rasterize {len(self.objects)} object(s) into the "
                       "base image? This can no longer be edited as objects."):
            return
        self._push_history()
        base = self.image.copy()
        if base.mode != "RGBA": base = base.convert("RGBA")
        for obj in self.objects:
            obj.render(base, discover_fn=self._discover_fonts_lazy)
        self.image = base
        self.objects.clear(); self.selected = None
        self._render(); self._refresh_layers_list(); self._refresh_property_panel()
        self.status.set("Objects flattened")

    # ------------------------------------------------------------------
    # Property panel
    # ------------------------------------------------------------------
    def _clear_prop_container(self) -> None:
        for w in self.prop_container.winfo_children():
            w.destroy()
        self._prop_widgets.clear()

    def _refresh_property_panel(self) -> None:
        self._clear_prop_container()
        obj = self.selected
        if obj is None:
            ttk.Label(self.prop_container,
                      text="No object selected.\n\n"
                           "Pick the Select tool then click a\n"
                           "text or shape to edit it.\n\n"
                           "Double-click a text object to change\n"
                           "its content.",
                      style="Muted.TLabel", justify="left").pack(
                padx=8, pady=12, anchor="w")
            return
        if isinstance(obj, TextObject):
            self._build_text_prop(obj)
        elif isinstance(obj, ShapeObject):
            self._build_shape_prop(obj)
        self._build_common_prop(obj)
        self._refresh_layers_list()

    def _build_common_prop(self, obj: BaseObject) -> None:
        f = ttk.LabelFrame(self.prop_container, text="  TRANSFORM  ")
        f.pack(fill=tk.X, pady=6)
        rot = tk.DoubleVar(value=obj.rotation)
        opa = tk.IntVar(value=obj.opacity)
        ttk.Label(f, text="Rotation°", style="Panel.TLabel").pack(
            anchor="w", padx=8, pady=(6, 0))
        ttk.Scale(f, from_=-180, to=180, variable=rot, orient=tk.HORIZONTAL,
                  command=lambda *_: self._set_obj_attr("rotation", rot.get())
                  ).pack(fill=tk.X, padx=8)
        ttk.Label(f, text="Opacity", style="Panel.TLabel").pack(
            anchor="w", padx=8, pady=(6, 0))
        ttk.Scale(f, from_=0, to=255, variable=opa, orient=tk.HORIZONTAL,
                  command=lambda *_: self._set_obj_attr("opacity", int(opa.get()))
                  ).pack(fill=tk.X, padx=8, pady=(0, 8))
        pos = ttk.Frame(f, style="Panel.TFrame"); pos.pack(fill=tk.X, padx=8)
        ttk.Label(pos, text=f"Pos {int(obj.x)},{int(obj.y)}   "
                          f"Size {int(obj.w)}×{int(obj.h)}",
                  style="Muted.TLabel").pack(anchor="w")
        btnrow = ttk.Frame(self.prop_container, style="Panel.TFrame")
        btnrow.pack(fill=tk.X, pady=6)
        ttk.Button(btnrow, text="Duplicate",
                   command=self.duplicate_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(btnrow, text="Delete", style="Danger.TButton",
                   command=self.delete_selected).pack(side=tk.LEFT, padx=4)

    def _set_obj_attr(self, key: str, value) -> None:
        if self._suppress_prop_update or self.selected is None: return
        setattr(self.selected, key, value)
        self._render()

    def _build_text_prop(self, obj: TextObject) -> None:
        f = ttk.LabelFrame(self.prop_container, text="  TEXT  ")
        f.pack(fill=tk.X, pady=6)

        ttk.Label(f, text="Content", style="Panel.TLabel").pack(
            anchor="w", padx=8, pady=(6, 0))
        txt = tk.Text(f, height=3, bg=BG_PANEL_ALT, fg=FG,
                      insertbackground=FG, borderwidth=0,
                      highlightthickness=1, highlightcolor=ACCENT,
                      wrap="word")
        txt.insert("1.0", obj.text)
        txt.pack(fill=tk.X, padx=8, pady=(2, 6))
        def on_text_change(event=None):
            if self._suppress_prop_update: return
            obj.text = txt.get("1.0", "end-1c")
            obj.refresh_size(self._discover_fonts_lazy)
            self._render(); self._refresh_layers_list()
        txt.bind("<KeyRelease>", on_text_change)

        ttk.Label(f, text="Font", style="Panel.TLabel").pack(
            anchor="w", padx=8)
        fam_var = tk.StringVar(value=obj.font_family or "")
        cb = ttk.Combobox(f, textvariable=fam_var,
                          values=[n for n, _ in self._font_choices],
                          state="readonly")
        cb.pack(fill=tk.X, padx=8, pady=(2, 6))
        def on_fam(*_):
            obj.font_family = fam_var.get()
            for n, p in self._font_choices:
                if n == fam_var.get(): obj.font_path = p; break
            obj.refresh_size(self._discover_fonts_lazy); self._render()
        cb.bind("<<ComboboxSelected>>", on_fam)

        # Size + bold/italic
        row = ttk.Frame(f, style="Panel.TFrame"); row.pack(fill=tk.X, padx=8)
        size_v = tk.IntVar(value=obj.font_size)
        ttk.Label(row, text="Size", style="Panel.TLabel").pack(side=tk.LEFT)
        sc = ttk.Scale(row, from_=8, to=400, variable=size_v,
                       orient=tk.HORIZONTAL)
        sc.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        def on_size(*_):
            obj.font_size = int(size_v.get())
            obj.refresh_size(self._discover_fonts_lazy); self._render()
        sc.configure(command=lambda *_: on_size())
        bold_v = tk.BooleanVar(value=obj.bold)
        it_v = tk.BooleanVar(value=obj.italic)
        ttk.Checkbutton(f, text="Bold", variable=bold_v,
                        command=lambda: (setattr(obj, "bold", bold_v.get()),
                                         obj.refresh_size(self._discover_fonts_lazy),
                                         self._render())
                        ).pack(anchor="w", padx=8)
        ttk.Checkbutton(f, text="Italic", variable=it_v,
                        command=lambda: (setattr(obj, "italic", it_v.get()),
                                         obj.refresh_size(self._discover_fonts_lazy),
                                         self._render())
                        ).pack(anchor="w", padx=8)

        # Alignment
        align_row = ttk.Frame(f, style="Panel.TFrame"); align_row.pack(fill=tk.X, padx=8, pady=(4, 0))
        ttk.Label(align_row, text="Align", style="Panel.TLabel").pack(side=tk.LEFT)
        align_v = tk.StringVar(value=obj.align)
        for a in ("left", "center", "right"):
            ttk.Radiobutton(align_row, text=a, variable=align_v, value=a,
                            command=lambda: (setattr(obj, "align", align_v.get()),
                                             self._render())
                            ).pack(side=tk.LEFT, padx=2)

        # Color
        col_btn = tk.Button(f, text="■  Fill color", bg=obj.color, fg="#000000",
                            relief="flat", bd=0,
                            activebackground=obj.color)
        def pick_c():
            c = colorchooser.askcolor(color=obj.color, parent=self)
            if c and c[1]:
                obj.color = c[1]
                col_btn.configure(bg=c[1], activebackground=c[1])
                self._render()
        col_btn.configure(command=pick_c)
        col_btn.pack(fill=tk.X, padx=8, pady=6)

        # Stroke
        sw_v = tk.IntVar(value=obj.stroke_width)
        ttk.Label(f, text="Outline width", style="Panel.TLabel").pack(
            anchor="w", padx=8)
        srow = ttk.Frame(f, style="Panel.TFrame"); srow.pack(fill=tk.X, padx=8)
        ttk.Scale(srow, from_=0, to=20, variable=sw_v, orient=tk.HORIZONTAL,
                  command=lambda *_: (setattr(obj, "stroke_width", int(sw_v.get())),
                                      obj.refresh_size(self._discover_fonts_lazy),
                                      self._render())
                  ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        sc_btn = tk.Button(f, text="■  Outline color", bg=obj.stroke_color,
                           fg="#ffffff", relief="flat", bd=0,
                           activebackground=obj.stroke_color)
        def pick_sc():
            c = colorchooser.askcolor(color=obj.stroke_color, parent=self)
            if c and c[1]:
                obj.stroke_color = c[1]
                sc_btn.configure(bg=c[1], activebackground=c[1])
                self._render()
        sc_btn.configure(command=pick_sc)
        sc_btn.pack(fill=tk.X, padx=8, pady=6)

        # Shadow
        sh_v = tk.BooleanVar(value=obj.shadow)
        ttk.Checkbutton(f, text="Drop shadow", variable=sh_v,
                        command=lambda: (setattr(obj, "shadow", sh_v.get()),
                                         self._render())
                        ).pack(anchor="w", padx=8, pady=(6, 4))

    def _build_shape_prop(self, obj: ShapeObject) -> None:
        f = ttk.LabelFrame(self.prop_container, text="  SHAPE  ")
        f.pack(fill=tk.X, pady=6)
        ttk.Label(f, text=f"Type: {obj.shape}", style="Muted.TLabel").pack(
            anchor="w", padx=8, pady=(6, 4))

        has_fill = tk.BooleanVar(value=obj.fill_color is not None)
        fill_btn = tk.Button(f, text="■  Fill color",
                             bg=obj.fill_color or "#000000", fg="#ffffff",
                             relief="flat", bd=0)
        def pick_fill():
            c = colorchooser.askcolor(color=obj.fill_color or "#4f8cff",
                                      parent=self)
            if c and c[1]:
                obj.fill_color = c[1]
                fill_btn.configure(bg=c[1], activebackground=c[1])
                self._render()
        fill_btn.configure(command=pick_fill)
        def toggle_fill():
            if has_fill.get():
                obj.fill_color = obj.fill_color or "#4f8cff"
                fill_btn.configure(bg=obj.fill_color)
            else:
                obj.fill_color = None
            self._render()
        ttk.Checkbutton(f, text="Filled", variable=has_fill,
                        command=toggle_fill).pack(anchor="w", padx=8)
        fill_btn.pack(fill=tk.X, padx=8, pady=6)

        sw_v = tk.IntVar(value=obj.stroke_width)
        ttk.Label(f, text="Stroke width", style="Panel.TLabel").pack(
            anchor="w", padx=8)
        srow = ttk.Frame(f, style="Panel.TFrame"); srow.pack(fill=tk.X, padx=8)
        ttk.Scale(srow, from_=0, to=40, variable=sw_v, orient=tk.HORIZONTAL,
                  command=lambda *_: (setattr(obj, "stroke_width", int(sw_v.get())),
                                      self._render())
                  ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        sc_btn = tk.Button(f, text="■  Stroke color",
                           bg=obj.stroke_color or "#ffffff", fg="#000000",
                           relief="flat", bd=0)
        def pick_sc():
            c = colorchooser.askcolor(color=obj.stroke_color or "#ffffff",
                                      parent=self)
            if c and c[1]:
                obj.stroke_color = c[1]
                sc_btn.configure(bg=c[1], activebackground=c[1])
                self._render()
        sc_btn.configure(command=pick_sc)
        sc_btn.pack(fill=tk.X, padx=8, pady=6)

    # ------------------------------------------------------------------
    # Mouse handling
    # ------------------------------------------------------------------
    def _canvas_to_image_xy(self, x: int, y: int,
                            clamp: bool = False) -> Optional[tuple[float, float]]:
        if self.image is None: return None
        cx = self.canvas.canvasx(x); cy = self.canvas.canvasy(y)
        s = self.display_scale
        ix, iy = cx / s, cy / s
        w, h = self.image.size
        if clamp:
            return (max(0, min(w, ix)), max(0, min(h, iy)))
        if 0 <= ix < w and 0 <= iy < h:
            return (ix, iy)
        return None

    def on_mouse_move(self, e) -> None:
        if self.image is None:
            self.cursor_var.set(""); return
        pt = self._canvas_to_image_xy(e.x, e.y)
        if pt is None:
            self.cursor_var.set("")
            self._hide_brush_cursor()
        else:
            self.cursor_var.set(f"x: {int(pt[0])}  y: {int(pt[1])}   ")
            if self.tool.get() in ("draw", "erase"):
                self._show_brush_cursor(e.x, e.y)
            else:
                self._hide_brush_cursor()
        # update cursor for handles
        if self.tool.get() == "select" and self.selected:
            handle = self._handle_at(e.x, e.y)
            cursors = {
                "nw": "size_nw_se", "se": "size_nw_se",
                "ne": "size_ne_sw", "sw": "size_ne_sw",
                "n": "size_ns", "s": "size_ns",
                "e": "size_we", "w": "size_we",
                "rotate": "exchange",
            }
            self.canvas.configure(cursor=cursors.get(handle, "arrow"))

    def _show_brush_cursor(self, x: int, y: int) -> None:
        r = max(2, self.brush_size.get() * self.display_scale / 2)
        cx = self.canvas.canvasx(x); cy = self.canvas.canvasy(y)
        color = "#ffffff" if self.tool.get() == "draw" else "#ff4f6a"
        if self.brush_cursor_id is None:
            self.brush_cursor_id = self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r, outline=color, width=1)
        else:
            self.canvas.coords(self.brush_cursor_id,
                               cx - r, cy - r, cx + r, cy + r)
            self.canvas.itemconfig(self.brush_cursor_id, outline=color)

    def _hide_brush_cursor(self) -> None:
        if self.brush_cursor_id is not None:
            try: self.canvas.delete(self.brush_cursor_id)
            except Exception: pass
            self.brush_cursor_id = None

    def _snap(self, x: float, y: float) -> tuple[float, float]:
        if self.snap_to_grid.get():
            g = max(1, int(self.grid_size.get()))
            x = round(x / g) * g
            y = round(y / g) * g
        return x, y

    # -- Handle geometry helpers --
    def _handles(self, obj: BaseObject) -> dict[str, tuple[float, float]]:
        cx, cy = obj.center()
        ang = math.radians(obj.rotation)
        cos_a, sin_a = math.cos(ang), math.sin(ang)
        half_w, half_h = obj.w / 2, obj.h / 2
        pts_local = {
            "nw": (-half_w, -half_h), "n": (0, -half_h),
            "ne": (half_w, -half_h),  "e": (half_w, 0),
            "se": (half_w, half_h),   "s": (0, half_h),
            "sw": (-half_w, half_h),  "w": (-half_w, 0),
            "rotate": (0, -half_h - 30 / max(0.1, self.display_scale)),
        }
        s = self.display_scale
        return {name: (
            (cx + x * cos_a - y * sin_a) * s,
            (cy + x * sin_a + y * cos_a) * s)
            for name, (x, y) in pts_local.items()}

    def _handle_at(self, cx_screen: int, cy_screen: int) -> Optional[str]:
        if self.selected is None: return None
        cx = self.canvas.canvasx(cx_screen)
        cy = self.canvas.canvasy(cy_screen)
        for name, (hx, hy) in self._handles(self.selected).items():
            if abs(cx - hx) <= 7 and abs(cy - hy) <= 7:
                return name
        return None

    def _hit_top_object(self, ix: float, iy: float) -> Optional[BaseObject]:
        for obj in reversed(self.objects):
            if obj.visible and obj.hit_test(ix, iy):
                return obj
        return None

    def on_mouse_down(self, e) -> None:
        if self.image is None: return
        tool = self.tool.get()

        # Pan tool
        if tool == "pan":
            self.canvas.scan_mark(e.x, e.y)
            self.pan_anchor = (e.x, e.y); return

        # Handle grab in select tool
        if tool == "select" and self.selected:
            handle = self._handle_at(e.x, e.y)
            if handle:
                self._push_history()
                self.drag_mode = "rotate" if handle == "rotate" else f"resize-{handle}"
                pt = self._canvas_to_image_xy(e.x, e.y, clamp=True)
                self.drag_start_img = pt
                self.drag_start_obj = self._obj_snapshot(self.selected)
                return

        pt = self._canvas_to_image_xy(e.x, e.y)

        if tool == "select":
            if pt is None:
                self.selected = None
                self._render(); self._refresh_property_panel(); return
            hit = self._hit_top_object(*pt)
            if hit:
                self.selected = hit
                self._push_history()
                self.drag_mode = "move"
                self.drag_start_img = pt
                self.drag_start_obj = self._obj_snapshot(hit)
                self._render(); self._refresh_property_panel()
            else:
                self.selected = None
                self._render(); self._refresh_property_panel()
            return

        if pt is None: return

        if tool == "draw":
            self._push_history()
            self.last_point = pt
            self._draw_dot(pt, self.brush_color)
            self._render()
        elif tool == "erase":
            self._push_history()
            self.last_point = pt
            self._erase_dot(pt)
            self._render()
        elif tool == "eyedropper":
            self._eyedrop(pt)
        elif tool == "bucket":
            self._push_history()
            self._bucket_fill(int(pt[0]), int(pt[1]))
            self._render()
        elif tool == "text":
            self._add_text_object_at(pt)
        elif tool.startswith("shape"):
            kind = tool.split("-", 1)[1]
            self._push_history()
            obj = ShapeObject(kind)
            obj.x, obj.y = pt
            obj.w = obj.h = 1
            obj.fill_color = self.brush_color if kind in ("rect", "ellipse") else None
            obj.stroke_color = self.brush_color if kind in ("line", "arrow") else "#ffffff"
            obj.stroke_width = int(self.brush_size.get()) if kind in ("line", "arrow") else 2
            self.objects.append(obj)
            self.selected = obj
            self.drag_mode = "draw-shape"
            self.drag_start_img = pt
            self.drag_start_obj = self._obj_snapshot(obj)
            self._render(); self._refresh_property_panel()
        elif tool == "crop":
            self._clear_crop_rect()
            cx = self.canvas.canvasx(e.x); cy = self.canvas.canvasy(e.y)
            self.crop_start = (cx, cy)
            self.crop_rect_id = self.canvas.create_rectangle(
                cx, cy, cx, cy, outline=ACCENT, width=2, dash=(5, 3))

    def _obj_snapshot(self, obj: BaseObject) -> dict:
        return {"x": obj.x, "y": obj.y, "w": obj.w, "h": obj.h,
                "rotation": obj.rotation,
                "font_size": getattr(obj, "font_size", None)}

    def on_mouse_drag(self, e) -> None:
        if self.image is None: return
        tool = self.tool.get()

        if tool == "pan" and self.pan_anchor is not None:
            self.canvas.scan_dragto(e.x, e.y, gain=1); return

        if self.drag_mode == "move" and self.selected:
            pt = self._canvas_to_image_xy(e.x, e.y, clamp=True)
            if pt is None or self.drag_start_img is None: return
            dx = pt[0] - self.drag_start_img[0]
            dy = pt[1] - self.drag_start_img[1]
            nx = self.drag_start_obj["x"] + dx
            ny = self.drag_start_obj["y"] + dy
            nx, ny = self._snap(nx, ny)
            self.selected.x = nx; self.selected.y = ny
            self._render(); return

        if self.drag_mode and self.drag_mode.startswith("resize-") and self.selected:
            pt = self._canvas_to_image_xy(e.x, e.y, clamp=True)
            if pt is None or self.drag_start_img is None: return
            self._resize_selected(pt, self.drag_mode.split("-", 1)[1],
                                  shift=bool(e.state & 0x0001))
            self._render(); return

        if self.drag_mode == "rotate" and self.selected:
            cx, cy = self.selected.center()
            pt = self._canvas_to_image_xy(e.x, e.y, clamp=True)
            if pt is None: return
            ang = math.degrees(math.atan2(pt[1] - cy, pt[0] - cx)) + 90
            if e.state & 0x0001:  # shift = snap 15°
                ang = round(ang / 15) * 15
            self.selected.rotation = ang
            self._render(); return

        if self.drag_mode == "draw-shape" and self.selected:
            pt = self._canvas_to_image_xy(e.x, e.y, clamp=True)
            if pt is None or self.drag_start_img is None: return
            x0, y0 = self.drag_start_img
            x1, y1 = pt
            self.selected.x = min(x0, x1); self.selected.y = min(y0, y1)
            self.selected.w = max(1, abs(x1 - x0))
            self.selected.h = max(1, abs(y1 - y0))
            if isinstance(self.selected, ShapeObject) and self.selected.shape in ("line", "arrow"):
                # keep height at least stroke_width * 2 so it's visible / hit-testable
                self.selected.h = max(self.selected.h,
                                      self.selected.stroke_width * 2 + 2)
            self._render(); return

        if tool == "draw" and self.last_point is not None:
            pt = self._canvas_to_image_xy(e.x, e.y)
            if pt is None: return
            self._brush_stroke(self.last_point, pt, self.brush_color)
            self.last_point = pt
            self._render()
            self._show_brush_cursor(e.x, e.y)
        elif tool == "erase" and self.last_point is not None:
            pt = self._canvas_to_image_xy(e.x, e.y)
            if pt is None: return
            self._erase_stroke(self.last_point, pt)
            self.last_point = pt
            self._render()
            self._show_brush_cursor(e.x, e.y)
        elif tool == "crop" and self.crop_start is not None:
            cx = self.canvas.canvasx(e.x); cy = self.canvas.canvasy(e.y)
            x0, y0 = self.crop_start
            if self.crop_ratio:
                dx = cx - x0; dy = cy - y0
                if abs(dx) / max(1, abs(dy)) > self.crop_ratio:
                    dy = math.copysign(abs(dx) / self.crop_ratio, dy)
                else:
                    dx = math.copysign(abs(dy) * self.crop_ratio, dx)
                cx = x0 + dx; cy = y0 + dy
            self.canvas.coords(self.crop_rect_id, x0, y0, cx, cy)

    def on_mouse_up(self, e) -> None:
        # commit shape draw only if it has non-trivial size
        if self.drag_mode == "draw-shape" and self.selected:
            if self.selected.w < 3 and self.selected.h < 3:
                # cancel: remove the tiny shape
                try: self.objects.remove(self.selected)
                except ValueError: pass
                self.selected = None
                self._render(); self._refresh_property_panel()
            else:
                self.tool.set("select"); self._tool_changed()
                self._refresh_property_panel(); self._refresh_layers_list()
        self.drag_mode = None
        self.drag_start_img = None
        self.drag_start_obj = None
        self.last_point = None
        self.pan_anchor = None

    def _resize_selected(self, pt: tuple[float, float], handle: str,
                         shift: bool = False) -> None:
        # We approximate: work in axis-aligned space (ignore rotation for resize math).
        obj = self.selected
        snap = self.drag_start_obj
        x0, y0 = snap["x"], snap["y"]
        w0, h0 = snap["w"], snap["h"]
        x1, y1 = x0 + w0, y0 + h0
        px, py = pt
        if "n" in handle: y0 = min(y1 - 2, py)
        if "s" in handle: y1 = max(y0 + 2, py)
        if "w" in handle: x0 = min(x1 - 2, px)
        if "e" in handle: x1 = max(x0 + 2, px)
        nw = x1 - x0; nh = y1 - y0
        if shift and w0 > 0 and h0 > 0:
            aspect = w0 / h0
            if nw / max(1, nh) > aspect:
                nh = nw / aspect
                if "n" in handle: y0 = y1 - nh
                else: y1 = y0 + nh
            else:
                nw = nh * aspect
                if "w" in handle: x0 = x1 - nw
                else: x1 = x0 + nw
        obj.x, obj.y = x0, y0
        obj.w, obj.h = max(2, x1 - x0), max(2, y1 - y0)
        # For text objects: scale font size proportionally to height
        if isinstance(obj, TextObject) and snap.get("font_size"):
            scale = obj.h / max(1, h0)
            obj.font_size = max(4, int(snap["font_size"] * scale))
            obj.refresh_size(self._discover_fonts_lazy)

    def on_double_click(self, e) -> None:
        if self.image is None: return
        pt = self._canvas_to_image_xy(e.x, e.y)
        if pt is None: return
        # If double-click hits a text object, edit content
        hit = self._hit_top_object(*pt)
        if isinstance(hit, TextObject):
            self.selected = hit
            self.tool.set("select"); self._tool_changed()
            self._refresh_property_panel()
            new = simpledialog.askstring("Edit text", "Text content:",
                                         initialvalue=hit.text, parent=self)
            if new is not None:
                self._push_history()
                hit.text = new
                hit.refresh_size(self._discover_fonts_lazy)
                self._render(); self._refresh_property_panel()

    def on_right_click(self, e) -> None:
        if self.image is None: return
        pt = self._canvas_to_image_xy(e.x, e.y)
        m = tk.Menu(self, tearoff=0, bg=BG_PANEL, fg=FG,
                    activebackground=ACCENT, activeforeground="#ffffff")
        if pt is not None:
            hit = self._hit_top_object(*pt)
            if hit is not None:
                self.selected = hit
                self._render(); self._refresh_property_panel()
                m.add_command(label="Duplicate", command=self.duplicate_selected)
                m.add_command(label="Delete", command=self.delete_selected)
                m.add_command(label="Bring to front",
                              command=lambda: self._reorder_selected("front"))
                m.add_command(label="Send to back",
                              command=lambda: self._reorder_selected("back"))
                m.add_separator()
        m.add_command(label="Paste from clipboard",
                      command=self.paste_from_clipboard)
        m.add_command(label="Add text here",
                      command=lambda: pt and self._add_text_object_at(pt))
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    def _brush_stroke(self, p0, p1, color) -> None:
        draw = ImageDraw.Draw(self.image)
        size = max(1, int(self.brush_size.get()))
        draw.line([p0, p1], fill=color, width=size, joint="curve")
        r = size / 2
        draw.ellipse([p1[0] - r, p1[1] - r, p1[0] + r, p1[1] + r], fill=color)

    def _draw_dot(self, pt, color) -> None:
        draw = ImageDraw.Draw(self.image)
        r = max(1, int(self.brush_size.get())) / 2
        draw.ellipse([pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r], fill=color)

    def _erase_dot(self, pt) -> None:
        if self.image.mode != "RGBA":
            self.image = self.image.convert("RGBA")
        r = max(1, int(self.brush_size.get())) / 2
        mask = Image.new("L", self.image.size, 0)
        d = ImageDraw.Draw(mask)
        d.ellipse([pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r], fill=255)
        alpha = self.image.split()[3]
        alpha = ImageChops.subtract(alpha, mask)
        self.image.putalpha(alpha)

    def _erase_stroke(self, p0, p1) -> None:
        if self.image.mode != "RGBA":
            self.image = self.image.convert("RGBA")
        size = max(1, int(self.brush_size.get()))
        mask = Image.new("L", self.image.size, 0)
        d = ImageDraw.Draw(mask)
        d.line([p0, p1], fill=255, width=size, joint="curve")
        r = size / 2
        d.ellipse([p1[0] - r, p1[1] - r, p1[0] + r, p1[1] + r], fill=255)
        alpha = self.image.split()[3]
        alpha = ImageChops.subtract(alpha, mask)
        self.image.putalpha(alpha)

    def _eyedrop(self, pt) -> None:
        try:
            px = self._flattened().getpixel((int(pt[0]), int(pt[1])))
            hx = rgba_to_hex(px)
            self.brush_color = hx
            self.brush_swatch.configure(bg=hx, activebackground=hx)
            self.status.set(f"Picked color {hx}")
            self._persist_settings()
        except Exception as e:
            self.status.set(f"Eyedrop failed: {e}")

    def _bucket_fill(self, sx: int, sy: int) -> None:
        try:
            fill = hex_to_rgba(self.brush_color, 255)
            base = self.image
            if base.mode != "RGBA":
                base = base.convert("RGBA")
                self.image = base
            ImageDraw.floodfill(base, (sx, sy), fill, thresh=25)
        except Exception as e:
            self.status.set(f"Fill failed: {e}")

    # ------- Panning (MMB) -------
    def _pan_start(self, e) -> None: self.canvas.scan_mark(e.x, e.y)
    def _pan_move(self, e) -> None: self.canvas.scan_dragto(e.x, e.y, gain=1)

    # ------- Text creation -------
    def _add_text_object_at(self, pt: tuple[float, float]) -> None:
        text = simpledialog.askstring("Add text", "Text to place:",
                                      parent=self, initialvalue="Sample text")
        if not text:
            return
        self._push_history()
        obj = TextObject()
        obj.text = text
        obj.font_family = self.text_family.get() or ""
        for n, p in self._font_choices:
            if n == obj.font_family: obj.font_path = p; break
        obj.font_size = int(self.text_size.get())
        obj.color = self.text_color
        obj.refresh_size(self._discover_fonts_lazy)
        obj.x, obj.y = pt
        self.objects.append(obj)
        self.selected = obj
        self.tool.set("select"); self._tool_changed()
        self._render(); self._refresh_layers_list(); self._refresh_property_panel()

    # ------- Crop -------
    def _clear_crop_rect(self) -> None:
        if self.crop_rect_id is not None:
            try: self.canvas.delete(self.crop_rect_id)
            except Exception: pass
        self.crop_rect_id = None
        self.crop_start = None

    def apply_crop(self) -> None:
        if self.image is None or self.crop_rect_id is None: return
        x0, y0, x1, y1 = self.canvas.coords(self.crop_rect_id)
        p0 = self._clamp_to_image(x0, y0)
        p1 = self._clamp_to_image(x1, y1)
        left, right  = sorted([p0[0], p1[0]])
        top,  bottom = sorted([p0[1], p1[1]])
        if right - left < 2 or bottom - top < 2:
            messagebox.showwarning("Crop", "Selection is too small."); return
        self._push_history()
        self.image = self.image.crop((int(left), int(top),
                                      int(right), int(bottom)))
        # Shift objects
        for obj in self.objects:
            obj.x -= left; obj.y -= top
        self._clear_crop_rect()
        self._render()
        self.status.set("Cropped")

    def _clamp_to_image(self, cx: float, cy: float) -> tuple[float, float]:
        s = self.display_scale
        w, h = self.image.size
        ix = max(0, min(w, cx / s))
        iy = max(0, min(h, cy / s))
        return (ix, iy)

    # ------------------------------------------------------------------
    # Zoom / rendering
    # ------------------------------------------------------------------
    def zoom_fit(self) -> None:
        self.zoom_mode = "fit"; self._render()

    def zoom_100(self) -> None:
        self.zoom_mode = "manual"; self.display_scale = 1.0; self._render()

    def zoom_by(self, factor: float) -> None:
        if self.image is None: return
        self.zoom_mode = "manual"
        self.display_scale = max(0.05, min(16.0, self.display_scale * factor))
        self._render()

    def _wheel_zoom(self, e) -> None:
        factor = 1.15 if e.delta > 0 else 1 / 1.15
        self._wheel_zoom_at(e, factor)

    def _wheel_zoom_at(self, e, factor: float) -> None:
        if self.image is None: return
        pre = self._canvas_to_image_xy(e.x, e.y, clamp=True)
        self.zoom_mode = "manual"
        new_scale = max(0.05, min(16.0, self.display_scale * factor))
        if new_scale == self.display_scale: return
        self.display_scale = new_scale
        self._render()
        if pre is not None:
            # scroll so that (pre) stays under cursor
            target_x = pre[0] * self.display_scale - e.x
            target_y = pre[1] * self.display_scale - e.y
            sr = self.canvas.cget("scrollregion").split()
            if len(sr) == 4:
                _, _, sw, sh = map(float, sr)
                if sw > 0: self.canvas.xview_moveto(max(0, min(1, target_x / sw)))
                if sh > 0: self.canvas.yview_moveto(max(0, min(1, target_y / sh)))

    def _wheel_scroll(self, e) -> None:
        self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")

    def _wheel_scroll_h(self, e) -> None:
        self.canvas.xview_scroll(-1 if e.delta > 0 else 1, "units")

    def _render(self) -> None:
        self.brush_cursor_id = None
        self.canvas.delete("all")
        if self.image is None:
            self.info_var.set("No image loaded")
            self.canvas.configure(scrollregion=(0, 0, 0, 0))
            return
        cw = max(self.canvas.winfo_width(), 10)
        ch = max(self.canvas.winfo_height(), 10)
        iw, ih = self.image.size
        if self.zoom_mode == "fit":
            self.display_scale = min(cw / iw, ch / ih, 1.0)
        s = self.display_scale
        dw, dh = max(1, int(iw * s)), max(1, int(ih * s))

        # composite objects onto a temp image at full resolution then scale
        composite = self._flattened()
        resample = Image.LANCZOS if s < 1.0 else Image.NEAREST
        disp = composite.resize((dw, dh), resample) if s != 1.0 else composite
        self.display_image = ImageTk.PhotoImage(disp)
        self.canvas.create_image(0, 0, anchor="nw", image=self.display_image)
        self.canvas.configure(scrollregion=(0, 0, dw, dh))

        # Grid overlay
        if self.show_grid.get():
            g = max(2, int(self.grid_size.get())) * s
            x = 0
            while x < dw:
                self.canvas.create_line(x, 0, x, dh, fill="#ffffff",
                                        stipple="gray25")
                x += g
            y = 0
            while y < dh:
                self.canvas.create_line(0, y, dw, y, fill="#ffffff",
                                        stipple="gray25")
                y += g

        # Rulers
        if self.show_rulers.get():
            step = 50
            for x in range(0, iw, step):
                sx = x * s
                self.canvas.create_line(sx, 0, sx, 6, fill=ACCENT)
                self.canvas.create_text(sx + 2, 8, text=str(x),
                                        anchor="nw", fill=FG_MUTED,
                                        font=("Segoe UI", 7))
            for y in range(0, ih, step):
                sy = y * s
                self.canvas.create_line(0, sy, 6, sy, fill=ACCENT)
                self.canvas.create_text(8, sy + 2, text=str(y),
                                        anchor="nw", fill=FG_MUTED,
                                        font=("Segoe UI", 7))

        # Rule-of-thirds while cropping
        if self.crop_rect_id is not None and self.crop_thirds:
            try:
                x0, y0, x1, y1 = self.canvas.coords(self.crop_rect_id)
                for i in (1, 2):
                    xx = x0 + (x1 - x0) * i / 3
                    yy = y0 + (y1 - y0) * i / 3
                    self.canvas.create_line(xx, y0, xx, y1,
                                            fill="#ffffff", dash=(2, 4))
                    self.canvas.create_line(x0, yy, x1, yy,
                                            fill="#ffffff", dash=(2, 4))
            except Exception:
                pass

        # Selection handles
        if self.tool.get() == "select" and self.selected is not None:
            self._draw_selection_outline(self.selected)

        self.info_var.set(
            f"{iw} × {ih} px  ·  zoom {s * 100:.0f}%"
            + (f"  ·  {os.path.basename(self.current_path)}"
               if self.current_path else "")
            + (f"  ·  {len(self.objects)} objects" if self.objects else ""))

    def _draw_selection_outline(self, obj: BaseObject) -> None:
        pts = obj.corners()
        s = self.display_scale
        spts = [(x * s, y * s) for x, y in pts]
        # dashed polygon
        for i in range(4):
            a = spts[i]; b = spts[(i + 1) % 4]
            self.canvas.create_line(a[0], a[1], b[0], b[1],
                                    fill=ACCENT, width=1, dash=(4, 3))
        # handles
        for name, (hx, hy) in self._handles(obj).items():
            if name == "rotate":
                # line from top-mid handle to rotate handle
                (tmx, tmy) = self._handles(obj)["n"]
                self.canvas.create_line(tmx, tmy, hx, hy, fill=ACCENT)
                r = 6
                self.canvas.create_oval(hx - r, hy - r, hx + r, hy + r,
                                        fill=ACCENT, outline="#ffffff")
            else:
                r = 5
                self.canvas.create_rectangle(hx - r, hy - r, hx + r, hy + r,
                                             fill=HANDLE_FILL,
                                             outline=HANDLE_OUT, width=1)

    # ------------------------------------------------------------------
    # Title / modified state
    # ------------------------------------------------------------------
    def _set_modified(self, v: bool) -> None:
        self.modified = v
        self._update_title()

    def _update_title(self) -> None:
        name = os.path.basename(self.current_path) if self.current_path else "Untitled"
        star = "●  " if self.modified else ""
        self.title(f"{star}{name}  —  {APP_NAME}  v{APP_VERSION}")

    # ------------------------------------------------------------------
    # Dialogs
    # ------------------------------------------------------------------
    def _show_about(self) -> None:
        self._open_about_dialog(title=f"About {APP_NAME}", is_splash=False)

    def _show_splash(self) -> None:
        # Only auto-show once per app run
        if getattr(self, "_splash_shown", False):
            return
        self._splash_shown = True
        self._open_about_dialog(title=f"Welcome to {APP_NAME}", is_splash=True)

    def _open_about_dialog(self, title: str, is_splash: bool) -> None:
        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=BG_PANEL)
        win.transient(self)
        win.resizable(False, False)
        try:
            win.attributes("-topmost", True)
            win.after(400, lambda: win.attributes("-topmost", False))
        except Exception:
            pass

        pad = tk.Frame(win, bg=BG_PANEL, padx=28, pady=22)
        pad.pack(fill=tk.BOTH, expand=True)

        # Header
        tk.Label(pad, text=APP_NAME, bg=BG_PANEL, fg=FG,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(pad, text=f"Version {APP_VERSION}", bg=BG_PANEL, fg=ACCENT,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(2, 12))

        tag = ("Welcome! A modern, keyboard-friendly image editor\n"
               "built with Python, Tkinter and Pillow.") if is_splash else \
              ("A modern, keyboard-friendly image editor built with\n"
               "Python, Tkinter and Pillow.")
        tk.Label(pad, text=tag, bg=BG_PANEL, fg=FG_MUTED,
                 font=("Segoe UI", 10), justify="left").pack(anchor="w")

        # Separator
        tk.Frame(pad, bg=BG_PANEL_ALT, height=1).pack(fill=tk.X, pady=14)

        # Developer block
        tk.Label(pad, text="Developer", bg=BG_PANEL, fg=FG_MUTED,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(pad, text=f"{APP_AUTHOR}   ·   {APP_AUTHOR_FA}",
                 bg=BG_PANEL, fg=FG,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(2, 12))

        def make_link(parent, label, url):
            lbl = tk.Label(parent, text=label, bg=BG_PANEL, fg=ACCENT,
                           cursor="hand2",
                           font=("Segoe UI", 10, "underline"))
            lbl.pack(anchor="w", pady=2)
            lbl.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            lbl.bind("<Enter>",
                     lambda e, l=lbl: l.configure(fg=ACCENT_HOVER))
            lbl.bind("<Leave>",
                     lambda e, l=lbl: l.configure(fg=ACCENT))
            return lbl

        make_link(pad, f"🌐  Website     —  {APP_WEBSITE}", APP_WEBSITE)
        make_link(pad, f"💼  GitHub      —  {APP_GITHUB}",  APP_GITHUB)
        make_link(pad, f"in  LinkedIn   —  {APP_LINKEDIN}", APP_LINKEDIN)

        tk.Frame(pad, bg=BG_PANEL_ALT, height=1).pack(fill=tk.X, pady=14)
        tk.Label(pad, text=APP_COPYRIGHT, bg=BG_PANEL, fg=FG_MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w")

        # Buttons
        btn_row = tk.Frame(pad, bg=BG_PANEL)
        btn_row.pack(fill=tk.X, pady=(16, 0))

        if is_splash:
            dont_var = tk.BooleanVar(
                value=not self.settings.get("show_splash", True))
            cb = tk.Checkbutton(
                btn_row, text="Don't show on startup", variable=dont_var,
                bg=BG_PANEL, fg=FG_MUTED, activebackground=BG_PANEL,
                activeforeground=FG, selectcolor=BG_PANEL_ALT,
                font=("Segoe UI", 9), bd=0, highlightthickness=0)
            cb.pack(side=tk.LEFT)

            def _close():
                self.settings["show_splash"] = not dont_var.get()
                save_settings(self.settings)
                win.destroy()
        else:
            _close = win.destroy

        close_btn = tk.Button(btn_row, text="Close", command=_close,
                              bg=ACCENT, fg="#ffffff",
                              activebackground=ACCENT_HOVER,
                              activeforeground="#ffffff",
                              bd=0, padx=18, pady=6,
                              font=("Segoe UI", 10, "bold"),
                              cursor="hand2")
        close_btn.pack(side=tk.RIGHT)

        # Respect "don't show" preference for splash auto-open
        if is_splash and not self.settings.get("show_splash", True):
            win.destroy()
            return

        win.update_idletasks()
        try:
            x = self.winfo_rootx() + (self.winfo_width() - win.winfo_reqwidth()) // 2
            y = self.winfo_rooty() + (self.winfo_height() - win.winfo_reqheight()) // 3
            win.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass
        win.protocol("WM_DELETE_WINDOW", _close)
        win.bind("<Escape>", lambda e: _close())
        win.grab_set()


    def _show_shortcuts(self) -> None:
        messagebox.showinfo(
            "Keyboard shortcuts",
            "File\n"
            "  Ctrl+N          New blank image\n"
            "  Ctrl+O          Open\n"
            "  Ctrl+S          Save\n"
            "  Ctrl+Shift+S    Save As\n"
            "  Ctrl+K          Compress to size…\n"
            "  Ctrl+Shift+C    Copy image to clipboard\n"
            "  Ctrl+Shift+V    Paste from clipboard\n"
            "  Ctrl+Q          Exit\n\n"
            "Edit\n"
            "  Ctrl+Z          Undo\n"
            "  Ctrl+Y / Ctrl+Shift+Z   Redo\n"
            "  Ctrl+D          Duplicate selected object\n"
            "  Delete          Delete selected object\n"
            "  Ctrl+]  /  Ctrl+[   Bring forward / send back\n"
            "  Arrows          Nudge selection (Shift = 10 px)\n\n"
            "View\n"
            "  Ctrl + / -      Zoom in / out\n"
            "  Ctrl+0          Fit to window\n"
            "  Ctrl+1          Actual pixels (100 %)\n"
            "  Ctrl+Wheel      Zoom under cursor\n"
            "  Middle-drag / H+drag   Pan\n\n"
            "Tools (when not typing)\n"
            "  V select · H pan · B brush · E eraser · I eyedropper\n"
            "  T text · R rect · O ellipse · L line · A arrow · C crop\n\n"
            "Crop\n"
            "  Enter           Apply crop\n"
            "  Esc             Cancel selection")

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------
    def _on_close(self) -> None:
        self._persist_settings()
        if self.modified:
            r = messagebox.askyesnocancel(
                "Unsaved changes",
                "You have unsaved changes. Save before exit?")
            if r is None: return
            if r: self.save()
        self.destroy()


# ---------------------------------------------------------------------------
# Small modal helper (themed)
# ---------------------------------------------------------------------------
class _ModalDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, title: str) -> None:
        super().__init__(parent)
        self.title(title); self.configure(bg=BG_PANEL)
        self.transient(parent); self.resizable(False, False)
        self.body = ttk.Frame(self, style="Panel.TFrame")
        self.body.pack(fill=tk.BOTH, expand=True)
        self._result = {"ok": False}
        btn_row = ttk.Frame(self, style="Panel.TFrame")
        btn_row.pack(fill=tk.X, pady=(6, 12))
        ttk.Button(btn_row, text="Cancel",
                   command=self._cancel).pack(side=tk.RIGHT, padx=(4, 14))
        ttk.Button(btn_row, text="OK", style="Accent.TButton",
                   command=self._ok).pack(side=tk.RIGHT, padx=4)
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self._cancel())

    def _ok(self):     self._result["ok"] = True;  self.destroy()
    def _cancel(self): self._result["ok"] = False; self.destroy()

    def run(self, *_vars, extra=None):
        self.update_idletasks()
        p = self.master
        try:
            x = p.winfo_rootx() + (p.winfo_width()  - self.winfo_reqwidth())  // 2
            y = p.winfo_rooty() + (p.winfo_height() - self.winfo_reqheight()) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass
        self.grab_set(); self.wait_window(self)
        return True if self._result["ok"] else None


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------
def main() -> None:
    app = ImageEditor()
    app.mainloop()


if __name__ == "__main__":
    main()

# Pro Image Editor

A professional, lightweight Windows image editor written in **Python** with a modern **Tkinter** UI and **Pillow** as the imaging backend. It gives you fast, everyday image-editing tools plus a smart compressor that hits a target file size **without downscaling** the image.

---

## Features

- **Open / Save** any common format: `PNG, JPG/JPEG, BMP, GIF, TIFF, WEBP`
- **Choose the exact output location** and format on save
- **Add text on image** — click anywhere, custom font size and color
- **Free-hand drawing / painting** — adjustable brush size and color
- **Crop** — drag a rectangle on the image and click *Apply Crop*
- **Rotate** 90° / -90° and **Flip** horizontally / vertically
- **Convert format** by saving into a different extension
- **Lossless saves by default**:
  - PNG: `compress_level=9`, `optimize=True`
  - JPEG: `quality=100`, `subsampling=0`
  - WEBP: `lossless=True, quality=100, method=6`
  - TIFF: LZW compression
- **Smart compression to a target size (KB)** — resolution is **preserved**; the app binary-searches the best JPEG/WEBP quality to fit your target while keeping the original dimensions
- **Undo / Redo** (Ctrl+Z / Ctrl+Y), **Reset to original**
- Modern dark UI, keyboard shortcuts, correct EXIF orientation on load

> Note on "compression without quality loss": true mathematical lossless compression to an arbitrary target size is not possible for photographic content. This app keeps the **full original resolution** (no resizing) and finds the highest visually-lossless quality that fits your size budget using JPEG or WEBP. For pure lossless output, save as PNG, WEBP-lossless, or TIFF-LZW (no target size).

---

## Requirements

- **Windows 10/11** (also works on macOS/Linux)
- **Python 3.10+**
- **Pillow**

Install Pillow:

```bash
pip install Pillow
```

Tkinter ships with the standard Python installer on Windows.

---

## Run

```bash
python image_editor.py
```

Or double-click `image_editor.py` if `.py` files are associated with Python.

---

## Build a single `.exe` (optional)

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "ProImageEditor" image_editor.py
```

The executable will appear in `dist/ProImageEditor.exe`.

---

## Keyboard Shortcuts

| Shortcut  | Action     |
|-----------|-----------|
| `Ctrl+O`  | Open image |
| `Ctrl+S`  | Save as    |
| `Ctrl+Z`  | Undo       |
| `Ctrl+Y`  | Redo       |

---

## How to Use

1. Click **Open…** and select an image.
2. Choose a tool from the left panel:
   - **Draw / Brush** — paint on the image
   - **Add Text (click)** — click on the canvas, type text, press OK
   - **Crop (drag)** — drag a rectangle, then click **Apply Crop**
3. Use **Rotate** / **Flip** in the top bar for orientation.
4. **Save As…** to export in your chosen format at maximum quality.
5. **Compress to size…** to save a JPEG/WEBP under a target KB size while keeping full resolution.

---

## License
All Rights Reserved to Mohammad Ali Bazzazi


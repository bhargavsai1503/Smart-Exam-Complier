"""
ocr_extract.py — Poppler-free OCR using PyMuPDF rendering

This module renders PDF pages to images using PyMuPDF (fitz) and then runs
OpenCV preprocessing + Tesseract OCR with rotation/PSM trials.

API:
    extract_text_from_file(filepath, dpi=800, debug_save_path=None)
    -> returns (full_text_str, line_conf_map)
"""

import os
from pathlib import Path
import fitz               # PyMuPDF
import pytesseract
from PIL import Image
import numpy as np
import cv2
import statistics
import io

# If you need to pin tesseract path uncomment & edit:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---------------------- helpers ------------------------------------

def _ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)

def _bgr_from_pil(pil_img):
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def _deskew_image(gray):
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(bw < 255))
    if coords.shape[0] < 10:
        return gray, 0.0
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    if abs(angle) < 0.3:
        return gray, 0.0
    (h, w) = gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return rotated, angle

def _auto_contrast_and_sharpen(gray):
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    cl = clahe.apply(gray)
    gaussian = cv2.GaussianBlur(cl, (0,0), 3)
    unsharp = cv2.addWeighted(cl, 1.5, gaussian, -0.5, 0)
    return unsharp

def _preprocess_image(cv_img, page_num=1, debug_path=None, upscale_min=1200):
    """
    cv_img: BGR image (numpy array)
    returns: preprocessed binary image (numpy array)
    """
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    # Upscale small images for clarity
    h, w = gray.shape
    if max(h, w) < upscale_min:
        scale = float(upscale_min) / max(h, w)
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

    gray = cv2.medianBlur(gray, 3)
    gray, _ = _deskew_image(gray)
    gray = _auto_contrast_and_sharpen(gray)

    # adaptive threshold (parameters tuned for scanned pages)
    th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 35, 15)

    # small morphological close to join broken characters
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel, iterations=1)

    if debug_path:
        _ensure_dir(debug_path)
        try:
            debug_img = os.path.join(debug_path, f"page_{page_num:03d}_prep.png")
            cv2.imwrite(debug_img, th)
        except Exception:
            pass

    return th

def _ocr_image(cv_img, config="--oem 3 --psm 3"):
    """
    Runs pytesseract.image_to_data and assembles line-level joined text + confidences.
    Returns (joined_text, raw_data_dict, line_conf_map)
    """
    data = pytesseract.image_to_data(cv_img, output_type=pytesseract.Output.DICT, config=config, lang='eng')
    n = len(data.get('level', []))
    lines, confs = {}, {}
    for i in range(n):
        text = str(data['text'][i]).strip()
        if not text:
            continue
        block = data.get('block_num', [0])[i]
        par = data.get('par_num', [0])[i]
        line = data.get('line_num', [0])[i]
        key = f"{block}-{par}-{line}"
        lines.setdefault(key, []).append(text)
        try:
            confs.setdefault(key, []).append(float(data['conf'][i]))
        except Exception:
            confs.setdefault(key, []).append(0.0)

    joined_lines = []
    line_conf_map = {}
    for k in sorted(lines.keys(), key=lambda x: tuple(map(int, x.split('-')))):
        txt = " ".join(lines[k])
        avg_conf = statistics.mean(confs.get(k, [0.0])) if confs.get(k) else 0.0
        joined_lines.append(txt)
        line_conf_map[k] = {"text": txt, "avg_conf": avg_conf}

    text = "\n".join(joined_lines)
    return text, data, line_conf_map

def _score_text(text, data):
    confs = []
    for c in data.get('conf', []):
        try:
            confs.append(float(c))
        except Exception:
            continue
    avg_conf = (sum(confs) / len(confs)) if confs else 0.0
    return len(text) * (1 + avg_conf / 100.0)

# ---------------- PDF rendering via PyMuPDF (no poppler) --------------------

def _render_pdf_page_to_pil(pdf_path, page_number, scale=2.0):
    """
    Render a single PDF page to a PIL Image using PyMuPDF.
    scale: multiplier for zoom (1.0 = 72 DPI). Use scale ~ 10 for high DPI or compute from dpi param.
    """
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)  # RGB pixmap
    mode = "RGB"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    doc.close()
    return img

def _render_pdf_pages_to_pil(pdf_path, dpi=800):
    """
    Render all pages to list of PIL Images. dpi controls scale.
    PyMuPDF default is 72 DPI. To get target DPI, scale = dpi / 72.
    """
    scale = dpi / 72.0
    doc = fitz.open(pdf_path)
    pil_pages = []
    try:
        for i in range(len(doc)):
            page = doc.load_page(i)
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pil_pages.append(img)
    finally:
        doc.close()
    return pil_pages

# ---------------- Main extract functions -----------------------------------

def extract_text_from_file(filepath, dpi=800, debug_save_path=None):
    ext = filepath.lower().split('.')[-1]
    if ext == 'pdf':
        return extract_from_pdf(filepath, dpi=dpi, debug_save_path=debug_save_path)
    elif ext in ('jpg', 'jpeg', 'png', 'tif', 'tiff', 'bmp'):
        return extract_from_image(filepath, dpi=dpi, debug_save_path=debug_save_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def extract_from_pdf(pdf_path, dpi=800, debug_save_path=None):
    """
    Try PyMuPDF text extraction first. If insufficient, render pages with PyMuPDF
    and run OCR on rendered images. This avoids pdf2image/poppler entirely.
    Returns (text, line_conf_map)
    """
    # 1) try PyMuPDF text layer
    try:
        doc = fitz.open(pdf_path)
        texts = []
        for p in doc:
            texts.append(p.get_text("text"))
        doc.close()
        combined = "\n".join(texts).strip()
        if len(combined) > 500 and any(ch.isalnum() for ch in combined):
            # Good searchable text -> return it (no OCR required)
            if debug_save_path:
                _ensure_dir(debug_save_path)
                with open(os.path.join(debug_save_path, "pymupdf_text.txt"), "w", encoding="utf-8") as f:
                    f.write(combined)
            return combined, {}
    except Exception:
        # If PyMuPDF text extraction fails, proceed to render+OCR
        pass

    # 2) Render pages to images using PyMuPDF and OCR each page
    debug_path = debug_save_path or None
    if debug_path:
        _ensure_dir(debug_path)

    pil_pages = _render_pdf_pages_to_pil(pdf_path, dpi=dpi)
    all_pages_text = []
    aggregate_line_map = {}

    for pnum, pil_img in enumerate(pil_pages, start=1):
        # Convert to OpenCV BGR
        cv_img = _bgr_from_pil(pil_img)
        prepped = _preprocess_image(cv_img, page_num=pnum, debug_path=debug_path)

        best_text = ""
        best_score = -1
        best_line_map = {}

        # Try multiple PSMs and small angle rotations
        for psm in (6, 3, 1, 11):
            for angle in (0, -2, 2, -5, 5, -8, 8):
                if angle == 0:
                    trial = prepped
                else:
                    (h, w) = prepped.shape
                    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
                    trial = cv2.warpAffine(prepped, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

                cfg = f"--oem 3 --psm {psm}"
                text, data, line_map = _ocr_image(trial, config=cfg)
                score = _score_text(text, data)
                if score > best_score:
                    best_score = score
                    best_text = text
                    best_line_map = line_map

        # clean hyphen breaks
        best_text = best_text.replace('-\n', '')
        all_pages_text.append(f"--- PAGE {pnum} ---\n{best_text}\n")

        # attach to aggregate map with page prefix
        for k, v in best_line_map.items():
            aggregate_line_map[f"{pnum}_{k}"] = v

    full_text = "\n".join(all_pages_text)
    if debug_path:
        _ensure_dir(debug_path)
        with open(os.path.join(debug_path, "extracted_cli.txt"), "w", encoding="utf-8") as f:
            f.write(full_text)

    return full_text, aggregate_line_map

def extract_from_image(image_path, dpi=800, debug_save_path=None):
    pil = Image.open(image_path).convert("RGB")
    cv_img = _bgr_from_pil(pil)
    prepped = _preprocess_image(cv_img, page_num=1, debug_path=debug_save_path)
    text, data, line_map = _ocr_image(prepped)
    text = text.replace('-\n', '')
    if debug_save_path:
        _ensure_dir(debug_save_path)
        with open(os.path.join(debug_save_path, "extracted_cli.txt"), "w", encoding="utf-8") as f:
            f.write(text)
    return text, line_map

# -------------------- CLI for quick testing -------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ocr_extract.py <pdf-or-image> [debug_folder]")
        sys.exit(1)
    inp = sys.argv[1]
    debug = sys.argv[2] if len(sys.argv) > 2 else "debug_images"
    txt, lines = extract_text_from_file(inp, dpi=800, debug_save_path=debug)
    _ensure_dir(debug)
    with open(os.path.join(debug, "extracted_cli.txt"), "w", encoding="utf-8") as f:
        f.write(txt)
    print("[INFO] Wrote extracted text to", os.path.join(debug, "extracted_cli.txt"))
    print("---- Preview ----")
    print(txt[:1500])

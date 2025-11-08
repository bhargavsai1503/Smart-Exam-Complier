"""
<<<<<<< HEAD
ocr_extract.py — Poppler-free OCR using PyMuPDF rendering

This module renders PDF pages to images using PyMuPDF (fitz) and then runs
OpenCV preprocessing + Tesseract OCR with rotation/PSM trials.
=======
ocr_extract.py — Google Cloud Vision API Implementation

This module replaces the local Tesseract/OpenCV implementation with
calls to the Google Cloud Vision API for much higher accuracy.

It maintains the *exact same function signature* as the original file
so it can be used as a drop-in replacement.
>>>>>>> final_version

API:
    extract_text_from_file(filepath, dpi=800, debug_save_path=None)
    -> returns (full_text_str, line_conf_map)
"""

import os
<<<<<<< HEAD
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
=======
import io
from pathlib import Path
import fitz  # PyMuPDF
from google.cloud import vision
>>>>>>> final_version

# ---------------------- helpers ------------------------------------

def _ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)

<<<<<<< HEAD
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
=======
def _save_debug_pdf_pages(pdf_path, debug_path):
    """
    Saves the original PDF pages as images for debugging.
    This replaces the old '_preprocess_image' debug output.
    """
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            page = doc.load_page(i)
            # Use a reasonable DPI for the debug preview
            pix = page.get_pixmap(dpi=200)
            debug_img = os.path.join(debug_path, f"page_{i+1:03d}_prep.png")
            pix.save(debug_img)
        doc.close()
    except Exception as e:
        print(f"[WARN] Could not save debug PDF pages: {e}")

def _parse_vision_response(response):
    """
    Parses a Google Cloud Vision 'full_text_annotation'
    into a full text string and a line_conf_map.
    """
    if not response or not response.full_text_annotation:
        return "", {}

    full_text = response.full_text_annotation.text
    line_conf_map = {}
    
    # Rebuild a line-map similar to the original script's output
    # Key: "page_block_paragraph_line"
    line_num = 1
    for p, page in enumerate(response.full_text_annotation.pages):
        for b, block in enumerate(page.blocks):
            for pa, paragraph in enumerate(block.paragraphs):
                line_text = ""
                line_confidences = []
                for word in paragraph.words:
                    word_text = "".join([s.text for s in word.symbols])
                    line_text += word_text + " "
                    line_confidences.append(word.confidence)
                
                if line_text:
                    avg_conf = sum(line_confidences) / len(line_confidences) if line_confidences else 0.0
                    key = f"{p+1}_{b+1}_{pa+1}_{line_num}"
                    line_conf_map[key] = {
                        "text": line_text.strip(),
                        "avg_conf": avg_conf
                    }
                    line_num += 1
    
    return full_text, line_conf_map
>>>>>>> final_version

# ---------------- Main extract functions -----------------------------------

def extract_text_from_file(filepath, dpi=800, debug_save_path=None):
<<<<<<< HEAD
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
=======
    """
    Main entry point. Detects file type and calls the appropriate extractor.
    'dpi' parameter is ignored as it's not needed for the Vision API,
    but it's kept for compatibility with the old function signature.
    """
    ext = str(filepath).lower().split('.')[-1]
    if ext == 'pdf':
        return extract_from_pdf(filepath, debug_save_path=debug_save_path)
    elif ext in ('jpg', 'jpeg', 'png', 'tif', 'tiff', 'bmp'):
        return extract_from_image(filepath, debug_save_path=debug_save_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def extract_from_pdf(pdf_path, debug_save_path=None):
    """
    Extracts text from a PDF.
    Tries PyMuPDF text layer first. If that fails, calls Google Vision API.
    """
    # 1) Try PyMuPDF text layer (same as old script)
>>>>>>> final_version
    try:
        doc = fitz.open(pdf_path)
        texts = []
        for p in doc:
            texts.append(p.get_text("text"))
        doc.close()
        combined = "\n".join(texts).strip()
        if len(combined) > 500 and any(ch.isalnum() for ch in combined):
<<<<<<< HEAD
            # Good searchable text -> return it (no OCR required)
=======
>>>>>>> final_version
            if debug_save_path:
                _ensure_dir(debug_save_path)
                with open(os.path.join(debug_save_path, "pymupdf_text.txt"), "w", encoding="utf-8") as f:
                    f.write(combined)
<<<<<<< HEAD
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
=======
            # Return text, empty map (no confidence for searchable text)
            return combined, {}
    except Exception:
        pass  # Failed text extraction, proceed to OCR

    # 2) Call Google Cloud Vision API for PDF
    print(f"[INFO] No searchable text found. Starting Google Vision API OCR for {pdf_path}")
    client = vision.ImageAnnotatorClient()

    with io.open(pdf_path, 'rb') as f:
        content = f.read()

    input_config = vision.InputConfig(
        content=content, mime_type='application/pdf')
    
    features = [vision.Feature(
        type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)]

    # PDF processing is asynchronous
    request = vision.AnnotateFileRequest(
        input_config=input_config, features=features)

    operation = client.async_batch_annotate_files(requests=[request])
    print('[INFO] Waiting for Vision API PDF operation to complete...')
    response = operation.result(timeout=300) # 300-second timeout

    # Get the first (and only) file response
    file_response = response.responses[0]
    
    # Parse the full response
    full_text, line_conf_map = _parse_vision_response(file_response)
    
    full_text = f"--- OCR Result from Google Cloud Vision ---\n\n{full_text}"

    if debug_save_path:
        _ensure_dir(debug_save_path)
        # Save the main text output
        with open(os.path.join(debug_save_path, "extracted_cli.txt"), "w", encoding="utf-8") as f:
            f.write(full_text)
        # Save debug images of the *original* pages
        _save_debug_pdf_pages(pdf_path, debug_save_path)

    return full_text, line_conf_map

def extract_from_image(image_path, debug_save_path=None):
    """
    Extracts text from a single image file using Google Vision API.
    """
    print(f"[INFO] Starting Google Vision API OCR for {image_path}")
    client = vision.ImageAnnotatorClient()

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    
    # Run document text detection
    response = client.document_text_detection(image=image)
    
    if response.error.message:
        raise Exception(
            f'{response.error.message}\nFor more info on error messages, '
            'check: https://cloud.google.com/apis/design/errors'
        )
    
    full_text, line_conf_map = _parse_vision_response(response)
    
    full_text = f"--- OCR Result from Google Cloud Vision ---\n\n{full_text}"

    if debug_save_path:
        _ensure_dir(debug_save_path)
        with open(os.path.join(debug_save_path, "extracted_cli.txt"), "w", encoding="utf-8") as f:
            f.write(full_text)
    
    return full_text, line_conf_map
>>>>>>> final_version

# -------------------- CLI for quick testing -------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ocr_extract.py <pdf-or-image> [debug_folder]")
<<<<<<< HEAD
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
=======
        print("\n[IMPORTANT] Make sure GOOGLE_APPLICATION_CREDENTIALS is set.")
        sys.exit(1)
    
    inp = sys.argv[1]
    debug = sys.argv[2] if len(sys.argv) > 2 else "debug_images"
    
    print(f"[INFO] Running extraction on: {inp}")
    try:
        txt, lines = extract_text_from_file(inp, debug_save_path=debug)
        _ensure_dir(debug)
        
        print("\n[INFO] Wrote extracted text to", os.path.join(debug, "extracted_cli.txt"))
        print("---- Text Preview (first 1500 chars) ----")
        print(txt[:1500])
        print("\n---- Line Map Preview (first 5 lines) ----")
        for i, (k, v) in enumerate(lines.items()):
            if i >= 5:
                break
            print(f"{k}: {v['text'][:50]}... (Conf: {v['avg_conf']:.2f})")

    except Exception as e:
        print(f"\n[ERROR] An error occurred during extraction: {e}")
        print("Please ensure your Google Cloud credentials are set correctly.")
>>>>>>> final_version

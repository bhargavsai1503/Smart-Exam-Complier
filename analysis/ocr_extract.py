"""
ocr_extract.py — Google Cloud Vision API Implementation

This module replaces the local Tesseract/OpenCV implementation with
calls to the Google Cloud Vision API for much higher accuracy.

It maintains the *exact same function signature* as the original file
so it can be used as a drop-in replacement.

API:
    extract_text_from_file(filepath, dpi=800, debug_save_path=None)
    -> returns (full_text_str, line_conf_map)
"""

import os
import io
from pathlib import Path
import fitz  # PyMuPDF
from google.cloud import vision

# ---------------------- helpers ------------------------------------

def _ensure_dir(p):
    Path(p).mkdir(parents=True, exist_ok=True)

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

# ---------------- Main extract functions -----------------------------------

def extract_text_from_file(filepath, dpi=800, debug_save_path=None):
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
    try:
        doc = fitz.open(pdf_path)
        texts = []
        for p in doc:
            texts.append(p.get_text("text"))
        doc.close()
        combined = "\n".join(texts).strip()
        if len(combined) > 500 and any(ch.isalnum() for ch in combined):
            if debug_save_path:
                _ensure_dir(debug_save_path)
                with open(os.path.join(debug_save_path, "pymupdf_text.txt"), "w", encoding="utf-8") as f:
                    f.write(combined)
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

# -------------------- CLI for quick testing -------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ocr_extract.py <pdf-or-image> [debug_folder]")
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

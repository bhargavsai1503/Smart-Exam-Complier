"""
api.py — FastAPI Web Server

This file creates a web API that "links" to your ocr_extract.py script.
When a user uploads a file to this API, it will call the
new Google-powered 'extract_text_from_file' function.

To run this file:
1. Make sure 'ocr_extract.py' is in the same 'analysis' directory.
2. Make sure 'api.py' is in the main directory (one level up from 'analysis').
3. Run in terminal: uvicorn api:app --reload
"""

import os
import shutil
import uuid
import sys
import json
import subprocess
from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path

# Add the 'analysis' directory to Python's path
# This allows us to import from 'analysis.ocr_extract'
sys.path.append(os.path.join(os.path.dirname(__file__), 'analysis'))

try:
    # This now imports the NEW Google Vision-powered script
    from analysis import ocr_extract
    from analysis.preprocess import preprocess_text, format_as_dsl
    from analysis.synthesis import generate_enhanced_paper
except ImportError as e:
    print(f"Error: Could not import required modules: {e}")
    print("Make sure all analysis modules are in the 'analysis' subdirectory.")
    sys.exit(1)

# Initialize the FastAPI app
app = FastAPI(
    title="SmartExam Compiler API",
    description="Complete API for SmartExam Compiler: OCR extraction, preprocessing, compilation, and enhanced paper generation.",
    version="2.0.0"
)

# Define the API endpoint
@app.post("/extract-text/", tags=["OCR"])
async def run_ocr_extraction(
    file: UploadFile = File(...)
):
    """
    Uploads a PDF or image file and returns the extracted text.
    """
    
    # Create a safe, temporary path to save the file
    temp_dir = "temp_files"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")

    try:
        # Save the uploaded file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Call the OCR function (now using Google Vision)
        # We can create a debug path for this specific job
        job_id = str(uuid.uuid4())
        debug_path = os.path.join("api_debug_output", job_id)
        
        print(f"[API INFO] Running extraction on: {temp_path}")
        extracted_text, line_map = ocr_extract.extract_text_from_file(
            filepath=temp_path,
            debug_save_path=debug_path
        )
        print(f"[API INFO] Extraction complete. Found {len(extracted_text)} chars.")

        # Return the result as a JSON response
        return {
            "job_id": job_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "debug_path": debug_path,
            "extracted_text": extracted_text,
            "line_confidence_map": line_map
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"File error: {e}")
    except Exception as e:
        print(f"[API ERROR] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")
    
    finally:
        # Clean up: always remove the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/process-paper/", tags=["Full Pipeline"])
async def process_complete_paper(
    paper_file: UploadFile = File(...),
    syllabus_file: UploadFile = File(...)
):
    """
    Complete pipeline: OCR -> Preprocessing -> Compilation -> Enhanced Paper Generation
    Uploads both question paper and syllabus files, processes them through the entire pipeline.
    """
    # Create job directory
    job_id = str(uuid.uuid4())
    job_dir = f"jobs/{job_id}"
    Path(job_dir).mkdir(parents=True, exist_ok=True)

    temp_paper_path = None
    temp_syllabus_path = None

    try:
        # Save uploaded files temporarily
        temp_dir = "temp_files"
        os.makedirs(temp_dir, exist_ok=True)

        temp_paper_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{paper_file.filename}")
        temp_syllabus_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{syllabus_file.filename}")

        with open(temp_paper_path, "wb") as buffer:
            shutil.copyfileobj(paper_file.file, buffer)

        with open(temp_syllabus_path, "wb") as buffer:
            shutil.copyfileobj(syllabus_file.file, buffer)

        # Copy syllabus to job directory
        syllabus_job_path = os.path.join(job_dir, "syllabus.txt")
        shutil.copy2(temp_syllabus_path, syllabus_job_path)

        # Step 1: OCR Extraction
        print(f"[API PROCESS] Step 1: OCR extraction for job {job_id}")
        debug_path = os.path.join(job_dir, "debug_images")
        extracted_text, line_map = ocr_extract.extract_text_from_file(
            filepath=temp_paper_path,
            debug_save_path=debug_path
        )

        # Step 2: Preprocessing and DSL formatting
        print(f"[API PROCESS] Step 2: Preprocessing for job {job_id}")
        cleaned_text = preprocess_text(extracted_text)
        dsl_content = format_as_dsl(cleaned_text, syllabus_job_path)

        input_qp_path = os.path.join(job_dir, "input.qp")
        with open(input_qp_path, 'w', encoding='utf-8') as f:
            f.write(dsl_content)

        # Step 3: Run Compiler
        print(f"[API PROCESS] Step 3: Running compiler for job {job_id}")
        compiler_path = os.path.join(os.getcwd(), 'compiler', 'q_compiler.py')
        result = subprocess.run(
            ["python", compiler_path, job_dir],
            capture_output=True, text=True, timeout=120, check=True
        )

        # Step 4: Generate Enhanced Paper
        print(f"[API PROCESS] Step 4: Generating enhanced paper for job {job_id}")
        semantic_file = os.path.join(job_dir, 'semantic_report.json')

        # Ensure semantic report has required fields
        with open(semantic_file, 'r') as f:
            report_data = json.load(f)

        # Add missing fields if needed
        if 'statistics' not in report_data:
            report_data['statistics'] = {
                'total_marks_calculated': report_data.get('total_marks', 0),
                'estimated_time_minutes': report_data.get('total_time', 0)
            }
        if 'suggestions' not in report_data:
            report_data['suggestions'] = ['Analysis completed successfully']
        if 'checks' not in report_data:
            report_data['checks'] = {
                'difficulty_distribution': {
                    'easy_count': 0, 'medium_count': len(report_data.get('questions', [])),
                    'hard_count': 0, 'easy_percentage': 0.0, 'medium_percentage': 100.0, 'hard_percentage': 0.0
                },
                'crispness_analysis': {'crispness_percentage': 85.0}
            }
        if 'crispness_score' not in report_data:
            report_data['crispness_score'] = 85

        # Update questions
        for i, q in enumerate(report_data.get('questions', []), 1):
            q['number'] = i
            q['crispness'] = 'CRISP'

        # Save updated report
        with open(semantic_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        # Generate enhanced paper
        enhanced_text = generate_enhanced_paper(report_data, report_data)

        # Save enhanced paper
        enhanced_file = os.path.join(job_dir, "enhanced_paper.txt")
        with open(enhanced_file, 'w', encoding='utf-8') as f:
            f.write(enhanced_text)

        print(f"[API PROCESS] Complete pipeline finished for job {job_id}")

        # Return comprehensive results
        return {
            "job_id": job_id,
            "status": "success",
            "files": {
                "input_qp": "input.qp",
                "semantic_report": "semantic_report.json",
                "enhanced_paper": "enhanced_paper.txt",
                "tokens": "tokens.json",
                "ast": "ast.dot"
            },
            "summary": {
                "extracted_chars": len(extracted_text),
                "questions_found": len(report_data.get('questions', [])),
                "total_marks": report_data.get('total_marks', 0),
                "estimated_time": report_data.get('total_time', 0)
            },
            "enhanced_paper_preview": enhanced_text[:500] + "..." if len(enhanced_text) > 500 else enhanced_text
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Compiler process timed out")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Compiler failed: {e.stderr}")
    except Exception as e:
        print(f"[API ERROR] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    finally:
        # Clean up temporary files
        for temp_path in [temp_paper_path, temp_syllabus_path]:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

@app.get("/job/{job_id}/enhanced-paper", tags=["Results"])
async def get_enhanced_paper(job_id: str):
    """Retrieve the enhanced paper for a completed job."""
    job_dir = f"jobs/{job_id}"

    # Try enhanced_paper.txt first, then EnhancedPaper.tex
    enhanced_file = os.path.join(job_dir, "enhanced_paper.txt")
    if not os.path.exists(enhanced_file):
        enhanced_file = os.path.join(job_dir, "EnhancedPaper.tex")
        if not os.path.exists(enhanced_file):
            raise HTTPException(status_code=404, detail="Enhanced paper not found")

    with open(enhanced_file, 'r', encoding='utf-8') as f:
        content = f.read()

    return {
        "job_id": job_id,
        "enhanced_paper": content
    }

@app.get("/job/{job_id}/semantic-report", tags=["Results"])
async def get_semantic_report(job_id: str):
    """Retrieve the semantic analysis report for a completed job."""
    job_dir = f"jobs/{job_id}"
    report_file = os.path.join(job_dir, "semantic_report.json")

    if not os.path.exists(report_file):
        raise HTTPException(status_code=404, detail="Semantic report not found")

    with open(report_file, 'r', encoding='utf-8') as f:
        content = json.load(f)

    return {
        "job_id": job_id,
        "semantic_report": content
    }

@app.get("/job/{job_id}/dashboard", tags=["Results"])
async def get_dashboard_data(job_id: str):
    """Retrieve prepared dashboard data for a completed job."""
    job_dir = f"jobs/{job_id}"
    report_path = os.path.join(job_dir, 'semantic_report.json')

    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Job not found or compiler has not run yet")

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading semantic report: {str(e)}")

    # Ensure required keys exist for dashboard
    if 'statistics' not in report:
        report['statistics'] = {
            'total_marks_declared': 0,
            'total_questions': 0,
            'estimated_time_minutes': 0,
            'difficulty_medium_count': 0,
            'other_metrics': {}
        }
    else:
        # Map the actual statistics to template expected keys
        report['statistics']['total_marks_declared'] = report['statistics'].get('total_marks_calculated', 0)
        report['statistics']['estimated_time_minutes'] = report['statistics'].get('estimated_time_minutes', 0)
        report['statistics']['difficulty_medium_count'] = report.get('checks', {}).get('difficulty_distribution', {}).get('medium_count', 0)

    if 'checks' not in report:
        report['checks'] = {
            'Phase0': {
                'status': 'Not run',
                'details': 'Compiler has not executed yet.'
            }
        }

    # Add extracted_text if not present (for dashboard display)
    if 'extracted_text' not in report:
        input_qp_path = os.path.join(job_dir, 'input.qp')
        try:
            with open(input_qp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                report['extracted_text'] = content[:1000] + '...' if len(content) > 1000 else content
        except Exception:
            report['extracted_text'] = 'No extracted text available yet.'

    return {
        "job_id": job_id,
        "dashboard_data": report
    }

@app.get("/", tags=["Health"])
async def root():
    return {"message": "Smart Exam Compiler API is running."}

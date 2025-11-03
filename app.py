"""
SmartExam Compiler: AI-Driven Question Paper Analyzer
Main Flask Application
(MODIFIED TO MATCH RFD "CONTROLLER-WORKER" ARCHITECTURE)
"""

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import os
import json
import subprocess
from werkzeug.utils import secure_filename
import uuid
import graphviz # For rendering the AST .dot file
#pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# --- Phase 0 Imports ---
from analysis.ocr_extract import extract_text_from_file
from analysis.preprocess import preprocess_text, format_as_dsl

app = Flask(__name__)
app.secret_key = 'smartexam_compiler_secret_key_2025'
app.config['JOBS_FOLDER'] = 'jobs'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg', 'txt'}

os.makedirs(app.config['JOBS_FOLDER'], exist_ok=True)
COMPILER_EXECUTABLE = os.path.join(os.getcwd(), 'compiler', 'q_compiler')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    # 'index.html' is the main dashboard/upload page
    return render_template('index.html')


# --- MODIFICATION 1: Added 'GET' to methods ---
# In app.py

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    
    # This part is correct:
    if request.method == 'GET':
        return render_template('upload.html') 
    
    # --- If method is 'POST', continue with the upload logic ---
    
    # 1. VALIDATE UPLOAD (Correct)
    if 'paper' not in request.files or 'syllabus' not in request.files:
        return "Error: Missing paper or syllabus file", 400
    
    paper_file = request.files['paper']
    syllabus_file = request.files['syllabus']

    if paper_file.filename == '' or syllabus_file.filename == '':
        return "Error: No file selected", 400

    if not (allowed_file(paper_file.filename) and allowed_file(syllabus_file.filename)):
        return "Error: Invalid file type", 400
        
    # 2. CREATE JOB DIRECTORY (Correct)
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(app.config['JOBS_FOLDER'], job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    paper_filename = secure_filename(paper_file.filename)
    syllabus_filename = "syllabus.txt" # Standardize name
    paper_path = os.path.join(job_dir, paper_filename)
    syllabus_path = os.path.join(job_dir, syllabus_filename)
    
    paper_file.save(paper_path)
    syllabus_file.save(syllabus_path)
    
    session['job_id'] = job_id
    
    try:
                # --- 3. RUN PHASE 0 (Fixed) ---
        print(f"[{job_id}] Running Phase 0: Extracting text...")
        from analysis.ocr_extract import extract_text_from_file
        ocr_result, line_conf_map = extract_text_from_file(
            paper_path,
            dpi=600,
            debug_save_path=os.path.join(job_dir, "debug_images")
            )


        # extract_text_from_file returns (text, line_map) — unpack explicitly
        if isinstance(ocr_result, tuple) and len(ocr_result) >= 1:
            raw_text = ocr_result[0]
            line_map = ocr_result[1] if len(ocr_result) > 1 else {}
        else:
            # fallback if some extractor returns only a string
            raw_text = ocr_result
            line_map = {}

        # OPTIONAL: save the line_map for debugging
        try:
            import json
            with open(os.path.join(job_dir, "debug_line_map.json"), "w", encoding="utf-8") as lm_f:
                json.dump(line_map, lm_f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        print(f"[{job_id}] Running Phase 0: Cleaning text...")
        cleaned_text = preprocess_text(raw_text)

        print(f"[{job_id}] Running Phase 0: Formatting DSL...")
        compiler_syllabus_path = os.path.join(job_dir, syllabus_filename)
        dsl_content = format_as_dsl(cleaned_text, compiler_syllabus_path)

        input_qp_path = os.path.join(job_dir, "input.qp")
        with open(input_qp_path, 'w', encoding='utf-8') as f:
            f.write(dsl_content)
        print(f"[{job_id}] Phase 0 Complete. input.qp saved.")


        # --- 4. RUN PHASES 1-6 (C/C++ COMPILER) ---
        
        # --- FIX 1: The compiler call is now UN-COMMENTED ---
        print(f"[{job_id}] Running compiler: {COMPILER_EXECUTABLE}")
        result = subprocess.run(
            ["python", COMPILER_EXECUTABLE + ".py", job_dir],
            capture_output=True, text=True, timeout=60, check=True
            )

        print(f"[{job_id}] Compiler STDOUT: {result.stdout}")
        # ---------------------------------------------------
            
    except subprocess.TimeoutExpired:
        print(f"[{job_id}] Error: Compiler timed out")
        return "Error: Compiler process timed out", 500
    except subprocess.CalledProcessError as e:
        print(f"[{job_id}] Error: Compiler failed. STDERR: {e.stderr}")
        return f"Error: Compiler failed to execute. <pre>{e.stderr}</pre>", 500
    except Exception as e:
        print(f"[{job_id}] Error during Phase 0: {str(e)}")
        import traceback
        traceback.print_exc() 
        return f"Error during pre-processing (Phase 0): {str(e)}", 500

    # --- 5. REDIRECT TO DASHBOARD ---
    
    # --- FIX 2: We now redirect to the dashboard ---
    return redirect(url_for('dashboard'))
    # ------------------------------------------------

# ... (rest of the app.py code remains the same) ...

# --- Helper to get job directory and check for errors ---
def get_job_dir():
    if 'job_id' not in session:
        return None, redirect(url_for('index'))
    job_dir = os.path.join(app.config['JOBS_FOLDER'], session['job_id'])
    if not os.path.exists(job_dir):
        session.clear()
        return None, redirect(url_for('index'))
    return job_dir, None

# --- DASHBOARD & DATA PAGES (Updated) ---
@app.route('/dashboard')
def dashboard():
    job_dir, error_response = get_job_dir()
    if error_response: 
        return error_response

    report_path = os.path.join(job_dir, 'semantic_report.json')
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except Exception:
        # Phase 0: Compiler has not run yet
        report = {}

    # Ensure required keys exist for template
    if 'statistics' not in report:
        report['statistics'] = {
            'total_marks_declared': 0,
            'total_questions': 0,
            'other_metrics': {}
        }

    if 'checks' not in report:
        # Dummy checks for Phase 0
        report['checks'] = {
            'Phase0': {
                'status': 'Not run',
                'details': 'Compiler has not executed yet.'
            }
        }

    return render_template('dashboard.html', 
                           report=report,
                           job_id=session.get('job_id', 'N/A'))


@app.route('/tree')
def tree():
    job_dir, error_response = get_job_dir()
    if error_response: return error_response

    ast_dot_path = os.path.join(job_dir, 'ast.dot')
    ast_svg = ""
    try:
        with open(ast_dot_path, 'r') as f:
            dot_source = f.read()
        g = graphviz.Source(dot_source)
        ast_svg = g.pipe(format='svg').decode('utf-8')
    except Exception as e:
        ast_svg = f"Error: 'ast.dot' not found. Compiler has not run. ({e})"

    return render_template('tree.html', ast_svg_data=ast_svg)

# In app.py

@app.route('/lexical')
def lexical():
    job_dir, error_response = get_job_dir()
    if error_response: return error_response
    
    # --- NEW: Read the input.qp file ---
    input_qp_path = os.path.join(job_dir, 'input.qp')
    input_qp_data = "" # Default to empty string
    try:
        with open(input_qp_path, 'r', encoding='utf-8') as f:
            input_qp_data = f.read()
    except Exception:
        input_qp_data = f"Error: Could not read {input_qp_path}"
    # ------------------------------------

    tokens_path = os.path.join(job_dir, 'tokens.json')
    tokens_data = [] # Default to empty list
    try:
        with open(tokens_path, 'r', encoding='utf-8') as f:
            tokens_data = json.load(f)
    except Exception:
        # This is now expected, as the compiler hasn't run
        tokens_data = [{"token": "---", "value": "Compiler has not run yet", "line": 0}]

    # --- NEW: Pass the input_qp_data to the template ---
    return render_template('lexical.html', 
                        tokens=tokens_data, 
                        input_qp_data=input_qp_data)

@app.route('/optimization')
def optimization():
    job_dir, error_response = get_job_dir()
    if error_response: return error_response
    
    opt_log_path = os.path.join(job_dir, 'optimization_log.json')
    try:
        with open(opt_log_path, 'r', encoding='utf-8') as f:
            opt_data = json.load(f)
    except Exception:
        opt_data = {"error": "'optimization_log.json' not found. Compiler has not run."}
        
    return render_template('optimization.html', optimization_log=opt_data)

# --- DOWNLOAD ROUTES (Updated) ---

def send_job_file(filename, download_name):
    job_dir, error_response = get_job_dir()
    if error_response: return error_response
    
    file_path = os.path.join(job_dir, filename)
    if not os.path.exists(file_path):
        return f"{filename} not found (Compiler has not run)", 404
        
    return send_file(file_path,
                     as_attachment=True,
                     download_name=download_name)

@app.route('/download/enhanced_paper')
def download_enhanced():
    return send_job_file('EnhancedPaper.pdf', 'EnhancedPaper.pdf')

@app.route('/download/analysis_report')
def download_pdf_report():
    return send_job_file('AnalysisReport.pdf', 'AnalysisReport.pdf')

@app.route('/download/tokens')
def download_tokens():
    return send_job_file('tokens.json', 'tokens.json')

@app.route('/download/ast')
def download_ast():
    return send_job_file('ast.dot', 'ast.dot')

@app.route('/download/semantic_report')
def download_semantic_report():
    return send_job_file('semantic_report.json', 'semantic_report.json')


if __name__ == '__main__':
    print("=" * 60)
    print("SmartExam Compiler: AI-Driven Question Paper Analyzer")
    print(f"COMPILER EXECUTABLE: {COMPILER_EXECUTABLE}")
    if not os.path.exists(COMPILER_EXECUTABLE):
        print("\n*** WARNING: COMPILER EXECUTABLE NOT FOUND! ***")
        print("This is OK for Phase 0 testing.")
        print("=" * 60)
    print("Access the application at: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
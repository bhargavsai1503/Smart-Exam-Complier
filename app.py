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
from analysis.synthesis import generate_enhanced_paper_with_pdf # <-- ADD THIS LINE
from analysis.semantic_analysis import perform_semantic_analysis



app = Flask(__name__)
app.secret_key = 'smartexam_compiler_secret_key_2025'
app.config['JOBS_FOLDER'] = 'jobs'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg', 'txt'}

os.makedirs(app.config['JOBS_FOLDER'], exist_ok=True)
COMPILER_EXECUTABLE = os.path.join(os.getcwd(), 'compiler', 'q_compiler')

# Configure Google Cloud Vision API credentials
# Set the path to your Google Cloud service account key file
# You can also set this as an environment variable: GOOGLE_APPLICATION_CREDENTIALS
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] ='[YOUR API KEY FILE PATH HERE]'

# Configure Gemini AI API key
os.environ['GEMINI_API_KEY'] = '[YOUR GEMINI API KEY HERE]'


def allowed_file(filename):
    """Check whether a filename has an allowed extension (case-insensitive) based on app configuration.
    Parameters:
        - filename (str): The name of the file to validate (may include a path). The function checks that the filename contains an extension and that the extension (after the last dot) is present in app.config['ALLOWED_EXTENSIONS'].
    Returns:
        - bool: True if the filename has an extension and that extension is in the allowed set; False otherwise.
    Example:
        - allowed_file("report.PDF") -> True
    """
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
            dpi=800,
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

        # --- 5. ENHANCE SEMANTIC REPORT WITH ANALYSIS ---
        print(f"[{job_id}] Enhancing semantic report with analysis...")
        semantic_report_path = os.path.join(job_dir, 'semantic_report.json')
        try:
            with open(semantic_report_path, 'r', encoding='utf-8') as f:
                semantic_data = json.load(f)

            # Perform semantic analysis using the extracted text
            enhanced_report = perform_semantic_analysis(semantic_data, cleaned_text)

            # Merge with existing semantic data
            semantic_data.update(enhanced_report)

            # Save enhanced report
            with open(semantic_report_path, 'w', encoding='utf-8') as f:
                json.dump(semantic_data, f, indent=2)

            print(f"[{job_id}] Semantic report enhanced successfully.")
        except Exception as e:
            print(f"[{job_id}] Warning: Could not enhance semantic report: {e}")
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
        # For testing purposes, use the first available job directory
        jobs_folder = app.config['JOBS_FOLDER']
        if os.path.exists(jobs_folder):
            job_dirs = [d for d in os.listdir(jobs_folder) if os.path.isdir(os.path.join(jobs_folder, d))]
            if job_dirs:
                session['job_id'] = job_dirs[0]
                job_dir = os.path.join(jobs_folder, job_dirs[0])
                return job_dir, None
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
            'total_marks_declared': report.get('total_marks', 0),
            'total_questions': len(report.get('questions', [])),
            'estimated_time_minutes': report.get('total_time', 0),
            'difficulty_medium_count': sum(1 for q in report.get('questions', []) if q.get('difficulty') == 'Medium'),
            'other_metrics': {}
        }
    else:
        # Map the actual statistics to template expected keys
        report['statistics']['total_marks_declared'] = report['statistics'].get('total_marks_calculated', report.get('total_marks', 0))
        report['statistics']['estimated_time_minutes'] = report['statistics'].get('estimated_time_minutes', report.get('total_time', 0))
        report['statistics']['difficulty_medium_count'] = report['statistics'].get('difficulty_medium_count', sum(1 for q in report.get('questions', []) if q.get('difficulty') == 'Medium'))

    # Add difficulty distribution data
    if 'checks' in report and 'difficulty_distribution' in report['checks']:
        diff_dist = report['checks']['difficulty_distribution']
        report['statistics']['difficulty_distribution'] = {
            'easy': diff_dist.get('easy_count', 0),
            'medium': diff_dist.get('medium_count', 0),
            'hard': diff_dist.get('hard_count', 0)
        }
    else:
        report['statistics']['difficulty_distribution'] = {'easy': 0, 'medium': 0, 'hard': 0}

    # Add marks distribution data
    if 'questions' in report:
        marks_dist = {}
        for q in report['questions']:
            marks = q.get('marks', 0)
            marks_dist[marks] = marks_dist.get(marks, 0) + 1
        report['statistics']['marks_distribution'] = marks_dist
    else:
        report['statistics']['marks_distribution'] = {}

    # Add time comparison data
    if 'statistics' in report:
        estimated_time = report['statistics'].get('estimated_time_minutes', 0)
        declared_time = report['statistics'].get('declared_time_minutes', 0)
        report['statistics']['time_comparison'] = {
            'estimated': estimated_time,
            'declared': declared_time,
            'difference': estimated_time - declared_time
        }
    else:
        report['statistics']['time_comparison'] = {'estimated': 0, 'declared': 0, 'difference': 0}

    if 'checks' not in report:
        # Dummy checks for Phase 0
        report['checks'] = {
            'Phase0': {
                'status': 'Not run',
                'details': 'Compiler has not executed yet.'
            }
        }

    # Add default values for missing keys
    if 'suggestions' not in report:
        report['suggestions'] = ['Analysis completed successfully']

    if 'crispness_score' not in report:
        report['crispness_score'] = 85

    # Ensure questions have required fields
    if 'questions' in report:
        for i, q in enumerate(report['questions'], 1):
            q['number'] = i
            if 'crispness' not in q:
                q['crispness'] = 'CRISP'

    # Add extracted_text if not present (for dashboard display)
    if 'extracted_text' not in report:
        # Try to read from input.qp file
        input_qp_path = os.path.join(job_dir, 'input.qp')
        try:
            with open(input_qp_path, 'r', encoding='utf-8') as f:
                report['extracted_text'] = f.read()[:1000] + "..." if len(f.read()) > 1000 else f.read()
        except Exception:
            report['extracted_text'] = "No extracted text available yet."

    # Load data for Lexical Analysis tab
    input_qp_path = os.path.join(job_dir, 'input.qp')
    input_qp_data = ""
    try:
        with open(input_qp_path, 'r', encoding='utf-8') as f:
            input_qp_data = f.read()
    except Exception:
        input_qp_data = "Error: Could not read input.qp file. Compiler has not run yet."

    tokens_path = os.path.join(job_dir, 'tokens.json')
    tokens_data = []
    try:
        with open(tokens_path, 'r', encoding='utf-8') as f:
            tokens_data = json.load(f)
    except Exception:
        tokens_data = [{"token": "---", "value": "Compiler has not run yet", "line": 0}]

    # Load data for Parse Tree tab
    ast_dot_path = os.path.join(job_dir, 'ast.dot')
    ast_svg = ""
    try:
        with open(ast_dot_path, 'r') as f:
            dot_source = f.read()
        g = graphviz.Source(dot_source)
        ast_svg = g.pipe(format='svg').decode('utf-8')
    except Exception as e:
        ast_svg = f"Error: 'ast.dot' not found. Compiler has not run. ({e})"

    return render_template('dashboard.html',
                           report=report,
                           job_id=session.get('job_id', 'N/A'),
                           input_qp_data=input_qp_data,
                           tokens=tokens_data,
                           ast=ast_svg)


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

    return render_template('tree.html', ast=ast_svg)

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
@app.route('/enhanced')
def enhanced_paper():
    job_dir, error_response = get_job_dir()
    if error_response:
        return error_response

    report_path = os.path.join(job_dir, 'semantic_report.json')
    syllabus_path = os.path.join(job_dir, 'syllabus.txt')

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            original_report = json.load(f)

    except Exception as e:
        return f"Error loading 'semantic_report.json': {e}. Has the compiler run?", 404

    # Check if the report has the data needed
    if 'statistics' not in original_report or 'suggestions' not in original_report or 'questions' not in original_report:
        return "Error: 'semantic_report.json' is incomplete. Cannot generate enhanced paper.", 404

    # Try to read syllabus content
    syllabus_content = None
    try:
        with open(syllabus_path, 'r', encoding='utf-8') as f:
            syllabus_content = f.read().strip()
    except Exception:
        # If syllabus file not found, use subject from report
        syllabus_content = original_report.get('subject', 'Computer Science')

    # Generate enhanced paper and report using syllabus content
    enhanced_text_content, enhanced_report = generate_enhanced_paper_with_pdf(original_report, syllabus_content, job_dir)

    # Render the enhanced.html template with both original and enhanced data
    return render_template('enhanced.html',
                           enhanced_text=enhanced_text_content,
                           suggestions=enhanced_report.get('suggestions', []),
                           original_report=original_report,
                           enhanced_report=enhanced_report)

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
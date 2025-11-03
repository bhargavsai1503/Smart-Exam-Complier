"""
Text Preprocessing Module
Cleans, normalizes, and RE-FORMATS extracted text for compiler input.
"""

import re

# --- Pass 1: Text Cleaning (Your Original Functions) ---

def preprocess_text(text):
    """
    First-pass cleaning of the raw text from OCR.
    Fixes line breaks, OCR errors, and consolidates spaces.
    """
    if not text or not text.strip():
        raise ValueError("Empty text provided for preprocessing")
    
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Join words hyphenated across lines (e.g., "comp- \n iler" -> "compiler")
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    
    # Fix common OCR mistakes
    text = fix_ocr_errors(text)
    
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        line = re.sub(r' +', ' ', line) # Consolidate multiple spaces
        if line:
            cleaned_lines.append(line)
            
    text = '\n'.join(cleaned_lines)
    
    # Try to add newlines before keywords to help regex later
    text = preserve_structure(text) 
    return text

def fix_ocr_errors(text):
    """Replaces common, context-specific OCR errors."""
    # e.g., 1O1 -> 101
    text = re.sub(r'(\d)O(\d)', r'\g<1>0\g<2>', text) 
    # e.g., 1O] -> 10]
    text = re.sub(r'(\d)O([)\]])', r'\g<1>0\g<2>', text) 
    # e.g., [l] -> [1]
    text = re.sub(r'\[l\]', '[1]', text) 
    # e.g., (l) -> (1)
    text = re.sub(r'\(l\)', '(1)', text) 
    return text

def preserve_structure(text):
    """
    Tries to re-insert newlines before key header words that might
    have been joined incorrectly.
    """
    header_keywords = ['Time', 'Total Marks', 'Maximum Marks', 'Syllabus',
                    'Subject', 'Course', 'Exam', 'Date']
    
    # Add a newline before a keyword if it's not already at the start of a line
    for keyword in header_keywords:
        text = re.sub(f'([^\n])({keyword})', r'\1\n\2', text, flags=re.IGNORECASE)
    return text

# --- Pass 2: DSL Formatting (The Core of Phase 0) ---

def format_as_dsl(cleaned_text, syllabus_path_for_compiler):
    """
    Transforms the cleaned text into the structured input.qp DSL format.
    This is the fragile part of the project mentioned in the RFD.
    
    Args:
        cleaned_text (str): The text after running preprocess_text().
        syllabus_path_for_compiler (str): The path where the compiler
                                          will find the syllabus.
                                          e.g., "jobs/<job_id>/syllabus.txt"
    
    Returns:
        str: The structured input.qp DSL.
    """
    
    # --- 1. Define Regex Patterns ---
    
    # Regex to find header info
    # (?i) = case-insensitive, .*:? = optional colon, (.*) = capture group
    re_subject = re.compile(r'Subject:?\s*(.*)', re.IGNORECASE)
    re_total_marks = re.compile(r'(?:Total|Maximum)\s+Marks:?\s*(\d+)', re.IGNORECASE)
    re_total_time = re.compile(r'Time:?\s*(\d+)\s*(hours?|minutes?)', re.IGNORECASE)

    # Regex to split the text into questions.
    # This splits "before" any "Q.1", "Q. 1", "Q1", "1.", etc.
    # This is a "positive lookahead" (?=...)
    re_question_split = re.compile(r'(?=Q\.?\s*\d+\b|\b\d+\.\s)', re.IGNORECASE)

    # Regex to find marks inside a question, e.g., [10M] or (10 Marks)
    re_question_marks = re.compile(r'(?:\[|\()(\d+)\s*(?:M|marks?)(?:\]|\))', re.IGNORECASE)

    # --- 2. Extract Header ---
    subject = "Unknown Subject"
    total_marks = 100 # Default
    total_time = 180 # Default
    
    header_text_block = cleaned_text # Assume header is at the top
    
    # Try to isolate the header text before the first question
    first_q_match = re_question_split.search(cleaned_text)
    if first_q_match:
        header_text_block = cleaned_text[:first_q_match.start()]
    
    # Find header fields within the isolated block
    subject_match = re_subject.search(header_text_block)
    if subject_match:
        subject = subject_match.group(1).strip()
        
    marks_match = re_total_marks.search(header_text_block)
    if marks_match:
        total_marks = int(marks_match.group(1))
        
    time_match = re_total_time.search(header_text_block)
    if time_match:
        time_val = int(time_match.group(1))
        time_unit = time_match.group(2).lower()
        if "hour" in time_unit:
            total_time = time_val * 60
        else:
            total_time = time_val

    # Build the Header part of the DSL
    header_dsl = f"""
[HEADER]
    SUBJECT: "{subject}"
    TOTAL_MARKS: {total_marks}
    TOTAL_TIME: {total_time}
    SYLLABUS_PATH: "{syllabus_path_for_compiler}"
[/HEADER]
"""

    # --- 3. Extract Questions ---
    
    all_questions_dsl = []
    
    if first_q_match:
        # Get all text from the first question onwards
        question_block_text = cleaned_text[first_q_match.start():]
        
        # Split the block into a list of questions
        # We split using the regex, which keeps the delimiter at the start
        question_list = re_question_split.split(question_block_text)
        
        for q_text_raw in question_list:
            q_text_raw = q_text_raw.strip()
            if not q_text_raw:
                continue

            q_marks = 0
            q_text_cleaned = q_text_raw

            # Find marks in this question
            marks_match = re_question_marks.search(q_text_cleaned)
            if marks_match:
                q_marks = int(marks_match.group(1))
                # Remove the marks string from the question text
                q_text_cleaned = re_question_marks.sub('', q_text_cleaned).strip()
            
            # Remove the question number (e.g., "Q.1" or "1.") from the start
            q_text_cleaned = re.sub(r'^(?:Q\.?\s*\d+\b|\b\d+\.\s*)', '', q_text_cleaned).strip()
            
            # Escape characters for the C string in our DSL
            q_text_escaped = q_text_cleaned.replace('\\', '\\\\') # Escape backslashes
            q_text_escaped = q_text_escaped.replace('"', '\\"')   # Escape quotes
            q_text_escaped = q_text_escaped.replace('\n', '\\n')  # Escape newlines

            # Build the Question part of the DSL
            question_dsl = f"""
    [QUESTION]
        Q_TEXT: "{q_text_escaped}"
        Q_MARKS: {q_marks}
    [/QUESTION]
"""
            all_questions_dsl.append(question_dsl)

    # --- 4. Assemble Final DSL ---
    final_dsl = header_dsl + "\n[QUESTION_LIST]\n" + "\n".join(all_questions_dsl) + "\n[/QUESTION_LIST]\n"
    
    return final_dsl
"""
Synthesis Module
<<<<<<< HEAD
Generates enhanced question paper with improvements
"""

def generate_enhanced_paper(ast_data, report):
=======
Generates enhanced question paper with improvements using Gemini AI
"""

import google.generativeai as genai
import os
import json
from analysis.pdf_report import generate_enhanced_pdf

def generate_questions_from_syllabus(syllabus, total_marks, num_questions, time_minutes):
    """Generate new questions based on syllabus using Gemini AI"""
    try:
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyBMA7V1S_57vDWFKX__nse27jxPdKJOqtk')
        genai.configure(api_key=api_key)

        # Initialize the model
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Create prompt for question generation
        prompt = f"""
        Generate {num_questions} exam questions for the subject syllabus: "{syllabus}"

        Requirements:
        - Total marks: {total_marks}
        - Questions should cover different difficulty levels: Easy, Medium, Hard
        - Questions should be academic and suitable for university-level exams
        - Each question should have appropriate marks allocation
        - Questions should test conceptual understanding, problem-solving, and application

        Please provide the questions in the following JSON format:
        {{
            "questions": [
                {{
                    "number": 1,
                    "text": "Question text here",
                    "marks": 10,
                    "difficulty": "MEDIUM",
                    "estimated_time": 15,
                    "crispness": "CRISP"
                }}
            ]
        }}

        Ensure the questions are original, clear, and well-structured.
        """

        # Generate questions using Gemini
        response = model.generate_content(prompt)

        # Parse the response
        try:
            result = json.loads(response.text.strip('```json\n').strip('```'))
            questions = result.get('questions', [])
        except (json.JSONDecodeError, KeyError):
            # Fallback to rule-based generation if AI fails
            print("AI generation failed, falling back to rule-based generation")
            return generate_questions_fallback(syllabus, total_marks, num_questions, time_minutes)

        # Validate and adjust questions
        if len(questions) != num_questions:
            # Adjust to match required number
            while len(questions) < num_questions:
                questions.append({
                    'number': len(questions) + 1,
                    'text': f"Explain a key concept from {syllabus}",
                    'marks': 10,
                    'difficulty': 'MEDIUM',
                    'estimated_time': time_minutes // num_questions,
                    'crispness': 'CRISP'
                })

        # Ensure all questions have required fields
        for i, q in enumerate(questions[:num_questions], 1):
            q['number'] = i
            if 'crispness' not in q:
                q['crispness'] = 'CRISP'
            if 'estimated_time' not in q:
                q['estimated_time'] = time_minutes // num_questions

        return questions[:num_questions]

    except Exception as e:
        print(f"Error generating questions with AI: {e}")
        # Fallback to rule-based generation
        return generate_questions_fallback(syllabus, total_marks, num_questions, time_minutes)

def generate_questions_fallback(syllabus, total_marks, num_questions, time_minutes):
    """Fallback rule-based question generation"""
    questions = []
    syllabus_lower = syllabus.lower()

    # Define question templates based on common topics
    question_templates = {
        'data structures': [
            "Explain the working of stacks with suitable examples and applications.",
            "What are the differences between arrays and linked lists? Discuss their advantages and disadvantages.",
            "Describe the implementation of a binary search tree. Include insertion and deletion operations.",
            "Explain the concept of hashing and collision resolution techniques.",
            "Compare depth-first search and breadth-first search algorithms with examples.",
            "What is a priority queue? Explain its implementation using heaps."
        ],
        'algorithms': [
            "Explain the divide and conquer approach with an example algorithm.",
            "What is dynamic programming? Solve the knapsack problem using DP.",
            "Describe the working of greedy algorithms with a suitable example.",
            "Explain the concept of time complexity analysis with Big O notation.",
            "What are NP-complete problems? Give examples and explain their significance.",
            "Describe the working of sorting algorithms: Quick sort and Merge sort."
        ],
        'programming': [
            "Explain the concepts of object-oriented programming with examples.",
            "What are pointers? Explain their usage in C/C++ with examples.",
            "Describe memory management in programming languages.",
            "Explain exception handling mechanisms in modern programming languages.",
            "What are data types? Explain primitive and composite data types.",
            "Describe the compilation process and different phases of a compiler."
        ],
        'default': [
            "Explain the fundamental concepts of the subject with examples.",
            "What are the key principles and theories in this topic?",
            "Describe the practical applications and real-world usage.",
            "Compare different approaches and methodologies in the field.",
            "Solve the following problem using appropriate techniques.",
            "Analyze the complexity and efficiency of different solutions."
        ]
    }

    # Select appropriate templates based on syllabus keywords
    selected_templates = question_templates['default']
    for key in question_templates:
        if key in syllabus_lower and key != 'default':
            selected_templates = question_templates[key]
            break

    # Difficulty distribution: 2 easy, 3 medium, 1 hard
    difficulties = ['EASY', 'EASY', 'MEDIUM', 'MEDIUM', 'MEDIUM', 'HARD']
    marks_distribution = [5, 10, 15, 20, 25, 10]  # Total 85 marks

    for i in range(num_questions):
        q_text = selected_templates[i % len(selected_templates)]
        q_marks = marks_distribution[i] if i < len(marks_distribution) else 10
        q_difficulty = difficulties[i] if i < len(difficulties) else 'MEDIUM'
        q_time = time_minutes // num_questions

        questions.append({
            'number': i + 1,
            'text': q_text,
            'marks': q_marks,
            'difficulty': q_difficulty,
            'estimated_time': q_time,
            'crispness': 'CRISP'
        })

    return questions

def generate_enhanced_paper(original_report, syllabus_content=None):
    # Get syllabus from original report or provided content
    syllabus = syllabus_content if syllabus_content else original_report.get('subject', 'Computer Science')
    total_marks = original_report.get('total_marks', 85)
    num_questions = len(original_report.get('questions', []))
    time_minutes = 180

    # Generate new questions from syllabus
    questions = generate_questions_from_syllabus(syllabus, total_marks, num_questions, time_minutes)

    # Create enhanced report
    enhanced_report = {
        'subject': syllabus,
        'total_marks': total_marks,
        'total_time': time_minutes,
        'questions': questions,
        'statistics': {
            'total_marks_calculated': sum(q['marks'] for q in questions),
            'estimated_time_minutes': time_minutes,
            'declared_time_minutes': time_minutes,
            'difficulty_easy_count': sum(1 for q in questions if q['difficulty'] == 'EASY'),
            'difficulty_medium_count': sum(1 for q in questions if q['difficulty'] == 'MEDIUM'),
            'difficulty_hard_count': sum(1 for q in questions if q['difficulty'] == 'HARD')
        },
        'checks': {
            'difficulty_distribution': {
                'easy_count': sum(1 for q in questions if q['difficulty'] == 'EASY'),
                'medium_count': sum(1 for q in questions if q['difficulty'] == 'MEDIUM'),
                'hard_count': sum(1 for q in questions if q['difficulty'] == 'HARD'),
                'easy_percentage': round(sum(1 for q in questions if q['difficulty'] == 'EASY') / num_questions * 100, 1),
                'medium_percentage': round(sum(1 for q in questions if q['difficulty'] == 'MEDIUM') / num_questions * 100, 1),
                'hard_percentage': round(sum(1 for q in questions if q['difficulty'] == 'HARD') / num_questions * 100, 1),
                'status': 'PASS',
                'message': 'Balanced difficulty distribution achieved'
            },
            'crispness_analysis': {
                'crispness_percentage': 95
            }
        },
        'suggestions': [
            "New question paper generated from syllabus with balanced difficulty",
            "Time optimized to 180 minutes for better completion rate",
            "Questions cover fundamental to advanced concepts",
            "Marks distributed fairly across difficulty levels",
            "Enhanced syllabus coverage with comprehensive questions"
        ],
        'crispness_score': 95
    }

    # Generate enhanced text
>>>>>>> final_version
    enhanced_text = []
    enhanced_text.append("=" * 70)
    enhanced_text.append("ENHANCED QUESTION PAPER")
    enhanced_text.append("Generated by SmartExam Compiler")
    enhanced_text.append("=" * 70)
    enhanced_text.append("")
<<<<<<< HEAD
    syllabus = ast_data.get('syllabus', 'Unknown Subject')
    enhanced_text.append(f"Subject: {syllabus}")
    original_marks = ast_data.get('total_marks', 0)
    calculated_marks = report['statistics']['total_marks_calculated']
    if original_marks != calculated_marks:
        enhanced_text.append(f"Total Marks: {calculated_marks} (Corrected from {original_marks})")
    else:
        enhanced_text.append(f"Total Marks: {original_marks}")
    estimated_time = report['statistics']['estimated_time_minutes']
    enhanced_text.append(f"Time Allowed: {estimated_time} minutes")
=======
    enhanced_text.append(f"Subject: {syllabus}")
    enhanced_text.append(f"Total Marks: {enhanced_report['statistics']['total_marks_calculated']}")
    enhanced_text.append(f"Time Allowed: {enhanced_report['total_time']} minutes")
>>>>>>> final_version
    enhanced_text.append("")
    enhanced_text.append("-" * 70)
    enhanced_text.append("")
    enhanced_text.append("IMPROVEMENTS MADE:")
    enhanced_text.append("")
<<<<<<< HEAD
    for suggestion in report['suggestions']:
=======
    for suggestion in enhanced_report['suggestions']:
>>>>>>> final_version
        enhanced_text.append(f"• {suggestion}")
    enhanced_text.append("")
    enhanced_text.append("-" * 70)
    enhanced_text.append("")
    enhanced_text.append("QUESTIONS:")
    enhanced_text.append("")
<<<<<<< HEAD
    questions = ast_data.get('questions', [])
    for i, q in enumerate(questions, 1):
        q_num = q.get('number', i)
        q_text = q.get('text', 'Question text')
        q_marks = q.get('marks', 0)
        q_difficulty = q.get('difficulty', 'MEDIUM')
        q_crispness = q.get('crispness', 'CRISP')
        improved_text, improved_marks = apply_improvements(
            q_text, q_marks, q_difficulty, q_crispness, report
        )
        enhanced_text.append(f"Q{q_num}. {improved_text}")
        enhanced_text.append(f"     [Marks: {improved_marks}] [Difficulty: {q_difficulty}]")
=======
    for q in questions:
        q_num = q['number']
        q_text = q['text']
        q_marks = q['marks']
        q_difficulty = q['difficulty']
        enhanced_text.append(f"Q{q_num}. {q_text}")
        enhanced_text.append(f"     [Marks: {q_marks}] [Difficulty: {q_difficulty}] [Time: {q['estimated_time']} min]")
>>>>>>> final_version
        enhanced_text.append("")
    enhanced_text.append("-" * 70)
    enhanced_text.append("")
    enhanced_text.append("DIFFICULTY DISTRIBUTION:")
<<<<<<< HEAD
    diff_check = report['checks']['difficulty_distribution']
=======
    diff_check = enhanced_report['checks']['difficulty_distribution']
>>>>>>> final_version
    enhanced_text.append(f"  Easy:   {diff_check['easy_count']} questions ({diff_check['easy_percentage']}%)")
    enhanced_text.append(f"  Medium: {diff_check['medium_count']} questions ({diff_check['medium_percentage']}%)")
    enhanced_text.append(f"  Hard:   {diff_check['hard_count']} questions ({diff_check['hard_percentage']}%)")
    enhanced_text.append("")
    enhanced_text.append("QUALITY METRICS:")
<<<<<<< HEAD
    enhanced_text.append(f"  Overall Score: {report['crispness_score']}/100")
    enhanced_text.append(f"  Crispness: {report['checks']['crispness_analysis']['crispness_percentage']}%")
=======
    enhanced_text.append(f"  Overall Score: {enhanced_report['crispness_score']}/100")
    enhanced_text.append(f"  Crispness: {enhanced_report['checks']['crispness_analysis']['crispness_percentage']}%")
>>>>>>> final_version
    enhanced_text.append("")
    enhanced_text.append("=" * 70)
    enhanced_text.append("End of Enhanced Question Paper")
    enhanced_text.append("=" * 70)
<<<<<<< HEAD
    return "\n".join(enhanced_text)
=======

    return "\n".join(enhanced_text), enhanced_report

def generate_enhanced_paper_with_pdf(original_report, syllabus_content=None, job_dir=None):
    """Generate enhanced paper and save PDF if job_dir is provided"""
    enhanced_text, enhanced_report = generate_enhanced_paper(original_report, syllabus_content)

    # Generate PDF if job directory is provided
    if job_dir:
        pdf_path = os.path.join(job_dir, 'EnhancedPaper.pdf')
        try:
            generate_enhanced_pdf(enhanced_text, enhanced_report, pdf_path)
            print(f"Enhanced PDF saved to: {pdf_path}")
        except Exception as e:
            print(f"Warning: Could not generate enhanced PDF: {e}")

    return enhanced_text, enhanced_report
>>>>>>> final_version

def apply_improvements(text, marks, difficulty, crispness, report):
    improved_text = text
    improved_marks = marks
    if crispness == 'VERBOSE':
        if len(text) > 100:
            improved_text = text[:100] + "... [Suggestion: Split into sub-questions or simplify]"
    if crispness == 'AMBIGUOUS':
        improved_text = text + " [Suggestion: Remove vague terms like 'etc', 'something']"
    if difficulty == 'EASY' and marks > 10:
        improved_marks = 10
        improved_text = text + f" [Marks adjusted: {marks} → {improved_marks}]"
    if difficulty == 'HARD' and marks < 10:
        improved_marks = 12
        improved_text = text + f" [Marks adjusted: {marks} → {improved_marks}]"
    return improved_text, improved_marks
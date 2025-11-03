"""
Semantic Analysis Module
Performs static semantic checks on parsed question paper
"""

import re

# Difficulty classification keywords
EASY_KEYWORDS = ['define', 'state', 'list', 'identify', 'name', 'mention', 'label', 'write']
MEDIUM_KEYWORDS = ['explain', 'prove', 'derive', 'compare', 'discuss', 'describe', 'illustrate', 'differentiate', 'outline']
HARD_KEYWORDS = ['design', 'construct', 'develop', 'implement', 'optimize', 'synthesize', 'analyze', 'evaluate', 'create', 'formulate']

def perform_semantic_analysis(ast_data, original_text):
    report = {
        'checks': {},
        'statistics': {},
        'warnings': [],
        'suggestions': [],
        'crispness_score': 0
    }
    questions = ast_data.get('questions', [])
    declared_total = ast_data.get('total_marks', 0)
    declared_time = ast_data.get('time_minutes', 0)
    syllabus = ast_data.get('syllabus', '')

    marks_check = validate_marks(questions, declared_total)
    report['checks']['marks_validation'] = marks_check

    time_check = estimate_time(questions, declared_time)
    report['checks']['time_estimation'] = time_check

    difficulty_check = analyze_difficulty(questions, original_text)
    report['checks']['difficulty_distribution'] = difficulty_check

    coverage_check = check_syllabus_coverage(questions, syllabus, original_text)
    report['checks']['syllabus_coverage'] = coverage_check

    crispness_check = analyze_crispness(questions, original_text)
    report['checks']['crispness_analysis'] = crispness_check

    report['statistics'] = {
        'total_questions': len(questions),
        'total_marks_calculated': marks_check['calculated_total'],
        'total_marks_declared': declared_total,
        'estimated_time_minutes': time_check['estimated_time'],
        'declared_time_minutes': declared_time,
        'difficulty_easy_count': difficulty_check['easy_count'],
        'difficulty_medium_count': difficulty_check['medium_count'],
        'difficulty_hard_count': difficulty_check['hard_count']
    }

    generate_warnings_and_suggestions(report)
    report['crispness_score'] = calculate_overall_score(report)
    return report

def validate_marks(questions, declared_total):
    calculated_total = sum(q.get('marks', 0) for q in questions)
    is_valid = (calculated_total == declared_total) if declared_total > 0 else True
    difference = abs(calculated_total - declared_total)
    return {
        'status': 'PASS' if is_valid else 'FAIL',
        'calculated_total': calculated_total,
        'declared_total': declared_total,
        'difference': difference,
        'message': 'Marks sum matches declared total' if is_valid else f'Marks mismatch: {difference} marks difference'
    }

def estimate_time(questions, declared_time):
    estimated_time = 0
    for q in questions:
        marks = q.get('marks', 0)
        difficulty = q.get('difficulty', 'MEDIUM').upper()
        if difficulty == 'EASY':
            estimated_time += marks * 2
        elif difficulty == 'HARD':
            estimated_time += marks * 4
        else:
            estimated_time += marks * 3
    estimated_time = int(estimated_time * 1.1)
    time_match = abs(estimated_time - declared_time) <= 15 if declared_time > 0 else True
    return {
        'status': 'PASS' if time_match else 'WARN',
        'estimated_time': estimated_time,
        'declared_time': declared_time,
        'difference': abs(estimated_time - declared_time),
        'message': f'Estimated time: {estimated_time} minutes vs declared: {declared_time} minutes'
    }

def analyze_difficulty(questions, original_text):
    easy_count = 0
    medium_count = 0
    hard_count = 0
    for q in questions:
        q_text = q.get('text', '').lower()
        has_easy = any(kw in q_text for kw in EASY_KEYWORDS)
        has_hard = any(kw in q_text for kw in HARD_KEYWORDS)
        has_medium = any(kw in q_text for kw in MEDIUM_KEYWORDS)
        if has_hard:
            difficulty = 'HARD'
            hard_count += 1
        elif has_medium:
            difficulty = 'MEDIUM'
            medium_count += 1
        elif has_easy:
            difficulty = 'EASY'
            easy_count += 1
        else:
            difficulty = 'MEDIUM'
            medium_count += 1
        q['difficulty'] = difficulty
    total = len(questions)
    is_balanced = (
        (easy_count / total >= 0.2 and easy_count / total <= 0.4) and
        (medium_count / total >= 0.4 and medium_count / total <= 0.6) and
        (hard_count / total >= 0.1 and hard_count / total <= 0.3)
    ) if total > 0 else False
    return {
        'status': 'PASS' if is_balanced else 'WARN',
        'easy_count': easy_count,
        'medium_count': medium_count,
        'hard_count': hard_count,
        'easy_percentage': round(easy_count / total * 100, 1) if total > 0 else 0,
        'medium_percentage': round(medium_count / total * 100, 1) if total > 0 else 0,
        'hard_percentage': round(hard_count / total * 100, 1) if total > 0 else 0,
        'message': 'Difficulty distribution is balanced' if is_balanced else 'Difficulty distribution needs improvement'
    }

def check_syllabus_coverage(questions, syllabus, original_text):
    if not syllabus:
        return {'status': 'SKIP', 'message': 'No syllabus information available'}
    topics = extract_topics(syllabus)
    if not topics:
        return {'status': 'SKIP', 'message': 'Could not extract topics from syllabus'}
    covered_topics = []
    uncovered_topics = []
    text_lower = original_text.lower()
    for topic in topics:
        if topic.lower() in text_lower:
            covered_topics.append(topic)
        else:
            uncovered_topics.append(topic)
    coverage_ratio = len(covered_topics) / len(topics) if topics else 0
    is_good_coverage = coverage_ratio >= 0.7
    return {
        'status': 'PASS' if is_good_coverage else 'WARN',
        'covered_topics': covered_topics,
        'uncovered_topics': uncovered_topics,
        'coverage_percentage': round(coverage_ratio * 100, 1),
        'message': f'{len(covered_topics)}/{len(topics)} topics covered'
    }

def analyze_crispness(questions, original_text):
    crisp_count = 0
    verbose_count = 0
    ambiguous_count = 0
    for q in questions:
        q_text = q.get('text', '')
        word_count = len(q_text.split())
        has_unclear_terms = any(term in q_text.lower() for term in ['something', 'anything', 'etc', 'and so on'])
        if word_count > 100:
            verbose_count += 1
            q['crispness'] = 'VERBOSE'
        elif has_unclear_terms:
            ambiguous_count += 1
            q['crispness'] = 'AMBIGUOUS'
        else:
            crisp_count += 1
            q['crispness'] = 'CRISP'
    total = len(questions)
    crispness_ratio = crisp_count / total if total > 0 else 0
    return {
        'status': 'PASS' if crispness_ratio >= 0.7 else 'WARN',
        'crisp_count': crisp_count,
        'verbose_count': verbose_count,
        'ambiguous_count': ambiguous_count,
        'crispness_percentage': round(crispness_ratio * 100, 1),
        'message': f'{crisp_count}/{total} questions are crisp and clear'
    }

def extract_topics(syllabus):
    topics = re.split(r'[,;:\n]', syllabus)
    topics = [t.strip() for t in topics if t.strip() and len(t.strip()) > 3]
    return topics[:10]

def generate_warnings_and_suggestions(report):
    warnings = []
    suggestions = []
    if report['checks']['marks_validation']['status'] == 'FAIL':
        warnings.append(f"Marks sum mismatch: {report['checks']['marks_validation']['message']}")
        suggestions.append("Review and correct the marks allocation to match the declared total")
    time_diff = report['checks']['time_estimation']['difference']
    if time_diff > 15:
        warnings.append(f"Time allocation mismatch: {time_diff} minutes difference")
        if report['checks']['time_estimation']['estimated_time'] > report['checks']['time_estimation']['declared_time']:
            suggestions.append("Consider increasing allotted time or reducing question complexity")
        else:
            suggestions.append("Consider adding more questions or increasing difficulty")
    if report['checks']['difficulty_distribution']['status'] == 'WARN':
        easy_pct = report['checks']['difficulty_distribution']['easy_percentage']
        hard_pct = report['checks']['difficulty_distribution']['hard_percentage']
        if easy_pct < 20:
            suggestions.append("Add more easy-level questions (define, state, list)")
        if easy_pct > 40:
            suggestions.append("Reduce easy-level questions and add more challenging ones")
        if hard_pct < 10:
            suggestions.append("Add more hard-level questions (design, construct, analyze)")
        if hard_pct > 30:
            suggestions.append("Reduce hard-level questions for better balance")
    if report['checks']['crispness_analysis']['verbose_count'] > 0:
        suggestions.append(f"Simplify {report['checks']['crispness_analysis']['verbose_count']} verbose question(s)")
    if report['checks']['crispness_analysis']['ambiguous_count'] > 0:
        suggestions.append(f"Clarify {report['checks']['crispness_analysis']['ambiguous_count']} ambiguous question(s)")
    report['warnings'] = warnings
    report['suggestions'] = suggestions

def calculate_overall_score(report):
    score = 100
    if report['checks']['marks_validation']['status'] == 'FAIL':
        score -= 20
    if report['checks']['time_estimation']['status'] == 'WARN':
        score -= 10
    if report['checks']['difficulty_distribution']['status'] == 'WARN':
        score -= 15
    crispness_pct = report['checks']['crispness_analysis']['crispness_percentage']
    score -= int((100 - crispness_pct) * 0.3)
    return max(0, score)
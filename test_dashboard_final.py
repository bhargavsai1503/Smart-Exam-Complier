import os
import json
import tempfile

# Create a temporary job directory with semantic_report.json
with tempfile.TemporaryDirectory() as temp_dir:
    job_id = 'test_job'
    job_dir = os.path.join(temp_dir, job_id)
    os.makedirs(job_dir)

    # Use the existing semantic_report.json from jobs/905c7e8b-a159-4ce0-91cf-4a04076d0478/
    real_report = 'jobs/905c7e8b-a159-4ce0-91cf-4a04076d0478/semantic_report.json'
    with open(real_report, 'r') as f:
        report_data = json.load(f)

    # Load the original text from input.qp
    with open('jobs/905c7e8b-a159-4ce0-91cf-4a04076d0478/input.qp', 'r') as f:
        original_text = f.read()

    # Perform semantic analysis to enhance the report
    from analysis.semantic_analysis import perform_semantic_analysis
    enhanced_report = perform_semantic_analysis(report_data, original_text)

    # Merge enhanced data with original report
    report_data.update(enhanced_report)

    report_path = os.path.join(job_dir, 'semantic_report.json')
    with open(report_path, 'w') as f:
        json.dump(report_data, f)

    # Create input.qp file
    input_qp_content = '''[HEADER]
SUBJECT: "Test Subject"
[/HEADER]
[QUESTION_LIST]
[QUESTION]
Q_TEXT: "Sample question"
Q_MARKS: 10
[/QUESTION]
[/QUESTION_LIST]'''
    input_qp_path = os.path.join(job_dir, 'input.qp')
    with open(input_qp_path, 'w') as f:
        f.write(input_qp_content)

    print('Testing dashboard data mapping with enhanced report...')

    # Simulate the dashboard function logic
    report = report_data

    # Ensure required keys exist for template
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
        report['statistics']['difficulty_medium_count'] = report['statistics'].get('difficulty_medium_count', 0)

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
        try:
            with open(input_qp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                report['extracted_text'] = content[:1000] + '...' if len(content) > 1000 else content
        except Exception:
            report['extracted_text'] = 'No extracted text available yet.'

    print('Dashboard data prepared successfully:')
    print('  Total Marks:', report['statistics']['total_marks_declared'])
    print('  Estimated Time:', report['statistics']['estimated_time_minutes'], 'min')
    print('  Difficulty Medium Count:', report['statistics']['difficulty_medium_count'])
    print('  Difficulty Distribution:', report['statistics']['difficulty_distribution'])
    print('  Marks Distribution:', report['statistics']['marks_distribution'])
    print('  Time Comparison:', report['statistics']['time_comparison'])
    print('  Crispness Score:', report.get('crispness_score'))
    print('  Extracted Text Length:', len(report['extracted_text']))
    print('  Checks Keys:', list(report['checks'].keys()))
    print('  Suggestions:', report['suggestions'])
    print('  Questions Count:', len(report.get('questions', [])))

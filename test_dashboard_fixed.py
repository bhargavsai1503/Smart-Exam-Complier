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

    report_path = os.path.join(job_dir, 'semantic_report.json')
    with open(report_path, 'w') as f:
        json.dump(report_data, f)

    # Create input.qp file
    input_qp_content = '[HEADER]\nSUBJECT: "Test Subject"\n[/HEADER]\n[QUESTION_LIST]\n[QUESTION]\nQ_TEXT: "Sample question"\nQ_MARKS: 10\n[/QUESTION]\n[/QUESTION_LIST]\n'
    input_qp_path = os.path.join(job_dir, 'input.qp')
    with open(input_qp_path, 'w') as f:
        f.write(input_qp_content)

    print('Testing dashboard data mapping...')

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
        report['statistics']['difficulty_medium_count'] = report.get('checks', {}).get('difficulty_distribution', {}).get('medium_count', 0)

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
    print('  Crispness Score:', report.get('crispness_score'))
    print('  Extracted Text Length:', len(report['extracted_text']))
    print('  Checks Keys:', list(report['checks'].keys()))
    print('  Suggestions:', report['suggestions'])
    print('  Questions Count:', len(report.get('questions', [])))

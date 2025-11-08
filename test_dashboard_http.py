import requests

try:
    response = requests.get('http://localhost:5000/dashboard')
    print('Status code:', response.status_code)
    if response.status_code == 200:
        html = response.text
        # Check for null values in the overview section
        import re
        overview_start = html.find('<div id="overview"')
        overview_end = html.find('<div id="charts"', overview_start)
        overview_section = html[overview_start:overview_end]
        print('Overview section contains null:', 'null' in overview_section.lower())
        # Extract the spans with values
        spans = re.findall(r'<span class="text-2xl font-bold">([^<]+)</span>', overview_section)
        print('Values in overview:', spans)
    else:
        print('Error:', response.text)
except Exception as e:
    print('Error:', e)

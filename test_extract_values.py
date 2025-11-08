import requests
import re

response = requests.get('http://localhost:5000/dashboard')
html = response.text
print('Full HTML length:', len(html))
print('First 500 characters:')
print(html[:500])
print('Last 500 characters:')
print(html[-500:])
# Check if dashboard is showing null
if 'null' in html.lower():
    print('HTML contains null values')
else:
    print('No null values found in HTML')
# Extract all spans with text-2xl font-bold
spans = re.findall(r'<span class="text-2xl font-bold">([^<]+)</span>', html)
print('All extracted values:', spans)

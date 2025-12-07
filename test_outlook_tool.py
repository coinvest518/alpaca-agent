import requests
import os

api_key = os.getenv('COMPOSIO_API_KEY')
headers = {'x-api-key': api_key, 'Content-Type': 'application/json'}
base_url = 'https://backend.composio.dev/api/v3'

# Get all tools and filter for OUTLOOK toolkit
response = requests.get(f'{base_url}/tools', headers=headers)
if response.status_code == 200:
    tools = response.json()
    items = tools.get('items', [])
    
    outlook_tools = []
    for tool in items:
        toolkit_slug = tool.get('toolkit', {}).get('slug', '')
        if toolkit_slug.upper() == 'OUTLOOK':
            outlook_tools.append(tool)
    
    print(f'Found {len(outlook_tools)} OUTLOOK tools:')
    for tool in outlook_tools:
        print(f'  Slug: {tool.get("slug")}')
        print(f'  Name: {tool.get("name")}')
        print(f'  Version: {tool.get("version")}')
        print()
else:
    print(f'Error getting tools: {response.status_code}')
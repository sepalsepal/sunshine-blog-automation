#!/usr/bin/env python3
import os, requests
from dotenv import load_dotenv
load_dotenv('.env')

NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

headers = {
    'Authorization': f'Bearer {NOTION_API_KEY}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}

url = f'https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query'
payload = {'filter': {'property': '번호', 'number': {'equals': 11}}}
resp = requests.post(url, headers=headers, json=payload)
data = resp.json()

if data.get('results'):
    page_id = data['results'][0]['id']
    update_url = f'https://api.notion.com/v1/pages/{page_id}'
    # Update posting status (게시 완료)
    props = {}
    resp = requests.patch(update_url, headers=headers, json={'properties': props})
    print('Updated 011 Strawberry Thread posting status')
    print('URL: https://www.threads.net/@sunshinedogfood/post/18066950156264859')
    resp = requests.patch(update_url, headers=headers, json={'properties': props})
    print('OK' if resp.status_code == 200 else f'FAIL: {resp.status_code} - {resp.text[:100]}')
else:
    print('Page not found')

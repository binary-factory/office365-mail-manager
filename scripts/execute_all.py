#!/usr/bin/env python3
"""
Execute all actions on the 100 emails.
"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from auth_microsoft import get_auth_headers, load_config
import requests

def main():
    # Load batch
    with open('memory/decision_history/2026-03-14-0048-batch.json') as f:
        data = json.load(f)
    
    mails = data['mails']
    
    # Load folder IDs
    try:
        with open('memory/folder_ids.json') as f:
            folders = json.load(f)
    except:
        folders = {}
    
    config = load_config()
    user = config['microsoft']['userPrincipalName']
    headers = get_auth_headers()
    
    flagged_count = 0
    forwarded_count = 0
    archived_2024_count = 0
    archived_2025_count = 0
    marked_read_count = 0
    failed_count = 0
    
    print('=' * 80)
    print('FUEHRE ALLE AKTIONEN AUS')
    print('=' * 80)
    print()
    
    for i, m in enumerate(mails, 1):
        mail_id = m['id']
        subject = m['subject']
        sender = m['from']
        year = m['received'][:4]
        
        action = None
        reason = ''
        
        # FLAG (important 2026 mails)
        if year == '2026':
            body = m['body_preview'].lower()
            subj_lower = subject.lower()
            snd_lower = sender.lower()
            
            if 'failed' in subj_lower and 'github' in snd_lower:
                action = 'flag'
                reason = 'Build/DevOps FAILED'
            elif i == 19 or 'partnership' in body:
                action = 'flag'
                reason = 'Business Partnership'
            elif i == 31 or 'finevoices' in body:
                action = 'flag'
                reason = 'FineVoices Kundenakquise'
            elif i == 34 or 'iso 27001' in body:
                action = 'flag'
                reason = 'ISO 27001 Zertifizierung'
            elif i == 30 or 'quotation' in body:
                action = 'flag'
                reason = 'Customer Web Quotation'
        
        # FORWARD (orders with attachments)
        if not action and m['has_attachments'] and 'order' in subject.lower():
            action = 'forward'
            reason = 'Order mit PDF'
        
        # ARCHIV (old mails)
        if not action:
            if year == '2024' and 'Archiv 2024' in folders:
                action = 'archive_2024'
                reason = 'Archiv 2024'
            elif year == '2025' and 'Archiv 2025' in folders:
                action = 'archive_2025'
                reason = 'Archiv 2025'
        
        # MARK READ (default)
        if not action:
            action = 'mark_read'
            reason = 'Info/Newsletter'
        
        print(f'{i:3}. {action:15} | {reason:30} | {subject[:40]}...')
        
        try:
            if action == 'flag':
                response = requests.patch(
                    f'https://graph.microsoft.com/v1.0/users/{user}/messages/{mail_id}',
                    headers=headers,
                    json={'importance': 'high'},
                    timeout=30
                )
                if response.status_code in [200, 202]:
                    flagged_count += 1
                else:
                    failed_count += 1
                    print(f'    FAILED: {response.status_code}')
            
            elif action == 'forward':
                forward_data = {
                    'comment': 'Hallo Lisa, hier ist eine neue Bestellung/Rechnung fuer die Buchhaltung. Liebe Gruesse, Jarvis',
                    'toRecipients': [{
                        'emailAddress': {
                            'address': 'l.pata@binary-factory.de',
                            'name': 'Lisa'
                        }
                    }]
                }
                response = requests.post(
                    f'https://graph.microsoft.com/v1.0/users/{user}/messages/{mail_id}/forward',
                    headers=headers,
                    json=forward_data,
                    timeout=30
                )
                if response.status_code in [200, 201, 202]:
                    forwarded_count += 1
                else:
                    failed_count += 1
                    print(f'    FAILED: {response.status_code}')
            
            elif action == 'archive_2024':
                response = requests.post(
                    f'https://graph.microsoft.com/v1.0/users/{user}/messages/{mail_id}/move',
                    headers=headers,
                    json={'destinationId': folders['Archiv 2024']},
                    timeout=30
                )
                if response.status_code in [200, 201]:
                    archived_2024_count += 1
                else:
                    failed_count += 1
                    print(f'    FAILED: {response.status_code}')
            
            elif action == 'archive_2025':
                response = requests.post(
                    f'https://graph.microsoft.com/v1.0/users/{user}/messages/{mail_id}/move',
                    headers=headers,
                    json={'destinationId': folders['Archiv 2025']},
                    timeout=30
                )
                if response.status_code in [200, 201]:
                    archived_2025_count += 1
                else:
                    failed_count += 1
                    print(f'    FAILED: {response.status_code}')
            
            elif action == 'mark_read':
                response = requests.patch(
                    f'https://graph.microsoft.com/v1.0/users/{user}/messages/{mail_id}',
                    headers=headers,
                    json={'isRead': True},
                    timeout=30
                )
                if response.status_code in [200, 202]:
                    marked_read_count += 1
                else:
                    failed_count += 1
                    print(f'    FAILED: {response.status_code}')
        
        except Exception as e:
            failed_count += 1
            print(f'    EXCEPTION: {e}')
    
    # Summary
    print()
    print('=' * 80)
    print('ERGEBNIS')
    print('=' * 80)
    print(f'Flagged:        {flagged_count} Mails')
    print(f'Forwarded:      {forwarded_count} Mails')
    print(f'Archived 2024:  {archived_2024_count} Mails')
    print(f'Archived 2025:  {archived_2025_count} Mails')
    print(f'Marked read:    {marked_read_count} Mails')
    print(f'Failed:         {failed_count} Mails')
    print('=' * 80)

if __name__ == '__main__':
    main()

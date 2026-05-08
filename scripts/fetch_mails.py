#!/usr/bin/env python3
"""
Fetch emails from Office 365 inbox.
Returns structured data for LLM analysis.
"""

import json
import sys
import requests
from datetime import datetime
from pathlib import Path
from auth_microsoft import get_auth_headers, load_config


def count_unread_mails():
    """Count total unread emails in inbox."""
    config = load_config()
    user = config['microsoft']['userPrincipalName']
    headers = get_auth_headers()
    
    filter_query = "isRead eq false"
    
    # Use $count to get total
    url = f"https://graph.microsoft.com/v1.0/users/{user}/messages/$count"
    params = {'$filter': filter_query}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        return int(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Failed to count mails: {e}", file=sys.stderr)
        return 0


def fetch_unread_mails(limit=20):
    """Fetch unread emails from inbox (only for configured user).
    
    If limit is 0 or 'all', fetches ALL unread mails in batches.
    """
    config = load_config()
    user = config['microsoft']['userPrincipalName']
    headers = get_auth_headers()
    
    # Query for unread messages
    filter_query = "isRead eq false"
    
    # If limit is 0 or 'all', fetch all in batches
    fetch_all = (limit == 0 or limit == 'all')
    batch_size = 20  # Microsoft Graph recommended batch size
    
    if fetch_all:
        total = count_unread_mails()
        print(f"Found {total} unread mails. Fetching in batches of {batch_size}...", file=sys.stderr)
        limit = total  # Set limit to total count
    
    url = f"https://graph.microsoft.com/v1.0/users/{user}/messages"
    
    mails = []
    next_link = None
    fetched = 0
    
    try:
        while fetched < limit:
            current_batch = min(batch_size, limit - fetched)
            
            if next_link:
                # Use @odata.nextLink for pagination
                response = requests.get(next_link, headers=headers, timeout=60)
            else:
                params = {
                    '$filter': filter_query,
                    '$orderby': 'receivedDateTime desc',
                    '$top': current_batch,
                    '$select': 'id,subject,receivedDateTime,from,toRecipients,ccRecipients,bodyPreview,importance,hasAttachments'
                }
                response = requests.get(url, headers=headers, params=params, timeout=60)
            
            response.raise_for_status()
            data = response.json()
            
            for msg in data.get('value', []):
                to_recipients = msg.get('toRecipients', [])
                
                mail = {
                    'id': msg['id'],
                    'subject': msg.get('subject', '(No subject)'),
                    'received': msg.get('receivedDateTime'),
                    'from': format_recipient(msg.get('from')),
                    'to': [format_recipient(r) for r in to_recipients],
                    'cc': [format_recipient(r) for r in msg.get('ccRecipients', [])],
                    'body_preview': msg.get('bodyPreview', ''),
                    'importance': msg.get('importance', 'normal'),
                    'has_attachments': msg.get('hasAttachments', False)
                }
                mails.append(mail)
                fetched += 1
            
            # Check for next page
            next_link = data.get('@odata.nextLink')
            if not next_link:
                break
        
        return mails
    
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch mails: {e}", file=sys.stderr)
        sys.exit(1)


def format_recipient(recipient):
    """Format email recipient object."""
    if not recipient:
        return 'Unknown'
    email = recipient.get('emailAddress', {})
    name = email.get('name', '')
    address = email.get('address', '')
    if name and address:
        return f"{name} <{address}>"
    return address or name or 'Unknown'


def save_batch(mails):
    """Save fetched mails to processing queue."""
    timestamp = datetime.now().strftime('%Y-%m-%d-%H%M')
    batch_file = Path(__file__).parent.parent / "memory" / "decision_history" / f"{timestamp}-batch.json"
    
    batch_file.parent.mkdir(parents=True, exist_ok=True)
    
    batch_data = {
        'timestamp': timestamp,
        'mails': mails,
        'status': 'fetched',
        'count': len(mails)
    }
    
    with open(batch_file, 'w') as f:
        json.dump(batch_data, f, indent=2)
    
    return batch_file


if __name__ == '__main__':
    config = load_config()
    limit = config.get('behavior', {}).get('maxMailsPerBatch', 20)
    
    mails = fetch_unread_mails(limit)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--save':
        batch_file = save_batch(mails)
        print(f"Saved {len(mails)} mails to {batch_file}")
    
    # Output for OpenClaw/LLM
    output = {
        'count': len(mails),
        'mails': mails,
        'timestamp': datetime.now().isoformat()
    }
    
    print(json.dumps(output, indent=2))

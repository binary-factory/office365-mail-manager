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


def fetch_unread_mails(limit=20):
    """Fetch unread emails from inbox (only for configured user)."""
    config = load_config()
    user = config['microsoft']['userPrincipalName']
    headers = get_auth_headers()
    
    # Query for unread messages - filter by current year and direct recipient
    current_year = datetime.now().year
    
    # Build filter: unread AND received this year AND addressed to configured user
    filter_query = f"isRead eq false and receivedDateTime ge {current_year}-01-01T00:00:00Z"
    
    url = f"https://graph.microsoft.com/v1.0/users/{user}/messages"
    params = {
        '$filter': filter_query,
        '$orderby': 'receivedDateTime desc',
        '$top': limit,
        '$select': 'id,subject,receivedDateTime,from,toRecipients,ccRecipients,bodyPreview,importance,hasAttachments'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        mails = []
        for msg in data.get('value', []):
            # Filter: only keep mails addressed to configured user
            to_recipients = msg.get('toRecipients', [])
            to_emails = [r.get('emailAddress', {}).get('address', '').lower() for r in to_recipients]
            
            # Skip if not addressed to configured user
            if user.lower() not in to_emails:
                continue
            
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

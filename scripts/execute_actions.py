#!/usr/bin/env python3
"""
Execute actions on emails based on LLM decisions.
Handles move, mark read, forward operations.
"""

import json
import sys
import requests
from pathlib import Path
from auth_microsoft import get_auth_headers, load_config


def execute_action(mail_id, action, params=None):
    """Execute a single action on an email."""
    config = load_config()
    user = config['microsoft']['userPrincipalName']
    headers = get_auth_headers()
    
    base_url = f"https://graph.microsoft.com/v1.0/users/{user}/messages/{mail_id}"
    
    try:
        if action == 'mark_read':
            response = requests.patch(
                base_url,
                headers=headers,
                json={'isRead': True},
                timeout=30
            )
            response.raise_for_status()
            return {'success': True, 'action': 'mark_read', 'mail_id': mail_id}
        
        elif action == 'mark_unread':
            response = requests.patch(
                base_url,
                headers=headers,
                json={'isRead': False},
                timeout=30
            )
            response.raise_for_status()
            return {'success': True, 'action': 'mark_unread', 'mail_id': mail_id}
        
        elif action == 'move':
            folder_name = params.get('folder', 'Inbox')
            folder_id = get_or_create_folder(folder_name, headers, user)
            
            response = requests.post(
                f"{base_url}/move",
                headers=headers,
                json={'destinationId': folder_id},
                timeout=30
            )
            response.raise_for_status()
            return {
                'success': True,
                'action': 'move',
                'mail_id': mail_id,
                'folder': folder_name
            }
        
        elif action == 'forward':
            to_address = params.get('to')
            if not to_address:
                raise ValueError("Forward action requires 'to' parameter")
            
            # Create forward message
            forward_data = {
                'comment': params.get('comment', 'Forwarded by OpenClaw Mail Manager'),
                'toRecipients': [{
                    'emailAddress': {
                        'address': to_address,
                        'name': to_address.split('@')[0]
                    }
                }]
            }
            
            response = requests.post(
                f"{base_url}/forward",
                headers=headers,
                json=forward_data,
                timeout=30
            )
            response.raise_for_status()
            return {
                'success': True,
                'action': 'forward',
                'mail_id': mail_id,
                'to': to_address
            }
        
        else:
            return {'success': False, 'error': f'Unknown action: {action}'}
    
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e), 'action': action, 'mail_id': mail_id}


# Cache für Ordner-IDs (pro Batch)
_folder_cache = {}

def get_or_create_folder(folder_name, headers, user):
    """Get folder ID or create if not exists. Uses caching to avoid duplicates."""
    global _folder_cache
    
    # Check cache first
    if folder_name in _folder_cache:
        return _folder_cache[folder_name]
    
    # Search for folder by name using filter
    try:
        response = requests.get(
            f"https://graph.microsoft.com/v1.0/users/{user}/mailFolders",
            headers=headers,
            params={"$filter": f"displayName eq '{folder_name}'"},
            timeout=30
        )
        response.raise_for_status()
        folders = response.json().get('value', [])
        
        if folders:
            folder_id = folders[0]['id']
            _folder_cache[folder_name] = folder_id
            return folder_id
    except Exception:
        pass  # Fall through to create
    
    # Create folder if not exists
    try:
        create_response = requests.post(
            f"https://graph.microsoft.com/v1.0/users/{user}/mailFolders",
            headers=headers,
            json={'displayName': folder_name},
            timeout=30
        )
        create_response.raise_for_status()
        folder_id = create_response.json()['id']
        _folder_cache[folder_name] = folder_id
        return folder_id
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            # Folder already exists, search again without filter
            response = requests.get(
                f"https://graph.microsoft.com/v1.0/users/{user}/mailFolders",
                headers=headers,
                params={'$top': 100},  # Get more folders
                timeout=30
            )
            response.raise_for_status()
            folders = response.json().get('value', [])
            for folder in folders:
                if folder.get('displayName') == folder_name:
                    _folder_cache[folder_name] = folder['id']
                    return folder['id']
        raise


def process_batch(decisions_file, dry_run=False):
    """Process a batch of decisions."""
    with open(decisions_file) as f:
        batch = json.load(f)
    
    results = {
        'timestamp': batch.get('timestamp'),
        'processed': [],
        'failed': [],
        'dry_run': dry_run
    }
    
    for decision in batch.get('decisions', []):
        mail_id = decision['mail_id']
        action = decision['action']
        params = decision.get('params', {})
        
        if dry_run:
            results['processed'].append({
                'mail_id': mail_id,
                'action': action,
                'params': params,
                'status': 'dry_run',
                'reasoning': decision.get('reasoning', '')
            })
            print(f"[DRY RUN] Would {action} mail {mail_id}")
        else:
            result = execute_action(mail_id, action, params)
            
            if result['success']:
                results['processed'].append(result)
                print(f"✓ {action}: {mail_id}")
            else:
                results['failed'].append(result)
                print(f"✗ {action} failed: {mail_id} - {result.get('error')}")
    
    # Save results
    results_file = Path(__file__).parent.parent / "memory" / "decision_history" / f"{batch['timestamp']}-results.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    print(f"Processed: {len(results['processed'])}, Failed: {len(results['failed'])}")
    
    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: execute_actions.py <decisions.json> [--dry-run]", file=sys.stderr)
        sys.exit(1)
    
    decisions_file = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    process_batch(decisions_file, dry_run)

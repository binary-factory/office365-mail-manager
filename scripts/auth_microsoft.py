#!/usr/bin/env python3
"""
Microsoft Graph API Authentication
Handles token acquisition and refresh for Office 365 access.
"""

import json
import sys
import os
import requests
import time
from pathlib import Path

# Token cache location
TOKEN_CACHE = Path(__file__).parent.parent / "memory" / "token_cache.json"


def load_config():
    """Load skill configuration from OpenClaw config."""
    # Config is passed via environment or stdin in OpenClaw
    config_path = os.environ.get('OPENCLAW_CONFIG_PATH', '~/.openclaw/openclaw.json')
    config_path = os.path.expanduser(config_path)
    
    try:
        with open(config_path) as f:
            config = json.load(f)
            return config.get('skills', {}).get('office365-mail-manager', {})
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)


def get_access_token(config):
    """Get access token, refresh if needed."""
    tenant_id = config['microsoft']['tenantId']
    client_id = config['microsoft']['clientId']
    client_secret = config['microsoft']['clientSecret']
    
    # Check cache first
    if TOKEN_CACHE.exists():
        try:
            with open(TOKEN_CACHE) as f:
                cache = json.load(f)
                if cache.get('expires_at', 0) > time.time() + 300:  # 5 min buffer
                    return cache['access_token']
        except:
            pass
    
    # Request new token
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://graph.microsoft.com/.default'
    }
    
    try:
        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()
        token_data = response.json()
        
        # Cache token
        token_data['expires_at'] = time.time() + token_data.get('expires_in', 3600)
        TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_CACHE, 'w') as f:
            json.dump(token_data, f)
        
        return token_data['access_token']
    
    except requests.exceptions.RequestException as e:
        print(f"Token acquisition failed: {e}", file=sys.stderr)
        sys.exit(1)


def test_connection():
    """Test Microsoft Graph API connection."""
    config = load_config()
    
    if not config.get('enabled'):
        print("Skill is disabled in config", file=sys.stderr)
        sys.exit(1)
    
    try:
        token = get_access_token(config)
        
        # Test API call
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        user = config['microsoft']['userPrincipalName']
        response = requests.get(
            f'https://graph.microsoft.com/v1.0/users/{user}',
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        user_data = response.json()
        print(f"✓ Connection successful")
        print(f"  User: {user_data.get('displayName')} ({user_data.get('mail')})")
        print(f"  Token expires: {time.ctime(TOKEN_CACHE.stat().st_mtime + 3600)}")
        return 0
        
    except Exception as e:
        print(f"✗ Connection failed: {e}", file=sys.stderr)
        sys.exit(1)


def get_auth_headers():
    """Get headers with valid access token."""
    config = load_config()
    token = get_access_token(config)
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_connection()
    else:
        config = load_config()
        token = get_access_token(config)
        print(token)

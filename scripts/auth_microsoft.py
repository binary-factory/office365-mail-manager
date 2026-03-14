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
            # OpenClaw uses skills.entries.<skillKey> structure
            skill_config = config.get('skills', {}).get('entries', {}).get('office365-mail-manager', {})
            
            if not skill_config:
                raise KeyError("office365-mail-manager")
            
            # Config is stored in 'env' as flat key-value pairs
            env = skill_config.get('env', {})
            
            # Support both formats: O365CLIENTID (new) and O365_CLIENT_ID (old)
            # Prioritize the new format (without underscores) as it contains the rotated secret
            def get_env(key_with_underscore, key_without_underscore):
                return env.get(key_without_underscore) or env.get(key_with_underscore)
            
            # Build nested config from flat env vars
            result = {
                'enabled': skill_config.get('enabled', False),
                'microsoft': {
                    'clientId': get_env('O365_CLIENT_ID', 'O365CLIENTID'),
                    'tenantId': get_env('O365_TENANT_ID', 'O365TENANTID'),
                    'clientSecret': get_env('O365_CLIENT_SECRET', 'O365CLIENTSECRET'),
                    'userPrincipalName': get_env('O365_USER_EMAIL', 'O365USEREMAIL'),
                    'emailSignature': get_env('O365_EMAIL_SIGNATURE', 'O365EMAILSIGNATURE') or '',
                },
                'behavior': {
                    'timezone': get_env('O365_TIMEZONE', 'O365TIMEZONE') or 'Europe/Berlin',
                    'checkIntervalMinutes': int(get_env('O365_CHECK_INTERVAL', 'O365CHECKINTERVAL') or '30'),
                    'maxMailsPerBatch': int(get_env('O365_MAX_MAILS', 'O365MAXMAILS') or '20'),
                    'dryRun': (get_env('O365_DRY_RUN', 'O365DRYRUN') or 'false').lower() == 'true',
                }
            }
            
            # Validate required fields
            if not result['microsoft']['clientId']:
                raise KeyError("O365_CLIENT_ID")
            if not result['microsoft']['tenantId']:
                raise KeyError("O365_TENANT_ID")
            if not result['microsoft']['clientSecret']:
                raise KeyError("O365_CLIENT_SECRET")
            if not result['microsoft']['userPrincipalName']:
                raise KeyError("O365_USER_EMAIL")
            
            return result
    except FileNotFoundError:
        print(f"Config file not found: {config_path}", file=sys.stderr)
        print("\nRequired OpenClaw config:", file=sys.stderr)
        print("  openclaw config set skills.entries.office365-mail-manager.enabled true", file=sys.stderr)
        print("  openclaw config set skills.entries.office365-mail-manager.env.O365_CLIENT_ID 'YOUR_ID'", file=sys.stderr)
        print("  openclaw config set skills.entries.office365-mail-manager.env.O365_TENANT_ID 'YOUR_ID'", file=sys.stderr)
        print("  openclaw config set skills.entries.office365-mail-manager.env.O365_CLIENT_SECRET 'YOUR_SECRET'", file=sys.stderr)
        print("  openclaw config set skills.entries.office365-mail-manager.env.O365_USER_EMAIL 'email@domain.com'", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"Missing config: {e}", file=sys.stderr)
        print("\nRequired OpenClaw config:", file=sys.stderr)
        print("  openclaw config set skills.entries.office365-mail-manager.enabled true", file=sys.stderr)
        print("  openclaw config set skills.entries.office365-mail-manager.env.O365_CLIENT_ID 'YOUR_ID'", file=sys.stderr)
        print("  openclaw config set skills.entries.office365-mail-manager.env.O365_TENANT_ID 'YOUR_ID'", file=sys.stderr)
        print("  openclaw config set skills.entries.office365-mail-manager.env.O365_CLIENT_SECRET 'YOUR_SECRET'", file=sys.stderr)
        print("  openclaw config set skills.entries.office365-mail-manager.env.O365_USER_EMAIL 'email@domain.com'", file=sys.stderr)
        sys.exit(1)
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

# Troubleshooting

## Common Issues

### "Unauthorized" or 401 Error

**Cause**: Token expired or invalid credentials

**Solution**:
```bash
# Test connection
openclaw skills run office365-mail-manager --action=test-connection

# If fails, check config
openclaw config get skills.office365-mail-manager.microsoft
```

### "Forbidden" or 403 Error

**Cause**: Missing API permissions or no admin consent

**Solution**:
1. Go to Azure Portal → App Registration → API Permissions
2. Ensure all required permissions are granted
3. Click "Grant admin consent"

### "Not Found" or 404 Error

**Cause**: User not found or wrong email

**Solution**:
```bash
# Check userPrincipalName
openclaw config get skills.office365-mail-manager.microsoft.userPrincipalName

# Should match exactly: user@domain.com
```

### Rate Limiting (429)

**Cause**: Too many requests

**Solution**:
- Increase checkIntervalMinutes (default: 30)
- The script automatically handles retries with backoff

### Token Cache Issues

**Cause**: Corrupted token cache

**Solution**:
```bash
# Delete token cache
rm ~/.openclaw/skills/office365-mail-manager/memory/token_cache.json

# Re-test
openclaw skills run office365-mail-manager --action=test-connection
```

## Debug Mode

Run with debug output:
```bash
OPENCLAW_DEBUG=1 openclaw skills run office365-mail-manager --action=process-once --dry-run
```

## Logs

Check logs:
```bash
# OpenClaw logs
tail -f ~/.openclaw/logs/openclaw.log

# Skill-specific logs
ls -la ~/.openclaw/skills/office365-mail-manager/memory/decision_history/
```

## Getting Help

1. Check `memory/decision_history/` for detailed logs
2. Verify Azure App configuration
3. Test with `--dry-run` first
4. Check OpenClaw system status: `openclaw status`

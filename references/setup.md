# Office 365 Mail Manager — Setup Guide

Complete guide for setting up the Office 365 Mail Manager skill.

## 1. Azure App Registration

1. Go to [Azure Portal](https://portal.azure.com) → **Azure Active Directory**
2. **App registrations** → **New registration**
3. **Name:** `OpenClaw-Mail-Manager`
4. **Supported account types:** Accounts in this organizational directory only
5. **Redirect URI:** `http://localhost` (for initial auth)
6. **Register** → note **Application (client) ID** and **Directory (tenant) ID**

## 2. Configure Authentication

1. **Certificates & secrets** → **New client secret**
2. Add description, set expiry
3. **Copy Value immediately** (shown only once)

## 3. Configure API Permissions

Add these **Microsoft Graph** permissions:

- `Mail.Read` — Read emails
- `Mail.ReadWrite` — Move/mark emails
- `Mail.Send` — Forward emails
- `MailboxSettings.Read` — Access folders
- `User.Read` — Basic profile

Click **Grant admin consent** for your tenant.

## 4. Configure OpenClaw

```bash
# Enable the skill
openclaw config set skills.entries.office365-mail-manager.enabled true

# Azure credentials (flat env format)
openclaw config set skills.entries.office365-mail-manager.env.O365_CLIENT_ID "YOUR_CLIENT_ID"
openclaw config set skills.entries.office365-mail-manager.env.O365_TENANT_ID "YOUR_TENANT_ID"
openclaw config set skills.entries.office365-mail-manager.env.O365_CLIENT_SECRET "YOUR_CLIENT_SECRET"
openclaw config set skills.entries.office365-mail-manager.env.O365_USER_EMAIL "your.email@domain.com"

# Optional: behavior settings
openclaw config set skills.entries.office365-mail-manager.env.O365_TIMEZONE "Europe/Berlin"
openclaw config set skills.entries.office365-mail-manager.env.O365_CHECK_INTERVAL "30"
openclaw config set skills.entries.office365-mail-manager.env.O365_MAX_MAILS "20"
openclaw config set skills.entries.office365-mail-manager.env.O365_DRY_RUN "false"

# Optional: HTML signature for outgoing emails
openclaw config set skills.entries.office365-mail-manager.env.O365_EMAIL_SIGNATURE "<br><br>--<br>Mit freundlichen Grüßen<br><strong>Your Name</strong>"
```

## 5. Test Connection

Call `o365_test_connection` to verify everything works.

## 6. First Run (Dry)

```
1. o365_fetch_unread_mails (limit: 10)
2. o365_classify_mails (with the fetched mails)
3. o365_execute_actions (dry_run: true, with the decisions)
```

## 7. Enable Scheduling (Optional)

Prefer OpenClaw `cron` jobs for scheduled runs. Use Gateway-backed cron instead of shell sleep loops.

Example cadence:

```bash
# Check every 30 minutes
openclaw cron add --name="mail-check-30min" --schedule="*/30 * * * *" \
  --command="openclaw skills run office365-mail-manager --action=check-and-process"

# Daily summary at 9 AM
openclaw cron add --name="mail-daily-summary" --schedule="0 9 * * *" \
  --command="openclaw skills run office365-mail-manager --action=send-summary"
```

## Runtime Data

The skill writes local runtime data under `memory/`:

- `learned_rules.json` — user feedback rules
- `sender_profiles.json` — sender behavior cache
- `folder_ids.json` — Graph folder lookup cache
- `token_cache.json` — Microsoft auth token cache
- `decision_history/` — batch logs and prompts

Do not commit `memory/` contents. They are user-specific operational data.

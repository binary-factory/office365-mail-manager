---
name: office365-mail-manager
description: Intelligent Office 365 email management with LLM-powered classification, learning from user feedback, and automated routing. Handles reading, categorizing (important/newsletter/invoice), forwarding, and daily summaries. Use when managing Office 365 inbox automatically, processing emails with AI context understanding, learning email preferences over time, or setting up email automation with feedback loop.
---

# Office 365 Mail Manager

Intelligent email management for Office 365 with LLM-powered classification and continuous learning.

## What This Skill Does

- **Fetch** unread emails from Office 365 inbox
- **Analyze** content with LLM for context-aware categorization
- **Decide** automatically: Important / Newsletter / Invoice / Info / Spam
- **Execute** actions: move, mark read, forward, archive
- **Report** decisions to user with reasoning
- **Learn** from user feedback to improve over time

## Quick Start

### 1. Azure App Registration

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory
2. App registrations → New registration
3. Name: `OpenClaw-Mail-Manager`
4. Supported account types: Accounts in this organizational directory only
5. Redirect URI: `http://localhost` (for initial auth)
6. Register → note **Application (client) ID** and **Directory (tenant) ID**

### 2. Configure Authentication

1. Certificates & secrets → New client secret
2. Add description, set expiry, copy **Value** immediately

### 3. Configure API Permissions

Add these Microsoft Graph permissions:

- `Mail.Read` (read emails)
- `Mail.ReadWrite` (move/mark emails)
- `Mail.Send` (forward emails)
- `MailboxSettings.Read` (access folders)
- `User.Read` (basic profile)

Click **Grant admin consent** for your tenant.

### 4. Configure OpenClaw

```bash
openclaw config set skills.office365-mail-manager.enabled true
openclaw config set skills.office365-mail-manager.microsoft.clientId "YOUR_CLIENT_ID"
openclaw config set skills.office365-mail-manager.microsoft.tenantId "YOUR_TENANT_ID"
openclaw config set skills.office365-mail-manager.microsoft.clientSecret "YOUR_CLIENT_SECRET"
openclaw config set skills.office365-mail-manager.microsoft.userPrincipalName "your.email@domain.com"
openclaw config set skills.office365-mail-manager.behavior.timezone "Europe/Berlin"
openclaw config set skills.office365-mail-manager.behavior.checkIntervalMinutes 30
```

### 5. Test Connection

```bash
openclaw skills run office365-mail-manager --action=test-connection
```

### 6. First Run

```bash
openclaw skills run office365-mail-manager --action=process-once --dry-run
```

### 7. Enable Cron

```bash
# Check every 30 minutes
openclaw cron add --name="mail-check-30min" --schedule="*/30 * * * *" \
  --command="openclaw skills run office365-mail-manager --action=check-and-process"

# Daily summary at 9 AM
openclaw cron add --name="mail-daily-summary" --schedule="0 9 * * *" \
  --command="openclaw skills run office365-mail-manager --action=send-summary"
```

## Configuration Reference

See [references/config_schema.md](references/config_schema.md) for complete configuration options.

## User Feedback

After each processing batch, you'll receive a report. Reply with:

- **"Alles gut"** — Confirm all decisions
- **"#2 falsch, wichtig"** — Mail #2 should be "important"
- **"Absender@firma.de immer Spam"** — Learn sender pattern
- **"Rechnungen immer an buchhaltung@... weiterleiten"** — Add forwarding rule

Your feedback updates `memory/learned_rules.json` automatically.

## Commands

| Command | Description |
|---------|-------------|
| `test-connection` | Verify Azure auth works |
| `process-once` | Single batch processing |
| `check-and-process` | Check + process (for cron) |
| `send-summary` | Send daily digest |
| `review-pending` | Show mails awaiting manual review |
| `reset-learning` | Clear learned rules (careful!) |

## Troubleshooting

See [references/troubleshooting.md](references/troubleshooting.md)

## Learning System

The skill maintains persistent memory:

- `memory/learned_rules.json` — Explicit rules from feedback
- `memory/sender_profiles.json` — Sender behavior patterns
- `memory/decision_history/` — Log of all decisions for review

Learned patterns are automatically applied to new emails.

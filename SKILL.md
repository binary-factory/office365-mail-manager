---
name: office365_mail_manager
description: Intelligent Office 365 email management with LLM-powered classification, learning from user feedback, and automated routing. Handles reading, categorizing (important/newsletter/invoice), forwarding, and daily summaries.
tools:
  - name: o365_test_connection
    description: Test the Office 365/Microsoft Graph API connection. Use this first to verify Azure credentials are working.
    command: "${SKILL_DIR}/tools/o365_test_connection"
    parameters:
      type: object
      properties: {}
      required: []
  
  - name: o365_fetch_unread_mails
    description: Fetch unread emails from Office 365 inbox. Returns structured email data including subject, sender, preview, and metadata.
    command: "${SKILL_DIR}/tools/o365_fetch_unread_mails"
    parameters:
      type: object
      properties:
        limit:
          type: number
          description: Maximum number of emails to fetch (default 20)
          default: 20
        save_batch:
          type: boolean
          description: Whether to save the batch to memory for later processing
          default: true
      required: []
  
  - name: o365_classify_mails
    description: Analyze emails with LLM and classify them into categories (important/newsletter/invoice/info/spam). Returns classification decisions with reasoning.
    command: "${SKILL_DIR}/tools/o365_classify_mails"
    parameters:
      type: object
      properties:
        mails:
          type: array
          description: Array of mail objects from o365_fetch_unread_mails
          items:
            type: object
        apply_learned_rules:
          type: boolean
          description: Whether to apply previously learned sender/subject rules
          default: true
      required: [mails]
  
  - name: o365_execute_actions
    description: Execute actions on emails based on classification decisions (move, mark_read, forward). Can run in dry-run mode.
    command: "${SKILL_DIR}/tools/o365_execute_actions"
    parameters:
      type: object
      properties:
        decisions:
          type: array
          description: Array of decision objects from o365_classify_mails
          items:
            type: object
        dry_run:
          type: boolean
          description: Show what would be done without actually doing it
          default: false
      required: [decisions]
  
  - name: o365_process_feedback
    description: Process user feedback to improve future classifications. Learns sender patterns, subject keywords, and user preferences.
    command: "${SKILL_DIR}/tools/o365_process_feedback"
    parameters:
      type: object
      properties:
        feedback:
          type: string
          description: User feedback text (e.g., "Alles gut", "3 falsch, wichtig", "absender@firma.de immer spam")
        batch_timestamp:
          type: string
          description: Optional timestamp of the batch this feedback refers to
      required: [feedback]
  
  - name: o365_send_daily_summary
    description: Send a daily summary of processed emails to the configured channel (WhatsApp/Telegram/etc).
    command: "${SKILL_DIR}/tools/o365_send_daily_summary"
    parameters:
      type: object
      properties:
        date:
          type: string
          description: Date for summary (YYYY-MM-DD), defaults to today
      required: []
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
```

### 5. Test Connection

Call the `o365_test_connection` tool to verify everything works.

### 6. First Run (Dry)

```
1. o365_fetch_unread_mails (limit: 10)
2. o365_classify_mails (with the fetched mails)
3. o365_execute_actions (dry_run: true, with the decisions)
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

## Tool Usage Guide

### o365_test_connection
**When to use:** First time setup or when troubleshooting connection issues.
**Returns:** Success/failure status and user info.

### o365_fetch_unread_mails
**When to use:** Starting a new processing batch.
**Parameters:**
- `limit`: How many emails to fetch (default 20)
- `save_batch`: Save to memory for later reference (default true)
**Returns:** Array of mail objects with id, subject, from, body_preview, etc.

### o365_classify_mails
**When to use:** After fetching mails, before executing actions.
**Parameters:**
- `mails`: The array from o365_fetch_unread_mails
- `apply_learned_rules`: Apply previous feedback (default true)
**Returns:** Decisions array with category, action, reasoning, confidence for each mail.

### o365_execute_actions
**When to use:** After classification, to actually process the emails.
**Parameters:**
- `decisions`: The decisions array from o365_classify_mails
- `dry_run`: Preview mode without actual changes (default false)
**Returns:** Results of each action (success/failure).
**Important:** Every email is automatically marked as read after processing, so it won't appear again in the next batch.

### o365_process_feedback
**When to use:** After showing user the classification results, to learn from corrections.
**Parameters:**
- `feedback`: User's natural language feedback
- `batch_timestamp`: Optional reference to specific batch
**Returns:** Parsed rules that were learned.

### o365_send_daily_summary
**When to use:** End of day or scheduled daily report.
**Parameters:**
- `date`: Which day to summarize (default today)
**Returns:** Summary sent to configured channel.

## Categories

| Category | Description | Default Action |
|----------|-------------|----------------|
| **important** | Direct to you, action needed, customers, partners | Move to "Wichtig" folder |
| **newsletter** | Bulk emails, marketing, automated updates | Mark read, move to "Newsletter" |
| **invoice** | Bills, payment requests | Forward to configured address, move to "Rechnungen" |
| **info** | FYI emails, no action needed | Mark read |
| **spam** | Unsolicited, irrelevant | Move to Junk |

## User Feedback Patterns

After showing results, accept feedback like:

- **"Alles gut"** — Confirm all decisions
- **"#2 falsch, wichtig"** — Mail #2 should be "important"
- **"Absender@firma.de immer Spam"** — Learn sender pattern
- **"Rechnungen immer an buchhaltung@... weiterleiten"** — Add forwarding rule

## Learning System

The skill maintains persistent memory:

- `memory/learned_rules.json` — Explicit rules from feedback
- `memory/sender_profiles.json` — Sender behavior patterns
- `memory/decision_history/` — Log of all decisions for review

## Configuration Reference

See `config.schema.json` for complete configuration options.

## Troubleshooting

**Connection fails:**
- Check Azure app has admin consent granted
- Verify client secret hasn't expired
- Ensure userPrincipalName matches exactly

**No mails fetched:**
- Check if inbox actually has unread messages
- Verify Mail.Read permission is granted

**Actions fail:**
- Check Mail.ReadWrite permission for move/mark
- Check Mail.Send permission for forward
- Verify folders exist or can be created

## Tool Locations

Tools are executable scripts in `tools/`:
- `tools/o365_test_connection` — Test Azure connection
- `tools/o365_fetch_unread_mails` — Fetch emails
- `tools/o365_classify_mails` — Prepare LLM classification
- `tools/o365_execute_actions` — Execute decisions
- `tools/o365_process_feedback` — Learn from feedback
- `tools/o365_send_daily_summary` — Daily reports

## Legacy Scripts

The original scripts in `scripts/` are still available for backward compatibility:
- `scripts/main.py` — CLI entry point
- `scripts/fetch_mails.py` — Email fetching
- `scripts/classify_mails.py` — Classification prep
- `scripts/execute_actions.py` — Action execution
- `scripts/process_feedback.py` — Learning system
- `scripts/auth_microsoft.py` — Authentication

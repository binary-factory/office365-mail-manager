# Office 365 Mail Manager — Tool Guide

Detailed guide for using each tool in the Office 365 Mail Manager skill.

## o365_test_connection

**Purpose:** Verify Azure credentials and Graph API connectivity.

**When to use:** First time setup or troubleshooting connection issues.

**Returns:** Success/failure status and user info.

## o365_fetch_unread_mails

**Purpose:** Fetch unread emails from Office 365 inbox.

**When to use:** Starting a new processing batch.

**Parameters:**
- `limit` (number, default: 20): Maximum emails to fetch
  - Use `0` or `"all"` to fetch ALL unread emails in batches of 20
- `save_batch` (boolean, default: true): Save to memory for later processing

**Returns:** Array of mail objects with:
- `id` — Unique identifier
- `subject` — Email subject
- `from` — Sender address
- `body_preview` — First 500 characters
- `received` — ISO timestamp
- `importance` — normal/high/low
- `has_attachments` — boolean

**Example:**
```json
{"limit": 100}
```

## o365_classify_mails

**Purpose:** Analyze emails with LLM and classify into categories.

**When to use:** After fetching mails, before executing actions.

**Parameters:**
- `mails` (array, required): Array from o365_fetch_unread_mails
- `apply_learned_rules` (boolean, default: true): Apply previous feedback

**Returns:** Decisions array with:
- `mail_id` — Email identifier
- `category` — important/newsletter/invoice/info/spam
- `action` — flag/move/mark_read/forward

**Default rule:** If the classifier is uncertain, return `important` + `flag`. Do not return `none` for mails that may need human review.
- `reasoning` — Why this decision
- `confidence` — 0.0 to 1.0

## o365_execute_actions

**Purpose:** Execute actions on emails based on classification decisions.

**When to use:** After classification, to actually process emails.

**Parameters:**
- `decisions` (array, required): Decisions from o365_classify_mails
- `dry_run` (boolean, default: false): Preview without changes

**Important:** Every email is automatically marked as read after processing.

**Returns:** Results of each action (success/failure).

## o365_process_feedback

**Purpose:** Learn from user feedback to improve future classifications.

**When to use:** After showing classification results to user.

**Parameters:**
- `feedback` (string, required): Natural language feedback
  - "Alles gut" — Confirm all decisions
  - "#2 falsch, wichtig" — Correct specific mail
  - "absender@firma.de immer spam" — Learn sender pattern
- `batch_timestamp` (string, optional): Reference to specific batch

**Returns:** Parsed rules that were learned.

## o365_send_daily_summary

**Purpose:** Send daily summary of processed emails.

**When to use:** End of day or scheduled daily report.

**Parameters:**
- `date` (string, optional): Which day to summarize (YYYY-MM-DD), defaults to today

**Returns:** Summary sent to configured channel.

## o365_send_email

**Purpose:** Send a new email via Office 365.

**⚠️ CRITICAL: NEVER use without explicit user approval!**

**Parameters:**
- `to` (string, required): Recipient address(es), comma-separated
- `subject` (string, required): Email subject
- `body` (string, required): Email body content
- `cc` (string, optional): CC recipients, comma-separated
- `bcc` (string, optional): BCC recipients, comma-separated
- `html` (boolean, default: false): Send as HTML

**Examples:**

Simple text email:
```json
{
  "to": "kunde@beispiel.de",
  "subject": "Angebot",
  "body": "Hallo, hier ist Ihr Angebot..."
}
```

HTML email with CC:
```json
{
  "to": "kunde@beispiel.de",
  "cc": "intern@binary-factory.de",
  "subject": "Angebot",
  "body": "<h1>Angebot</h1><p>Details...</p>",
  "html": true
}
```

Multiple recipients:
```json
{
  "to": "a@beispiel.de,b@beispiel.de",
  "subject": "Newsletter",
  "body": "Hallo zusammen..."
}
```

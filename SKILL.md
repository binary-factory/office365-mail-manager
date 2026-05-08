---
name: office365-mail-manager
description: Intelligent Office 365 email management with LLM-powered classification, learning from user feedback, and automated routing. Handles reading, categorizing (important/newsletter/invoice), forwarding, and daily summaries. Use when working with Office 365 emails for automated processing, classification, or sending.
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
          description: Maximum number of emails to fetch (default 20, use 0 or "all" for ALL unread mails)
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
    description: Execute actions on emails based on classification decisions (flag, mark_read, forward, move). Can run in dry-run mode.
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
    description: Send a daily summary of processed emails to the configured channel.
    command: "${SKILL_DIR}/tools/o365_send_daily_summary"
    parameters:
      type: object
      properties:
        date:
          type: string
          description: Date for summary (YYYY-MM-DD), defaults to today
      required: []

  - name: o365_send_email
    description: Send a new email via Office 365. Supports HTML or plain text, CC/BCC recipients. NEVER use without explicit user approval.
    command: "${SKILL_DIR}/tools/o365_send_email"
    parameters:
      type: object
      properties:
        to:
          type: string
          description: Recipient email address(es), comma-separated for multiple
        subject:
          type: string
          description: Email subject line
        body:
          type: string
          description: Email body content
        cc:
          type: string
          description: CC recipient(s), comma-separated (optional)
        bcc:
          type: string
          description: BCC recipient(s), comma-separated (optional)
        html:
          type: boolean
          description: Send as HTML instead of plain text (default false)
          default: false
      required: [to, subject, body]
---

# Office 365 Mail Manager

Intelligent email management for Office 365 with LLM-powered classification and continuous learning.

## What This Skill Does

- **Fetch** unread emails from Office 365 inbox
- **Analyze** content with LLM for context-aware categorization
- **Decide** automatically: Important / Newsletter / Invoice / Info / Spam
- **Execute** actions: flag, mark read, forward, move
- **Report** decisions to user with reasoning
- **Learn** from user feedback to improve over time

## Quick Start

1. **Configure** Azure credentials (see [references/setup.md](references/setup.md))
2. **Test** connection with `o365_test_connection`
3. **Process** emails:
   ```
   o365_fetch_unread_mails → o365_classify_mails → o365_execute_actions
   ```
4. **Give feedback** to improve classifications

See [references/tool_guide.md](references/tool_guide.md) for detailed tool usage.

## Categories

| Category | Description | Default Action |
|----------|-------------|----------------|
| **important** | Direct to you, action needed, customers, partners, security, banking, accounting, or unclear | **Flag** as important |
| **newsletter** | Clearly bulk emails, marketing, automated updates | Mark read |
| **invoice** | Clear bills, payment requests, receipts | Forward to configured address |
| **info** | Clear FYI emails with no action needed | Mark read |
| **spam** | Clearly unsolicited, irrelevant | Move to Junk or mark read |

**Default rule:** If a mail is not clearly safe to mark read and not clearly an invoice to forward, flag it. No uncertain mail should be left unprocessed as `none`.

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

## Agent Behavior Rules

### Sending Emails (CRITICAL)
**NEVER send emails without explicit user approval!**

**Workflow:**
1. **Draft** — Create email draft with suggested content
2. **Ask** — Present to user: "Soll ich diese Email senden?"
3. **Wait** — Wait for explicit confirmation ("Ja", "Senden", etc.)
4. **Send** — Only then use `o365_send_email`

**When to propose replies:**
- Customer inquiries requiring response
- Simple acknowledgments ("Danke, erhalten")
- Standard requests with clear answers
- Follow-ups on previous conversations

**When NOT to propose:**
- Complex negotiations
- Sensitive topics
- Legal matters
- When unsure about tone/content

## References

- [Setup Guide](references/setup.md) — Azure app registration and configuration
- [Tool Guide](references/tool_guide.md) — Detailed tool usage and examples
- [Troubleshooting](references/troubleshooting.md) — Common issues and solutions
- [Graph API](references/graph_api.md) — Microsoft Graph API documentation

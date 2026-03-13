# Office 365 Mail Manager

Intelligenter E-Mail-Manager für Office 365 mit LLM-gestützter Klassifizierung und Lernfähigkeit.

## Features

- 🤖 **LLM-gestützte Analyse** — Versteht Kontext, nicht nur Keywords
- 📧 **Automatische Verarbeitung** — Wichtig/Newsletter/Rechnung/Info erkennen
- 📤 **Weiterleitung** — Rechnungen automatisch an Buchhaltung
- 📚 **Lernfähig** — Merkt sich Feedback und verbessert sich
- 📊 **Reports** — Zusammenfassungen mit Begründungen
- ⏰ **Cron-Ready** — Automatische Prüfung im Hintergrund

## Schnellstart

1. [Azure App erstellen](SKILL.md#1-azure-app-registration)
2. Konfigurieren:
   ```bash
   openclaw config set skills.office365-mail-manager.enabled true
   openclaw config set skills.office365-mail-manager.microsoft.clientId "..."
   openclaw config set skills.office365-mail-manager.microsoft.tenantId "..."
   openclaw config set skills.office365-mail-manager.microsoft.clientSecret "..."
   openclaw config set skills.office365-mail-manager.microsoft.userPrincipalName "deine@email.de"
   ```
3. Testen:
   ```bash
   openclaw skills run office365-mail-manager --action=test-connection
   ```
4. Erster Lauf:
   ```bash
   openclaw skills run office365-mail-manager --action=process-once --dry-run
   ```

## Feedback geben

Nach jedem Report:
- `"Alles gut"` — Bestätigen
- `"3 falsch, wichtig"` — Korrektur
- `"newsletter@spam.de immer spam"` — Muster lernen

## Lizenz

MIT — Für OpenClaw/ClawHub entwickelt.

# Installation & Setup Guide

## Office 365 Mail Manager für OpenClaw

Dieser Skill verwaltet automatisch Office 365 E-Mails mit LLM-gestützter Klassifizierung.

---

## 📋 Voraussetzungen

- OpenClaw installiert und konfiguriert
- Office 365 Account (Microsoft 365)
- Azure Portal Zugriff für App-Registrierung

---

## 🔧 Schritt 1: Azure App Registrierung

1. **Azure Portal öffnen**: https://portal.azure.com
2. **Azure Active Directory** → **App registrations** → **New registration**
3. **Name**: `OpenClaw-Mail-Manager`
4. **Supported account types**: "Accounts in this organizational directory only"
5. **Redirect URI**: `http://localhost`
6. **Register** klicken

### API Berechtigungen hinzufügen

1. Im Menü: **API permissions** → **Add a permission**
2. **Microsoft Graph** → **Application permissions**
3. Folgende Berechtigungen hinzufügen:
   - `Mail.Read` (E-Mails lesen)
   - `Mail.ReadWrite` (E-Mails verschieben/markieren)
   - `Mail.Send` (E-Mails weiterleiten)
   - `MailboxSettings.Read` (Ordner verwalten)
   - `User.Read` (Benutzerprofil lesen)
4. **Grant admin consent** klicken (wichtig!)

### Client Secret erstellen

1. **Certificates & secrets** → **New client secret**
2. **Description**: `OpenClaw Production`
3. **Expires**: 24 months
4. **Add** klicken
5. **Value sofort kopieren!** (wird nur einmal angezeigt)

### IDs notieren

- **Application (client) ID**: z.B. `4034fe5d-aeab-4f10-87c9-f542d1e98893`
- **Directory (tenant) ID**: z.B. `01427649-e86d-4474-ac05-afa66ddb5b0c`
- **Client Secret**: z.B. `3yG8Q~...`

---

## 💻 Schritt 2: Skill Installation

### Option A: Von GitHub (empfohlen)

```bash
# In OpenClaw
openclaw skills install github:dein-username/office365-mail-manager
```

### Option B: Manuell

```bash
# Skill-Ordner erstellen
mkdir -p ~/.openclaw/skills/office365-mail-manager
cd ~/.openclaw/skills/office365-mail-manager

# Dateien kopieren (oder Git clone)
git clone https://github.com/dein-username/office365-mail-manager.git .

# Python Dependencies installieren
python3 -m venv .venv
source .venv/bin/activate
pip install requests
```

---

## ⚙️ Schritt 3: Konfiguration

### OpenClaw Config setzen

```bash
# Skill aktivieren
openclaw config set skills.office365-mail-manager.enabled true

# Microsoft Auth
openclaw config set skills.office365-mail-manager.microsoft.clientId "DEINE-CLIENT-ID"
openclaw config set skills.office365-mail-manager.microsoft.tenantId "DEINE-TENANT-ID"
openclaw config set skills.office365-mail-manager.microsoft.clientSecret "DEIN-CLIENT-SECRET"
openclaw config set skills.office365-mail-manager.microsoft.userPrincipalName "dein.email@domain.de"

# Verhalten
openclaw config set skills.office365-mail-manager.behavior.timezone "Europe/Berlin"
openclaw config set skills.office365-mail-manager.behavior.checkIntervalMinutes 30
```

### Direkt in openclaw.json

```json
{
  "skills": {
    "office365-mail-manager": {
      "enabled": true,
      "microsoft": {
        "clientId": "DEINE-CLIENT-ID",
        "tenantId": "DEINE-TENANT-ID",
        "clientSecret": "DEIN-CLIENT-SECRET",
        "userPrincipalName": "dein.email@domain.de"
      },
      "behavior": {
        "timezone": "Europe/Berlin",
        "checkIntervalMinutes": 30
      }
    }
  }
}
```

---

## 🧪 Schritt 4: Test

```bash
# Verbindung testen
cd ~/.openclaw/skills/office365-mail-manager
source .venv/bin/activate
python3 scripts/auth_microsoft.py test

# Erster Dry-Run
python3 scripts/main.py process-once --dry-run --limit 5
```

---

## ⏰ Schritt 5: Cronjob einrichten

### Wochentags, 3x täglich

```bash
# Morgens 09:30
openclaw cron add \
  --name="mail-check-morning" \
  --schedule="30 9 * * 1-5" \
  --command="openclaw skills run office365-mail-manager --action=check-and-process"

# Mittags 13:00
openclaw cron add \
  --name="mail-check-noon" \
  --schedule="0 13 * * 1-5" \
  --command="openclaw skills run office365-mail-manager --action=check-and-process"

# Nachmittags 16:30
openclaw cron add \
  --name="mail-check-afternoon" \
  --schedule="30 16 * * 1-5" \
  --command="openclaw skills run office365-mail-manager --action=check-and-process"
```

---

## 📁 Verzeichnisstruktur

```
office365-mail-manager/
├── SKILL.md                    # Hauptdokumentation
├── README.md                   # Schnellstart
├── INSTALL.md                  # Diese Datei
├── config.schema.json          # Config-Validierung
├── scripts/
│   ├── auth_microsoft.py       # OAuth2 / Token
│   ├── fetch_mails.py          # Mails holen
│   ├── classify_mails.py       # LLM-Analyse
│   ├── execute_actions.py      # Aktionen ausführen
│   ├── process_feedback.py     # Feedback verarbeiten
│   └── main.py                 # Entry point
├── memory/                     # Lern-Daten (automatisch erstellt)
│   ├── learned_rules.json      # Gelernte Regeln
│   ├── sender_profiles.json    # Absender-Profile
│   ├── token_cache.json        # Token-Cache
│   └── decision_history/       # Verlauf
├── references/
│   ├── graph_api.md            # API-Dokumentation
│   └── troubleshooting.md      # Problembehebung
└── templates/
    └── report_template.md      # Report-Format
```

---

## 🎯 Verwendung

### Manuelle Ausführung

```bash
# Einzelner Durchlauf
openclaw skills run office365-mail-manager --action=process-once

# Mit Dry-Run (nur zeigen, nicht ausführen)
openclaw skills run office365-mail-manager --action=process-once --dry-run

# Test-Verbindung
openclaw skills run office365-mail-manager --action=test-connection
```

### Befehle

| Command | Beschreibung |
|---------|--------------|
| `test-connection` | Verbindung testen |
| `process-once` | Einmalige Verarbeitung |
| `check-and-process` | Prüfen + verarbeiten (für Cron) |
| `send-summary` | Tägliche Zusammenfassung |
| `review-pending` | Ausstehende Reviews zeigen |
| `reset-learning` | Gelernte Regeln löschen |

---

## 🔄 Feedback geben

Nach jedem Report antworte mit:

- `"Alles gut"` — Bestätigen
- `"3 falsch, wichtig"` — Korrektur (Mail #3 sollte wichtig sein)
- `"newsletter@spam.de immer spam"` — Absender lernen
- `"Rechnungen immer an buchhaltung@..."` — Weiterleitungsregel

---

## 🐛 Troubleshooting

### "Unauthorized" oder 401
```bash
# Token löschen und neu holen
rm ~/.openclaw/skills/office365-mail-manager/memory/token_cache.json
openclaw skills run office365-mail-manager --action=test-connection
```

### "Forbidden" oder 403
- Admin Consent in Azure Portal prüfen
- API Permissions prüfen

### Rate Limiting (429)
- `checkIntervalMinutes` erhöhen (Standard: 30)

---

## 🔒 Security

- **Token Cache** wird lokal gespeichert (`memory/token_cache.json`)
- **Client Secret** in OpenClaw Config (nicht im Code)
- **Scope minimal**: Nur `Mail.*` und `User.Read`

---

## 📞 Support

Bei Problemen:
1. `memory/decision_history/` prüfen (Logs)
2. Azure App-Konfiguration prüfen
3. `--dry-run` für Tests verwenden

---

**Erfolgreich installiert?** Jetzt alle 30 Minuten automatische Mail-Verarbeitung! 🎉

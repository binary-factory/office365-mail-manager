#!/usr/bin/env python3
"""
Classify emails using LLM (OpenClaw) for context-aware decisions.
Prepares data for LLM analysis and processes decisions.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import subprocess

sys.path.insert(0, str(Path(__file__).parent))
from process_feedback import load_learned_rules, get_rules_for_sender, get_rules_for_subject


def prepare_llm_prompt(mails, learned_rules):
    """Prepare prompt for LLM classification."""
    
    prompt = """Du bist ein intelligenter E-Mail-Assistent. Analysiere die folgenden E-Mails und kategorisiere sie.

## Deine Aufgabe

Für jede E-Mail entscheide:
1. **Kategorie**: important / newsletter / invoice / info / spam
2. **Aktion**: move / mark_read / forward / none
3. **Begründung**: Warum diese Entscheidung?

## Kategorien

- **important**: Direkt an dich adressiert, Handlungsbedarf, Kunden, Partner
- **newsletter**: Massenmails, Marketing, automatisierte Updates
- **invoice**: Rechnungen, Zahlungsaufforderungen
- **info**: FYI-Mails ohne Handlungsbedarf
- **spam**: Unsolicited, irrelevant

## Aktionen

- **move**: In entsprechenden Ordner verschieben
- **mark_read**: Als gelesen markieren (bei Newsletters)
- **forward**: Weiterleiten (bei Rechnungen)
- **none**: Keine Aktion

## Gelernte Regeln (beachten)

"""
    
    # Add learned sender rules
    sender_rules = learned_rules.get('sender_rules', {})
    if sender_rules:
        prompt += "\n**Bekannte Absender:**\n"
        for email, rule in list(sender_rules.items())[:10]:
            prompt += f"- {email} → {rule['category']}\n"
    
    # Add subject patterns
    subject_rules = learned_rules.get('subject_rules', [])
    if subject_rules:
        prompt += "\n**Betreff-Muster:**\n"
        for rule in subject_rules[:5]:
            prompt += f"- \"{rule['keyword']}\" → {rule['action']}\n"
    
    prompt += "\n## Zu verarbeitende E-Mails\n\n"
    
    for i, mail in enumerate(mails, 1):
        prompt += f"\n### E-Mail #{i}\n"
        prompt += f"**ID**: {mail['id']}\n"
        prompt += f"**Von**: {mail['from']}\n"
        prompt += f"**Betreff**: {mail['subject']}\n"
        prompt += f"**Empfangen**: {mail['received']}\n"
        prompt += f"**Wichtigkeit**: {mail['importance']}\n"
        prompt += f"**Vorschau**: {mail['body_preview'][:500]}...\n"
        
        # Check for learned rules on this sender/subject
        sender_rule = get_rules_for_sender(mail['from'])
        subject_rule = get_rules_for_subject(mail['subject'])
        
        if sender_rule:
            prompt += f"\n*[Gelernt: Absender ist '{sender_rule['category']}']*\n"
        if subject_rule:
            prompt += f"\n*[Gelernt: Betreff enthält '{subject_rule['keyword']}']*\n"
    
    prompt += """

## Antwortformat (JSON)

```json
{
  "decisions": [
    {
      "mail_id": "...",
      "mail_index": 1,
      "category": "important",
      "action": "move",
      "action_params": {"folder": "Wichtig"},
      "reasoning": "Direkt an dich adressiert, Kundenanfrage",
      "confidence": 0.9
    }
  ]
}
```

Gib nur das JSON zurück, keine Erklärungen davor oder danach.
"""
    
    return prompt


def process_llm_response(response_text, mails):
    """Process LLM JSON response into decisions."""
    
    # Extract JSON from response
    try:
        # Try to find JSON block
        if '```json' in response_text:
            json_start = response_text.find('```json') + 7
            json_end = response_text.find('```', json_start)
            json_str = response_text[json_start:json_end].strip()
        elif '```' in response_text:
            json_start = response_text.find('```') + 3
            json_end = response_text.find('```', json_start)
            json_str = response_text[json_start:json_end].strip()
        else:
            json_str = response_text.strip()
        
        decisions_data = json.loads(json_str)
        decisions = decisions_data.get('decisions', [])
        
        # Validate decisions match mails
        validated_decisions = []
        mail_lookup = {m['id']: m for m in mails}
        
        for decision in decisions:
            mail_id = decision.get('mail_id')
            if mail_id in mail_lookup:
                # Add mail metadata to decision
                mail = mail_lookup[mail_id]
                decision['mail_metadata'] = {
                    'subject': mail['subject'],
                    'from': mail['from'],
                    'received': mail['received']
                }
                validated_decisions.append(decision)
        
        return validated_decisions
    
    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response: {e}", file=sys.stderr)
        print(f"Response was:\n{response_text}", file=sys.stderr)
        return []


def classify_batch(mails_data_file, output_file=None):
    """Process a batch of mails through LLM classification."""
    
    # Load mails
    with open(mails_data_file) as f:
        data = json.load(f)
    
    mails = data.get('mails', [])
    
    if not mails:
        print("No mails to classify")
        return []
    
    # Load learned rules
    learned_rules = load_learned_rules()
    
    # Prepare prompt
    prompt = prepare_llm_prompt(mails, learned_rules)
    
    # Save prompt for debugging
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    prompt_file = Path(__file__).parent.parent / "memory" / "decision_history" / f"{timestamp}-prompt.txt"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    with open(prompt_file, 'w') as f:
        f.write(prompt)
    
    print(f"Prompt saved to: {prompt_file}")
    print(f"Classifying {len(mails)} mails...")
    
    # In OpenClaw context, we return the prompt for the LLM to process
    # The LLM will then call back with the decisions
    return {
        'prompt': prompt,
        'mails_count': len(mails),
        'timestamp': timestamp,
        'mails_file': mails_data_file
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: classify_mails.py <mails.json>", file=sys.stderr)
        print("\nOutputs JSON with 'prompt' field for LLM processing", file=sys.stderr)
        sys.exit(1)
    
    mails_file = sys.argv[1]
    result = classify_batch(mails_file)
    
    print(json.dumps(result, indent=2))

#!/usr/bin/env python3
"""
Process user feedback and update learned rules.
Maintains sender profiles and decision patterns.
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path(__file__).parent.parent / "memory"


def load_learned_rules():
    """Load existing learned rules."""
    rules_file = MEMORY_DIR / "learned_rules.json"
    if rules_file.exists():
        with open(rules_file) as f:
            return json.load(f)
    return {
        'version': 1,
        'created': datetime.now().isoformat(),
        'sender_rules': {},
        'subject_rules': [],
        'content_rules': [],
        'feedback_history': []
    }


def load_sender_profiles():
    """Load sender behavior profiles."""
    profiles_file = MEMORY_DIR / "sender_profiles.json"
    if profiles_file.exists():
        with open(profiles_file) as f:
            return json.load(f)
    return {}


def save_learned_rules(rules):
    """Save learned rules to file."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    rules_file = MEMORY_DIR / "learned_rules.json"
    rules['last_updated'] = datetime.now().isoformat()
    with open(rules_file, 'w') as f:
        json.dump(rules, f, indent=2)


def save_sender_profiles(profiles):
    """Save sender profiles."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    profiles_file = MEMORY_DIR / "sender_profiles.json"
    with open(profiles_file, 'w') as f:
        json.dump(profiles, f, indent=2)


def process_feedback(feedback_text, batch_timestamp=None):
    """Process user feedback and update rules."""
    rules = load_learned_rules()
    profiles = load_sender_profiles()
    
    feedback_entry = {
        'timestamp': datetime.now().isoformat(),
        'batch': batch_timestamp,
        'raw': feedback_text,
        'parsed_rules': []
    }
    
    # Pattern 1: "Alles gut" / "All good" / "Correct"
    if re.search(r'^(alles\s+gut|all\s+good|correct|stimmt|ok)$', feedback_text.strip(), re.I):
        feedback_entry['type'] = 'confirm_all'
        print("✓ Feedback: Alle Entscheidungen bestätigt")
    
    # Pattern 2: "{number} falsch, {correction}"
    # e.g., "3 falsch, wichtig" or "#2 should be newsletter"
    elif match := re.search(r'(?:#?\s*(\d+)\s+(?:falsch|wrong|should be|sollte sein)\s*,?\s*(.+))', feedback_text, re.I):
        mail_index = match.group(1)
        correction = match.group(2).strip().lower()
        
        # Map common terms
        category = map_to_category(correction)
        
        new_rule = {
            'type': 'specific_correction',
            'mail_index': mail_index,
            'category': category,
            'source': feedback_text
        }
        
        feedback_entry['parsed_rules'].append(new_rule)
        print(f"✓ Feedback: Mail #{mail_index} sollte "{category}" sein")
    
    # Pattern 3: "{email} always {category}"
    # e.g., "newsletter@tech.de always newsletter"
    elif match := re.search(r'([\w\.-]+@[\w\.-]+)\s+(?:immer|always)\s+(.+)', feedback_text, re.I):
        email = match.group(1).lower()
        category = map_to_category(match.group(2).strip())
        
        rules['sender_rules'][email] = {
            'category': category,
            'confidence': 1.0,
            'learned_at': datetime.now().isoformat(),
            'source': feedback_text
        }
        
        new_rule = {
            'type': 'sender_pattern',
            'email': email,
            'category': category
        }
        
        feedback_entry['parsed_rules'].append(new_rule)
        print(f"✓ Gelernt: {email} → immer {category}")
    
    # Pattern 4: "{keyword} immer {action}"
    # e.g., "Rechnung always forward"
    elif match := re.search(r'"?(.+?)"?\s+(?:immer|always)\s+(.+)', feedback_text, re.I):
        keyword = match.group(1).strip().lower()
        action = match.group(2).strip().lower()
        
        new_rule = {
            'type': 'keyword_pattern',
            'keyword': keyword,
            'action': action,
            'learned_at': datetime.now().isoformat()
        }
        
        if 'subject' in action or 'betreff' in action:
            rules['subject_rules'].append(new_rule)
        else:
            rules['content_rules'].append(new_rule)
        
        feedback_entry['parsed_rules'].append(new_rule)
        print(f"✓ Gelernt: "{keyword}" → immer {action}")
    
    else:
        print(f"? Feedback nicht erkannt: {feedback_text}")
        print("  Nutze: 'Alles gut', '3 falsch, wichtig', 'absender@firma.de immer spam'")
        return False
    
    # Save feedback to history
    rules['feedback_history'].append(feedback_entry)
    
    # Trim history if too large (keep last 100)
    if len(rules['feedback_history']) > 100:
        rules['feedback_history'] = rules['feedback_history'][-100:]
    
    save_learned_rules(rules)
    save_sender_profiles(profiles)
    
    return True


def map_to_category(term):
    """Map user terms to standard categories."""
    term = term.lower().strip()
    
    mappings = {
        'wichtig': 'important',
        'important': 'important',
        'vip': 'important',
        'dringend': 'important',
        'newsletter': 'newsletter',
        'bulk': 'newsletter',
        'werbung': 'newsletter',
        'spam': 'newsletter',
        'rechnung': 'invoice',
        'invoice': 'invoice',
        'bill': 'invoice',
        'info': 'info',
        'fyi': 'info',
        'information': 'info',
        'archiv': 'archive',
        'archive': 'archive',
        'gelesen': 'mark_read',
        'read': 'mark_read'
    }
    
    return mappings.get(term, term)


def get_rules_for_sender(email):
    """Get learned rules for a specific sender."""
    rules = load_learned_rules()
    return rules.get('sender_rules', {}).get(email.lower())


def get_rules_for_subject(subject):
    """Check subject against learned patterns."""
    rules = load_learned_rules()
    subject_lower = subject.lower()
    
    for rule in rules.get('subject_rules', []):
        keyword = rule.get('keyword', '').lower()
        if keyword in subject_lower:
            return rule
    
    return None


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: process_feedback.py <feedback_text> [batch_timestamp]", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print('  process_feedback.py "Alles gut"', file=sys.stderr)
        print('  process_feedback.py "3 falsch, wichtig"', file=sys.stderr)
        print('  process_feedback.py "newsletter@spam.de immer spam"', file=sys.stderr)
        sys.exit(1)
    
    feedback = sys.argv[1]
    batch_ts = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = process_feedback(feedback, batch_ts)
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Main entry point for Office 365 Mail Manager.
Coordinates fetch, classify, execute, report workflow.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from auth_microsoft import test_connection
from fetch_mails import fetch_unread_mails, save_batch
from classify_mails import classify_batch
from execute_actions import process_batch
from process_feedback import load_learned_rules


def cmd_test_connection():
    """Test Microsoft Graph API connection."""
    print("Testing Microsoft Graph API connection...")
    try:
        test_connection()
        return 0
    except Exception as e:
        print(f"✗ Test failed: {e}", file=sys.stderr)
        return 1


def cmd_process_once(dry_run=False, limit=20):
    """Process one batch of emails."""
    print(f"{'[DRY RUN] ' if dry_run else ''}Processing up to {limit} emails...\n")
    
    # Step 1: Fetch
    print("Step 1: Fetching unread emails...")
    try:
        mails = fetch_unread_mails(limit)
        print(f"  ✓ Found {len(mails)} unread emails")
        
        if not mails:
            print("\nNo emails to process.")
            return 0
    except Exception as e:
        print(f"  ✗ Fetch failed: {e}", file=sys.stderr)
        return 1
    
    # Save batch for reference
    batch_file = save_batch({'mails': mails, 'timestamp': datetime.now().isoformat()})
    print(f"  ✓ Saved to: {batch_file}")
    
    # Step 2: Classify (prepares prompt for LLM)
    print("\nStep 2: Preparing classification...")
    try:
        classify_result = classify_batch(batch_file)
        prompt_file = classify_result.get('timestamp')
        print(f"  ✓ Prompt ready: memory/decision_history/{prompt_file}-prompt.txt")
        print(f"\n⚠️  MANUAL STEP REQUIRED:")
        print(f"   The LLM (you) must now review the prompt and provide decisions.")
        print(f"   See: memory/decision_history/{prompt_file}-prompt.txt")
        
        if dry_run:
            print(f"\n   (In production, this would be processed automatically)")
        
    except Exception as e:
        print(f"  ✗ Classification prep failed: {e}", file=sys.stderr)
        return 1
    
    return 0


def cmd_check_and_process():
    """Check and process (for cron)."""
    return cmd_process_once(dry_run=False)


def cmd_send_summary():
    """Send daily summary."""
    print("Generating daily summary...")
    
    # Load recent decisions
    history_dir = Path(__file__).parent.parent / "memory" / "decision_history"
    
    today = datetime.now().strftime('%Y-%m-%d')
    processed_count = 0
    categories = {'important': 0, 'newsletter': 0, 'invoice': 0, 'info': 0}
    
    # Count today's processed emails
    for result_file in history_dir.glob(f"{today.replace('-', '')}*-results.json"):
        try:
            with open(result_file) as f:
                data = json.load(f)
                processed_count += len(data.get('processed', []))
        except:
            pass
    
    summary = f"""
📧 **Tägliche E-Mail-Zusammenfassung**

Heute verarbeitet: **{processed_count} E-Mails**

Kategorien:
- Wichtig: {categories['important']}
- Newsletter: {categories['newsletter']}
- Rechnungen: {categories['invoice']}
- Info: {categories['info']}

Gelernte Regeln: {len(load_learned_rules().get('sender_rules', {}))}

_Weiter so! Feedback hilft mir, besser zu werden._
"""
    
    print(summary)
    print("\n(Summary would be sent to configured channel)")
    
    return 0


def cmd_review_pending():
    """Show mails awaiting manual review."""
    print("Pending reviews...")
    
    history_dir = Path(__file__).parent.parent / "memory" / "decision_history"
    
    # Find unprocessed prompts
    prompts = sorted(history_dir.glob("*-prompt.txt"))[-5:]  # Last 5
    
    if not prompts:
        print("  No pending reviews.")
        return 0
    
    print(f"\n  {len(prompts)} recent classifications awaiting decisions:")
    for prompt_file in prompts:
        print(f"  - {prompt_file.name}")
    
    return 0


def cmd_reset_learning():
    """Reset learned rules."""
    import shutil
    
    memory_dir = Path(__file__).parent.parent / "memory"
    
    print("⚠️  This will delete all learned rules!")
    confirm = input("Type 'RESET' to confirm: ")
    
    if confirm == "RESET":
        for file in ["learned_rules.json", "sender_profiles.json"]:
            path = memory_dir / file
            if path.exists():
                path.unlink()
                print(f"  ✓ Deleted {file}")
        
        # Keep history but rename
        history_dir = memory_dir / "decision_history"
        if history_dir.exists():
            backup_dir = memory_dir / f"decision_history_backup_{datetime.now().strftime('%Y%m%d')}"
            shutil.move(history_dir, backup_dir)
            print(f"  ✓ History backed up to {backup_dir.name}")
        
        print("\n✓ Learning data reset.")
    else:
        print("  Cancelled.")
    
    return 0


def main():
    parser = argparse.ArgumentParser(description='Office 365 Mail Manager')
    parser.add_argument('action', choices=[
        'test-connection',
        'process-once',
        'check-and-process',
        'send-summary',
        'review-pending',
        'reset-learning'
    ])
    parser.add_argument('--dry-run', action='store_true', help='Show actions without executing')
    parser.add_argument('--limit', type=int, default=20, help='Max emails to process')
    
    args = parser.parse_args()
    
    if args.action == 'test-connection':
        return cmd_test_connection()
    elif args.action == 'process-once':
        return cmd_process_once(dry_run=args.dry_run, limit=args.limit)
    elif args.action == 'check-and-process':
        return cmd_check_and_process()
    elif args.action == 'send-summary':
        return cmd_send_summary()
    elif args.action == 'review-pending':
        return cmd_review_pending()
    elif args.action == 'reset-learning':
        return cmd_reset_learning()
    
    return 1


if __name__ == '__main__':
    sys.exit(main())

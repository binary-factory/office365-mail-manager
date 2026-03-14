#!/usr/bin/env python3
"""
Tool wrapper for OpenClaw integration.
Handles JSON input/output for tool-based execution.
"""

import json
import sys
import os

# Add script directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth_microsoft import test_connection, get_auth_headers, load_config
from fetch_mails import fetch_unread_mails, save_batch
from classify_mails import prepare_llm_prompt, process_llm_response, load_learned_rules
from execute_actions import execute_action, process_batch
from process_feedback import process_feedback as process_feedback_internal


def handle_test_connection(params):
    """Handle o365_test_connection tool."""
    try:
        # Run test and capture output
        import io
        from contextlib import redirect_stdout, redirect_stderr
        
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            result = test_connection()
        
        output = stdout_capture.getvalue()
        errors = stderr_capture.getvalue()
        
        return {
            "success": result == 0,
            "output": output,
            "errors": errors if errors else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def handle_fetch_unread_mails(params):
    """Handle o365_fetch_unread_mails tool."""
    try:
        limit = params.get('limit', 20)
        save = params.get('save_batch', True)
        
        mails = fetch_unread_mails(limit)
        
        result = {
            "count": len(mails),
            "mails": mails,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
        
        if save and mails:
            batch_file = save_batch(mails)
            result["batch_file"] = str(batch_file)
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def handle_classify_mails(params):
    """Handle o365_classify_mails tool."""
    try:
        mails = params.get('mails', [])
        apply_rules = params.get('apply_learned_rules', True)
        
        if not mails:
            return {
                "success": False,
                "error": "No mails provided for classification"
            }
        
        learned_rules = load_learned_rules() if apply_rules else {}
        prompt = prepare_llm_prompt(mails, learned_rules)
        
        # Save prompt for reference
        from datetime import datetime
        from pathlib import Path
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        prompt_file = Path(__file__).parent.parent / "memory" / "decision_history" / f"{timestamp}-prompt.txt"
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        
        return {
            "prompt": prompt,
            "mails_count": len(mails),
            "timestamp": timestamp,
            "prompt_file": str(prompt_file),
            "note": "LLM should process this prompt and return decisions JSON"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def handle_execute_actions(params):
    """Handle o365_execute_actions tool."""
    try:
        decisions = params.get('decisions', [])
        dry_run = params.get('dry_run', False)
        
        if not decisions:
            return {
                "success": False,
                "error": "No decisions provided"
            }
        
        # Create a temporary decisions file
        from datetime import datetime
        from pathlib import Path
        import tempfile
        
        timestamp = datetime.now().strftime('%Y-%m-%d-%H%M')
        batch_data = {
            'timestamp': timestamp,
            'decisions': decisions,
            'status': 'pending'
        }
        
        # Process the batch
        results = {
            'timestamp': timestamp,
            'processed': [],
            'failed': [],
            'dry_run': dry_run
        }
        
        for decision in decisions:
            mail_id = decision.get('mail_id')
            action = decision.get('action')
            action_params = decision.get('action_params', {})
            
            if dry_run:
                results['processed'].append({
                    'mail_id': mail_id,
                    'action': action,
                    'params': action_params,
                    'status': 'dry_run',
                    'reasoning': decision.get('reasoning', '')
                })
            else:
                result = execute_action(mail_id, action, action_params)
                if result['success']:
                    results['processed'].append(result)
                else:
                    results['failed'].append(result)
        
        # Save results
        results_file = Path(__file__).parent.parent / "memory" / "decision_history" / f"{timestamp}-results.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        return {
            "success": True,
            "processed_count": len(results['processed']),
            "failed_count": len(results['failed']),
            "dry_run": dry_run,
            "results_file": str(results_file),
            "processed": results['processed'],
            "failed": results['failed']
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def handle_process_feedback(params):
    """Handle o365_process_feedback tool."""
    try:
        feedback = params.get('feedback', '')
        batch_timestamp = params.get('batch_timestamp')
        
        if not feedback:
            return {
                "success": False,
                "error": "No feedback provided"
            }
        
        success = process_feedback_internal(feedback, batch_timestamp)
        
        return {
            "success": success,
            "feedback": feedback,
            "batch_timestamp": batch_timestamp,
            "message": "Feedback processed and rules updated" if success else "Failed to parse feedback"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def handle_send_daily_summary(params):
    """Handle o365_send_daily_summary tool."""
    try:
        from datetime import datetime, timedelta
        
        date_str = params.get('date')
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            target_date = datetime.now().date()
        
        # Load config
        config = load_config()
        summary_config = config.get('summary', {})
        
        if not summary_config.get('enabled', True):
            return {
                "success": False,
                "error": "Daily summary is disabled in config"
            }
        
        # Find decision history for the date
        from pathlib import Path
        history_dir = Path(__file__).parent.parent / "memory" / "decision_history"
        
        date_prefix = target_date.strftime('%Y-%m-%d')
        results_files = list(history_dir.glob(f"{date_prefix}*-results.json"))
        
        if not results_files:
            return {
                "success": True,
                "message": f"No email activity found for {target_date}",
                "summary": {
                    "date": str(target_date),
                    "total_processed": 0,
                    "categories": {}
                }
            }
        
        # Aggregate statistics
        total_processed = 0
        categories = {}
        
        for results_file in results_files:
            with open(results_file) as f:
                data = json.load(f)
                total_processed += len(data.get('processed', []))
                
                for item in data.get('processed', []):
                    # Try to infer category from action or folder
                    action = item.get('action', 'unknown')
                    if action not in categories:
                        categories[action] = 0
                    categories[action] += 1
        
        summary = {
            "date": str(target_date),
            "total_processed": total_processed,
            "categories": categories,
            "files_processed": len(results_files)
        }
        
        # TODO: Send to configured channel (whatsapp/telegram/etc)
        # For now, just return the summary
        return {
            "success": True,
            "summary": summary,
            "channel": summary_config.get('channel', 'not_configured'),
            "message": f"Daily summary for {target_date}: {total_processed} emails processed"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Main entry point for tool execution."""
    # Read JSON input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "success": False,
            "error": f"Invalid JSON input: {str(e)}"
        }))
        sys.exit(1)
    
    tool_name = input_data.get('tool')
    params = input_data.get('params', {})
    
    # Route to appropriate handler
    handlers = {
        'o365_test_connection': handle_test_connection,
        'o365_fetch_unread_mails': handle_fetch_unread_mails,
        'o365_classify_mails': handle_classify_mails,
        'o365_execute_actions': handle_execute_actions,
        'o365_process_feedback': handle_process_feedback,
        'o365_send_daily_summary': handle_send_daily_summary,
    }
    
    handler = handlers.get(tool_name)
    if not handler:
        print(json.dumps({
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }))
        sys.exit(1)
    
    result = handler(params)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Git push automation script
Performs git add, commit, and push operations
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Execute a shell command and return the result"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def main():
    """Main function to perform git operations"""
    repo_path = Path(__file__).parent
    
    print("=" * 70)
    print("GIT PUSH AUTOMATION SCRIPT")
    print("=" * 70)
    
    # Configure git user
    print("\n1. Configuring git user...")
    code, stdout, stderr = run_command('git config user.name "GitHub Copilot"', cwd=repo_path)
    if code == 0:
        run_command('git config user.email "copilot@github.com"', cwd=repo_path)
        print("   ✓ Git user configured")
    else:
        print(f"   ✗ Error configuring git: {stderr}")
    
    # Add all changes
    print("\n2. Staging all changes...")
    code, stdout, stderr = run_command('git add -A', cwd=repo_path)
    if code == 0:
        print("   ✓ All changes staged")
    else:
        print(f"   ✗ Error staging changes: {stderr}")
        return 1
    
    # Check status
    print("\n3. Checking git status...")
    code, stdout, stderr = run_command('git status --short', cwd=repo_path)
    if code == 0:
        if stdout.strip():
            print("   Staged files:")
            for line in stdout.strip().split('\n'):
                print(f"     {line}")
        else:
            print("   ✓ No changes to commit")
            return 0
    
    # Commit changes
    print("\n4. Committing changes...")
    commit_msg = """Implement price alert system with external monitoring

- Add price_monitor.py: External script for checking price alerts every 5-10 minutes
- Add pages/Price_Alerts.py: User interface for managing alerts
- Add 4 comprehensive documentation files (SETUP, QUICK_REFERENCE, CRONTAB_EXAMPLES, IMPLEMENTATION_SUMMARY)
- Update auth_utils.py: Add 6 new functions for alert management
- Update README.md: Add price alerts feature and setup instructions
- Fix CSS font typo in Stock_Tracker.py (Josefin+Sans)
- Replace exposed credentials in secrets.toml with placeholders
- Implement JSON-based alert storage with SMTP email notifications
- Support multiple deployment options: cron, cloud scheduler, Docker, etc.

Features:
- Email notifications when stocks reach target prices
- Create alerts for 'above' or 'below' price thresholds
- View active and triggered alerts
- Delete alerts from UI
- External monitoring independent of web app
- Cloud-ready architecture
- Comprehensive setup guides for all platforms"""
    
    code, stdout, stderr = run_command(f'git commit -m "{commit_msg}"', cwd=repo_path)
    if code == 0:
        print("   ✓ Changes committed")
        print(f"   {stdout.strip().split(chr(10))[0] if stdout else 'Commit successful'}")
    else:
        print(f"   ✗ Error committing: {stderr}")
        return 1
    
    # Push to main
    print("\n5. Pushing to main branch...")
    code, stdout, stderr = run_command('git push -u origin main', cwd=repo_path)
    if code == 0:
        print("   ✓ Changes pushed to GitHub")
        print(f"   {stdout.strip() if stdout else 'Push successful'}")
    else:
        print(f"   ⚠ Push failed: {stderr}")
        print("   Tip: You may need to authenticate or check your branch settings")
        return 1
    
    print("\n" + "=" * 70)
    print("✅ ALL OPERATIONS COMPLETED SUCCESSFULLY")
    print("=" * 70)
    return 0

if __name__ == "__main__":
    sys.exit(main())

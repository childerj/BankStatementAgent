#!/usr/bin/env python3
"""
Check Azure Function logs for the most recent execution
"""

import subprocess
import sys
from datetime import datetime, timedelta

def check_azure_logs():
    """Check Azure Function logs"""
    print("🔍 Checking Azure Function logs for recent execution...")
    
    try:
        # Try to get logs using Azure CLI
        cmd = [
            "az", "functionapp", "logs", "tail",
            "--name", "BankStatementAgent",
            "--resource-group", "Geek-Fortress-RG"
        ]
        
        print(f"📝 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Function logs retrieved successfully!")
            print("=" * 80)
            print(result.stdout)
            print("=" * 80)
        else:
            print(f"❌ Error getting logs: {result.stderr}")
            
            # Try alternative command
            print("\n🔄 Trying alternative log command...")
            cmd2 = [
                "az", "monitor", "activity-log", "list",
                "--resource-group", "Geek-Fortress-RG",
                "--max-events", "10"
            ]
            
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=30)
            if result2.returncode == 0:
                print("✅ Activity logs retrieved!")
                print(result2.stdout)
            else:
                print(f"❌ Activity log error: {result2.stderr}")
    
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_azure_logs()

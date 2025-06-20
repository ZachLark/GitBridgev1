#!/usr/bin/env python3
"""
GitBridge Master Execution Script

This script provides a user-friendly command-line interface to manage the
GitBridge application lifecycle, including starting, stopping, and monitoring
the web server as a background process.

MAS Lite Protocol v2.1 Compliance: This script ensures the application
environment is correctly set up for protocol-compliant operations.
"""

import os
import sys
import time
import webbrowser
import subprocess
import socket
import argparse
from pathlib import Path

# --- Configuration ---
PID_FILE = Path(".gitbridge.pid")
LOG_FILE = Path("logs/server.log")
HOST = "127.0.0.1"
# ---------------------

def find_available_port(start_port=5000, max_attempts=20):
    """Find an available TCP port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((HOST, port))
                return port
        except OSError:
            continue
    return None

def is_server_running():
    """Check if the server is running by checking the PID file."""
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text())
        # Check if a process with this PID is running
        # This is OS-dependent. A simple check is to send signal 0.
        os.kill(pid, 0)
    except (IOError, ValueError, OSError):
        return False
    else:
        return True

def get_server_pid():
    """Get the server PID from the PID file."""
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text())
    except (IOError, ValueError):
        return None

def start_server():
    """Start the GitBridge web server as a background process."""
    if is_server_running():
        print("✅ Server is already running.")
        return

    print("🚀 Starting GitBridge server...")

    # 1. Find an available port
    port = find_available_port()
    if port is None:
        print("❌ Error: No available ports found between 5000-5020.")
        sys.exit(1)
    print(f"✅ Found available port: {port}")

    # 2. Ensure log directory exists
    LOG_FILE.parent.mkdir(exist_ok=True)

    # 3. Start the server process
    try:
        with open(LOG_FILE, "w") as log:
            process = subprocess.Popen(
                [sys.executable, "app.py", "--port", str(port)],
                stdout=log,
                stderr=subprocess.PIPE,
                # Use platform-specific flags for detaching
                creationflags=subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0,
                preexec_fn=os.setsid if sys.platform != "win32" else None
            )
        
        # 4. Store the PID
        PID_FILE.write_text(str(process.pid))
        print(f"✅ Server process started with PID: {process.pid}")
        print(f"🪵 Logs are being written to: {LOG_FILE}")

    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

    # 5. Health Check
    print("🩺 Waiting for server to become healthy...")
    time.sleep(2) # Give it a moment to boot
    for i in range(10): # 10 attempts, 1 second apart
        try:
            with socket.create_connection((HOST, port), timeout=1):
                print("💚 Server is healthy!")
                break
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(1)
    else:
        print("❌ Server failed to start in time. Check logs for errors:")
        print(f"   python run.py logs")
        stop_server()
        sys.exit(1)

    # 6. Open Browser
    url = f"http://{HOST}:{port}/startup"
    print(f"🌐 Opening demo startup page: {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        print(f"   Please manually open: {url}")
    
    print("\n🎉 GitBridge is running! Use 'python run.py status' or 'python run.py stop'.")


def stop_server():
    """Stop the GitBridge web server."""
    pid = get_server_pid()
    if not pid or not is_server_running():
        print("✅ Server is not running.")
        if PID_FILE.exists():
            PID_FILE.unlink()
        return

    print(f"🛑 Stopping server process (PID: {pid})...")
    try:
        # Use platform-specific commands for graceful shutdown
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True, capture_output=True)
        else:
            os.killpg(os.getpgid(pid), 15) # SIGTERM
        
        # Wait a bit for the process to terminate
        time.sleep(2)

        if is_server_running():
             print("   Process did not terminate gracefully, forcing...")
             os.kill(pid, 9) # SIGKILL
        
        print("✅ Server stopped successfully.")
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"⚠️  Could not stop process {pid} cleanly: {e}")
        print("   It may already be stopped or require manual intervention.")
    finally:
        if PID_FILE.exists():
            PID_FILE.unlink()

def show_status():
    """Display the current status of the server."""
    pid = get_server_pid()
    if is_server_running():
        print(f"✅ Server is RUNNING (PID: {pid})")
        # Optional: Add a check to see if we can connect to the port
    else:
        print("❌ Server is STOPPED")

def show_logs(tail_lines=20):
    """Show the last N lines of the server log."""
    if not LOG_FILE.exists():
        print("🤷 No log file found. Has the server been started yet?")
        return
    
    print(f"📜 Displaying last {tail_lines} lines of {LOG_FILE}:")
    print("-" * 50)
    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
            for line in lines[-tail_lines:]:
                print(line, end="")
    except IOError as e:
        print(f"❌ Error reading log file: {e}")
    print("-" * 50)


def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(
        description="GitBridge Master Execution Script",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')
    
    # Start command
    subparsers.add_parser('start', help='Start the GitBridge server as a background process.')
    
    # Stop command
    subparsers.add_parser('stop', help='Stop the GitBridge server.')
    
    # Status command
    subparsers.add_parser('status', help='Check the status of the GitBridge server.')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show the latest server logs.')
    logs_parser.add_argument('-n', '--lines', type=int, default=20, help='Number of log lines to show.')

    args = parser.parse_args()

    if args.command == 'start':
        start_server()
    elif args.command == 'stop':
        stop_server()
    elif args.command == 'status':
        show_status()
    elif args.command == 'logs':
        show_logs(args.lines)

if __name__ == "__main__":
    main() 
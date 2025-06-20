# GitBridge Phase 24 Demo - Quick Start Guide

This guide provides simple, user-friendly instructions to launch the GitBridge Phase 24 demo.

---

## 🚀 Quick Start Instructions

The entire application is now managed by a single, simple command.

1.  **Open your Terminal** (or Command Prompt on Windows).
2.  **Navigate to the project directory**: `cd /path/to/GitBridgev1`
3.  **Run the `start` command**:
    ```bash
    python run.py start
    ```
4.  **Wait a moment**: The script will automatically find an available port, start the server in the background, and open the demo page in your default web browser.
5.  **Click "Start Live Demo"** on the web page that opens.

---

## ⚙️ How to Manage the Application

You now have full control over the application without needing technical expertise.

### Check the Status
Is the server running? Use the `status` command.
```bash
python run.py status
```

### Stop the Application
When you are finished, use the `stop` command.
```bash
python run.py stop
```

### View Logs
If something seems wrong, you can easily view the server logs.
```bash
python run.py logs
```
This will show the last 20 lines. To see more, use the `-n` flag (e.g., `python run.py logs -n 100`).

---

## 🎯 What You'll See

-   A **user-friendly startup page** that checks the system status.
-   **Real-time collaboration** between AI and human agents.
-   **Live attribution tracking** for every single code change.
-   A **dynamic activity feed** showing all actions as they happen.
-   **Visual diffs** that clearly show what code was changed.

---

## 🛠️ Troubleshooting

-   **"Command not found"**: Ensure you are in the correct `GitBridgev1` directory.
-   **"Python not found"**: Make sure Python (version 3.8+) is installed and available in your system's PATH.
-   **Browser doesn't open**: The script will print the URL (e.g., `http://127.0.0.1:5001/startup`). You can copy and paste this into your browser manually.
-   **Server fails to start**: Use the `python run.py logs` command to see any error messages from the server.

---

**🎉 Enjoy the new, simplified GitBridge Phase 24 Demo!** 
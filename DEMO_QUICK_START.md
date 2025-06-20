# GitBridge Phase 24 Demo - The Easiest Quick Start Guide

Welcome! This guide provides the simplest possible way to launch the GitBridge demo.

---

## 🚀 One-Click Launch Instructions

No terminal, no commands. Just a simple double-click.

1.  **Find the correct file for your operating system:**
    *   **On Windows:** `GitBridge Test Launch.bat`
    *   **On macOS or Linux:** `GitBridge Test Launch.sh`

2.  **Double-click the file.**

That's it! A new window will appear, the server will start in the background, and your default web browser will automatically open to the demo startup page.

---

## ▶️ What Happens When You Launch

1.  A terminal or command prompt window will open to show the startup progress.
2.  The script automatically finds an available port and starts the server.
3.  Your web browser opens to the GitBridge startup page.
4.  Once the browser is open, you can safely close the terminal/command window. The server will keep running in the background.

---

## ⏹️ How to Stop the Application

Since the server runs in the background, you need a way to stop it when you're done.

1.  **Open your Terminal** (or Command Prompt).
2.  **Navigate to the project directory** (if you aren't there already).
3.  **Run the `stop` command:**
    ```bash
    python run.py stop
    ```
    This will gracefully shut down the background server.

---

## 🛠️ Troubleshooting

-   **"Permission Denied" on macOS/Linux:** If the `.sh` file doesn't run, you may need to give it permission. Open a terminal in the project folder and run: `chmod +x "GitBridge Test Launch.sh"`. Then try double-clicking it again.
-   **"Python not found"**: This means Python is not installed or not in your system's PATH. Please install Python 3.8 or higher.
-   **Browser doesn't open**: The terminal window will show the exact URL (like `http://127.0.0.1:5001/startup`). You can copy and paste this into your browser.
-   **Server fails to start**: The terminal window may show an error. You can also get more details by running `python run.py logs`.

---

**🎉 Enjoy the one-click GitBridge Phase 24 Demo!** 
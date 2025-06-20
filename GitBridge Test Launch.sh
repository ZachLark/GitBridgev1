#!/bin/bash
# GitBridge Test Launch - macOS & Linux
# This script launches the GitBridge application without requiring the user
# to open a terminal or manually navigate directories.

clear
echo "
   **********************************************
   *                                            *
   *      🚀 Launching GitBridge Test Server      *
   *                                            *
   **********************************************
"
echo "Please wait, this may take a few moments..."
echo "A browser window will open automatically when the server is ready."
echo

# Get the absolute path of the directory where the script is located.
# This ensures the script can be run from anywhere by double-clicking.
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Change to the script's directory before running the application.
cd "$DIR"

# Execute the main 'run.py' script to start the server.
# The 'start' command handles everything in the background.
python3 run.py start

echo "
=================================================================
The startup command has been sent.

- If a browser window did not open, check the output above.
- This terminal window can now be closed. The server runs in the background.
- To stop the server, open a new terminal in this folder and run: 
  'python3 run.py stop'
=================================================================
"

# Keep the terminal open for a moment to allow the user to read messages.
sleep 15 
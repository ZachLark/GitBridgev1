@echo off
:: GitBridge Test Launch - Windows
:: This script launches the GitBridge application without requiring the user
:: to open a terminal or manually navigate directories.

echo.
echo    **********************************************
echo    *                                            *
echo    *      🚀 Launching GitBridge Test Server      *
echo    *                                            *
echo    **********************************************
echo.
echo Please wait, this may take a few moments...
echo A browser window will open automatically when the server is ready.
echo.

:: Change the current directory to the script's own directory.
:: This is crucial for ensuring all project files are found correctly.
cd /d "%~dp0"

:: Execute the main 'run.py' script to start the server.
:: The 'start' command handles everything in the background.
python run.py start

echo.
echo =================================================================
echo The startup command has been sent.
echo.
echo - If a browser window did not open, check the output above.
echo - This window can be closed. The server runs in the background.
echo - To stop the server, run 'python run.py stop' from this directory.
echo =================================================================
echo.

:: Pause to keep the window open so the user can read any messages.
pause 
@echo off
setlocal

rem Edit this path if you move the project folder
set "PROJECT_DIR=C:\Users\daniel\Documents\GitHub\youtube_downloading"
set "PYDIR=%PROJECT_DIR%\.venv\Scripts"
if not exist "%PYDIR%\python.exe" (
    echo Virtual environment not found.
    echo From this folder, run:  uv sync
    pause
    exit /b 1
)

if exist "%PYDIR%\pythonw.exe" (
    start "" "%PYDIR%\pythonw.exe" "%PROJECT_DIR%\yt-playlist-download.py"
) else (
    "%PYDIR%\python.exe" "%PROJECT_DIR%\yt-playlist-download.py"
)

endlocal

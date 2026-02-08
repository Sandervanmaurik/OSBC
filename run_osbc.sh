#!/usr/bin/env bash
# OSBC Launcher Script for macOS
# This script ensures a clean Python environment without debuggers

# Change to script directory
cd "$(dirname "$0")"

# Unset VS Code debugger environment variables that can cause SIGTRAP
unset PYTHONSTARTUP
unset VSCODE_DEBUGPY_ADAPTER_ENDPOINTS
unset BUNDLED_DEBUGPY_PATH
unset PYTHON_BASIC_REPL
unset PYTHON_BREAKPOINT

# Disable Python breakpoints completely
export PYTHONBREAKPOINT=0

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Please run: python3 -m pip install -e ."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Launch OSBC with correct case-sensitive path
echo "Starting OSBC..."
python3 src/OSBC.py "$@"

import subprocess
import webbrowser
import os
import time
import atexit
import sys

def main():
    """
    Starts the FastAPI server and opens the frontend in a web browser.
    """
    # Check if main.py exists
    if not os.path.exists("main.py"):
        sys.exit(1)

    # Command to run the FastAPI server using uv
    command = ["uv", "run", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]

    # Start the server as a background process
    try:
        # Use Popen to run the server in a new process
        server_process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        sys.exit(1)


    # Register a function to kill the server process when this script exits
    def cleanup():
        server_process.terminate()
        server_process.wait()
    
    atexit.register(cleanup)

    # Give the server a moment to start up
    time.sleep(3)

    # Open the frontend HTML file in the default web browser
    frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'frontend', 'index.html'))
    if not os.path.exists(frontend_path):
        pass
    else:
        webbrowser.open(f'file://{frontend_path}')


    try:
        # Wait for the server process to complete (e.g., if it's manually stopped or crashes)
        server_process.wait()
    except KeyboardInterrupt:
        # On Ctrl+C, the atexit handler will be called to clean up.
        pass

if __name__ == "__main__":
    main() 
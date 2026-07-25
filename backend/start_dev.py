"""Start the backend development server."""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app",
     "--host", "0.0.0.0", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

print(f"Backend started (PID: {proc.pid})")
sys.stdout.flush()

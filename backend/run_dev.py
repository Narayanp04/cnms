"""Development server launcher - runs uvicorn in the background."""
import subprocess
import sys
import os
import time
import urllib.request


def is_port_in_use(port):
    """Check if a port is in use."""
    try:
        req = urllib.request.Request(f"http://localhost:{port}/api/health")
        urllib.request.urlopen(req, timeout=2)
        return True
    except Exception:
        return False


def main():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)

    # Check if port is already in use
    if is_port_in_use(8000):
        print("Port 8000 is in use. Kill existing process first.")
        sys.exit(1)

    # Start uvicorn
    log_path = os.path.join(backend_dir, "backend_uvicorn.log")
    log_file = open(log_path, "w")

    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", "8000"],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        creationflags=creation_flags,
    )

    print(f"Backend server started (PID: {process.pid})")
    print(f"Logs: {log_path}")

    # Wait for it to be ready
    for i in range(10):
        time.sleep(1)
        if process.poll() is not None:
            print(f"Server crashed (exit code {process.returncode})")
            log_file.close()
            sys.exit(1)
        try:
            req = urllib.request.Request("http://localhost:8000/api/health")
            response = urllib.request.urlopen(req, timeout=2)
            if response.status == 200:
                print(f"Backend is ready at http://localhost:8000")
                log_file.close()
                sys.exit(0)
        except Exception:
            if i == 9:
                print("Backend failed to start. Check logs.")
                log_file.close()
                sys.exit(1)
            print(f"  Waiting... ({i+1}/10)")


if __name__ == "__main__":
    main()

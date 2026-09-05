"""
Launch both backend and frontend dev servers with a single command.

Usage:
    python dev.py

Starts:
    - Backend:  uvicorn api:app --reload  (port 8000)
    - Frontend: npm run dev               (port 5173)

Press Ctrl+C once to shut down both.
"""

import subprocess
import sys
import signal
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")


def main():
    procs = []

    try:
        # --- Backend ---
        print("\033[94m[dev]\033[0m Starting backend  →  http://localhost:8000")
        backend = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            cwd=ROOT_DIR,
        )
        procs.append(("backend", backend))

        # --- Frontend ---
        print("\033[92m[dev]\033[0m Starting frontend →  http://localhost:5173")
        frontend = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            shell=True,  # needed on Windows for npm
        )
        procs.append(("frontend", frontend))

        print()
        print("\033[93m[dev]\033[0m Both servers running. Press Ctrl+C to stop.")
        print()

        # Wait for either process to exit
        while True:
            for name, proc in procs:
                ret = proc.poll()
                if ret is not None:
                    print(f"\033[91m[dev]\033[0m {name} exited with code {ret}")
                    raise SystemExit(ret)
            # Short sleep to avoid busy-waiting
            import time
            time.sleep(0.5)

    except (KeyboardInterrupt, SystemExit):
        print()
        print("\033[93m[dev]\033[0m Shutting down...")
        for name, proc in procs:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                    print(f"\033[94m[dev]\033[0m {name} stopped")
                except subprocess.TimeoutExpired:
                    proc.kill()
                    print(f"\033[91m[dev]\033[0m {name} killed (didn't stop in time)")
        print("\033[92m[dev]\033[0m Done.")


if __name__ == "__main__":
    main()

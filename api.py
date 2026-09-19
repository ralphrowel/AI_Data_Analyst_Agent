"""Root entrypoint: starts both the FastAPI backend and the Vite frontend dev server."""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    import uvicorn

    root = Path(__file__).resolve().parent
    frontend_dir = root / "frontend"

    # Start Vite frontend dev server in the background
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    vite = subprocess.Popen(
        [npm, "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"[api.py] Frontend started (pid {vite.pid}) -> http://localhost:5173")

    try:
        uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
    finally:
        vite.terminate()
        print("[api.py] Frontend process stopped.")
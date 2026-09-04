"""Root entrypoint proxy for backward compatibility.
Points to the modular FastAPI application in backend/app/main.py.
"""
from backend.app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
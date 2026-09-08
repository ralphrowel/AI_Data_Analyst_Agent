from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import ALLOWED_ORIGINS
from backend.app.api.routes import router

app = FastAPI(
    title="Visiq — Autonomous AI Data Analyst API",
    description="Modular backend for structured data analysis and RAG retrieval",
    version="1.0.0",
)

# Allow React to communicate with the FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

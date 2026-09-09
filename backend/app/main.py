from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import ALLOWED_ORIGINS
from backend.app.api.routes import router
from contextlib import asynccontextmanager
from backend.app import storage
from backend.app.http_security import RequestBoundary, JsonFormatter
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
import logging

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app):
    # Ensure database schema is initialized
    storage.initialize()
    with storage.engine().connect() as connection:
        connection.execute(storage.records.select().limit(0))
    yield

app = FastAPI(
    lifespan=lifespan,
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
app.add_middleware(RequestBoundary)

@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse({'detail': 'Invalid request'}, status_code=422)

@app.exception_handler(Exception)
async def server_error(request, exc):
    logging.getLogger(__name__).error('Request failed: %s', type(exc).__name__)
    return JSONResponse({'detail': 'Internal server error'}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

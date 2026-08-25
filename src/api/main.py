import time
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.db.database import init_db
from src.knowledge.retriever import TranscriptRetriever
from src.api.routes import router

# Configure structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("lenny_api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & Shutdown Lifespan: auto-inits DB and vector index."""
    logger.info("Initializing database schema...")
    await init_db()
    logger.info("Checking transcript vector index...")
    retriever = TranscriptRetriever()
    if retriever.count() == 0:
        logger.info("Vector index empty. Ingesting transcripts from data/transcripts...")
        indexed = retriever.index_directory("data/transcripts")
        logger.info(f"Successfully indexed {indexed} chunks into SQLite vector store.")
    else:
        logger.info(f"Vector index ready with {retriever.count()} chunks.")
    yield
    logger.info("Shutting down Lenny Growth Assistant API...")

app = FastAPI(
    title="The Lenny Growth Assistant API",
    description="Conversational AI & Growth Assistant grounded in 200+ hours of Lenny's Podcast transcripts.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    """Logs latency, method, path, and response status for observability."""
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
    return response

# Register API routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)

"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .database import db_manager
from .auth import router as auth_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle"""
    logger.info("🚀 Starting GPAlytics...")
    db_manager.initialize()
    await db_manager.create_tables()
    logger.info("✅ Ready")
    
    yield
    
    logger.info("🛑 Shutting down...")
    await db_manager.close()

app = FastAPI(
    title="GPAlytics Backend",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "GPAlytics API", "docs": "/docs"}

@app.get("/health")
async def health():
    try:
        healthy = await db_manager.health_check()
        return {"status": "healthy" if healthy else "degraded"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

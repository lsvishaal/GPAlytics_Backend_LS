"""
Health utilities for liveness and readiness checks.

Design:
- Liveness: quick, no external I/O. Always cheap and reliable for container/orchestrator.
- Readiness: aggregate dependency checks (DB, Redis, AI config) with graceful degradation.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Dict, Any
from fastapi import APIRouter

from .config import settings
from .database import db_manager

logger = logging.getLogger(__name__)

# Create health router
router = APIRouter(prefix="/health", tags=["Health"])


def liveness() -> Dict[str, Any]:
    """Return a fast, allocation-free liveness signal.
    Do not perform network or DB I/O here.
    """
    return {
        "status": "healthy",
        "service": "GPAlytics Backend",
        "environment": settings.environment,
        "version": "2.0.0",
    }


async def check_db(max_retries: int = 1, base_delay: float = 0.0) -> Dict[str, Any]:
    """Check database readiness. Resilient to serverless cold starts.

    This performs minimal work: initializes the manager if needed and calls health_check().
    Optionally retries with a small backoff when serverless indicates a cold start.
    """
    # If DB not configured, report skipped instead of unhealthy
    if not settings.has_database_url:
        return {"name": "database", "status": "skipped", "details": {"configured": False}}

    attempt = 0
    last_error: str | None = None
    while attempt < max_retries:
        try:
            if not getattr(db_manager, "_initialized", False):
                db_manager.initialize()
            # Perform a focused, detailed health probe with explicit exception capture
            engine = getattr(db_manager, "async_engine", None)
            if engine is None:
                last_error = "engine not initialized"
            else:
                from sqlalchemy import text  # local import to avoid overhead in hot path
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                return {"name": "database", "status": "healthy", "details": {"type": "serverless"}}
        except Exception as e:  # noqa: BLE001 - surface DB errors as readiness detail
            last_error = str(e)
            # Known serverless warmup keywords
            em = last_error.lower()
            if any(k in em for k in ("timeout", "not currently available", "login timeout")) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
            else:
                break
        attempt += 1

    return {
        "name": "database",
        "status": "unhealthy",
        "details": {"error": last_error or "unknown"},
    }


async def check_redis() -> Dict[str, Any]:
    """Best-effort Redis readiness.
    We avoid importing a client; we only report configured vs missing.
    """
    url = os.getenv("REDIS_URL")
    if not url:
        return {"name": "redis", "status": "skipped", "details": {"configured": False}}
    # If configured, we still avoid network I/O for readiness speed and stability.
    return {"name": "redis", "status": "assumed_healthy", "details": {"configured": True}}


async def check_ai() -> Dict[str, Any]:
    """Check Gemini AI configuration presence and library availability (no network call)."""
    key_present = bool(settings.gemini_key_str)
    try:
        import google.generativeai as _  # noqa: F401
        lib_ok = True
    except Exception:  # noqa: BLE001 - treat any import error uniformly
        lib_ok = False
    status = "healthy" if key_present and lib_ok else "degraded"
    return {
        "name": "gemini_ai",
        "status": status,
        "details": {"key_present": key_present, "library_available": lib_ok},
    }


async def readiness(max_db_retries: int = 1, base_delay: float = 0.0) -> Dict[str, Any]:
    """Aggregate readiness over dependencies.

    Returns overall status and per-dependency details. Does not raise.
    """
    db_task = check_db(max_retries=max_db_retries, base_delay=base_delay)
    redis_task = check_redis()
    ai_task = check_ai()

    results = await asyncio.gather(db_task, redis_task, ai_task, return_exceptions=False)

    # overall status: unhealthy if any critical dependency is unhealthy
    overall = "healthy"
    for r in results:
        if r["name"] == "database" and r["status"] not in ("healthy", "skipped"):
            overall = "unhealthy"
            break

    return {
        "status": overall,
        "service": "GPAlytics Backend",
        "environment": settings.environment,
        "version": "2.0.0",
        "checks": results,
    }


# Health endpoints
@router.get("/live")
async def get_liveness():
    """Liveness probe endpoint"""
    return liveness()


@router.get("/ready")
async def get_readiness():
    """Readiness probe endpoint"""
    return await readiness()


@router.get("/")
async def get_health():
    """General health endpoint"""
    return await readiness()
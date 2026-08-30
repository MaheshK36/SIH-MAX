"""
server.py - Unified Cyber Defense Command Center FastAPI Server

Unites Blockchain Audit Logging, Digital Twin Simulation Engine, CyberSeer GNN Forecasting,
and Live Flow Ingestion into a single REST API platform.
"""

from __future__ import annotations
from datetime import datetime, timezone
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.audit import router as audit_router
from backend.api.twin import router as twin_router
from backend.api.forecast import router as forecast_router
from backend.api.live_ingest import router as live_ingest_router

app = FastAPI(
    title="AI Cyber Defense Command Center API",
    version="2.0.0",
    description="Unified API combining Digital Twin, CyberSeer Forecasting, Attack World Model, and Blockchain Audit Logging."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(audit_router)
app.include_router(twin_router)
app.include_router(forecast_router)
app.include_router(live_ingest_router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "service": "unified-cybersecurity-platform",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modules": {
            "blockchain_audit": "active",
            "digital_twin": "active",
            "cyberseer_forecast": "active",
            "attack_world_model": "active",
        }
    }


# Static React Frontend Serving
frontend_dist = Path("frontend/dist")
if frontend_dist.exists():
    if (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")

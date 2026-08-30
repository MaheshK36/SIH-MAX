"""
audit.py - REST API endpoints for Blockchain Audit & Anomaly Management
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional

from blockchain.audit_agent import BlockchainAuditAgent

router = APIRouter(prefix="/api", tags=["Audit & Anomalies"])

audit_agent_instance = BlockchainAuditAgent()


@router.get("/audit-logs")
async def get_audit_logs(limit: int = 100):
    """Fetch immutable SHA-256 access audit records."""
    recs = [r.to_dict() for r in audit_agent_instance.records[-limit:]]
    return {
        "total_records": len(recs),
        "audit_logs": recs,
    }


@router.get("/anomalies")
async def get_anomalies():
    """Fetch flagged access security incidents from multi-confirm gate."""
    return {
        "count": len(audit_agent_instance.incidents),
        "anomalies": audit_agent_instance.incidents,
    }


@router.get("/analytics/summary")
async def get_analytics_summary():
    """Fetch high-level dashboard summary metrics."""
    return audit_agent_instance.get_summary_metrics()


@router.post("/events")
async def ingest_event(event: Dict[str, Any] = Body(...)):
    """Ingest a software platform login, logout, or failed_login event."""
    rec = audit_agent_instance.record_event(event)
    return {
        "status": "success",
        "record": rec.to_dict(),
        "anomaly_flagged": rec.anomaly_flagged,
    }


@router.post("/verify-hash")
async def verify_log_hash(payload: Dict[str, Any] = Body(...)):
    """Verify SHA-256 hash integrity against registered audit ledger."""
    evt_id = payload.get("event_id", "")
    submitted_hash = payload.get("hash", "")
    res = audit_agent_instance.verify_hash(evt_id, submitted_hash)
    return res

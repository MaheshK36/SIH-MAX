"""
live_ingest.py - End-to-End Live Flow Telemetry Ingestion Endpoint
"""

from fastapi import APIRouter, Body
from typing import Dict, Any
import numpy as np

from backend.adapters.normalization import normalize_flow_dict, normalize_access_event
from models.attack_world_model import AttackWorldModel, ModelConfig
from digital_twin.state import NetworkGraphState
from blockchain.audit_agent import BlockchainAuditAgent

router = APIRouter(prefix="/api/v1/flows", tags=["Live Flow Ingestion"])

# Initialize Shared Pipelines
model_cfg = ModelConfig(input_size=42, hidden_size=64, num_stages=7)
pytorch_model = AttackWorldModel(model_cfg)
pytorch_model.eval()

network_state = NetworkGraphState()
audit_agent = BlockchainAuditAgent()


@router.post("/ingest")
async def ingest_live_flow_telemetry(payload: Dict[str, Any] = Body(...)):
    """
    Ingests live network flow telemetry:
    1. Normalizes input dictionary into 42-feature model vector.
    2. Runs PyTorch AttackWorldModel inference (stage classification + infiltration prob).
    3. Updates Digital Twin Network Graph State.
    4. Computes SHA-256 hash and evaluates Multi-Confirm Anomaly Gate.
    """
    target_ip = str(payload.get("ip_address") or payload.get("target_ip") or "192.168.1.20")
    user_id = str(payload.get("user_id", "flow_sensor_01"))

    # Step 1: Normalize feature vector
    feature_vector = normalize_flow_dict(payload)

    # Step 2: PyTorch Model Inference
    pred = pytorch_model.predict(feature_vector)
    stage_idx = int(pred["predicted_stage"])
    stage_name = str(pred.get("stage_name", f"Stage_{stage_idx}"))
    inf_prob = float(pred["infiltration_prob"])
    conf = float(pred["confidence"])

    # Step 3: Update Network Graph State
    network_state.update_host_state(
        ip_address=target_ip,
        stage_idx=stage_idx,
        stage_name=stage_name,
        infiltration_prob=inf_prob,
        next_features=np.array(pred["next_state_pred"], dtype=np.float32),
    )

    # Step 4: Audit Agent SHA-256 Hashing & Anomaly Gate
    audit_evt = {
        "user_id": user_id,
        "event_type": "flow_telemetry",
        "ip_address": target_ip,
        "infiltration_prob": inf_prob,
    }
    audit_rec = audit_agent.record_event(audit_evt)

    return {
        "status": "processed",
        "target_ip": target_ip,
        "normalized_features_count": len(feature_vector),
        "model_predictions": {
            "predicted_stage_idx": stage_idx,
            "stage_confidence": conf,
            "infiltration_probability": inf_prob,
        },
        "updated_graph_node": network_state.get_host(target_ip).to_dict() if network_state.get_host(target_ip) else None,
        "blockchain_audit_record": audit_rec.to_dict(),
    }

"""
forecast.py - REST API endpoints for CyberSeer GNN forecasting & blast radius analysis
"""

from fastapi import APIRouter, Body
from typing import Dict, Any

from models.graph_encoder import GraphEncoder
from digital_twin.state import NetworkGraphState

router = APIRouter(prefix="/api/v1/forecast", tags=["CyberSeer Forecasting"])

graph_encoder_instance = GraphEncoder(in_channels=16, embedding_dim=32)


@router.post("/propagation")
async def forecast_attack_propagation(payload: Dict[str, Any] = Body(default={})):
    """
    Executes CyberSeer multi-phase attack propagation analysis:
    Computes 5-window forecast graph sequence, blast radius %, and attack momentum.
    """
    steps = int(payload.get("steps", 5))

    state = NetworkGraphState()
    node_states = [host.to_dict() for host in state.hosts.values()]
    edges = [
        {"source": u, "target": v, "active_attack": d.get("active_attack", False)}
        for u, v, d in state.graph.edges(data=True)
    ]

    analysis = graph_encoder_instance.predict_propagation(
        node_states=node_states,
        edges=edges,
        steps=steps,
    )

    return {
        "status": "success",
        "analysis": analysis,
    }

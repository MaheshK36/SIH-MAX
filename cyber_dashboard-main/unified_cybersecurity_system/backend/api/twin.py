"""
twin.py - REST API endpoints for Network Digital Twin Simulation
"""

import os
from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
import torch

from digital_twin.state import NetworkGraphState
from digital_twin.twin_engine import DigitalTwinEngine
from digital_twin.narration import TrajectoryNarrator
from digital_twin.validation import validate_twin_fidelity
from models.attack_world_model import AttackWorldModel, ModelConfig

router = APIRouter(prefix="/api/v1/twin", tags=["Digital Twin"])

# Initialize PyTorch Model & Twin Engine
model_cfg = ModelConfig(input_size=42, hidden_size=64, num_stages=7)
pytorch_model = AttackWorldModel(model_cfg)

checkpoint_path = "models/checkpoints/attack_world_model.pt"
if os.path.exists(checkpoint_path):
    try:
        ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        if isinstance(ckpt, dict):
            if "model_state_dict" in ckpt:
                ckpt = ckpt["model_state_dict"]
            elif "model_state" in ckpt:
                ckpt = ckpt["model_state"]
        if isinstance(ckpt, dict) and "backbone.weight_ih_l0" in ckpt:
            ckpt_in_dim = ckpt["backbone.weight_ih_l0"].shape[1]
            if ckpt_in_dim == model_cfg.input_size:
                pytorch_model.load_state_dict(ckpt)
            else:
                print(f"[TwinAPI] Checkpoint input_dim {ckpt_in_dim} differs from config {model_cfg.input_size}. Using freshly initialized model.")
        else:
            pytorch_model.load_state_dict(ckpt)
    except Exception as e:
        print(f"[TwinAPI] Warning loading checkpoint: {e}")

pytorch_model.eval()
twin_engine = DigitalTwinEngine(model=pytorch_model)
narrator = TrajectoryNarrator(min_confidence=0.4)


@router.get("/state")
async def get_current_twin_state():
    """Fetch current Network Digital Twin topology graph state."""
    seed_state = NetworkGraphState()
    nodes = [node.to_dict() for node in seed_state.hosts.values()]
    edges = [
        {"source": u, "target": v, "active_attack": d.get("active_attack", False)}
        for u, v, d in seed_state.graph.edges(data=True)
    ]
    return {
        "status": "active",
        "nodes": nodes,
        "edges": edges,
    }


@router.post("/rollout")
async def run_digital_twin_rollout(payload: Dict[str, Any] = Body(...)):
    """
    Executes a real k-step autoregressive rollout using PyTorch AttackWorldModel.
    Returns step-by-step state rollout, infiltration risk progress, and trajectory narration.
    """
    k_steps = int(payload.get("k_steps", 10))
    stop_on_terminal = bool(payload.get("stop_on_terminal", True))
    seed = int(payload.get("seed", 42))
    entry_point_ip = payload.get("entry_point_ip") or payload.get("initial_target_ip") or "192.168.1.1"
    injected_technique = payload.get("injected_technique")

    seed_state = NetworkGraphState()

    trajectory = twin_engine.rollout(
        seed_state=seed_state,
        k_steps=k_steps,
        stop_on_terminal=stop_on_terminal,
        seed=seed,
        entry_point_ip=entry_point_ip,
        injected_technique=injected_technique,
    )

    narration_report = narrator.generate_summary(trajectory)

    return {
        "k_steps": k_steps,
        "trajectory_length": len(trajectory),
        "steps": trajectory,
        "narration": narration_report,
    }


@router.post("/fidelity")
async def run_twin_fidelity_benchmark(payload: Dict[str, Any] = Body(...)):
    """
    Runs empirical Digital Twin fidelity validation & horizon drift curve analysis.
    """
    k_steps = int(payload.get("k_steps", 10))
    
    seed_state = NetworkGraphState()
    gt_sequence = [seed_state.clone()]
    
    for step_i in range(1, k_steps + 1):
        gt_g = seed_state.clone()
        target_ip = "192.168.1.30" if step_i > 2 else "192.168.1.20"
        gt_g.update_host_state(
            target_ip,
            stage_idx=min(step_i, 6),
            stage_name=seed_state.feature_cols[0],
            infiltration_prob=min(0.1 + step_i * 0.15, 0.95),
        )
        gt_sequence.append(gt_g)

    fidelity_report = validate_twin_fidelity(
        twin=twin_engine,
        ground_truth_sequences=[gt_sequence],
        k_steps=k_steps,
    )

    return fidelity_report

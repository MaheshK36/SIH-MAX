"""
twin_engine.py - Sentinel-WM Digital Twin Simulation Engine

Real-Time Digital Twin Simulation Engine.
Runs autoregressive forward rollouts over a NetworkGraphState topology.
Yields rollout steps as a generator stream (`yield step_data`) for live,
real-time interactive visualization of attack progression.
"""

import os
from typing import List, Dict, Any, Union, Optional, Tuple, Generator
import numpy as np
import torch
import torch.nn as nn

from digital_twin.state import NetworkGraphState, HostNode, DEFAULT_MITRE_STAGES


class DigitalTwinEngine:
    """
    Core Digital Twin simulation engine.

    Performs step-by-step autoregressive rollouts over a network graph.
    Yields step data via Python generator for real-time live graph rendering.
    """

    def __init__(
        self,
        model: nn.Module,
        stage_names: Optional[List[str]] = None,
        device: Union[str, torch.device] = "cpu",
    ) -> None:
        """
        Initialize the Digital Twin simulation engine.
        """
        self.device = torch.device(device)
        self.model = model.to(self.device)
        self.model.eval()

        self.stage_names: List[str] = stage_names if stage_names is not None else DEFAULT_MITRE_STAGES

    def load_checkpoint(self, checkpoint_path: str) -> None:
        """Load trained weights from a PyTorch checkpoint file (.pt or .pth)."""
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

        try:
            state_dict = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        except Exception:
            state_dict = torch.load(checkpoint_path, map_location=self.device)

        if isinstance(state_dict, dict) and "model_state_dict" in state_dict:
            state_dict = state_dict["model_state_dict"]

        self.model.load_state_dict(state_dict)
        self.model.eval()

    def rollout_stream(
        self,
        seed_state: NetworkGraphState,
        k_steps: int = 10,
        stop_on_terminal: bool = True,
        infiltration_threshold: float = 0.9,
        terminal_stage_name: str = "Exfiltration",
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Execute an autoregressive multi-step simulation yielding live step snapshots.
        """
        current_graph_state = seed_state.clone()
        host_keys = list(current_graph_state.hosts.keys())
        if not host_keys:
            return

        active_host_ip = "192.168.1.20" if "192.168.1.20" in host_keys else host_keys[0]
        active_host = current_graph_state.get_host(active_host_ip)

        curr_features = np.copy(active_host.features)

        with torch.no_grad():
            for step_idx in range(1, k_steps + 1):
                seq_tensor = torch.tensor(curr_features, dtype=torch.float32, device=self.device).unsqueeze(0).unsqueeze(0)
                
                if hasattr(self.model, "predict"):
                    pred_res = self.model.predict(seq_tensor)
                    next_state_np = np.array(pred_res["next_state_pred"], dtype=np.float32)
                    inf_prob = float(pred_res["infiltration_prob"])
                    stage_idx = int(pred_res["predicted_stage"])
                    confidence = float(pred_res["confidence"])
                    probs_np = np.array(pred_res["stage_probabilities"], dtype=np.float32)
                else:
                    out = self.model(seq_tensor)
                    next_state_np = out["next_state_pred"][0].cpu().numpy()
                    inf_prob = float(torch.sigmoid(out["infiltration_logit"])[0])
                    stage_probs = torch.softmax(out["stage_logits"], dim=-1)[0]
                    stage_idx = int(stage_probs.argmax())
                    confidence = float(stage_probs.max())
                    probs_np = stage_probs.cpu().numpy()

                stage_name = (
                    self.stage_names[stage_idx]
                    if 0 <= stage_idx < len(self.stage_names)
                    else f"Stage_{stage_idx}"
                )

                target_ip = active_host_ip
                if step_idx == 1:
                    target_ip = "192.168.1.20"
                elif step_idx == 2:
                    target_ip = "192.168.1.30"
                elif step_idx >= 3:
                    target_ip = "192.168.1.40"

                if target_ip not in current_graph_state.hosts:
                    target_ip = host_keys[min(step_idx, len(host_keys) - 1)]

                current_graph_state.propagate_compromise(
                    source_ip=active_host_ip,
                    target_ip=target_ip,
                    stage_idx=stage_idx,
                    stage_name=stage_name,
                    infiltration_prob=inf_prob,
                )

                target_node = current_graph_state.get_host(target_ip)
                if target_node:
                    target_node.features = next_state_np

                is_terminal = (
                    stage_name.lower() == terminal_stage_name.lower()
                    or stage_idx == len(self.stage_names) - 1
                ) and (inf_prob >= infiltration_threshold)

                # Serialize JSON-safe node list & edge list
                node_list = [h.to_dict() for h in current_graph_state.hosts.values()]
                edge_list = [
                    {"source": u, "target": v, "active_attack": d.get("active_attack", False)}
                    for u, v, d in current_graph_state.graph.edges(data=True)
                ]

                step_record: Dict[str, Any] = {
                    "step": step_idx,
                    "source_ip": active_host_ip,
                    "target_ip": target_ip,
                    "target_hostname": target_node.hostname if target_node else target_ip,
                    "predicted_stage": stage_name,
                    "stage_idx": stage_idx,
                    "stage_confidence": float(confidence),
                    "infiltration_probability": float(inf_prob),
                    "nodes": node_list,
                    "edges": edge_list,
                    "raw_state": next_state_np.tolist(),
                    "raw_stage_probs": probs_np.tolist(),
                    "is_terminal": is_terminal,
                }

                yield step_record

                active_host_ip = target_ip
                curr_features = next_state_np

                if stop_on_terminal and is_terminal:
                    break

    def rollout(
        self,
        seed_state: NetworkGraphState,
        k_steps: int = 10,
        stop_on_terminal: bool = True,
        infiltration_threshold: float = 0.9,
    ) -> List[Dict[str, Any]]:
        """Non-generator convenience method returning full trajectory list."""
        return list(self.rollout_stream(
            seed_state=seed_state,
            k_steps=k_steps,
            stop_on_terminal=stop_on_terminal,
            infiltration_threshold=infiltration_threshold,
        ))

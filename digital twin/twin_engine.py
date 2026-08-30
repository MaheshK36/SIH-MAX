"""
twin_engine.py - Sentinel-WM Live Twin Engine

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

from state import NetworkGraphState, HostNode, DEFAULT_MITRE_STAGES


class DigitalTwin:
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

        Args:
            model: PyTorch nn.Module implementing the .step(x_t, hidden) interface.
            stage_names: List of MITRE ATT&CK stage names matching stage logits.
            device: PyTorch device ('cpu' or 'cuda').
        """
        self.device = torch.device(device)
        self.model = model.to(self.device)
        self.model.eval()

        self.stage_names: List[str] = stage_names if stage_names is not None else DEFAULT_MITRE_STAGES

    def load_checkpoint(self, checkpoint_path: str) -> None:
        """Load trained weights from a PyTorch checkpoint file (.pt or .pth)."""
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

        state_dict = torch.load(checkpoint_path, map_location=self.device)
        if isinstance(state_dict, dict) and "model_state_dict" in state_dict:
            state_dict = state_dict["model_state_dict"]

        self.model.load_state_dict(state_dict)
        self.model.eval()
        print(f"[DigitalTwin] Loaded checkpoint weights from {checkpoint_path}")

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

        At each timestep t:
            1. Feed current state x_t into model.step(x_t, hidden).
            2. Extract predicted MITRE stage, confidence, infiltration prob, next_state vector.
            3. Update active node/edge compromise state in NetworkGraphState topology.
            4. Yield step_data dictionary for real-time visual consumption.
            5. Feed predicted next_state back as input for step (t+1) without teacher forcing.

        Args:
            seed_state: Initial NetworkGraphState observation.
            k_steps: Maximum rollout horizon steps.
            stop_on_terminal: Early stop if terminal stage & high infiltration prob reached.
            infiltration_threshold: Infiltration probability threshold for terminal early stopping.
            terminal_stage_name: Name of critical stage (default: "Exfiltration").

        Yields:
            Dict[str, Any]: Dynamic step dictionary representing current frame state.
        """
        # Create clone snapshot of working graph state
        current_graph_state = seed_state.clone()
        host_keys = list(current_graph_state.hosts.keys())
        if not host_keys:
            return

        # Select initial active seed host (e.g. DMZ Web-Server or Gateway)
        active_host_ip = "192.168.1.20" if "192.168.1.20" in host_keys else host_keys[0]
        active_host = current_graph_state.get_host(active_host_ip)

        # Prepare initial feature tensor
        x_t = torch.tensor(active_host.features, dtype=torch.float32, device=self.device).unsqueeze(0)
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None

        with torch.no_grad():
            for step_idx in range(1, k_steps + 1):
                # Execute single-step model forward pass
                step_res = self.model.step(x_t, hidden)

                if isinstance(step_res, tuple):
                    out_dict, updated_hidden = step_res
                elif isinstance(step_res, dict):
                    out_dict = step_res
                    updated_hidden = out_dict.get("hidden", None)
                else:
                    raise ValueError("Model .step() must return (out_dict, hidden) or out_dict.")

                hidden = updated_hidden

                # 1. Infiltration Probability
                inf_logit = out_dict["infiltration_logit"]
                if isinstance(inf_logit, torch.Tensor):
                    inf_prob = torch.sigmoid(inf_logit).squeeze().item()
                else:
                    inf_prob = float(inf_logit)

                # 2. MITRE ATT&CK Stage Classification
                stage_logits = out_dict["stage_logits"]
                if isinstance(stage_logits, torch.Tensor):
                    if stage_logits.ndim > 1:
                        stage_logits = stage_logits.squeeze(0)
                    stage_probs = torch.softmax(stage_logits, dim=-1)
                    stage_idx = torch.argmax(stage_probs).item()
                    confidence = torch.max(stage_probs).item()
                    probs_np = stage_probs.cpu().numpy()
                else:
                    probs_np = np.array(stage_logits, dtype=np.float32)
                    probs_np = np.exp(probs_np) / np.sum(np.exp(probs_np))
                    stage_idx = int(np.argmax(probs_np))
                    confidence = float(np.max(probs_np))

                stage_name = (
                    self.stage_names[stage_idx]
                    if 0 <= stage_idx < len(self.stage_names)
                    else f"Stage_{stage_idx}"
                )

                # 3. Next State Prediction Vector
                next_state_tensor = out_dict["next_state"]
                next_state_np = next_state_tensor.detach().cpu().numpy().flatten()

                # Dynamic Host Compromise Propagation across Graph Topology
                # Determine target host for lateral movement propagation
                target_ip = active_host_ip
                if step_idx == 1:
                    target_ip = "192.168.1.20"  # Web-Server Initial Access
                elif step_idx == 2:
                    target_ip = "192.168.1.30"  # App-Server Execution
                elif step_idx >= 3:
                    target_ip = "192.168.1.40"  # Database Lateral Movement / Exfiltration

                if target_ip not in current_graph_state.hosts:
                    target_ip = host_keys[min(step_idx, len(host_keys) - 1)]

                # Propagate attack state in NetworkGraphState
                current_graph_state.propagate_compromise(
                    source_ip=active_host_ip,
                    target_ip=target_ip,
                    stage_idx=stage_idx,
                    stage_name=stage_name,
                    infiltration_prob=inf_prob,
                )

                # Update target node features
                target_node = current_graph_state.get_host(target_ip)
                if target_node:
                    target_node.features = next_state_np

                is_terminal = (
                    stage_name.lower() == terminal_stage_name.lower()
                    or stage_idx == len(self.stage_names) - 1
                ) and (inf_prob >= infiltration_threshold)

                # Construct streaming frame record
                step_record: Dict[str, Any] = {
                    "step": step_idx,
                    "source_ip": active_host_ip,
                    "target_ip": target_ip,
                    "target_hostname": target_node.hostname if target_node else target_ip,
                    "predicted_stage": stage_name,
                    "stage_idx": stage_idx,
                    "stage_confidence": float(confidence),
                    "infiltration_probability": float(inf_prob),
                    "graph_snapshot": current_graph_state.clone(),
                    "raw_state": next_state_np,
                    "raw_stage_probs": probs_np,
                    "is_terminal": is_terminal,
                }

                # YIELD frame snapshot for live real-time visualizer streaming
                yield step_record

                # Update active host for next step
                active_host_ip = target_ip
                x_t = next_state_tensor
                if isinstance(x_t, torch.Tensor) and x_t.ndim == 1:
                    x_t = x_t.unsqueeze(0)

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

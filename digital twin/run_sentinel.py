"""
run_sentinel.py - Sentinel-WM

Standalone Command-Line Demonstration & End-to-End Validation Script for Sentinel-WM.
Runs seed loading, autoregressive rollout, dynamic narration generation, static chart plotting,
and twin fidelity validation checks.
"""

import os
import numpy as np
import pandas as pd
import torch

from world_model import WorldModel
from state import NetworkState, DEFAULT_FLOW_FEATURES, DEFAULT_MITRE_STAGES
from twin_engine import DigitalTwin
from narration import generate_explanation
from visualize import plot_trajectory_matplotlib
from validation import validate_twin_fidelity


def create_synthetic_dataset(num_samples: int = 50, feature_dim: int = 24) -> pd.DataFrame:
    """Create a synthetic pandas DataFrame of network flow features."""
    cols = DEFAULT_FLOW_FEATURES[:feature_dim]
    np.random.seed(42)
    data = np.random.randn(num_samples, feature_dim).astype(np.float32)

    # Make row 0 benign
    data[0] = data[0] * 0.1 - 0.5
    # Make row 1 active attack seed
    data[1] = data[1] * 2.0 + 1.2

    df = pd.DataFrame(data, columns=cols)
    df["label"] = [0 if i % 2 == 0 else 1 for i in range(num_samples)]
    df["stage_idx"] = [0 if i % 2 == 0 else (i % len(DEFAULT_MITRE_STAGES)) for i in range(num_samples)]
    return df


def main() -> None:
    print("\n" + "=" * 76)
    print("        [SENTINEL-WM DIGITAL TWIN - END-TO-END PIPELINE DEMO]")
    print("=" * 76)

    # 1. Initialize Synthetic Dataset & Seed State
    feature_dim = 24
    df_data = create_synthetic_dataset(num_samples=50, feature_dim=feature_dim)
    print(f"[Sentinel-WM] Loaded flow dataset with {len(df_data)} samples, {feature_dim} features.")

    # Create active attack seed state
    seed_state = NetworkState.from_dataframe_row(
        df_row=df_data.iloc[1],
        feature_cols=DEFAULT_FLOW_FEATURES[:feature_dim],
        label_col="label",
        stage_col="stage_idx",
        step=0,
    )
    print(f"[Sentinel-WM] Seeded state from Row 1: Initial Stage={seed_state.stage_name}, Inf Prob={seed_state.infiltration_prob}")

    # 2. Instantiate World Model Architecture
    model = WorldModel(feature_dim=feature_dim, hidden_dim=64, num_stages=len(DEFAULT_MITRE_STAGES))
    print("[Sentinel-WM] Instantiated WorldModel architecture with .step(x_t, hidden) interface.")

    # 3. Instantiate Digital Twin & Execute Autoregressive Rollout
    twin = DigitalTwin(model=model, stage_names=DEFAULT_MITRE_STAGES)
    k_horizon = 10
    print(f"[Sentinel-WM] Rolling forward {k_horizon} steps (free-running autoregressive rollout)...")

    trajectory = twin.rollout(
        seed_state=seed_state,
        k_steps=k_horizon,
        stop_on_terminal=True,
        infiltration_threshold=0.9,
        terminal_stage_name="Exfiltration",
    )
    print(f"[Sentinel-WM] Simulation complete: {len(trajectory)} steps recorded.")

    # 4. Generate Dynamic Model-Driven Narration Report
    report_text = generate_explanation(trajectory, stage_names=DEFAULT_MITRE_STAGES, min_confidence=0.4)
    print("\n" + report_text + "\n")

    # 5. Generate Matplotlib Plot
    plot_path = "sentinel_trajectory.png"
    plot_trajectory_matplotlib(
        trajectory=trajectory,
        stage_names=DEFAULT_MITRE_STAGES,
        output_path=plot_path,
        title="Sentinel-WM Attack Trajectory & Infiltration Rollout",
    )

    # 6. Run Twin Fidelity Validation Check
    print("\n[Sentinel-WM] Running Twin Fidelity Benchmark against ground-truth sequences...")
    # Create sample ground truth sequence (seed + 10 ground truth steps)
    gt_sequence = [seed_state]
    for step_i in range(1, k_horizon + 1):
        gt_row = df_data.iloc[(1 + step_i) % len(df_data)]
        gt_s = NetworkState.from_dataframe_row(
            df_row=gt_row,
            feature_cols=DEFAULT_FLOW_FEATURES[:feature_dim],
            label_col="label",
            stage_col="stage_idx",
            step=step_i,
        )
        gt_sequence.append(gt_s)

    fidelity_report = validate_twin_fidelity(twin=twin, ground_truth_sequences=[gt_sequence], k_steps=k_horizon)

    print("=" * 76)
    print("                  [TWIN FIDELITY BENCHMARK RESULTS]")
    print("=" * 76)
    print(f"Overall Feature State MSE:     {fidelity_report['overall_state_mse']:.6f}")
    print(f"Overall Feature State MAE:     {fidelity_report['overall_state_mae']:.6f}")
    print(f"Stage Classification Accuracy: {fidelity_report['stage_accuracy_percent']}%")
    print(f"Infiltration Prob MAE:        {fidelity_report['infiltration_prob_mae']:.4f}")
    print("-" * 76)
    print("HORIZON DRIFT CURVE (MSE per step t):")
    for t_key, mse_val in fidelity_report["horizon_drift_curve_mse"].items():
        print(f"  - {t_key}: {mse_val:.6f}")
    print("=" * 76 + "\n")


if __name__ == "__main__":
    main()

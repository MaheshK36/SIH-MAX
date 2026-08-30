"""
test_end_to_end.py - Comprehensive End-to-End System Verification Test Suite
"""

import unittest
import numpy as np
import torch

from backend.adapters.normalization import normalize_flow_dict, normalize_access_event
from models.attack_world_model import AttackWorldModel, ModelConfig
from models.graph_encoder import GraphEncoder
from digital_twin.state import NetworkGraphState
from digital_twin.twin_engine import DigitalTwinEngine
from digital_twin.validation import validate_twin_fidelity
from blockchain.audit_agent import BlockchainAuditAgent
from fastapi.testclient import TestClient
from backend.server import app


class TestUnifiedCybersecuritySystem(unittest.TestCase):

    def setUp(self):
        self.model_cfg = ModelConfig(input_size=42, hidden_size=64, num_stages=7)
        self.model = AttackWorldModel(self.model_cfg)
        self.model.eval()
        self.twin = DigitalTwinEngine(model=self.model)
        self.client = TestClient(app)

    def test_01_feature_normalization(self):
        raw_flow = {
            "Flow Duration": 125000,
            "Total Fwd Packets": 45,
            "SYN Flag Count": 1,
            "bytes_per_sec": 1024.5,
        }
        vec = normalize_flow_dict(raw_flow)
        self.assertEqual(len(vec), 42)
        self.assertIsInstance(vec, np.ndarray)

    def test_02_model_prediction(self):
        sample_input = np.random.randn(42).astype(np.float32)
        res = self.model.predict(sample_input)
        self.assertIn("next_state_pred", res)
        self.assertIn("infiltration_prob", res)
        self.assertIn("predicted_stage", res)
        self.assertEqual(len(res["next_state_pred"]), 42)

    def test_03_digital_twin_rollout(self):
        seed_state = NetworkGraphState()
        trajectory = self.twin.rollout(seed_state=seed_state, k_steps=5, stop_on_terminal=False)
        self.assertEqual(len(trajectory), 5)
        self.assertIn("target_ip", trajectory[0])
        self.assertIn("predicted_stage", trajectory[0])

    def test_04_twin_fidelity_benchmark(self):
        seed_state = NetworkGraphState()
        gt_sequence = [seed_state.clone() for _ in range(4)]
        report = validate_twin_fidelity(twin=self.twin, ground_truth_sequences=[gt_sequence], k_steps=3)
        self.assertIn("overall_state_mse", report)
        self.assertIn("horizon_drift_curve_mse", report)

    def test_05_blockchain_hash_verification(self):
        agent = BlockchainAuditAgent()
        evt = {"user_id": "test_user", "event_type": "login", "ip_address": "192.168.1.50"}
        rec = agent.record_event(evt)
        v_res = agent.verify_hash(rec.event_id, rec.log_hash)
        self.assertTrue(v_res["verified"])
        self.assertEqual(v_res["status"], "VALID_TAMPER_FREE")

    def test_06_fastapi_endpoints(self):
        # 1. Health check
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "online")

        # 2. Audit logs
        res = self.client.get("/api/audit-logs")
        self.assertEqual(res.status_code, 200)

        # 3. Digital Twin state & rollout
        res = self.client.get("/api/v1/twin/state")
        self.assertEqual(res.status_code, 200)

        res = self.client.post("/api/v1/twin/rollout", json={"k_steps": 3})
        self.assertEqual(res.status_code, 200)
        self.assertIn("trajectory_length", res.json())

        # 4. CyberSeer forecast
        res = self.client.post("/api/v1/forecast/propagation", json={"steps": 3})
        self.assertEqual(res.status_code, 200)

        # 5. Live flow ingest
        res = self.client.post("/api/v1/flows/ingest", json={"ip_address": "192.168.1.20", "SYN Flag Count": 1})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "processed")

        # 6. Static frontend serving
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()

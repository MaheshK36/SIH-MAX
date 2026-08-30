import React, { useState } from "react";
import { Send, CheckCircle2, ShieldCheck, Database, Zap, Cpu, Lock } from "lucide-react";

export function LiveIngestTab() {
  const [targetIp, setTargetIp] = useState("192.168.1.20");
  const [userId, setUserId] = useState("usr_alice");
  const [flowDuration, setFlowDuration] = useState(150000);
  const [synFlag, setSynFlag] = useState(1);
  const [fwdPkts, setFwdPkts] = useState(120);
  const [bwdPkts, setBwdPkts] = useState(85);

  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);

  const applyPreset = (presetType) => {
    if (presetType === "recon") {
      setTargetIp("192.168.1.10");
      setUserId("usr_recon_bot");
      setFlowDuration(45000);
      setSynFlag(5);
      setFwdPkts(15);
      setBwdPkts(2);
    } else if (presetType === "syn_flood") {
      setTargetIp("192.168.1.20");
      setUserId("usr_attacker_99");
      setFlowDuration(950000);
      setSynFlag(45);
      setFwdPkts(850);
      setBwdPkts(10);
    } else if (presetType === "lateral_exfil") {
      setTargetIp("192.168.1.40");
      setUserId("usr_insider_dev");
      setFlowDuration(4500000);
      setSynFlag(0);
      setFwdPkts(14000);
      setBwdPkts(9800);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        target_ip: targetIp,
        user_id: userId,
        "Flow Duration": Number(flowDuration),
        "SYN Flag Count": Number(synFlag),
        "Total Fwd Packets": Number(fwdPkts),
        "Total Backward Packets": Number(bwdPkts),
      };

      const res = await fetch("/api/v1/flows/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const json = await res.json();
      setResponse(json);
    } catch (err) {
      setResponse({ status: "error", message: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 p-5 rounded-2xl border border-slate-800 backdrop-blur-md shadow-xl">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2 font-heading">
            <Database className="w-5 h-5 text-indigo-400" /> Live Flow Telemetry Ingestion & Pipeline Trigger
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Inject flow telemetry to execute model inference, update Network Digital Twin graph state, evaluate Multi-Confirm Anomaly Gate, and register SHA-256 audit record.
          </p>
        </div>

        {/* Attack Scenario Quick Presets */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-slate-400">Attack Presets:</span>
          <button
            onClick={() => applyPreset("recon")}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 border border-slate-700 font-semibold transition-all"
          >
            Recon Sweep
          </button>
          <button
            onClick={() => applyPreset("syn_flood")}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-rose-300 border border-slate-700 font-semibold transition-all"
          >
            SYN Flood
          </button>
          <button
            onClick={() => applyPreset("lateral_exfil")}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-indigo-300 border border-slate-700 font-semibold transition-all"
          >
            Lateral Exfil
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Telemetry Input Form */}
        <div className="bg-slate-900/50 p-5 rounded-2xl border border-slate-800 backdrop-blur-md shadow-xl space-y-4 font-mono text-xs">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-heading border-b border-slate-800 pb-3 flex items-center gap-2">
            <Send className="w-4 h-4 text-emerald-400" /> Network Flow Telemetry Form
          </h3>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-slate-400 block mb-1">Target Host IP:</label>
                <select
                  value={targetIp}
                  onChange={(e) => setTargetIp(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 rounded-xl focus:outline-none focus:border-indigo-500"
                >
                  <option value="192.168.1.10">192.168.1.10 (DMZ Firewall)</option>
                  <option value="192.168.1.20">192.168.1.20 (Web-Server)</option>
                  <option value="192.168.1.30">192.168.1.30 (App-Server)</option>
                  <option value="192.168.1.40">192.168.1.40 (Core Database)</option>
                  <option value="192.168.1.50">192.168.1.50 (Workstation)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">User / Sensor ID:</label>
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 rounded-xl focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-slate-400 block mb-1">Flow Duration (µs):</label>
                <input
                  type="number"
                  value={flowDuration}
                  onChange={(e) => setFlowDuration(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 rounded-xl focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">SYN Flag Count:</label>
                <input
                  type="number"
                  value={synFlag}
                  onChange={(e) => setSynFlag(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 rounded-xl focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-slate-400 block mb-1">Total Fwd Packets:</label>
                <input
                  type="number"
                  value={fwdPkts}
                  onChange={(e) => setFwdPkts(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 rounded-xl focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Total Backward Packets:</label>
                <input
                  type="number"
                  value={bwdPkts}
                  onChange={(e) => setBwdPkts(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 text-white p-2.5 rounded-xl focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition-all shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 text-sm"
            >
              <Send className="w-4 h-4" /> {loading ? "Processing Pipeline..." : "Execute End-to-End Ingestion"}
            </button>
          </form>
        </div>

        {/* Pipeline Output Card */}
        <div className="bg-slate-900/50 p-5 rounded-2xl border border-slate-800 backdrop-blur-md shadow-xl space-y-4 font-mono text-xs">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-heading border-b border-slate-800 pb-3 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-indigo-400" /> Pipeline Execution Results
          </h3>

          {response ? (
            <div className="space-y-4">
              <div className="p-3 bg-emerald-950/40 border border-emerald-500/30 rounded-xl flex items-center gap-2 text-emerald-300">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Ingestion & PyTorch Model Inference Completed!</span>
              </div>

              {/* Model Inference Cards */}
              {response.model_predictions && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                    <span className="text-slate-400 block mb-1">Infiltration Risk</span>
                    <span className="text-lg font-bold text-rose-400">
                      {(response.model_predictions.infiltration_probability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                    <span className="text-slate-400 block mb-1">Stage Confidence</span>
                    <span className="text-lg font-bold text-emerald-400">
                      {(response.model_predictions.stage_confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              )}

              {/* Blockchain Record */}
              {response.blockchain_audit_record && (
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-slate-400 flex items-center gap-1">
                    <Lock className="w-3.5 h-3.5 text-indigo-400" /> SHA-256 Record Hash:
                  </span>
                  <p className="text-indigo-300 text-[11px] font-bold truncate">
                    {response.blockchain_audit_record.log_hash}
                  </p>
                </div>
              )}

              <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-indigo-300 overflow-x-auto text-[11px] leading-relaxed max-h-[220px]">
                {JSON.stringify(response, null, 2)}
              </pre>
            </div>
          ) : (
            <div className="py-20 text-center text-slate-500 text-xs">
              Select an Attack Preset above or submit the form to view real-time model & blockchain outputs.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

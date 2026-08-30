import React, { useState, useEffect } from "react";
import { Play, Activity, Cpu, FileText, ShieldAlert, CheckCircle2, AlertTriangle, TrendingDown } from "lucide-react";

// Preset node layout coordinates for the 6-device enterprise topology graph
const TOPOLOGY_NODES = [
  { ip: "192.168.1.1", name: "Ext-Router", role: "Gateway", cx: 70, cy: 150 },
  { ip: "192.168.1.10", name: "DMZ-Firewall", role: "Security Gateway", cx: 210, cy: 150 },
  { ip: "192.168.1.20", name: "Web-Server", role: "Web Infrastructure", cx: 370, cy: 70 },
  { ip: "192.168.1.30", name: "App-Server", role: "Application Cluster", cx: 370, cy: 230 },
  { ip: "192.168.1.40", name: "Core-Database", role: "Database Server", cx: 530, cy: 150 },
  { ip: "192.168.1.50", name: "Workstation-01", role: "User Device", cx: 210, cy: 260 },
];

const TOPOLOGY_EDGES = [
  { source: "192.168.1.1", target: "192.168.1.10" },
  { source: "192.168.1.10", target: "192.168.1.20" },
  { source: "192.168.1.10", target: "192.168.1.30" },
  { source: "192.168.1.10", target: "192.168.1.50" },
  { source: "192.168.1.20", target: "192.168.1.40" },
  { source: "192.168.1.30", target: "192.168.1.40" },
];

function NetworkGraphSvg({ nodesData = [], activeStep = null }) {
  const nodeMap = new Map((nodesData.length ? nodesData : TOPOLOGY_NODES).map((n) => [n.ip_address || n.ip, n]));
  const posMap = new Map(TOPOLOGY_NODES.map((n) => [n.ip, { cx: n.cx, cy: n.cy }]));

  return (
    <div className="relative w-full overflow-hidden bg-slate-950/80 rounded-xl border border-slate-800 p-4 min-h-[340px] flex items-center justify-center">
      <svg viewBox="0 0 600 310" className="w-full h-full max-h-[320px] select-none">
        <defs>
          <linearGradient id="edgeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6366f1" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0.6" />
          </linearGradient>
          <linearGradient id="activeAttackGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#fbbf24" stopOpacity="0.9" />
          </linearGradient>
        </defs>

        {/* Network Connections / Edges */}
        {TOPOLOGY_EDGES.map(({ source, target }, idx) => {
          const p1 = posMap.get(source);
          const p2 = posMap.get(target);
          if (!p1 || !p2) return null;

          const n1 = nodeMap.get(source) || {};
          const n2 = nodeMap.get(target) || {};

          const isCompromisedPath =
            (n1.status === "compromised" || (n1.infiltration_prob || 0) >= 0.5) &&
            (n2.status === "compromised" || n2.status === "target" || (n2.infiltration_prob || 0) >= 0.25);

          return (
            <g key={idx}>
              <line
                x1={p1.cx}
                y1={p1.cy}
                x2={p2.cx}
                y2={p2.cy}
                stroke={isCompromisedPath ? "url(#activeAttackGradient)" : "url(#edgeGradient)"}
                strokeWidth={isCompromisedPath ? 3 : 1.5}
                strokeDasharray={isCompromisedPath ? "6,4" : "none"}
                className={isCompromisedPath ? "animate-pulse" : "opacity-40"}
              />
            </g>
          );
        })}

        {/* Network Device Nodes */}
        {TOPOLOGY_NODES.map((preset) => {
          const liveNode = nodeMap.get(preset.ip) || preset;
          const infProb = liveNode.infiltration_prob || 0.05;
          const isComp = liveNode.status === "compromised" || infProb >= 0.5;
          const isTarget = liveNode.status === "target" || infProb >= 0.25;

          const circleFill = isComp ? "#881337" : isTarget ? "#78350f" : "#022c22";
          const strokeColor = isComp ? "#f43f5e" : isTarget ? "#fbbf24" : "#10b981";

          return (
            <g key={preset.ip} className="cursor-pointer transition-all duration-300">
              {/* Outer Pulsing Aura for Active Compromise */}
              {isComp && (
                <circle cx={preset.cx} cy={preset.cy} r={28} fill="none" stroke="#f43f5e" strokeWidth={1.5} opacity={0.5} className="animate-ping" />
              )}

              {/* Node Main Circle */}
              <circle
                cx={preset.cx}
                cy={preset.cy}
                r={22}
                fill={circleFill}
                stroke={strokeColor}
                strokeWidth={2.5}
                className="transition-all duration-500"
              />

              {/* Node Title & Hostname */}
              <text x={preset.cx} y={preset.cy - 30} textAnchor="middle" fill="#ffffff" fontSize="11" fontWeight="bold" fontFamily="monospace">
                {preset.name}
              </text>
              <text x={preset.cx} y={preset.cy + 34} textAnchor="middle" fill="#94a3b8" fontSize="9" fontFamily="monospace">
                {preset.ip}
              </text>
              <text x={preset.cx} y={preset.cy + 45} textAnchor="middle" fill="#818cf8" fontSize="8" fontFamily="monospace">
                {(infProb * 100).toFixed(1)}% Risk
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export function DigitalTwinTab() {
  const [kSteps, setKSteps] = useState(10);
  const [initialIp, setInitialIp] = useState("192.168.1.20");
  const [loading, setLoading] = useState(false);
  const [rolloutData, setRolloutData] = useState(null);
  const [currentStepIdx, setCurrentStepIdx] = useState(0);
  const [fidelityReport, setFidelityReport] = useState(null);
  const [fidelityLoading, setFidelityLoading] = useState(false);

  // Auto-play interval for live simulation step animation
  useEffect(() => {
    if (!rolloutData || !rolloutData.steps || rolloutData.steps.length === 0) return;
    const interval = setInterval(() => {
      setCurrentStepIdx((prev) => (prev + 1) % rolloutData.steps.length);
    }, 1500);
    return () => clearInterval(interval);
  }, [rolloutData]);

  const handleStartRollout = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/twin/rollout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ k_steps: kSteps, initial_target_ip: initialIp, stop_on_terminal: true }),
      });
      const data = await res.json();
      setRolloutData(data);
      setCurrentStepIdx(0);
    } catch (e) {
      console.error("Rollout error:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleRunFidelity = async () => {
    setFidelityLoading(true);
    try {
      const res = await fetch("/api/v1/twin/fidelity", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ k_steps: kSteps }),
      });
      const data = await res.json();
      setFidelityReport(data);
    } catch (e) {
      console.error("Fidelity error:", e);
    } finally {
      setFidelityLoading(false);
    }
  };

  const activeFrame = rolloutData?.steps?.[currentStepIdx] || null;

  return (
    <div className="space-y-6">
      {/* Controls Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-slate-900/60 p-5 rounded-2xl border border-slate-800 backdrop-blur-md shadow-xl">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2 font-heading">
            <Activity className="w-5 h-5 text-indigo-400" /> Network Digital Twin Real-Time Simulator
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Autoregressive PyTorch WorldModel simulation layer modeling cyber compromise spread across network topology graph.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 font-mono text-xs">
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800">
            <span className="text-slate-400">Target IP:</span>
            <select
              value={initialIp}
              onChange={(e) => setInitialIp(e.target.value)}
              className="bg-transparent text-white focus:outline-none"
            >
              <option value="192.168.1.20">192.168.1.20 (Web-Server)</option>
              <option value="192.168.1.30">192.168.1.30 (App-Server)</option>
              <option value="192.168.1.40">192.168.1.40 (Core Database)</option>
            </select>
          </div>

          <div className="flex items-center gap-2 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800">
            <span className="text-slate-400">Horizon (k):</span>
            <input
              type="number"
              min="3"
              max="20"
              value={kSteps}
              onChange={(e) => setKSteps(Number(e.target.value))}
              className="w-12 bg-transparent text-white focus:outline-none"
            />
          </div>

          <button
            onClick={handleStartRollout}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition-all shadow-lg shadow-indigo-600/30 disabled:opacity-50"
          >
            <Play className="w-4 h-4 fill-current" /> {loading ? "Simulating..." : "Start Live Rollout"}
          </button>

          <button
            onClick={handleRunFidelity}
            disabled={fidelityLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold transition-all"
          >
            <Cpu className="w-4 h-4" /> {fidelityLoading ? "Evaluating..." : "Run Fidelity Benchmark"}
          </button>
        </div>
      </div>

      {/* Interactive Topology Graph & Side Telemetry Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Dynamic SVG Topology Graph */}
        <div className="lg:col-span-2 bg-slate-900/50 p-5 rounded-2xl border border-slate-800 backdrop-blur-md shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider font-heading flex items-center gap-2">
              <Cpu className="w-4 h-4 text-emerald-400" /> Dynamic Network Graph Topology State
            </h3>
            {activeFrame && (
              <span className="text-xs font-mono px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Rollout Step {activeFrame.step} of {rolloutData?.steps?.length || kSteps}
              </span>
            )}
          </div>

          {/* SVG Visual Graph */}
          <NetworkGraphSvg nodesData={activeFrame?.nodes} activeStep={activeFrame} />
        </div>

        {/* Right 1 Col: Telemetry Viewport */}
        <div className="bg-slate-900/50 p-5 rounded-2xl border border-slate-800 backdrop-blur-md shadow-xl space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-heading border-b border-slate-800 pb-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-indigo-400" /> Live Simulation Snapshot
          </h3>

          {activeFrame ? (
            <div className="space-y-4 font-mono text-xs">
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex justify-between items-center">
                <span className="text-slate-400">Target Host:</span>
                <span className="text-white font-bold">{activeFrame.target_hostname}</span>
              </div>

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex justify-between items-center">
                <span className="text-slate-400">Predicted MITRE Stage:</span>
                <span className="text-amber-400 font-bold">{activeFrame.predicted_stage}</span>
              </div>

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex justify-between items-center">
                <span className="text-slate-400">Stage Confidence:</span>
                <span className="text-emerald-400 font-bold">{(activeFrame.stage_confidence * 100).toFixed(1)}%</span>
              </div>

              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Infiltration Risk:</span>
                  <span className="text-rose-400 font-bold">{(activeFrame.infiltration_probability * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-rose-500 transition-all duration-300"
                    style={{ width: `${Math.min(activeFrame.infiltration_probability * 100, 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-16 text-center text-slate-500 text-xs font-mono">
              Click <strong>Start Live Rollout</strong> to trigger PyTorch WorldModel simulation.
            </div>
          )}
        </div>
      </div>

      {/* Empirical Fidelity Benchmark Results & Drift Curve */}
      {fidelityReport && (
        <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 backdrop-blur-md space-y-4 shadow-xl font-mono text-xs">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-heading flex items-center gap-2">
            <Cpu className="w-4 h-4 text-emerald-400" /> Digital Twin Fidelity & Horizon Drift Curve Benchmark
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-slate-400">State MSE:</span>
              <p className="text-lg font-bold text-indigo-400 mt-1">{fidelityReport.overall_state_mse?.toFixed(6)}</p>
            </div>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-slate-400">Stage Accuracy:</span>
              <p className="text-lg font-bold text-emerald-400 mt-1">{fidelityReport.stage_accuracy_percent}%</p>
            </div>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-slate-400">Infiltration MAE:</span>
              <p className="text-lg font-bold text-amber-400 mt-1">{fidelityReport.infiltration_prob_mae?.toFixed(4)}</p>
            </div>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-slate-400">Evaluated Sequences:</span>
              <p className="text-lg font-bold text-white mt-1">{fidelityReport.num_sequences_evaluated}</p>
            </div>
          </div>

          {/* Visual Step-by-step Horizon Drift Curve */}
          {fidelityReport.horizon_drift_curve_mse && (
            <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
              <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                <span className="text-xs text-slate-300 font-bold flex items-center gap-2">
                  <TrendingDown className="w-4 h-4 text-amber-400" /> Simulation Error Horizon Degradation Drift Curve
                </span>
                <span className="text-[10px] text-slate-500">MSE per step $k$</span>
              </div>
              <div className="grid grid-cols-5 sm:grid-cols-10 gap-2">
                {Object.entries(fidelityReport.horizon_drift_curve_mse).map(([stepKey, mseVal]) => (
                  <div key={stepKey} className="p-2 bg-slate-900 rounded border border-slate-800 text-center">
                    <span className="text-[10px] text-slate-400 block">{stepKey.replace("step_", "k=")}</span>
                    <span className="font-bold text-indigo-300 text-xs">{Number(mseVal).toFixed(4)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Trajectory Security Report */}
      {rolloutData?.narration && (
        <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 backdrop-blur-md space-y-3 shadow-xl">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-heading flex items-center gap-2">
            <FileText className="w-4 h-4 text-indigo-400" /> Model-Driven Trajectory Security Report
          </h3>
          <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-indigo-300 font-mono text-xs overflow-x-auto leading-relaxed">
            {rolloutData.narration}
          </pre>
        </div>
      )}
    </div>
  );
}

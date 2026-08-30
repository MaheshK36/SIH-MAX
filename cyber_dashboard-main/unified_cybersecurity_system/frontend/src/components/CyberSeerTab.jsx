import React, { useState } from "react";
import { Zap, ShieldAlert, Cpu, AlertTriangle, TrendingUp, CheckCircle2 } from "lucide-react";

export function CyberSeerTab() {
  const [forecastSteps, setForecastSteps] = useState(5);
  const [loading, setLoading] = useState(false);
  const [forecastData, setForecastData] = useState(null);

  const handleRunForecast = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/forecast/propagation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ steps: forecastSteps }),
      });
      const data = await res.json();
      setForecastData(data.analysis);
    } catch (e) {
      console.error("Forecast error:", e);
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
            <Zap className="w-5 h-5 text-indigo-400" /> CyberSeer Hybrid GNN + Transformer Attack Propagation
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Multi-phase GNN forecasting modeling attack blast radius, future attack surface expansion, and attack momentum.
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <div className="flex items-center gap-2 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800">
            <span className="text-slate-400">Forecast Horizon:</span>
            <input
              type="number"
              min="1"
              max="10"
              value={forecastSteps}
              onChange={(e) => setForecastSteps(Number(e.target.value))}
              className="w-12 bg-transparent text-white focus:outline-none"
            />
          </div>

          <button
            onClick={handleRunForecast}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition-all shadow-lg shadow-indigo-600/30 disabled:opacity-50"
          >
            <Zap className="w-4 h-4" /> {loading ? "Computing Forecast..." : "Run GNN Propagation Forecast"}
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md space-y-1">
          <span className="text-xs text-slate-400 font-mono">Blast Radius Impact</span>
          <p className="text-2xl font-bold text-rose-400">
            {forecastData ? `${forecastData.blast_radius_percent}%` : "0.0%"}
          </p>
          <p className="text-[10px] text-slate-500 font-mono">Target Network Scope</p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md space-y-1">
          <span className="text-xs text-slate-400 font-mono">Attack Momentum Score</span>
          <p className="text-2xl font-bold text-amber-400">
            {forecastData ? forecastData.attack_momentum : "0.00"}
          </p>
          <p className="text-[10px] text-slate-500 font-mono">Acceleration rate</p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md space-y-1">
          <span className="text-xs text-slate-400 font-mono">High Risk Nodes</span>
          <p className="text-2xl font-bold text-white">
            {forecastData ? forecastData.high_risk_nodes : 0}
          </p>
          <p className="text-[10px] text-slate-500 font-mono">Infiltration prob ≥ 50%</p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-md space-y-1">
          <span className="text-xs text-slate-400 font-mono">Total Monitored Nodes</span>
          <p className="text-2xl font-bold text-indigo-400">
            {forecastData ? forecastData.num_nodes : 6}
          </p>
          <p className="text-[10px] text-slate-500 font-mono">Topology devices</p>
        </div>
      </div>

      {/* Summary Recommendation Alert */}
      {forecastData && (
        <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 backdrop-blur-md flex items-center justify-between gap-4 font-mono text-xs">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0" />
            <span className="text-slate-200">{forecastData.summary_recommendation}</span>
          </div>
          <span className="px-3 py-1 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 font-bold shrink-0">
            RECOMMENDATION
          </span>
        </div>
      )}

      {/* Step-by-Step Propagation Grid */}
      {forecastData?.forecast_steps && (
        <div className="bg-slate-900/50 p-5 rounded-2xl border border-slate-800 backdrop-blur-md space-y-4 shadow-xl">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-heading flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-emerald-400" /> Multi-Step Propagation Window Forecast
          </h3>

          <div className="space-y-4 font-mono text-xs">
            {forecastData.forecast_steps.map((step) => (
              <div key={step.step} className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
                <div className="flex justify-between items-center border-b border-slate-800/80 pb-2">
                  <span className="font-bold text-indigo-400">Forecast Step {step.step}</span>
                  <span className="text-slate-400">
                    Network Avg Risk: <strong className="text-white">{(step.avg_network_risk * 100).toFixed(1)}%</strong>
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {step.hosts.map((h) => (
                    <div key={h.ip_address} className="p-2.5 bg-slate-900/80 rounded-lg border border-slate-800/80 flex justify-between items-center">
                      <div>
                        <p className="text-white font-bold">{h.hostname}</p>
                        <p className="text-[10px] text-slate-500">{h.ip_address}</p>
                      </div>
                      <span className={`font-bold ${h.status === "compromised" ? "text-rose-400" : h.status === "target" ? "text-amber-400" : "text-emerald-400"}`}>
                        {(h.risk_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

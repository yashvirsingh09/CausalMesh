"use client";

import React, { useState, useEffect } from "react";
import { Flame, RotateCcw, Play, ShieldAlert, Zap, Bot, Cpu } from "lucide-react";

interface IncidentTriggerProps {
  activeGraph: string;
  isTriggering: boolean;
  onTrigger: (scenario: string, mode: "autonomous" | "hitl", engine: "simulated" | "live_llm") => void;
  onReset: () => void;
}

const SCENARIOS = [
  {
    id: "db_pool_exhaustion",
    title: "DB Pool Starvation (PR-88)",
    description: "504 Gateway Timeout on /checkout caused by aggressive DB idle timeout PR",
    epicenter: "checkout-service",
    severity: "critical",
  },
  {
    id: "cache_eviction_storm",
    title: "Cart Cache Eviction Storm (PR-83)",
    description: "Redis eviction policy change causes sudden cart drop spikes under load",
    epicenter: "checkout-service",
    severity: "high",
  },
  {
    id: "canary_error_spike",
    title: "Canary Regression (PR-86)",
    description: "Model upgrade in recommendation-service causes inference latency spike",
    epicenter: "recommendation-service",
    severity: "medium",
  },
];

export default function IncidentTrigger({
  activeGraph,
  isTriggering,
  onTrigger,
  onReset,
}: IncidentTriggerProps) {
  const [selectedScenario, setSelectedScenario] = useState("db_pool_exhaustion");
  const [mode, setMode] = useState<"autonomous" | "hitl">("autonomous");
  const [engine, setEngine] = useState<"simulated" | "live_llm">("simulated");
  const [llmInfo, setLlmInfo] = useState<{ provider: string; model: string } | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((data) => {
        if (data.llm) {
          setLlmInfo(data.llm);
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className="bg-[#fdfcf9] border border-[#e8e2d8] rounded-xl p-2.5 shadow-[0_1px_4px_rgba(0,0,0,0.03)] space-y-2">
      {/* Top Controls Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#e8e2d8] pb-1.5">
        <div className="flex items-center space-x-1.5">
          <Flame className="w-3.5 h-3.5 text-rose-600" />
          <h2 className="font-bold text-[11px] uppercase tracking-wide text-stone-800">
            Swarm Orchestration
          </h2>
        </div>

        {/* Governance & Engine Pill Controls */}
        <div className="flex items-center space-x-2 text-[10px]">
          {/* Governance Mode */}
          <div className="flex items-center space-x-0.5 bg-[#ede7dd] p-0.5 rounded-md">
            <button
              onClick={() => setMode("autonomous")}
              className={`px-2 py-0.5 rounded text-[10px] font-semibold flex items-center gap-1 transition ${
                mode === "autonomous"
                  ? "bg-white text-indigo-700 shadow-sm border border-[#e8e2d8]"
                  : "text-stone-600 hover:text-stone-900"
              }`}
            >
              <Zap className="w-2.5 h-2.5 text-amber-500" /> Auto
            </button>
            <button
              onClick={() => setMode("hitl")}
              className={`px-2 py-0.5 rounded text-[10px] font-semibold flex items-center gap-1 transition ${
                mode === "hitl"
                  ? "bg-white text-amber-700 shadow-sm border border-[#e8e2d8]"
                  : "text-stone-600 hover:text-stone-900"
              }`}
            >
              <ShieldAlert className="w-2.5 h-2.5 text-amber-600" /> HITL
            </button>
          </div>

          {/* Swarm Engine */}
          <div className="flex items-center space-x-0.5 bg-[#ede7dd] p-0.5 rounded-md">
            <button
              onClick={() => setEngine("simulated")}
              className={`px-2 py-0.5 rounded text-[10px] font-semibold flex items-center gap-1 transition ${
                engine === "simulated"
                  ? "bg-white text-indigo-700 shadow-sm border border-slate-200"
                  : "text-slate-600 hover:text-slate-900"
              }`}
              title="Deterministic fast graph reasoning simulation"
            >
              <Cpu className="w-2.5 h-2.5 text-indigo-600" /> Fast Sim
            </button>
            <button
              onClick={() => setEngine("live_llm")}
              className={`px-2 py-0.5 rounded text-[10px] font-semibold flex items-center gap-1 transition ${
                engine === "live_llm"
                  ? "bg-white text-purple-700 shadow-sm border border-slate-200"
                  : "text-slate-600 hover:text-slate-900"
              }`}
              title={`Live LLM agent tool-call loops via ${llmInfo?.provider || "provider"}`}
            >
              <Bot className="w-2.5 h-2.5 text-purple-600" /> Live LLM
            </button>
          </div>

          <button
            onClick={onReset}
            className="flex items-center gap-1 text-[10px] font-medium text-stone-600 hover:text-stone-900 px-2 py-0.5 rounded-md bg-[#f5f1ea] hover:bg-[#ede7dd] border border-[#e8e2d8] transition"
            title="Reset all service states to healthy"
          >
            <RotateCcw className="w-2.5 h-2.5 text-stone-500" /> Reset
          </button>
        </div>
      </div>

      {/* Scenario Selection */}
      <div className="space-y-1.5">
        <label className="text-[11px] text-stone-600 font-semibold uppercase tracking-wider">Select Failure Scenario:</label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {SCENARIOS.map((sc) => (
            <div
              key={sc.id}
              onClick={() => setSelectedScenario(sc.id)}
              className={`p-2 rounded-lg border text-xs cursor-pointer transition select-none flex flex-col justify-between ${
                selectedScenario === sc.id
                  ? "bg-indigo-50/80 border-indigo-500 shadow-sm ring-1 ring-indigo-500/30"
                  : "bg-[#f7f4ee] hover:bg-[#ede7dd] border-[#e8e2d8] text-stone-700"
              }`}
            >
              <div className="flex items-center justify-between gap-1">
                <span className={`font-bold text-[11px] truncate ${selectedScenario === sc.id ? "text-indigo-950" : "text-stone-800"}`}>
                  {sc.title.split("(")[0]}
                </span>
                <span
                  className={`text-[8.5px] uppercase px-1 py-0.5 rounded font-bold shrink-0 ${
                    sc.severity === "critical"
                      ? "bg-rose-100 text-rose-800 border border-rose-300"
                      : "bg-amber-100 text-amber-800 border border-amber-300"
                  }`}
                >
                  {sc.severity}
                </span>
              </div>
              <p className="text-[9.5px] text-stone-500 mt-1 line-clamp-1 leading-snug">{sc.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Fire Incident CTA */}
      <button
        disabled={isTriggering}
        onClick={() => onTrigger(selectedScenario, mode, engine)}
        className={`w-full py-2.5 px-4 rounded-lg font-bold text-xs flex items-center justify-center space-x-2 transition shadow-sm ${
          isTriggering
            ? "bg-stone-300 text-stone-500 cursor-not-allowed border border-stone-300"
            : "bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-200 active:scale-[0.98]"
        }`}
      >
        {isTriggering ? (
          <>
            <span className="w-3.5 h-3.5 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
            <span>
              Swarm Resolving ({engine === "live_llm" ? "Live LLM" : "Fast Sim"} • {mode === "hitl" ? "HITL" : "Auto"})...
            </span>
          </>
        ) : (
          <>
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Trigger Incident & Activate Tri-Agent Swarm</span>
          </>
        )}
      </button>
    </div>
  );
}

"use client";

import React, { useEffect, useState } from "react";
import { Activity, Database, Layers, ShieldCheck } from "lucide-react";

interface HeaderProps {
  activeGraph: string;
  onSwitchGraph: (graph: string) => void;
}

export default function Header({ activeGraph, onSwitchGraph }: HeaderProps) {
  const [dbStatus, setDbStatus] = useState<"online" | "in_memory">("in_memory");

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((data) => {
        if (data.falkordb?.connected) {
          setDbStatus("online");
        } else {
          setDbStatus("in_memory");
        }
      })
      .catch(() => setDbStatus("in_memory"));
  }, []);

  return (
    <header className="h-16 border-b border-[#e7e2d9] bg-[#fdfcf9] px-6 flex items-center justify-between shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center shadow-sm">
            <Activity className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-stone-900 tracking-tight">
              CausalMesh
            </h1>
            <p className="text-[10px] text-stone-500 font-medium">
              Autonomous SRE & Incident Memory Mesh
            </p>
          </div>
        </div>

        <div className="hidden md:flex items-center space-x-2 pl-4 border-l border-[#e7e2d9]">
          <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-purple-50 border border-purple-200 text-purple-700">
            FalkorDB Graph Hacks 2026
          </span>
          <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#f5f1ea] border border-[#e8e2d8] text-stone-700 flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-indigo-600" /> All 3 Tracks
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {/* Multigraph Environment Selector */}
        <div className="flex items-center bg-slate-100 border border-slate-200 rounded-lg p-0.5 text-xs">
          <span className="text-slate-500 px-2 flex items-center gap-1 font-medium text-[11px]">
            <Layers className="w-3.5 h-3.5 text-indigo-600" /> Graph:
          </span>
          <button
            onClick={() => onSwitchGraph("causalmesh_prod")}
            className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition ${
              activeGraph === "causalmesh_prod"
                ? "bg-white text-indigo-700 shadow-sm border border-slate-200/80"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            prod
          </button>
          <button
            onClick={() => onSwitchGraph("causalmesh_staging")}
            className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition ${
              activeGraph === "causalmesh_staging"
                ? "bg-white text-indigo-700 shadow-sm border border-slate-200/80"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            staging
          </button>
        </div>

        {/* FalkorDB Connection Badge */}
        <div className="flex items-center space-x-2 px-2.5 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
          <Database className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-slate-600 font-medium">FalkorDB:</span>
          {dbStatus === "online" ? (
            <span className="flex items-center gap-1.5 text-emerald-700 font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> Live Server
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-amber-700 font-semibold" title="In-Memory Graph Engine Active">
              <span className="w-2 h-2 rounded-full bg-amber-500" /> In-Memory Mode
            </span>
          )}
        </div>
      </div>
    </header>
  );
}

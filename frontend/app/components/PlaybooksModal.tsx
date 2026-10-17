"use client";

import React, { useEffect, useState } from "react";
import { X, Wrench, ShieldCheck, ArrowRight, Play, Database, CheckCircle2 } from "lucide-react";

interface Step {
  step_id: string;
  name: string;
  tool: string;
  params: string | Record<string, any>;
  order: number;
}

interface Playbook {
  trigger_pattern: string;
  name: string;
  description: string;
  success_rate: number;
  step_count: number;
  steps: Step[];
}

interface PlaybooksModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeGraph: string;
}

export default function PlaybooksModal({ isOpen, onClose, activeGraph }: PlaybooksModalProps) {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [selectedPlaybook, setSelectedPlaybook] = useState<Playbook | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    fetch(`/api/graph/playbooks?graph_name=${activeGraph}`)
      .then((r) => r.json())
      .then((data) => {
        setPlaybooks(data);
        if (data.length > 0) setSelectedPlaybook(data[0]);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch playbooks:", err);
        setLoading(false);
      });
  }, [isOpen, activeGraph]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-4xl bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[88vh]">
        {/* Header */}
        <div className="h-14 px-6 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700">
              <Wrench className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-900">
                  Procedural Memory Playbooks
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Automated Runbooks
                </span>
              </div>
              <p className="text-[10px] text-slate-500">
                Executable graph workflows persisted in FalkorDB: <code className="text-indigo-600 font-mono">{"(:Procedure)-[:STEP]->(:Action)-[:NEXT]->(:Action)"}</code>
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left Column: Playbook List */}
          <div className="w-1/3 border-r border-slate-200 bg-slate-50/50 p-4 space-y-2.5 overflow-y-auto">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              Stored Playbooks ({playbooks.length})
            </span>

            {loading ? (
              <div className="py-8 text-center text-xs text-slate-400">Loading playbooks...</div>
            ) : (
              playbooks.map((pb) => (
                <div
                  key={pb.trigger_pattern}
                  onClick={() => setSelectedPlaybook(pb)}
                  className={`p-3 rounded-xl border text-xs cursor-pointer transition ${
                    selectedPlaybook?.trigger_pattern === pb.trigger_pattern
                      ? "bg-white border-indigo-500 shadow-sm text-slate-900 ring-1 ring-indigo-500/20"
                      : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between font-bold text-slate-900">
                    <span className="line-clamp-1">{pb.name}</span>
                    <span className="text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                      {(pb.success_rate * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 mt-1 text-[10px] text-slate-500">
                    <span className="font-mono bg-slate-100 px-1 rounded">{pb.trigger_pattern}</span>
                    <span>• {pb.step_count} steps</span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Right Column: Selected Playbook Workflow */}
          <div className="flex-1 p-6 overflow-y-auto space-y-5 bg-white">
            {selectedPlaybook ? (
              <>
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold text-slate-900 font-mono">
                      {selectedPlaybook.name}
                    </h3>
                    <div className="flex items-center gap-1.5 text-xs text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>Historical Success: {(selectedPlaybook.success_rate * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {selectedPlaybook.description}
                  </p>
                  <div className="pt-1 flex items-center gap-2 text-xs text-slate-500">
                    <span className="text-[11px] font-semibold text-slate-400">Trigger Pattern:</span>
                    <code className="text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded text-[11px] font-mono border border-indigo-100">
                      {selectedPlaybook.trigger_pattern}
                    </code>
                  </div>
                </div>

                {/* Ordered Step Sequence Graph */}
                <div className="space-y-3">
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
                    <Play className="w-3 h-3 text-indigo-600" />
                    Executable Procedural Step Chain
                  </span>

                  <div className="space-y-2.5">
                    {selectedPlaybook.steps.map((step, idx) => (
                      <div
                        key={step.step_id || idx}
                        className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-slate-50 transition space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2.5">
                            <span className="w-5 h-5 rounded-full bg-indigo-600 text-white font-bold text-[10px] flex items-center justify-center">
                              {step.order}
                            </span>
                            <span className="font-bold text-xs text-slate-900 font-mono">
                              {step.name}
                            </span>
                          </div>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white text-indigo-700 border border-slate-200 font-semibold">
                            {step.tool}
                          </span>
                        </div>

                        <div className="pl-7 text-[11px] text-slate-600 space-y-1">
                          <div className="flex items-start gap-1.5">
                            <span className="text-slate-400 font-medium">Parameters:</span>
                            <code className="bg-white px-2 py-0.5 rounded text-[10px] font-mono text-slate-700 border border-slate-200">
                              {typeof step.params === "string" ? step.params : JSON.stringify(step.params)}
                            </code>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* OpenCypher Traversal Box */}
                <div className="p-3.5 rounded-xl bg-slate-900 text-slate-200 text-xs space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <Database className="w-3 h-3 text-purple-400" /> OpenCypher Procedural Traversal
                    </span>
                    <span className="text-purple-400 text-[10px]">FalkorDB GraphBLAS</span>
                  </div>
                  <pre className="font-mono text-[10px] text-indigo-300 overflow-x-auto whitespace-pre">
{`MATCH (p:Procedure {trigger_pattern: '${selectedPlaybook.trigger_pattern}'})-[:STEP]->(first:Action)
MATCH path = (first)-[:NEXT*0..10]->(step:Action)
RETURN step.name, step.tool, step.params, step.order
ORDER BY step.order ASC`}
                  </pre>
                </div>
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                Select a playbook to inspect its workflow graph.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

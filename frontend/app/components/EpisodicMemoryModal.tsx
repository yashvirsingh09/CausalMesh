"use client";

import React, { useState } from "react";
import { X, History, Clock, GitPullRequest, CheckCircle2, Database, Search } from "lucide-react";

interface Episode {
  incident_id: string;
  alert_name: string;
  root_cause: string;
  root_cause_pr_id?: string;
  mttr_seconds: number;
  status: string;
  timestamp: string;
  involved_services?: string[];
}

interface EpisodicMemoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  episodes: Episode[];
  activeGraph: string;
}

export default function EpisodicMemoryModal({
  isOpen,
  onClose,
  episodes,
  activeGraph,
}: EpisodicMemoryModalProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedEpisode, setSelectedEpisode] = useState<Episode | null>(null);

  if (!isOpen) return null;

  const filteredEpisodes = episodes.filter(
    (ep) =>
      ep.incident_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ep.alert_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ep.root_cause.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (ep.root_cause_pr_id && ep.root_cause_pr_id.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-4xl bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[88vh]">
        {/* Header */}
        <div className="h-14 px-6 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-blue-50 border border-blue-200 text-blue-700">
              <History className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-900">
                  FalkorDB Episodic Memory Vault
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                  Incident History Vault
                </span>
              </div>
              <p className="text-[10px] text-slate-500">
                Persistent incident history in <code className="text-indigo-600 font-mono">{activeGraph}</code>: Agents query past episodes by symptom matching.
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
          {/* Left Column: Episodes List */}
          <div className="w-2/5 border-r border-slate-200 bg-slate-50/50 p-4 space-y-3 flex flex-col">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search episodes by symptom, PR, ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="flex-1 space-y-2 overflow-y-auto">
              {filteredEpisodes.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-400">
                  No episodes found matching search.
                </div>
              ) : (
                filteredEpisodes.map((ep) => (
                  <div
                    key={ep.incident_id}
                    onClick={() => setSelectedEpisode(ep)}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition ${
                      selectedEpisode?.incident_id === ep.incident_id
                        ? "bg-white border-blue-500 shadow-sm ring-1 ring-blue-500/20"
                        : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"
                    }`}
                  >
                    <div className="flex items-center justify-between font-bold text-slate-900">
                      <span className="font-mono text-[11px] text-indigo-700">{ep.incident_id}</span>
                      <span className="flex items-center gap-1 text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                        <Clock className="w-3 h-3" /> {ep.mttr_seconds}s
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-800 font-semibold mt-1 line-clamp-1">
                      {ep.alert_name}
                    </p>
                    <p className="text-[10px] text-slate-500 mt-0.5 line-clamp-1">
                      {ep.root_cause}
                    </p>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Right Column: Episode Inspector */}
          <div className="flex-1 p-6 overflow-y-auto space-y-5 bg-white">
            {selectedEpisode ? (
              <>
                <div className="space-y-2 border-b border-slate-100 pb-4">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-bold text-indigo-700">
                      {selectedEpisode.incident_id}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Resolved
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900">
                    {selectedEpisode.alert_name}
                  </h3>
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-400" /> MTTR:{" "}
                      <strong className="text-emerald-700 font-bold">{selectedEpisode.mttr_seconds}s</strong>
                    </span>
                    {selectedEpisode.root_cause_pr_id && (
                      <span className="flex items-center gap-1">
                        <GitPullRequest className="w-3.5 h-3.5 text-rose-500" /> Root-Cause PR:{" "}
                        <strong className="text-rose-700 font-bold">{selectedEpisode.root_cause_pr_id}</strong>
                      </span>
                    )}
                  </div>
                </div>

                {/* Root Cause Details */}
                <div className="space-y-1.5">
                  <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                    Root Cause Diagnosis & Attribution
                  </span>
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 leading-relaxed font-sans">
                    {selectedEpisode.root_cause}
                  </div>
                </div>

                {/* Involved Services */}
                {selectedEpisode.involved_services && selectedEpisode.involved_services.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                      Involved Services Subgraph
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedEpisode.involved_services.map((svc) => (
                        <span
                          key={svc}
                          className="px-2 py-1 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-mono font-medium"
                        >
                          {svc}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* OpenCypher Query Box */}
                <div className="p-3.5 rounded-xl bg-slate-900 text-slate-200 text-xs space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span className="flex items-center gap-1">
                      <Database className="w-3 h-3 text-purple-400" /> FalkorDB Episodic Memory Query
                    </span>
                    <span className="text-purple-400 text-[10px]">OpenCypher</span>
                  </div>
                  <pre className="font-mono text-[10px] text-indigo-300 overflow-x-auto whitespace-pre">
{`MATCH (ep:Episode {incident_id: '${selectedEpisode.incident_id}'})
OPTIONAL MATCH (ep)-[:INVOLVED]->(svc:Service)
RETURN ep.incident_id, ep.alert_name, ep.root_cause, ep.mttr_seconds, collect(svc.name) AS services`}
                  </pre>
                </div>
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                Select an incident episode to inspect its resolution memory.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

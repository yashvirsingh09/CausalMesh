"use client";

import React, { useState } from "react";
import {
  X,
  FileText,
  Copy,
  Check,
  Clock,
  GitPullRequest,
  User,
  ShieldCheck,
  AlertTriangle,
  Code2,
  Workflow,
  CheckCircle2,
} from "lucide-react";

interface PostmortemModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: {
    incident_id: string;
    content: string;
    mttr_seconds: number;
    root_cause_pr?: string;
    author?: string;
  } | null;
}

export default function PostmortemModal({ isOpen, onClose, data }: PostmortemModalProps) {
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<"document" | "raw">("document");

  if (!isOpen || !data) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(data.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-stone-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-[#fdfcf9] border border-[#e8e2d8] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Document Header */}
        <div className="h-14 px-6 border-b border-[#e8e2d8] flex items-center justify-between bg-[#f7f4ee]">
          <div className="flex items-center space-x-3">
            <div className="p-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-stone-900">
                  Incident Postmortem Report
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#ede7dd] text-stone-700 font-semibold border border-[#e8e2d8]">
                  {data.incident_id}
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
                  RESOLVED
                </span>
              </div>
              <p className="text-[10px] text-stone-500">
                Generated from FalkorDB causal dependency topology & Company Brain knowledge graph
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <div className="flex items-center bg-[#ede7dd] p-0.5 rounded-lg text-[11px] font-medium border border-[#e8e2d8]">
              <button
                onClick={() => setViewMode("document")}
                className={`px-2.5 py-1 rounded transition ${
                  viewMode === "document"
                    ? "bg-white text-stone-900 font-semibold shadow-sm"
                    : "text-stone-600 hover:text-stone-900"
                }`}
              >
                Document
              </button>
              <button
                onClick={() => setViewMode("raw")}
                className={`px-2.5 py-1 rounded transition ${
                  viewMode === "raw"
                    ? "bg-white text-stone-900 font-semibold shadow-sm"
                    : "text-stone-600 hover:text-stone-900"
                }`}
              >
                Markdown
              </button>
            </div>

            <button
              onClick={handleCopy}
              className="flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-[#f5f1ea] hover:bg-[#ede7dd] border border-[#e8e2d8] text-stone-700 text-xs font-semibold transition"
              title="Copy markdown text to clipboard"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-stone-500" />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-stone-400 hover:text-stone-700 hover:bg-[#ede7dd] transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Key Metrics Bar */}
        <div className="px-6 py-2.5 bg-[#fbf9f5] border-b border-[#e8e2d8] grid grid-cols-3 gap-4 text-xs">
          <div className="flex items-center space-x-2.5">
            <div className="p-1 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
              <Clock className="w-3.5 h-3.5" />
            </div>
            <div>
              <span className="text-[10px] text-stone-500 uppercase font-semibold">Resolution MTTR</span>
              <p className="font-bold text-emerald-800 text-sm">{data.mttr_seconds} Seconds</p>
            </div>
          </div>
          <div className="flex items-center space-x-2.5">
            <div className="p-1 rounded-md bg-rose-50 text-rose-700 border border-rose-200">
              <GitPullRequest className="w-3.5 h-3.5" />
            </div>
            <div>
              <span className="text-[10px] text-stone-500 uppercase font-semibold">Root Cause PR</span>
              <p className="font-bold text-stone-900 text-sm font-mono">{data.root_cause_pr || "PR-88"}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2.5">
            <div className="p-1 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200">
              <User className="w-3.5 h-3.5" />
            </div>
            <div>
              <span className="text-[10px] text-stone-500 uppercase font-semibold">Attributed Author</span>
              <p className="font-bold text-stone-900 text-sm">{data.author || "Dave Kim"}</p>
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 p-6 overflow-y-auto text-xs leading-relaxed text-stone-800 bg-[#fdfcf9] space-y-5">
          {viewMode === "document" ? (
            <div className="space-y-5">
              {/* Executive Summary */}
              <section className="space-y-1.5">
                <h3 className="text-xs font-bold uppercase tracking-wider text-stone-600">
                  1. Executive Summary
                </h3>
                <div className="p-3.5 rounded-xl bg-[#f7f4ee] border border-[#e8e2d8] text-stone-800 text-[12px] leading-relaxed">
                  Prometheus reported an active 504 Gateway Timeout regression on the checkout flow.
                  The autonomous tri-agent swarm inspected the connected microservice topology in FalkorDB,
                  computed downstream blast radius, correlated recent Git commits in Company Brain,
                  and successfully applied the verified rollback patch in {data.mttr_seconds} seconds.
                </div>
              </section>

              {/* Root Cause & Code Attribution */}
              <section className="space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-stone-600">
                  2. Root Cause Analysis & Code Attribution (Company Brain)
                </h3>
                <div className="p-4 rounded-xl bg-white border border-[#e8e2d8] space-y-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
                  <div className="grid grid-cols-2 gap-3 text-[11.5px]">
                    <div>
                      <span className="text-stone-500 font-medium">Breaking Pull Request:</span>
                      <p className="font-bold text-stone-900 font-mono mt-0.5">{data.root_cause_pr || "PR-88"} (Reduce DB idle timeout)</p>
                    </div>
                    <div>
                      <span className="text-stone-500 font-medium">Author & Slack:</span>
                      <p className="font-bold text-stone-900 mt-0.5">{data.author || "Dave Kim"} <span className="text-stone-500 font-mono font-normal">(@dave)</span></p>
                    </div>
                    <div>
                      <span className="text-stone-500 font-medium">Code Reviewer:</span>
                      <p className="font-bold text-stone-900 mt-0.5">Alice Mehta <span className="text-stone-500 font-mono font-normal">(@alice)</span></p>
                    </div>
                    <div>
                      <span className="text-stone-500 font-medium">Impact Mechanism:</span>
                      <p className="font-semibold text-rose-800 mt-0.5">Connection pool exhaustion under peak concurrency</p>
                    </div>
                  </div>

                  <div className="p-2.5 rounded-lg bg-stone-900 text-stone-100 font-mono text-[11px] space-y-1">
                    <span className="text-stone-400 text-[10px] uppercase font-bold tracking-wider">Configuration Diff Preview</span>
                    <p className="text-rose-400">- db_pool.idle_timeout_seconds = 30</p>
                    <p className="text-emerald-400">+ db_pool.idle_timeout_seconds = 2  # aggressive timeout thrashing</p>
                  </div>
                </div>
              </section>

              {/* Blast Radius & Topology Impact */}
              <section className="space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-stone-600">
                  3. Topological Propagation & Blast Radius (Connected Data)
                </h3>
                <div className="p-3.5 rounded-xl bg-white border border-[#e8e2d8] space-y-2 text-[11.5px]">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-stone-500 font-medium">Causal Chain:</span>
                    <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 font-mono text-[11px] font-bold">
                      checkout-service
                    </span>
                    <span className="text-stone-400">→</span>
                    <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 font-mono text-[11px] font-semibold">
                      inventory-service
                    </span>
                    <span className="text-stone-400">→</span>
                    <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 font-mono text-[11px] font-bold">
                      inventory-postgres
                    </span>
                  </div>
                  <p className="text-stone-600 text-[11px] pt-1">
                    FalkorDB shortestPath algorithm isolated the single point of failure (SPOF) to <strong className="text-stone-900">inventory-postgres</strong> across 2 transitive hops.
                  </p>
                </div>
              </section>

              {/* Remediation & Corrective Actions */}
              <section className="space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-stone-600">
                  4. Corrective Remediation (Procedural Memory Playbook)
                </h3>
                <div className="rounded-xl border border-[#e8e2d8] overflow-hidden">
                  <table className="w-full text-left text-[11px]">
                    <thead className="bg-[#f7f4ee] border-b border-[#e8e2d8] text-stone-600 font-bold uppercase tracking-wider">
                      <tr>
                        <th className="px-3.5 py-2">Step</th>
                        <th className="px-3.5 py-2">Action</th>
                        <th className="px-3.5 py-2">MCP Tool</th>
                        <th className="px-3.5 py-2">Result</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#e8e2d8] bg-white">
                      <tr>
                        <td className="px-3.5 py-2 font-mono text-stone-500">01</td>
                        <td className="px-3.5 py-2 font-medium text-stone-800">Rollback idle timeout config</td>
                        <td className="px-3.5 py-2 font-mono text-indigo-700">mcp_infra:patch_config</td>
                        <td className="px-3.5 py-2 text-emerald-700 font-semibold">Completed</td>
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 font-mono text-stone-500">02</td>
                        <td className="px-3.5 py-2 font-medium text-stone-800">Execute rolling restart</td>
                        <td className="px-3.5 py-2 font-mono text-indigo-700">mcp_infra:rollout_restart</td>
                        <td className="px-3.5 py-2 text-emerald-700 font-semibold">Completed</td>
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 font-mono text-stone-500">03</td>
                        <td className="px-3.5 py-2 font-medium text-stone-800">Verify health & error rates</td>
                        <td className="px-3.5 py-2 font-mono text-indigo-700">mcp_metrics:error_rate</td>
                        <td className="px-3.5 py-2 text-emerald-700 font-semibold">Verified Healthy</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              {/* Preventative Follow-Up Actions */}
              <section className="space-y-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-stone-600">
                  5. Action Items & Future Prevention
                </h3>
                <div className="p-3.5 rounded-xl bg-[#f7f4ee] border border-[#e8e2d8] space-y-2 text-[11.5px]">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                    <span className="text-stone-800">
                      <strong>CI Pipeline Guardrail:</strong> Add automated synthetic connection pool saturation test before merging Helm or DB config PRs.
                    </span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                    <span className="text-stone-800">
                      <strong>Helm Configuration Floor:</strong> Enforce a minimum database connection pool size floor of 50 in staging and production.
                    </span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 shrink-0" />
                    <span className="text-stone-800">
                      <strong>FalkorDB Episodic Memory:</strong> Resolution graph node recorded with incident ID <code className="font-mono text-stone-900 bg-white px-1 py-0.5 rounded border border-[#e8e2d8]">{data.incident_id}</code> for sub-second recognition on future occurrences.
                    </span>
                  </div>
                </div>
              </section>
            </div>
          ) : (
            <pre className="whitespace-pre-wrap font-mono text-[11px] text-stone-800 bg-[#f7f4ee] p-4 rounded-xl border border-[#e8e2d8] leading-relaxed overflow-x-auto">
              {data.content}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}

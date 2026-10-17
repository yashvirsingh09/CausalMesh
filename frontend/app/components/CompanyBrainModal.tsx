"use client";

import React, { useEffect, useState } from "react";
import {
  X,
  Brain,
  Users,
  Ticket,
  MessageSquare,
  BookOpen,
  GitPullRequest,
  ExternalLink,
  Search,
  Database,
  Shield,
  Layers,
} from "lucide-react";

interface Contributor {
  engineer: string;
  slack: string;
  role: string;
  contribution_count: number;
}

interface TicketItem {
  id: string;
  title: string;
  pr_id: string;
  service: string;
  priority: string;
  status: string;
}

interface SlackItem {
  id: string;
  channel: string;
  author: string;
  service: string;
  pr_id?: string | null;
  text: string;
  timestamp: string;
}

interface DocItem {
  id: string;
  title: string;
  service: string;
  url: string;
  category: string;
  summary: string;
}

interface CompanyBrainData {
  service: string;
  tickets: TicketItem[];
  slack_messages: SlackItem[];
  docs: DocItem[];
  contributors: Contributor[];
}

interface CompanyBrainModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeGraph: string;
  initialService?: string;
}

export default function CompanyBrainModal({
  isOpen,
  onClose,
  activeGraph,
  initialService = "",
}: CompanyBrainModalProps) {
  const [selectedService, setSelectedService] = useState(initialService);
  const [activeTab, setActiveTab] = useState<"directory" | "tickets" | "slack" | "docs">("directory");
  const [data, setData] = useState<CompanyBrainData | null>(null);
  const [loading, setLoading] = useState(true);
  const [servicesList, setServicesList] = useState<string[]>([]);

  // Update selectedService when initialService prop changes
  useEffect(() => {
    if (initialService) {
      setSelectedService(initialService);
    }
  }, [initialService]);

  // Fetch list of services for filter dropdown
  useEffect(() => {
    if (!isOpen) return;
    fetch(`/api/graph/services?graph_name=${activeGraph}`)
      .then((r) => r.json())
      .then((services: Array<{ name: string }>) => {
        setServicesList(services.map((s) => s.name).sort());
      })
      .catch((err) => console.error("Failed to fetch services:", err));
  }, [isOpen, activeGraph]);

  // Fetch company brain data for the selected service or all services
  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    const queryParam = selectedService ? `?service_name=${encodeURIComponent(selectedService)}&graph_name=${activeGraph}` : `?graph_name=${activeGraph}`;
    fetch(`/api/graph/company-brain${queryParam}`)
      .then((r) => r.json())
      .then((res: CompanyBrainData) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch company brain:", err);
        setLoading(false);
      });
  }, [isOpen, selectedService, activeGraph]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-5xl bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="h-16 px-6 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-900">
                  Company Brain & Knowledge Graph
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                  Context Engine
                </span>
              </div>
              <p className="text-[10px] text-slate-500">
                Connected graph of Engineers, Jira Tickets, Slack Discussions, Runbooks, and Git PRs in FalkorDB
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Service Filter Dropdown */}
            <div className="flex items-center gap-2 bg-white px-2.5 py-1 rounded-lg border border-slate-200 text-xs shadow-sm">
              <Search className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={selectedService}
                onChange={(e) => setSelectedService(e.target.value)}
                className="bg-transparent font-medium text-slate-700 focus:outline-none text-xs cursor-pointer"
              >
                <option value="">All Services (Company-Wide)</option>
                {servicesList.map((svc) => (
                  <option key={svc} value={svc}>
                    {svc}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 border-b border-slate-200 bg-white flex items-center gap-6 text-xs font-medium">
          <button
            onClick={() => setActiveTab("directory")}
            className={`py-3 flex items-center gap-1.5 border-b-2 transition ${
              activeTab === "directory"
                ? "border-indigo-600 text-indigo-600 font-bold"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <Users className="w-4 h-4" />
            <span>"Who Knows What" Directory</span>
            {data?.contributors && (
              <span className="px-1.5 py-0.2 rounded-full bg-slate-100 text-[10px] text-slate-600">
                {data.contributors.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("tickets")}
            className={`py-3 flex items-center gap-1.5 border-b-2 transition ${
              activeTab === "tickets"
                ? "border-indigo-600 text-indigo-600 font-bold"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <Ticket className="w-4 h-4" />
            <span>Jira Tickets</span>
            {data?.tickets && (
              <span className="px-1.5 py-0.2 rounded-full bg-slate-100 text-[10px] text-slate-600">
                {data.tickets.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("slack")}
            className={`py-3 flex items-center gap-1.5 border-b-2 transition ${
              activeTab === "slack"
                ? "border-indigo-600 text-indigo-600 font-bold"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span>Slack Discussions</span>
            {data?.slack_messages && (
              <span className="px-1.5 py-0.2 rounded-full bg-slate-100 text-[10px] text-slate-600">
                {data.slack_messages.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("docs")}
            className={`py-3 flex items-center gap-1.5 border-b-2 transition ${
              activeTab === "docs"
                ? "border-indigo-600 text-indigo-600 font-bold"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span>Runbooks & Architecture Docs</span>
            {data?.docs && (
              <span className="px-1.5 py-0.2 rounded-full bg-slate-100 text-[10px] text-slate-600">
                {data.docs.length}
              </span>
            )}
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 p-6 overflow-y-auto bg-slate-50/50">
          {loading ? (
            <div className="py-16 text-center text-xs text-slate-400">Loading connected company knowledge...</div>
          ) : (
            <>
              {/* Tab 1: Who Knows What Directory */}
              {activeTab === "directory" && (
                <div className="space-y-4">
                  <div className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-sm flex items-start justify-between">
                    <div>
                      <h3 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                        <Users className="w-4 h-4 text-indigo-600" />
                        Domain Knowledge Attribution (PR Authors + Code Ownership)
                      </h3>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        {selectedService
                          ? `Engineers who modified or own '${selectedService}', ordered by direct graph contributions.`
                          : "Company-wide engineering leads and domain specialists tracked in the graph."}
                      </p>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100">
                      MATCH (e:Engineer)-[:AUTHORED]-&gt;(:PR)
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {data?.contributors && data.contributors.length > 0 ? (
                      data.contributors.map((c, i) => (
                        <div
                          key={i}
                          className="p-4 rounded-xl border border-slate-200 bg-white hover:border-indigo-300 transition shadow-sm space-y-2.5"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <div className="w-8 h-8 rounded-full bg-indigo-100 border border-indigo-200 text-indigo-700 font-bold text-xs flex items-center justify-center">
                                {c.engineer
                                  .split(" ")
                                  .map((n) => n[0])
                                  .join("")}
                              </div>
                              <div>
                                <h4 className="font-bold text-xs text-slate-900">{c.engineer}</h4>
                                <span className="text-[10px] text-slate-500">{c.role}</span>
                              </div>
                            </div>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
                              {c.contribution_count} PRs / Ownership
                            </span>
                          </div>

                          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-600">
                            <span className="font-mono text-indigo-600 font-semibold">{c.slack}</span>
                            <span className="text-[10px] text-slate-400">Direct Slack Reachable</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="col-span-2 py-10 text-center text-xs text-slate-400">
                        Select a specific service from the dropdown above to run the Hackathon "Who Knows What" Cypher traversal.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Tab 2: Jira Tickets */}
              {activeTab === "tickets" && (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 gap-2.5">
                    {data?.tickets && data.tickets.length > 0 ? (
                      data.tickets.map((t) => (
                        <div
                          key={t.id}
                          className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition shadow-sm flex items-start justify-between"
                        >
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs font-bold text-slate-900">{t.id}</span>
                              <span
                                className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                                  t.priority === "P1"
                                    ? "bg-rose-50 text-rose-700 border border-rose-200"
                                    : t.priority === "P2"
                                    ? "bg-amber-50 text-amber-700 border border-amber-200"
                                    : "bg-slate-100 text-slate-600 border border-slate-200"
                                }`}
                              >
                                {t.priority}
                              </span>
                              <span className="text-[10px] font-mono bg-slate-100 px-1.5 py-0.2 rounded text-slate-600">
                                {t.service}
                              </span>
                            </div>
                            <p className="text-xs text-slate-700 font-medium">{t.title}</p>
                          </div>

                          <div className="flex items-center gap-2 text-right">
                            <div className="text-[10px] font-mono text-slate-500">
                              Linked PR: <span className="font-bold text-indigo-600">{t.pr_id}</span>
                            </div>
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase">
                              {t.status}
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="py-12 text-center text-xs text-slate-400">
                        No tickets linked to {selectedService || "this service"}.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Tab 3: Slack Discussions */}
              {activeTab === "slack" && (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 gap-2.5">
                    {data?.slack_messages && data.slack_messages.length > 0 ? (
                      data.slack_messages.map((m) => (
                        <div
                          key={m.id}
                          className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition shadow-sm space-y-2"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-xs text-indigo-600 font-mono">{m.channel}</span>
                              <span className="text-[11px] font-semibold text-slate-800">{m.author}</span>
                              <span className="text-[10px] font-mono bg-slate-100 px-1.5 py-0.2 rounded text-slate-600">
                                {m.service}
                              </span>
                            </div>
                            <span className="text-[10px] text-slate-400">
                              {new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          <p className="text-xs text-slate-700 leading-relaxed font-sans">{m.text}</p>
                          {m.pr_id && (
                            <div className="pt-1 flex items-center gap-1 text-[10px] text-slate-500">
                              <GitPullRequest className="w-3 h-3 text-slate-400" />
                              <span>Referenced Pull Request: </span>
                              <span className="font-mono font-bold text-indigo-600">{m.pr_id}</span>
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="py-12 text-center text-xs text-slate-400">
                        No Slack discussions found for {selectedService || "this service"}.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Tab 4: Docs & Runbooks */}
              {activeTab === "docs" && (
                <div className="space-y-3">
                  <div className="grid grid-cols-1 gap-2.5">
                    {data?.docs && data.docs.length > 0 ? (
                      data.docs.map((d) => (
                        <div
                          key={d.id}
                          className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition shadow-sm space-y-2"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-xs text-slate-900">{d.title}</span>
                              <span className="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-purple-50 text-purple-700 border border-purple-200 uppercase">
                                {d.category}
                              </span>
                            </div>
                            <span className="text-[10px] font-mono text-slate-400">{d.service}</span>
                          </div>
                          <p className="text-xs text-slate-600 leading-relaxed">{d.summary}</p>
                          <div className="pt-1 flex items-center justify-between">
                            <span className="text-[10px] font-mono text-indigo-600 flex items-center gap-1 hover:underline cursor-pointer">
                              <ExternalLink className="w-3 h-3" />
                              {d.url}
                            </span>
                            <span className="text-[10px] text-slate-400 font-mono">FalkorDB: (:Doc)-[:DOCUMENTS]-&gt;(:Service)</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="py-12 text-center text-xs text-slate-400">
                        No runbook documentation found for {selectedService || "this service"}.
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer with OpenCypher Query Showcase */}
        <div className="p-3 bg-slate-900 text-slate-200 border-t border-slate-800 text-[11px] flex items-center justify-between">
          <div className="flex items-center gap-2 font-mono text-slate-400">
            <Database className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-indigo-300">OpenCypher Knowledge Traversal:</span>
            <span className="text-slate-300">
              {selectedService
                ? `MATCH (e:Engineer)-[:AUTHORED]->(pr:PullRequest)-[:MODIFIED_SERVICE]->(:Service {name: '${selectedService}'})`
                : "MATCH (t:Ticket)-[:ATTACHED_TO]->(:PR)-[:MODIFIED_SERVICE]->(s:Service), (m:SlackMessage)-[:REFERENCES]->(s)"}
            </span>
          </div>
          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
            FalkorDB GraphBLAS Native
          </span>
        </div>
      </div>
    </div>
  );
}

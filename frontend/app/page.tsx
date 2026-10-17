"use client";

import React, { useState, useEffect } from "react";
import Header from "./components/Header";
import ServiceMap from "./components/ServiceMap";
import AgentPanel, { LogEntry } from "./components/AgentPanel";
import IncidentTrigger from "./components/IncidentTrigger";
import PostmortemModal from "./components/PostmortemModal";
import PlaybooksModal from "./components/PlaybooksModal";
import EpisodicMemoryModal from "./components/EpisodicMemoryModal";
import CompanyBrainModal from "./components/CompanyBrainModal";
import {
  Activity,
  Database,
  History,
  FileText,
  CheckCircle,
  ShieldAlert,
  Check,
  X,
  Wrench,
  Brain,
} from "lucide-react";

export default function Dashboard() {
  const [activeGraph, setActiveGraph] = useState("causalmesh_prod");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [highlightedNodes, setHighlightedNodes] = useState<string[]>([]);
  const [highlightStatus, setHighlightStatus] = useState<"failing" | "traversing" | "resolved" | null>(null);
  const [postmortemData, setPostmortemData] = useState<any>(null);
  const [isPostmortemOpen, setIsPostmortemOpen] = useState(false);
  const [isPlaybooksOpen, setIsPlaybooksOpen] = useState(false);
  const [isEpisodicOpen, setIsEpisodicOpen] = useState(false);
  const [isCompanyBrainOpen, setIsCompanyBrainOpen] = useState(false);
  const [companyBrainService, setCompanyBrainService] = useState("");
  const [episodes, setEpisodes] = useState<any[]>([]);
  const [pendingApproval, setPendingApproval] = useState<any | null>(null);
  const [graphRevision, setGraphRevision] = useState(0);

  const getApiUrl = (path: string) => {
    if (typeof window !== "undefined") {
      const host = window.location.hostname;
      if (host === "localhost" || host === "127.0.0.1") {
        return `http://${host}:8000${path}`;
      }
    }
    return path;
  };

  // Connect to SSE stream
  useEffect(() => {
    const streamUrl = getApiUrl("/api/stream");
    const eventSource = new EventSource(streamUrl);

    eventSource.onopen = () => {
      console.log("[CausalMesh SSE] Connected to stream:", streamUrl);
    };

    eventSource.onerror = (err) => {
      console.warn("[CausalMesh SSE] Stream notice:", err);
    };

    eventSource.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        const { type, data } = payload;

        if (type === "agent_log") {
          setLogs((prev) => [
            ...prev,
            {
              id: `${Date.now()}-${Math.random()}`,
              timestamp: new Date().toLocaleTimeString(),
              agent: data.agent,
              stage: data.stage,
              tool: data.tool,
              message: data.message,
              data: data.data || (data.result ? data.result : undefined),
            },
          ]);
        } else if (type === "path_highlight") {
          setHighlightedNodes(data.nodes || []);
          setHighlightStatus(data.status || "traversing");
        } else if (type === "incident_started") {
          setIsStreaming(true);
          setPendingApproval(null);
          setLogs([]);
          setGraphRevision((r) => r + 1);
        } else if (type === "approval_requested") {
          setPendingApproval(data);
        } else if (type === "postmortem") {
          setPostmortemData(data);
          setIsPostmortemOpen(true);
          setIsStreaming(false);
          setPendingApproval(null);
          setGraphRevision((r) => r + 1);
          loadEpisodes();
        } else if (type === "graph_reset") {
          setHighlightedNodes([]);
          setHighlightStatus(null);
          setPendingApproval(null);
          setLogs([]);
          setGraphRevision((r) => r + 1);
        } else if (type === "graph_update") {
          setGraphRevision((r) => r + 1);
        }
      } catch (err) {
        console.error("SSE parse error:", err);
      }
    };

    return () => {
      eventSource.close();
    };
  }, []);

  const loadEpisodes = () => {
    fetch(getApiUrl(`/api/graph/episodes?graph_name=${activeGraph}`))
      .then((r) => r.json())
      .then((data) => setEpisodes(data))
      .catch((e) => console.error(e));
  };

  useEffect(() => {
    loadEpisodes();
  }, [activeGraph]);

  const handleTriggerIncident = async (
    scenario: string,
    mode: "autonomous" | "hitl" = "autonomous",
    engine: "simulated" | "live_llm" = "simulated"
  ) => {
    setIsStreaming(true);
    setPendingApproval(null);
    try {
      await fetch(getApiUrl("/api/incident/trigger"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario,
          mode,
          engine,
          graph_name: activeGraph,
        }),
      });
    } catch (err) {
      console.error("Trigger incident error:", err);
      setIsStreaming(false);
    }
  };

  const handleTriggerAlertOnService = async (serviceName: string) => {
    setIsStreaming(true);
    setPendingApproval(null);
    try {
      await fetch(getApiUrl("/api/incident/trigger"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          alert_name: `HighErrorRate:500 on ${serviceName}`,
          epicenter_service: serviceName,
          scenario: "db_pool_exhaustion",
          mode: "autonomous",
          engine: "simulated",
          graph_name: activeGraph,
        }),
      });
    } catch (err) {
      console.error("Trigger incident on service error:", err);
      setIsStreaming(false);
    }
  };

  const handleDecision = async (approved: boolean) => {
    if (!pendingApproval) return;
    try {
      await fetch(getApiUrl("/api/incident/approve"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          incident_id: pendingApproval.incident_id,
          approved,
        }),
      });
      setPendingApproval(null);
    } catch (err) {
      console.error("Approval error:", err);
    }
  };

  const handleResetGraph = async () => {
    setIsStreaming(false);
    setPendingApproval(null);
    setPostmortemData(null);
    setHighlightedNodes([]);
    setHighlightStatus(null);
    setLogs([]);
    setGraphRevision((r) => r + 1);
    try {
      await fetch(getApiUrl(`/api/graph/reset?graph_name=${activeGraph}`), { method: "POST" });
    } catch (err) {
      console.error("Reset graph error:", err);
    }
  };

  const handleOpenCompanyBrain = (serviceName: string = "") => {
    setCompanyBrainService(serviceName);
    setIsCompanyBrainOpen(true);
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#faf8f5] text-[#292524]">
      {/* Header */}
      <Header activeGraph={activeGraph} onSwitchGraph={setActiveGraph} />

      {/* Metric Cards Top Bar */}
      <div className="px-4 py-1.5 bg-[#fdfcf9] border-b border-[#e7e2d9] grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 text-xs shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
        <div className="flex items-center space-x-2.5 p-1 rounded-lg bg-[#f7f4ee] border border-[#e8e2d8]">
          <div className="p-1.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[10px] text-stone-500 uppercase font-semibold">Services Monitored</span>
            <p className="font-bold text-stone-900 text-sm">25 Microservices</p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5 p-1 rounded-lg bg-[#f7f4ee] border border-[#e8e2d8]">
          <div className="p-1.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[10px] text-stone-500 uppercase font-semibold">Mean MTTR</span>
            <p className="font-bold text-emerald-800 text-sm">18.4 Seconds</p>
          </div>
        </div>

        {/* Procedural Playbooks Card */}
        <div
          onClick={() => setIsPlaybooksOpen(true)}
          className="flex items-center space-x-2.5 p-1 rounded-lg bg-[#f7f4ee] hover:bg-purple-50/70 border border-[#e8e2d8] hover:border-purple-300 cursor-pointer transition shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
          title="Click to view Procedural Memory Playbooks stored in FalkorDB"
        >
          <div className="p-1.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200">
            <Wrench className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[10px] text-stone-500 uppercase font-semibold">Procedural Memory</span>
            <p className="font-bold text-purple-900 text-sm">3 Playbooks Active</p>
          </div>
        </div>

        {/* Episodic Memory Card */}
        <div
          onClick={() => setIsEpisodicOpen(true)}
          className="flex items-center space-x-2.5 p-1 rounded-lg bg-[#f7f4ee] hover:bg-amber-50/70 border border-[#e8e2d8] hover:border-amber-300 cursor-pointer transition shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
          title="Click to inspect past incident episodes stored in FalkorDB"
        >
          <div className="p-1.5 rounded-md bg-amber-50 text-amber-700 border border-amber-200">
            <History className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[10px] text-stone-500 uppercase font-semibold">Episodic Memories</span>
            <p className="font-bold text-amber-900 text-sm">{episodes.length} Incidents Stored</p>
          </div>
        </div>

        {/* Company Brain Card */}
        <div
          onClick={() => handleOpenCompanyBrain("")}
          className="flex items-center space-x-2.5 p-1 rounded-lg bg-[#f7f4ee] hover:bg-indigo-50/70 border border-[#e8e2d8] hover:border-indigo-300 cursor-pointer transition shadow-[0_1px_2px_rgba(0,0,0,0.02)]"
          title="Click to explore Company Brain: Tickets, Slack Chats, Docs & Engineer Directory"
        >
          <div className="p-1.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <span className="text-[10px] text-stone-500 uppercase font-semibold">Company Brain</span>
            <p className="font-bold text-indigo-900 text-sm">Knowledge Graph</p>
          </div>
        </div>

        {/* Quick Actions / Postmortem */}
        <div className="flex items-center space-x-2 justify-end">
          {postmortemData ? (
            <button
              onClick={() => setIsPostmortemOpen(true)}
              className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs shadow-sm transition"
            >
              <FileText className="w-3.5 h-3.5" /> Latest Postmortem
            </button>
          ) : (
            <div className="hidden lg:flex items-center gap-1.5 px-2 py-1 text-[11px] text-slate-400">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>All Systems Operational</span>
            </div>
          )}
        </div>
      </div>

      {/* Human-in-the-Loop Approval Action Banner */}
      {pendingApproval && (
        <div className="mx-4 mt-3 p-3 bg-amber-50 border border-amber-300 rounded-xl flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-amber-100 text-amber-700 border border-amber-200">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-amber-950 uppercase tracking-wider">
                  ⚠️ Human Approval Required: {pendingApproval.incident_id}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] bg-amber-100 text-amber-800 border border-amber-300 font-semibold">
                  Playbook: {pendingApproval.playbook_name}
                </span>
              </div>
              <p className="text-xs text-amber-900 mt-0.5">
                Mitigator Agent proposes executing infrastructure changes on{" "}
                <code className="bg-amber-100 px-1 py-0.5 rounded text-amber-950 font-semibold">
                  {pendingApproval.target_service}
                </code>{" "}
                via MCP.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleDecision(true)}
              className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs rounded-lg flex items-center gap-1.5 shadow-sm transition"
            >
              <Check className="w-3.5 h-3.5" /> Approve & Remediate
            </button>
            <button
              onClick={() => handleDecision(false)}
              className="px-3 py-1.5 bg-white hover:bg-rose-50 text-slate-700 hover:text-rose-700 font-semibold text-xs rounded-lg flex items-center gap-1.5 border border-slate-300 transition"
            >
              <X className="w-3.5 h-3.5" /> Reject
            </button>
          </div>
        </div>
      )}

      {/* Main Content Workspace */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 p-3 overflow-hidden">
        {/* Left Column: Topology Map + Incident Trigger (8 cols for spacious graph) */}
        <div className="lg:col-span-8 flex flex-col space-y-2.5 h-full overflow-hidden">
          <div className="flex-1 min-h-[340px]">
            <ServiceMap
              activeGraph={activeGraph}
              highlightedNodes={highlightedNodes}
              highlightStatus={highlightStatus}
              graphRevision={graphRevision}
              onTriggerAlertOnService={handleTriggerAlertOnService}
              onOpenCompanyBrain={handleOpenCompanyBrain}
            />
          </div>

          <div className="shrink-0">
            <IncidentTrigger
              activeGraph={activeGraph}
              isTriggering={isStreaming}
              onTrigger={handleTriggerIncident}
              onReset={handleResetGraph}
            />
          </div>
        </div>

        {/* Right Column: Tri-Agent Swarm Reasoning Feed (4 cols) */}
        <div className="lg:col-span-4 h-full overflow-hidden">
          <AgentPanel
            logs={logs}
            isStreaming={isStreaming}
            onClearLogs={() => setLogs([])}
          />
        </div>
      </div>

      {/* Postmortem Modal */}
      <PostmortemModal
        isOpen={isPostmortemOpen}
        onClose={() => setIsPostmortemOpen(false)}
        data={postmortemData}
      />

      {/* Procedural Playbooks Modal */}
      <PlaybooksModal
        isOpen={isPlaybooksOpen}
        onClose={() => setIsPlaybooksOpen(false)}
        activeGraph={activeGraph}
      />

      {/* Episodic Memory Modal */}
      <EpisodicMemoryModal
        isOpen={isEpisodicOpen}
        onClose={() => setIsEpisodicOpen(false)}
        episodes={episodes}
        activeGraph={activeGraph}
      />

      {/* Company Brain Modal */}
      <CompanyBrainModal
        isOpen={isCompanyBrainOpen}
        onClose={() => setIsCompanyBrainOpen(false)}
        activeGraph={activeGraph}
        initialService={companyBrainService}
      />
    </div>
  );
}

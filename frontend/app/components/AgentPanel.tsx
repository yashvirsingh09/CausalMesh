"use client";

import React, { useEffect, useRef } from "react";
import { Bot, Terminal, Cpu, Wrench, ShieldAlert } from "lucide-react";

export interface LogEntry {
  id: string;
  timestamp: string;
  agent?: "SENTINEL" | "INVESTIGATOR" | "MITIGATOR" | "SYSTEM";
  stage?: string;
  tool?: string;
  message: string;
  data?: any;
}

interface AgentPanelProps {
  logs: LogEntry[];
  isStreaming: boolean;
  onClearLogs: () => void;
}

export default function AgentPanel({ logs, isStreaming, onClearLogs }: AgentPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const getAgentBadge = (agent?: string) => {
    switch (agent) {
      case "SENTINEL":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200 flex items-center gap-1">
            <ShieldAlert className="w-3 h-3 text-purple-600" /> SENTINEL
          </span>
        );
      case "INVESTIGATOR":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1">
            <Bot className="w-3 h-3 text-blue-600" /> INVESTIGATOR
          </span>
        );
      case "MITIGATOR":
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
            <Wrench className="w-3 h-3 text-emerald-600" /> MITIGATOR
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-200 flex items-center gap-1">
            <Cpu className="w-3 h-3 text-slate-500" /> SYSTEM
          </span>
        );
    }
  };

  return (
    <div className="w-full h-full bg-[#fdfcf9] border border-[#e8e2d8] rounded-xl overflow-hidden flex flex-col shadow-[0_1px_4px_rgba(0,0,0,0.03)]">
      {/* Header */}
      <div className="h-11 px-4 border-b border-[#e8e2d8] bg-[#f7f4ee] flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-indigo-700" />
          <span className="font-semibold text-xs text-stone-800 tracking-wide uppercase">
            Tri-Agent Swarm Reasoning Stream
          </span>
        </div>
        <div className="flex items-center space-x-2">
          {isStreaming && (
            <span className="flex items-center gap-1.5 text-[11px] font-semibold text-indigo-700 animate-pulse">
              <span className="w-2 h-2 rounded-full bg-indigo-600" /> Swarm Active
            </span>
          )}
          <button
            onClick={onClearLogs}
            className="text-[11px] text-stone-500 hover:text-stone-800 px-2 py-1 rounded hover:bg-[#ede7dd] transition"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Log Feed */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3 font-mono text-xs bg-[#faf8f5]">
        {logs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-2">
            <Bot className="w-8 h-8 text-slate-300" />
            <p className="text-xs text-slate-500">Swarm is idle. Trigger an incident to observe live graph reasoning.</p>
          </div>
        ) : (
          logs.map((log) => (
            <div
              key={log.id}
              className="p-3 rounded-lg bg-white border border-slate-200 hover:border-slate-300 transition shadow-[0_1px_2px_rgba(0,0,0,0.02)] space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {getAgentBadge(log.agent)}
                  {log.tool && (
                    <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 text-indigo-700 font-mono border border-slate-200 font-medium">
                      tool: {log.tool}
                    </span>
                  )}
                </div>
                <span className="text-[10px] text-slate-400">{log.timestamp}</span>
              </div>

              <p className="text-slate-800 text-xs leading-relaxed font-sans">{log.message}</p>

              {/* Tool Execution or Structured Data Details */}
              {log.data && (
                <div className="mt-2 p-2 rounded bg-slate-50 border border-slate-200 text-[11px] text-slate-700 overflow-x-auto">
                  <pre className="font-mono text-[10px] text-slate-600">
                    {JSON.stringify(log.data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

"use client";

import React, { useEffect, useRef, useState } from "react";
import cytoscape, { Core } from "cytoscape";
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  X,
  Search,
  User,
  GitPullRequest,
  ArrowRight,
  Flame,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Brain,
} from "lucide-react";

interface ServiceMapProps {
  activeGraph: string;
  highlightedNodes: string[];
  highlightStatus: "failing" | "traversing" | "resolved" | null;
  graphRevision?: number;
  onSelectService?: (serviceName: string) => void;
  onTriggerAlertOnService?: (serviceName: string) => void;
  onOpenCompanyBrain?: (serviceName: string) => void;
}

export default function ServiceMap({
  activeGraph,
  highlightedNodes,
  highlightStatus,
  graphRevision = 0,
  onSelectService,
  onTriggerAlertOnService,
  onOpenCompanyBrain,
}: ServiceMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const lastActiveGraphRef = useRef(activeGraph);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [nodeDetails, setNodeDetails] = useState<any>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  // Fetch and render graph elements
  const loadGraph = async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/graph/elements?graph_name=${activeGraph}`);
      const data = await res.json();

      if (!containerRef.current) return;

      const isGraphSwitch = lastActiveGraphRef.current !== activeGraph;
      lastActiveGraphRef.current = activeGraph;

      if (cyRef.current && !isGraphSwitch) {
        // In-place node status update without destroying the canvas!
        data.nodes.forEach((n: any) => {
          const ele = cyRef.current?.$(`node[id = "${n.data.id}"]`);
          if (ele && ele.length > 0) {
            ele.data("status", n.data.status);
            if (n.data.status === "failing") {
              ele.addClass("highlight-failing");
            } else if (n.data.status === "healthy") {
              ele.removeClass("highlight-failing highlight-traversing");
            }
          }
        });
        setLoading(false);
        return;
      }

      if (cyRef.current) {
        cyRef.current.destroy();
      }

      const cy = cytoscape({
        container: containerRef.current,
        elements: [...data.nodes, ...data.edges],
        style: [
          {
            selector: "node",
            style: {
              label: "data(label)",
              color: "#1c1917",
              "font-size": "11px",
              "font-weight": 700,
              "font-family": "system-ui, -apple-system, sans-serif",
              "text-valign": "bottom",
              "text-margin-y": 6,
              width: 48,
              height: 48,
              "background-color": "#ffffff",
              "border-width": 3,
              "border-color": "#a8a29e",
              "text-background-color": "#fefdfa",
              "text-background-opacity": 0.94,
              "text-background-padding": "3px",
              "text-background-shape": "roundrectangle",
              "text-border-width": 1,
              "text-border-color": "#e7e2d9",
              "text-border-opacity": 0.95,
              "transition-property": "background-color, border-color, border-width, width, height",
              "transition-duration": 0.25,
            },
          },
          // Rich, High-Contrast Tier Accents for Warm Theme
          {
            selector: 'node[tier = "api"]',
            style: {
              "background-color": "#e0e7ff",
              "border-color": "#4f46e5",
              "border-width": 3.5,
              color: "#1e1b4b",
            },
          },
          {
            selector: 'node[tier = "database"]',
            style: {
              "background-color": "#d1fae5",
              "border-color": "#059669",
              "border-width": 3.5,
              shape: "round-rectangle",
              width: 52,
              height: 46,
              color: "#064e3b",
            },
          },
          {
            selector: 'node[tier = "cache"]',
            style: {
              "background-color": "#fef3c7",
              "border-color": "#d97706",
              "border-width": 3.5,
              shape: "diamond",
              width: 56,
              height: 56,
              color: "#78350f",
            },
          },
          {
            selector: 'node[tier = "queue"]',
            style: {
              "background-color": "#ede9fe",
              "border-color": "#7c3aed",
              "border-width": 3.5,
              shape: "hexagon",
              width: 52,
              height: 52,
              color: "#4c1d95",
            },
          },
          {
            selector: 'node[tier = "worker"]',
            style: {
              "background-color": "#ffe4e6",
              "border-color": "#e11d48",
              "border-width": 3.5,
              shape: "ellipse",
              color: "#881337",
            },
          },
          {
            selector: 'node[tier = "external"]',
            style: {
              "background-color": "#f1f5f9",
              "border-color": "#475569",
              "border-width": 3,
              shape: "round-tag",
              width: 50,
              height: 44,
              color: "#0f172a",
            },
          },
          // High-visibility crisp edges
          {
            selector: "edge",
            style: {
              width: 2.2,
              "line-color": "#a8a29e",
              "target-arrow-color": "#78716c",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              "arrow-scale": 1.1,
              opacity: 0.9,
            },
          },
          // High-Priority Edge Highlights
          {
            selector: "edge.highlight-failing",
            style: {
              width: 4,
              "line-color": "#ef4444",
              "target-arrow-color": "#dc2626",
              opacity: 1,
              "z-index": 9998,
            },
          },
          {
            selector: "edge.highlight-traversing",
            style: {
              width: 3.8,
              "line-color": "#a855f7",
              "target-arrow-color": "#7e22ce",
              opacity: 1,
              "z-index": 9997,
            },
          },
          // High-Priority Failing State (Overrides tier styles)
          {
            selector: 'node[tier].highlight-failing, node.highlight-failing, node[status = "failing"]',
            style: {
              "background-color": "#ef4444",
              "border-color": "#b91c1c",
              "border-width": 6,
              width: 60,
              height: 60,
              color: "#ffffff",
              "text-background-color": "#b91c1c",
              "text-background-opacity": 1,
              "text-border-color": "#7f1d1d",
              "font-size": "12px",
              "font-weight": 900,
              "z-index": 9999,
            },
          },
          {
            selector: 'node[tier][status = "degraded"]',
            style: {
              "background-color": "#f59e0b",
              "border-color": "#b45309",
              "border-width": 5,
              width: 54,
              height: 54,
              color: "#ffffff",
              "text-background-color": "#b45309",
              "text-background-opacity": 1,
              "font-weight": 800,
              "z-index": 9995,
            },
          },
          // High-Priority Traversing State (Purple pulse/glow)
          {
            selector: 'node[tier].highlight-traversing, node.highlight-traversing',
            style: {
              "background-color": "#a855f7",
              "border-color": "#6b21a8",
              "border-width": 6,
              width: 56,
              height: 56,
              color: "#ffffff",
              "text-background-color": "#6b21a8",
              "text-background-opacity": 1,
              "text-border-color": "#3b0764",
              "font-size": "12px",
              "font-weight": 900,
              "z-index": 9998,
            },
          },
          // High-Priority Resolved State (Healthy Green)
          {
            selector: 'node[tier].highlight-resolved, node.highlight-resolved',
            style: {
              "background-color": "#10b981",
              "border-color": "#047857",
              "border-width": 5,
              width: 52,
              height: 52,
              color: "#ffffff",
              "text-background-color": "#047857",
              "text-background-opacity": 1,
              "z-index": 9990,
            },
          },
          {
            selector: ".search-matched",
            style: {
              "border-color": "#4f46e5",
              "border-width": 4,
              "font-weight": "bold",
            },
          },
        ],
        layout: {
          name: "cose",
          idealEdgeLength: 140,
          nodeOverlap: 25,
          refresh: 20,
          fit: true,
          padding: 35,
          randomize: false,
          componentSpacing: 130,
          nodeRepulsion: 900000,
          edgeElasticity: 100,
          nestingFactor: 5,
        },
      });

      // Node selection click handler
      cy.on("tap", "node", (evt) => {
        const node = evt.target;
        const nodeData = node.data();
        setSelectedNode(nodeData);
        if (onSelectService) {
          onSelectService(nodeData.id);
        }
        fetchNodeDetails(nodeData.id);
      });

      // Background click dismisses selection
      cy.on("tap", (evt) => {
        if (evt.target === cy) {
          setSelectedNode(null);
          setNodeDetails(null);
        }
      });

      cyRef.current = cy;
      setLoading(false);
    } catch (err) {
      console.error("Failed to load graph elements:", err);
      setLoading(false);
    }
  };

  const fetchNodeDetails = async (serviceName: string) => {
    try {
      setLoadingDetails(true);
      const res = await fetch(`/api/graph/service/${serviceName}?graph_name=${activeGraph}`);
      if (res.ok) {
        const data = await res.json();
        setNodeDetails(data);
      } else {
        setNodeDetails(null);
      }
      setLoadingDetails(false);
    } catch {
      setNodeDetails(null);
      setLoadingDetails(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, [activeGraph, graphRevision]);

  // Handle dynamic node highlights from agent events
  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;

    if (highlightedNodes.length > 0 && highlightStatus) {
      const selector = highlightedNodes.map((id) => `node[id = "${id}"]`).join(", ");
      const matched = cy.$(selector);

      if (highlightStatus === "failing") {
        cy.nodes().removeClass("highlight-traversing highlight-resolved");
        cy.edges().removeClass("highlight-traversing highlight-resolved");
        matched.addClass("highlight-failing");
        matched.connectedEdges().addClass("highlight-failing");

        // Center smoothly on the failing epicenter
        if (matched.length > 0) {
          cy.animate({
            center: { eles: matched.first() },
            zoom: 1.25,
            duration: 600,
          });
        }
      } else if (highlightStatus === "traversing") {
        // Clear previous traversal step, BUT KEEP failing nodes red!
        cy.nodes().removeClass("highlight-traversing");
        cy.edges().removeClass("highlight-traversing");
        matched.addClass("highlight-traversing");
        matched.connectedEdges().addClass("highlight-traversing");
      } else if (highlightStatus === "resolved") {
        cy.nodes().removeClass("highlight-failing highlight-traversing");
        cy.edges().removeClass("highlight-failing highlight-traversing");
        matched.addClass("highlight-resolved");
      }
    } else if (highlightStatus === null) {
      cy.nodes().removeClass("highlight-failing highlight-traversing highlight-resolved");
      cy.edges().removeClass("highlight-failing highlight-traversing highlight-resolved");
    }
  }, [highlightedNodes, highlightStatus]);

  // Search filter
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!cyRef.current || !searchQuery.trim()) return;
    const cy = cyRef.current;
    cy.nodes().removeClass("search-matched");

    const matched = cy.nodes().filter((node) =>
      node.data("id").toLowerCase().includes(searchQuery.toLowerCase().trim())
    );

    if (matched.length > 0) {
      matched.addClass("search-matched");
      cy.animate({
        center: { eles: matched.first() },
        zoom: 1.5,
        duration: 400,
      });
      setSelectedNode(matched.first().data());
      fetchNodeDetails(matched.first().data("id"));
    }
  };

  return (
    <div
      className="relative w-full h-full bg-[#fdfcf9] border border-[#e8e2d8] rounded-xl overflow-hidden shadow-[0_1px_4px_rgba(0,0,0,0.03)] flex flex-col"
      style={{
        backgroundImage: "radial-gradient(#d6cec3 1.2px, transparent 1.2px)",
        backgroundSize: "22px 22px",
      }}
    >
      {/* Top Action Bar */}
      <div className="absolute top-3 left-3 z-10 flex items-center space-x-2 bg-[#fdfcf9]/95 backdrop-blur border border-[#e8e2d8] rounded-lg p-1 shadow-sm text-xs">
        <span className="text-stone-800 font-bold px-2">Topology Map</span>
        <div className="h-4 w-px bg-[#e8e2d8]" />
        <button
          onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 1.2)}
          className="p-1.5 hover:bg-[#f5f1ea] text-stone-600 rounded transition"
          title="Zoom In"
        >
          <ZoomIn className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => cyRef.current?.zoom(cyRef.current.zoom() * 0.8)}
          className="p-1.5 hover:bg-[#f5f1ea] text-stone-600 rounded transition"
          title="Zoom Out"
        >
          <ZoomOut className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => cyRef.current?.fit(undefined, 30)}
          className="p-1.5 hover:bg-[#f5f1ea] text-stone-600 rounded transition"
          title="Fit to Screen"
        >
          <Maximize2 className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={loadGraph}
          className="p-1.5 hover:bg-[#f5f1ea] text-stone-600 rounded transition"
          title="Reload Graph"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>

        {/* Quick Search */}
        <form onSubmit={handleSearch} className="flex items-center pl-1 border-l border-[#e8e2d8]">
          <div className="relative flex items-center">
            <Search className="w-3 h-3 text-stone-400 absolute left-2 pointer-events-none" />
            <input
              type="text"
              placeholder="Find node..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-6 pr-2 py-0.5 bg-[#f7f4ee] border border-[#e8e2d8] rounded text-[11px] w-28 focus:w-36 transition-all focus:outline-none focus:ring-1 focus:ring-indigo-500 text-stone-800"
            />
          </div>
        </form>
      </div>

      {/* Legend Badge */}
      <div className="absolute bottom-3 left-3 z-10 hidden sm:flex items-center space-x-3 bg-[#fdfcf9]/95 backdrop-blur border border-[#e8e2d8] rounded-lg px-3 py-1.5 text-[11px] text-stone-700 shadow-sm">
        <span className="flex items-center gap-1.5 font-semibold">
          <span className="w-2.5 h-2.5 rounded-full bg-indigo-600" /> API
        </span>
        <span className="flex items-center gap-1.5 font-semibold">
          <span className="w-2.5 h-2.5 rounded bg-emerald-600" /> Database
        </span>
        <span className="flex items-center gap-1.5 font-semibold">
          <span className="w-2.5 h-2.5 rotate-45 bg-amber-500" /> Cache
        </span>
        <span className="flex items-center gap-1.5 font-semibold">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" /> Failing
        </span>
        <span className="flex items-center gap-1.5 font-semibold">
          <span className="w-2.5 h-2.5 rounded-full bg-purple-600" /> Traversing
        </span>
      </div>

      {/* Cytoscape Canvas Container */}
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Node Inspector Drawer with Track 03 Company Brain details */}
      {selectedNode && (
        <div className="absolute top-3 right-3 z-20 w-80 max-h-[85%] bg-[#fdfcf9]/98 backdrop-blur-md border border-[#e8e2d8] rounded-xl p-4 shadow-xl text-xs space-y-3 overflow-y-auto">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-indigo-600" />
              <span className="font-bold text-sm text-slate-900">{selectedNode.label}</span>
            </div>
            <button
              onClick={() => {
                setSelectedNode(null);
                setNodeDetails(null);
              }}
              className="text-slate-400 hover:text-slate-700 p-1 rounded hover:bg-slate-100"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-1.5 text-slate-600">
            <div className="flex justify-between items-center">
              <span className="text-slate-400">Status:</span>
              <span
                className={`font-semibold uppercase px-2 py-0.5 rounded text-[10px] ${
                  selectedNode.status === "failing"
                    ? "bg-rose-50 text-rose-700 border border-rose-200"
                    : selectedNode.status === "degraded"
                    ? "bg-amber-50 text-amber-700 border border-amber-200"
                    : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                }`}
              >
                {selectedNode.status}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Tier:</span>
              <span className="font-medium text-slate-800">{selectedNode.tier}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Team:</span>
              <span className="font-medium text-slate-800">{selectedNode.team}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Language:</span>
              <span className="font-medium text-slate-800">{selectedNode.language}</span>
            </div>
          </div>

          {/* Track 03: Company Brain Attribution */}
          {loadingDetails ? (
            <div className="py-2 text-center text-slate-400 text-[11px]">Loading provenance...</div>
          ) : nodeDetails ? (
            <div className="space-y-3 pt-2 border-t border-slate-100">
              {/* Service Owner */}
              {nodeDetails.owner && (
                <div className="p-2 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
                  <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                    <User className="w-3 h-3 text-indigo-600" /> Service Owner
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800">{nodeDetails.owner.name}</span>
                    <span className="text-[11px] font-mono text-indigo-600 font-semibold">
                      {nodeDetails.owner.slack}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500">{nodeDetails.owner.role} • {nodeDetails.owner.team}</p>
                </div>
              )}

              {/* Recent PRs */}
              {nodeDetails.recent_commits && nodeDetails.recent_commits.length > 0 && (
                <div className="space-y-1.5">
                  <div className="flex items-center gap-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                    <GitPullRequest className="w-3 h-3 text-rose-500" /> Recent Pull Requests ({nodeDetails.recent_commits.length})
                  </div>
                  <div className="space-y-1.5">
                    {nodeDetails.recent_commits.slice(0, 2).map((pr: any) => (
                      <div key={pr.pr_id} className="p-2 rounded-lg bg-slate-50 border border-slate-200 text-[11px]">
                        <div className="flex items-center justify-between font-bold">
                          <span className="text-indigo-700 font-mono">{pr.pr_id}</span>
                          <span className="text-[10px] text-slate-500">{pr.author_name}</span>
                        </div>
                        <p className="text-slate-700 font-medium line-clamp-1 mt-0.5">{pr.title}</p>
                        <p className="text-[10px] text-slate-500 line-clamp-2 mt-0.5 bg-white p-1 rounded border border-slate-100 font-mono">
                          {pr.diff_summary}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Dependencies Summary */}
              <div className="flex justify-between text-[11px] text-slate-500 pt-1">
                <span>Inbound: <strong>{nodeDetails.upstream_callers?.length || 0}</strong></span>
                <span>Outbound: <strong>{nodeDetails.downstream_dependencies?.length || 0}</strong></span>
              </div>

              {/* Quick Actions */}
              <div className="space-y-1.5 pt-1">
                {onOpenCompanyBrain && (
                  <button
                    onClick={() => onOpenCompanyBrain(selectedNode.id)}
                    className="w-full py-1.5 px-3 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-[11px] flex items-center justify-center gap-1.5 border border-indigo-200 transition shadow-sm"
                  >
                    <Brain className="w-3.5 h-3.5 text-indigo-600" /> Explore in Company Brain
                  </button>
                )}

                {onTriggerAlertOnService && (
                  <button
                    onClick={() => onTriggerAlertOnService(selectedNode.id)}
                    className="w-full py-1.5 px-3 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold text-[11px] flex items-center justify-center gap-1.5 border border-rose-200 transition"
                  >
                    <Flame className="w-3 h-3 text-rose-600" /> Simulate Alert on {selectedNode.id}
                  </button>
                )}
              </div>
            </div>
          ) : null}

          <div className="pt-2 border-t border-slate-100">
            <p className="text-[10px] text-slate-500">
              💡 <span className="font-semibold text-slate-700">FalkorDB Provenance:</span> Node in{" "}
              <code className="text-indigo-600 font-semibold">{activeGraph}</code> with OpenCypher graph traversals.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

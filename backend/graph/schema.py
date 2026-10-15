"""
graph/schema.py — Node and edge type definitions as Python dataclasses.
These map 1:1 to FalkorDB node labels and relationship types.
"""
from dataclasses import dataclass, field
from typing import Literal


# ─── NODE TYPES ───────────────────────────────────────────────────────────────

@dataclass
class ServiceNode:
    name: str
    team: str
    language: str = "python"
    tier: Literal["api", "worker", "cache", "database", "queue", "external"] = "api"
    status: Literal["healthy", "degraded", "failing"] = "healthy"
    owner_slack: str = ""
    version: str = "1.0.0"
    repo_url: str = ""


@dataclass
class EngineerNode:
    id: str                # e.g. "eng_alice"
    name: str
    slack: str
    role: str              # e.g. "Staff SRE", "Backend Dev"
    team: str


@dataclass
class PullRequestNode:
    id: str                # e.g. "PR-88"
    title: str
    merged_at: str         # ISO 8601
    diff_summary: str
    url: str = ""
    lines_changed: int = 0


@dataclass
class ProcedureNode:
    name: str              # e.g. "resolve_db_pool_starvation"
    trigger_pattern: str   # e.g. "db_pool_exhaustion"
    success_rate: float    # 0.0–1.0
    description: str = ""


@dataclass
class ActionNode:
    name: str              # e.g. "scale_db_pool"
    tool: str              # MCP tool identifier
    params: dict = field(default_factory=dict)
    timeout_sec: int = 30


@dataclass
class EpisodeNode:
    incident_id: str
    alert_name: str
    root_cause: str
    root_cause_pr_id: str
    mttr_seconds: int
    timestamp: str         # ISO 8601
    status: Literal["resolved", "mitigated", "escalated"] = "resolved"


# ─── EDGE / RELATIONSHIP TYPES ────────────────────────────────────────────────

@dataclass
class CallsEdge:
    protocol: str = "http"
    latency_p99_ms: float = 0.0
    error_rate: float = 0.0
    requests_per_sec: float = 0.0


@dataclass
class DependsOnEdge:
    conn_pool_size: int = 10
    pool_utilization: float = 0.0   # 0.0–1.0


# ─── CONSTANTS ────────────────────────────────────────────────────────────────

# Node labels used in Cypher queries
LABELS = {
    "service": "Service",
    "engineer": "Engineer",
    "pr": "PullRequest",
    "procedure": "Procedure",
    "action": "Action",
    "episode": "Episode",
}

# Relationship types used in Cypher queries
REL = {
    "calls": "CALLS",
    "depends_on": "DEPENDS_ON",
    "authored": "AUTHORED",
    "approved": "APPROVED",
    "modified": "MODIFIED_SERVICE",
    "owns": "OWNS",
    "resolved_by": "RESOLVED_BY",
    "step": "STEP",
    "next": "NEXT",
    "involved": "INVOLVED",
}

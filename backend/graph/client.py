"""
graph/client.py — FalkorDB connection singleton with in-memory fallback.
Supports multigraph isolation (e.g. causalmesh_prod vs causalmesh_staging).
If a live FalkorDB server is offline, transparently falls back to an
in-memory graph engine so development, testing, and demonstrations always work.
"""
from typing import Any
from config import (
    FALKORDB_HOST,
    FALKORDB_PORT,
    FALKORDB_PASSWORD,
    FALKORDB_USERNAME,
    FALKORDB_SSL,
    ACTIVE_GRAPH,
)

_client = None
_in_memory_graphs: dict[str, "InMemoryGraph"] = {}


class QueryResult:
    """Wraps result rows mimicking FalkorDB's query result structure."""
    def __init__(self, result_set: list[list[Any]] | None = None):
        self.result_set = result_set or []


class InMemoryGraph:
    """
    In-memory graph store matching FalkorDB's interface.
    Stores nodes and directed relationships in memory.
    """
    def __init__(self, name: str):
        self.name = name
        self.services: dict[str, dict] = {}
        self.dependencies: list[dict] = []
        self.engineers: dict[str, dict] = {}
        self.ownership: dict[str, str] = {}  # service_name -> engineer_id
        self.pull_requests: list[dict] = []
        self.procedures: dict[str, dict] = {}
        self.episodes: list[dict] = []
        self.tickets: list[dict] = []
        self.slack_messages: list[dict] = []
        self.docs: list[dict] = []
        self.semantic_rules: dict[str, dict] = {}
        self.handoffs: list[dict] = []
        self._init_defaults()

    def _init_defaults(self):
        # Default 25 services
        default_services = [
            ("api-gateway",              "platform",    "api",      "go"),
            ("auth-service",             "platform",    "api",      "python"),
            ("checkout-service",         "commerce",    "api",      "python"),
            ("payment-service",          "payments",    "api",      "java"),
            ("inventory-service",        "commerce",    "worker",   "python"),
            ("notification-service",     "platform",    "worker",   "python"),
            ("product-service",          "catalog",     "api",      "python"),
            ("search-service",           "catalog",     "api",      "python"),
            ("recommendation-service",   "ml",          "api",      "python"),
            ("user-profile-service",     "platform",    "api",      "node"),
            ("fraud-detection-service",  "payments",    "worker",   "python"),
            ("shipping-service",         "logistics",   "worker",   "python"),
            ("returns-service",          "commerce",    "api",      "python"),
            ("analytics-service",        "data",        "worker",   "python"),
            ("email-worker",             "platform",    "worker",   "python"),
            ("sms-worker",               "platform",    "worker",   "python"),
            ("inventory-postgres",       "commerce",    "database", "postgres"),
            ("payment-postgres",         "payments",    "database", "postgres"),
            ("user-postgres",            "platform",    "database", "postgres"),
            ("product-postgres",         "catalog",     "database", "postgres"),
            ("redis-session",            "platform",    "cache",    "redis"),
            ("redis-cart",               "commerce",    "cache",    "redis"),
            ("kafka-events",             "platform",    "queue",    "kafka"),
            ("stripe-api",               "payments",    "external", "external"),
            ("sendgrid-api",             "platform",    "external", "external"),
        ]
        for name, team, tier, lang in default_services:
            self.services[name] = {
                "name": name, "team": team, "tier": tier,
                "language": lang, "status": "healthy", "version": "1.0.0"
            }

        default_dependencies = [
            ("api-gateway",            "auth-service",            "http",   8,   3200),
            ("api-gateway",            "checkout-service",        "http",   45,  800),
            ("api-gateway",            "product-service",         "http",   20,  2100),
            ("api-gateway",            "search-service",          "http",   30,  1800),
            ("api-gateway",            "user-profile-service",    "http",   15,  1200),
            ("checkout-service",       "payment-service",         "http",   120, 400),
            ("checkout-service",       "inventory-service",       "http",   35,  400),
            ("checkout-service",       "notification-service",    "amqp",   5,   400),
            ("checkout-service",       "redis-cart",              "redis",  2,   800),
            ("inventory-service",      "inventory-postgres",      "tcp",    4,   800),
            ("inventory-service",      "redis-session",           "redis",  1,   400),
            ("payment-service",        "payment-postgres",        "tcp",    5,   400),
            ("payment-service",        "fraud-detection-service", "grpc",   25,  400),
            ("payment-service",        "stripe-api",              "https",  200, 400),
            ("notification-service",   "email-worker",            "amqp",   3,   200),
            ("notification-service",   "sms-worker",              "amqp",   3,   100),
            ("email-worker",           "sendgrid-api",            "https",  150, 200),
            ("product-service",        "product-postgres",        "tcp",    3,   2100),
            ("recommendation-service", "product-postgres",        "tcp",    10,  500),
            ("recommendation-service", "analytics-service",       "grpc",   50,  200),
            ("search-service",         "product-postgres",        "tcp",    5,   1800),
            ("user-profile-service",   "user-postgres",           "tcp",    4,   1200),
            ("shipping-service",       "inventory-postgres",      "tcp",    4,   150),
            ("returns-service",        "inventory-service",       "http",   30,  50),
            ("returns-service",        "payment-service",         "http",   100, 50),
            ("analytics-service",      "kafka-events",            "kafka",  2,   500),
        ]
        for src, dst, proto, lat, rps in default_dependencies:
            self.dependencies.append({
                "source": src, "target": dst, "protocol": proto,
                "latency_p99_ms": lat, "rps": rps, "error_rate": 0.0
            })

        default_engineers = [
            ("eng_alice",  "Alice Mehta",   "@alice",   "Staff SRE",       "platform"),
            ("eng_dave",   "Dave Kim",      "@dave",    "Backend Dev",     "commerce"),
            ("eng_priya",  "Priya Nair",    "@priya",   "Senior Dev",      "payments"),
            ("eng_sam",    "Sam Torres",    "@sam",     "ML Engineer",     "ml"),
            ("eng_chen",   "Chen Wei",      "@chen",    "Principal Eng",   "platform"),
        ]
        for eid, name, slack, role, team in default_engineers:
            self.engineers[eid] = {"id": eid, "name": name, "slack": slack, "role": role, "team": team}

        self.ownership = {
            "api-gateway": "eng_alice", "auth-service": "eng_alice", "redis-session": "eng_alice",
            "checkout-service": "eng_dave", "inventory-service": "eng_dave", "inventory-postgres": "eng_dave",
            "payment-service": "eng_priya", "fraud-detection-service": "eng_priya", "payment-postgres": "eng_priya",
            "recommendation-service": "eng_sam", "analytics-service": "eng_sam",
            "kafka-events": "eng_chen", "notification-service": "eng_chen"
        }

        # PRs
        from datetime import datetime, timezone, timedelta
        def _ago(m): return (datetime.now(timezone.utc) - timedelta(minutes=m)).isoformat()
        self.pull_requests = [
            {"id": "PR-88", "title": "Reduce DB idle timeout 30s→2s for lower memory",
             "author_id": "eng_dave", "reviewer_id": "eng_alice", "service": "inventory-service",
             "merged_at": _ago(35), "diff_summary": "Changed db_pool.idle_timeout from 30 to 2 in inventory/config.py"},
            {"id": "PR-87", "title": "Add retry logic to payment webhook handler",
             "author_id": "eng_priya", "reviewer_id": "eng_chen", "service": "payment-service",
             "merged_at": _ago(90), "diff_summary": "Added exponential backoff on Stripe webhook failures"},
            {"id": "PR-86", "title": "Upgrade recommendation model to v3.2",
             "author_id": "eng_sam", "reviewer_id": "eng_alice", "service": "recommendation-service",
             "merged_at": _ago(200), "diff_summary": "Swapped sklearn model artifact, updated inference pipeline"},
            {"id": "PR-85", "title": "Fix session token expiry race condition",
             "author_id": "eng_alice", "reviewer_id": "eng_chen", "service": "auth-service",
             "merged_at": _ago(480), "diff_summary": "Added distributed lock on token refresh endpoint"},
            {"id": "PR-83", "title": "Increase redis-cart maxmemory-policy to allkeys-lru",
             "author_id": "eng_dave", "reviewer_id": "eng_priya", "service": "redis-cart",
             "merged_at": _ago(2880), "diff_summary": "Changed eviction policy to prevent OOM on cart spike"},
        ]

        # Procedures
        self.procedures = {
            "db_pool_exhaustion": {
                "name": "resolve_db_pool_starvation",
                "trigger_pattern": "db_pool_exhaustion",
                "success_rate": 0.95,
                "description": "Fixes connection pool exhaustion by scaling max connections and restarting service.",
                "steps": [
                    {"step_id": "step_pool_1", "name": "scale_db_pool", "tool": "mcp_infra:patch_config", "params": "{'param': 'max_conn=250'}", "order": 1},
                    {"step_id": "step_pool_2", "name": "restart_pods", "tool": "mcp_k8s:rollout_restart", "params": "{'service': 'inventory-service', 'timeout': 60}", "order": 2},
                    {"step_id": "step_pool_3", "name": "verify_error_rate", "tool": "mcp_metrics:error_rate", "params": "{'threshold': 0.01}", "order": 3},
                ],
            },
            "cache_eviction_storm": {
                "name": "resolve_cache_miss_storm",
                "trigger_pattern": "cache_eviction_storm",
                "success_rate": 0.88,
                "description": "Clears corrupted cache keys and warms cache for hot paths.",
                "steps": [
                    {"step_id": "step_cache_1", "name": "flush_cache_namespace", "tool": "mcp_redis:flush_ns", "params": "{'namespace': 'cart:*'}", "order": 1},
                    {"step_id": "step_cache_2", "name": "warm_cache", "tool": "mcp_infra:trigger_warmup", "params": "{'endpoint': '/warmup'}", "order": 2},
                    {"step_id": "step_cache_3", "name": "verify_hit_rate", "tool": "mcp_metrics:cache_hit_rate", "params": "{'threshold': 0.8}", "order": 3},
                ],
            },
            "canary_error_spike": {
                "name": "resolve_canary_regression",
                "trigger_pattern": "canary_error_spike",
                "success_rate": 0.99,
                "description": "Rolls back a bad canary deployment to the previous stable version.",
                "steps": [
                    {"step_id": "step_canary_1", "name": "rollback_canary", "tool": "mcp_k8s:rollout_undo", "params": "{}", "order": 1},
                    {"step_id": "step_canary_2", "name": "verify_stable", "tool": "mcp_metrics:error_rate", "params": "{'threshold': 0.005}", "order": 2},
                    {"step_id": "step_canary_3", "name": "notify_team", "tool": "mcp_slack:notify", "params": "{'channel': '#incidents'}", "order": 3},
                ],
            },
        }

        # Past Episodes
        self.episodes = [
            {
                "incident_id": "INC-2026-09-03",
                "alert_name": "HighErrorRate:checkout-service",
                "root_cause": "PR-83 changed Redis eviction policy causing cart key evictions under load",
                "root_cause_pr_id": "PR-83",
                "mttr_seconds": 28,
                "timestamp": "2026-09-03T14:22:00+00:00",
                "status": "resolved",
                "involved_services": ["checkout-service", "redis-cart"],
            },
            {
                "incident_id": "INC-2026-08-17",
                "alert_name": "DatabaseConnectionsExhausted:payment-postgres",
                "root_cause": "Scheduled batch job triggered connection pool exhaustion on payment-postgres",
                "root_cause_pr_id": "PR-82",
                "mttr_seconds": 47,
                "timestamp": "2026-08-17T03:11:00+00:00",
                "status": "resolved",
                "involved_services": ["payment-service", "payment-postgres"],
            },
        ]

        # Context Engine: Company Knowledge (Tickets, Slack Chats, Docs)
        self.tickets = [
            {"id": "TICK-1042", "title": "Memory pressure on inventory workers under peak load", "pr_id": "PR-88", "service": "inventory-service", "priority": "P2", "status": "closed"},
            {"id": "TICK-980", "title": "Payment webhook failures causing checkout dropoffs", "pr_id": "PR-87", "service": "payment-service", "priority": "P1", "status": "closed"},
            {"id": "TICK-744", "title": "Upgrade recommendation model accuracy for catalog search", "pr_id": "PR-86", "service": "recommendation-service", "priority": "P3", "status": "closed"},
            {"id": "TICK-610", "title": "Session token race condition during token refresh", "pr_id": "PR-85", "service": "auth-service", "priority": "P2", "status": "closed"},
            {"id": "TICK-520", "title": "Cart cache OOM eviction spike during flash sales", "pr_id": "PR-83", "service": "redis-cart", "priority": "P1", "status": "closed"},
        ]

        self.slack_messages = [
            {"id": "MSG-902", "channel": "#deployments", "author": "@dave", "service": "inventory-service", "pr_id": "PR-88", "text": "Merged PR-88 (tuning idle timeout 30s -> 2s on inventory-service to reduce memory footprint).", "timestamp": _ago(34)},
            {"id": "MSG-890", "channel": "#payments-alerts", "author": "@priya", "service": "payment-service", "pr_id": "PR-87", "text": "Shipped exponential backoff for Stripe webhooks in PR-87.", "timestamp": _ago(88)},
            {"id": "MSG-810", "channel": "#ml-ops", "author": "@sam", "service": "recommendation-service", "pr_id": "PR-86", "text": "Canary deployment of model v3.2 artifact initiated for recommendation-service.", "timestamp": _ago(195)},
            {"id": "MSG-750", "channel": "#incidents", "author": "@alice", "service": "inventory-postgres", "pr_id": None, "text": "Remember runbook DOC-1 if Postgres connection pool utilization spikes above 90%.", "timestamp": _ago(1440)},
        ]

        self.docs = [
            {"id": "DOC-1", "title": "Postgres Connection Pool Starvation & Recovery Runbook", "service": "inventory-postgres", "url": "https://wiki.internal/runbooks/db-pool", "category": "runbook", "summary": "Procedure to scale pool connections and trigger pod rolling restart during starvation."},
            {"id": "DOC-2", "title": "Redis Cache Invalidation & Eviction Architecture RFC", "service": "redis-cart", "url": "https://wiki.internal/rfc/redis-eviction", "category": "architecture", "summary": "Standards for cache TTL, allkeys-lru eviction, and warming hot keys."},
            {"id": "DOC-3", "title": "Machine Learning Canary Rollback Procedures", "service": "recommendation-service", "url": "https://wiki.internal/runbooks/canary-undo", "category": "runbook", "summary": "Step-by-step rollout undo and baseline latency verification."},
        ]

        # Semantic Memory (Domain Ontology & Architecture Rules)
        self.semantic_rules = {
            "db_pool_exhaustion": {
                "pattern": "db_pool_exhaustion",
                "category": "ResourceStarvation",
                "layer": "database_pool",
                "impact": "Connection pool saturation cascades upstream 504 gateway timeouts",
                "suggested_mitigation": "Scale pool capacity and rollout restart",
                "blast_risk": "Critical",
            },
            "cache_eviction_storm": {
                "pattern": "cache_eviction_storm",
                "category": "CacheThrashing",
                "layer": "caching_layer",
                "impact": "Uncached requests saturate backend database",
                "suggested_mitigation": "Flush corrupted namespace and warm hot keys",
                "blast_risk": "High",
            },
            "canary_error_spike": {
                "pattern": "canary_error_spike",
                "category": "RegressionDeployment",
                "layer": "application_code",
                "impact": "Inference latency spike degrades user-facing response times",
                "suggested_mitigation": "Roll back canary deployment to previous revision",
                "blast_risk": "Medium",
            },
        }

        self.handoffs = []

    def query(self, cypher: str, params: dict | None = None) -> QueryResult:
        """Parses and executes queries against in-memory graph."""
        params = params or {}
        cypher_clean = cypher.strip()

        # Update service status
        if "SET s.status" in cypher_clean:
            name = params.get("name")
            status = params.get("status")
            if name and name in self.services:
                self.services[name]["status"] = status
            return QueryResult([])

        # Shortest path algorithm (Track 01: Graph algorithms as agent tools)
        if "shortestPath" in cypher_clean:
            src = params.get("src", "")
            dst = params.get("dst", "")
            if src == dst:
                return QueryResult([[[src], 0]])
            queue = [[src]]
            visited = {src}
            found_path = None
            while queue:
                path = queue.pop(0)
                node = path[-1]
                if node == dst:
                    found_path = path
                    break
                for dep in self.dependencies:
                    if dep["source"] == node and dep["target"] not in visited:
                        visited.add(dep["target"])
                        queue.append(path + [dep["target"]])
            if found_path:
                return QueryResult([[found_path, len(found_path) - 1]])
            return QueryResult([])

        # Get blast radius
        if "length(path) AS hop_distance" in cypher_clean:
            root_name = params.get("name", "")
            hops_max = params.get("hops", 3)
            results = []
            visited = {root_name}
            current_level = [root_name]

            for h in range(1, hops_max + 1):
                next_level = []
                for s in current_level:
                    for dep in self.dependencies:
                        nbr = None
                        if dep["source"] == s and dep["target"] not in visited:
                            nbr = dep["target"]
                        elif dep["target"] == s and dep["source"] not in visited:
                            nbr = dep["source"]
                        if nbr:
                            visited.add(nbr)
                            next_level.append(nbr)
                            svc = self.services.get(nbr, {"status": "healthy", "team": "unknown"})
                            results.append([nbr, svc.get("status", "healthy"), svc.get("team", "unknown"), h])
                current_level = next_level
            return QueryResult(results)

        # Get all services
        if "MATCH (s:Service)" in cypher_clean and "RETURN s.name, s.status" in cypher_clean:
            rows = [
                [s["name"], s["status"], s["tier"], s["team"], s["language"]]
                for s in self.services.values()
            ]
            return QueryResult(rows)

        # Get all dependencies
        if "MATCH (a:Service)-[r:CALLS]->(b:Service)" in cypher_clean:
            rows = [
                [d["source"], d["target"], d["protocol"], d["latency_p99_ms"], d["error_rate"], d["rps"]]
                for d in self.dependencies
            ]
            return QueryResult(rows)

        # Get service status
        if "MATCH (s:Service {name: $name})" in cypher_clean:
            name = params.get("name")
            s = self.services.get(name)
            if s:
                return QueryResult([[s["name"], s["status"], s["tier"], s["team"], s["language"]]])
            return QueryResult([])

        # Recent commits
        if "MATCH (pr:PullRequest)-[:MODIFIED_SERVICE]" in cypher_clean:
            svc_name = params.get("svc")
            rows = []
            for pr in self.pull_requests:
                if pr["service"] == svc_name:
                    author = self.engineers.get(pr["author_id"], {})
                    reviewer = self.engineers.get(pr["reviewer_id"], {})
                    rows.append([
                        pr["id"], pr["title"], pr["merged_at"], pr["diff_summary"],
                        author.get("name", "Unknown"), author.get("slack", "@dev"), author.get("role", "Dev"),
                        reviewer.get("name", "Unknown"), reviewer.get("slack", "@lead"),
                    ])
            return QueryResult(rows)

        # Service owner
        if "MATCH (e:Engineer)-[:OWNS]" in cypher_clean:
            svc_name = params.get("name")
            eng_id = self.ownership.get(svc_name)
            if eng_id and eng_id in self.engineers:
                e = self.engineers[eng_id]
                return QueryResult([[e["name"], e["slack"], e["role"], e["team"]]])
            return QueryResult([])

        # Procedure metadata
        if "MATCH (p:Procedure {trigger_pattern: $pattern})" in cypher_clean:
            pat = params.get("pattern")
            p = self.procedures.get(pat)
            if p:
                return QueryResult([[p["name"], p["description"], p["success_rate"]]])
            return QueryResult([])

        # Procedure steps
        if "MATCH (p:Procedure {name: $proc_name})-[:STEP]" in cypher_clean:
            p_name = params.get("proc_name")
            for proc in self.procedures.values():
                if proc["name"] == p_name:
                    rows = [
                        [step["step_id"], step["name"], step["tool"], step["params"], step["order"]]
                        for step in proc["steps"]
                    ]
                    return QueryResult(rows)
            return QueryResult([])

        # Find similar episodes
        if "MATCH (ep:Episode)" in cypher_clean and "symptoms" in params:
            symptoms = [s.lower() for s in params.get("symptoms", [])]
            rows = []
            for ep in self.episodes:
                match = any(sym in ep["root_cause"].lower() or sym in ep["alert_name"].lower() for sym in symptoms)
                if match:
                    rows.append([
                        ep["incident_id"], ep["alert_name"], ep["root_cause"],
                        ep["root_cause_pr_id"], ep["mttr_seconds"], ep["status"],
                        ep["timestamp"], ep.get("involved_services", []),
                    ])
            return QueryResult(rows)

        # Get all episodes
        if "MATCH (ep:Episode)" in cypher_clean and "RETURN ep.incident_id" in cypher_clean:
            rows = [
                [ep["incident_id"], ep["alert_name"], ep["root_cause"], ep["mttr_seconds"], ep["status"], ep["timestamp"]]
                for ep in self.episodes
            ]
            return QueryResult(rows)

        # Write episode
        if "MERGE (ep:Episode {incident_id: $incident_id})" in cypher_clean:
            self.episodes.insert(0, {
                "incident_id": params.get("incident_id"),
                "alert_name": params.get("alert_name"),
                "root_cause": params.get("root_cause"),
                "root_cause_pr_id": params.get("pr_id"),
                "mttr_seconds": params.get("mttr", 15),
                "timestamp": params.get("ts"),
                "status": "resolved",
                "involved_services": [],
            })
            return QueryResult([])

        # Who knows about this service (Track 03: Company Brain)
        if "who_knows" in cypher_clean or ("AUTHORED" in cypher_clean and "MODIFIED_SERVICE" in cypher_clean and ("count" in cypher_clean or "pr_count" in cypher_clean)):
            svc_name = params.get("svc") or params.get("service") or params.get("name")
            counts = {}
            for pr in self.pull_requests:
                if pr["service"] == svc_name:
                    aid = pr["author_id"]
                    counts[aid] = counts.get(aid, 0) + 1
            if svc_name in self.ownership:
                oid = self.ownership[svc_name]
                counts[oid] = counts.get(oid, 0) + 2
            rows = []
            for eid, c in sorted(counts.items(), key=lambda x: x[1], reverse=True):
                e = self.engineers.get(eid, {})
                rows.append([e.get("name", "Unknown"), e.get("slack", "@eng"), e.get("role", "Engineer"), c])
            return QueryResult(rows)

        # Company Brain Context: tickets, slack chats, docs
        if "CompanyBrain" in cypher_clean or "Ticket" in cypher_clean or "SlackMessage" in cypher_clean or "Doc" in cypher_clean:
            svc_name = params.get("svc") or params.get("service") or params.get("name")
            tickets = [t for t in self.tickets if not svc_name or t["service"] == svc_name]
            slack = [m for m in self.slack_messages if not svc_name or m["service"] == svc_name]
            docs = [d for d in self.docs if not svc_name or d["service"] == svc_name]
            return QueryResult([[tickets, slack, docs]])

        # Semantic Rule & Failure Ontology
        if "SemanticRule" in cypher_clean or "FailureOntology" in cypher_clean:
            pat = params.get("pattern")
            if pat and pat in self.semantic_rules:
                r = self.semantic_rules[pat]
                return QueryResult([[r["pattern"], r["category"], r["layer"], r["impact"], r["suggested_mitigation"], r["blast_risk"]]])
            rows = [[r["pattern"], r["category"], r["layer"], r["impact"], r["suggested_mitigation"], r["blast_risk"]] for r in self.semantic_rules.values()]
            return QueryResult(rows)

        # Multi-Agent Handoff State
        if "AgentHandoff" in cypher_clean:
            if "CREATE" in cypher_clean or "MERGE" in cypher_clean:
                self.handoffs.append({
                    "from_agent": params.get("from_agent"),
                    "to_agent": params.get("to_agent"),
                    "incident_id": params.get("incident_id"),
                    "summary": params.get("summary"),
                    "timestamp": params.get("ts"),
                })
                return QueryResult([])
            inc = params.get("incident_id")
            matches = [h for h in self.handoffs if not inc or h.get("incident_id") == inc]
            return QueryResult([[h["from_agent"], h["to_agent"], h["incident_id"], h["summary"], h["timestamp"]] for h in matches])

        return QueryResult([])


import socket
import time

_is_falkordb_available: bool | None = None
_last_ping_time: float = 0
PING_CACHE_TTL = 15.0  # seconds


def _connect_falkordb():
    from falkordb import FalkorDB
    kwargs = {
        "host": FALKORDB_HOST,
        "port": FALKORDB_PORT,
        "socket_timeout": 5.0,
        "socket_connect_timeout": 3.0,
    }
    if FALKORDB_PASSWORD:
        kwargs["password"] = FALKORDB_PASSWORD
    if FALKORDB_USERNAME:
        kwargs["username"] = FALKORDB_USERNAME
    if FALKORDB_SSL:
        kwargs["ssl"] = True
    return FalkorDB(**kwargs)


def ping(force_refresh: bool = False) -> bool:
    """Checks if a live FalkorDB instance is reachable with fast socket probing and caching."""
    global _is_falkordb_available, _last_ping_time
    now = time.time()
    if not force_refresh and _is_falkordb_available is not None and (now - _last_ping_time) < PING_CACHE_TTL:
        return _is_falkordb_available

    try:
        with socket.create_connection((FALKORDB_HOST, FALKORDB_PORT), timeout=2.0):
            pass
    except Exception:
        _is_falkordb_available = False
        _last_ping_time = now
        return False

    try:
        client = _connect_falkordb()
        client.connection.ping()
        _is_falkordb_available = True
    except Exception:
        _is_falkordb_available = False
    _last_ping_time = now
    return _is_falkordb_available


def get_client():
    global _client
    if _client is None:
        try:
            _client = _connect_falkordb()
        except Exception:
            _client = None
    return _client


def get_graph(graph_name: str = ACTIVE_GRAPH):
    """
    Returns an isolated FalkorDB graph.
    If FalkorDB server is reachable, uses the official FalkorDB client.
    Otherwise, returns an isolated InMemoryGraph instance.
    """
    if ping():
        try:
            client = get_client()
            if client:
                return client.select_graph(graph_name)
        except Exception:
            pass

    # In-memory fallback
    if graph_name not in _in_memory_graphs:
        _in_memory_graphs[graph_name] = InMemoryGraph(graph_name)
    return _in_memory_graphs[graph_name]


def get_prod_graph():
    return get_graph("causalmesh_prod")


def get_staging_graph():
    return get_graph("causalmesh_staging")

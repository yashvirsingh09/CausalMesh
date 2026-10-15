"""
graph/seed.py — Synthetic data generator.
Creates a realistic 25-service e-commerce platform topology in FalkorDB
with engineers, PRs, procedures, and past incident episodes.

Run directly:  python graph/seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone, timedelta
from graph.client import get_graph
from config import ACTIVE_GRAPH

# ─── TOPOLOGY ─────────────────────────────────────────────────────────────────

SERVICES = [
    # (name, team, tier, language)
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

# Service call dependencies: (caller, callee, protocol, avg_latency_ms, rps)
DEPENDENCIES = [
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

# ─── ENGINEERS ────────────────────────────────────────────────────────────────

ENGINEERS = [
    # (id, name, slack, role, team)
    ("eng_alice",  "Alice Mehta",   "@alice",   "Staff SRE",       "platform"),
    ("eng_dave",   "Dave Kim",      "@dave",    "Backend Dev",     "commerce"),
    ("eng_priya",  "Priya Nair",    "@priya",   "Senior Dev",      "payments"),
    ("eng_sam",    "Sam Torres",    "@sam",     "ML Engineer",     "ml"),
    ("eng_chen",   "Chen Wei",      "@chen",    "Principal Eng",   "platform"),
]

# Service ownership: (engineer_id, service_name)
OWNERSHIP = [
    ("eng_alice",  "api-gateway"),
    ("eng_alice",  "auth-service"),
    ("eng_alice",  "redis-session"),
    ("eng_dave",   "checkout-service"),
    ("eng_dave",   "inventory-service"),
    ("eng_dave",   "inventory-postgres"),
    ("eng_priya",  "payment-service"),
    ("eng_priya",  "fraud-detection-service"),
    ("eng_priya",  "payment-postgres"),
    ("eng_sam",    "recommendation-service"),
    ("eng_sam",    "analytics-service"),
    ("eng_chen",   "kafka-events"),
    ("eng_chen",   "notification-service"),
]

# ─── PULL REQUESTS ────────────────────────────────────────────────────────────

def _ago(minutes: int) -> str:
    """Returns ISO timestamp N minutes in the past."""
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()

PULL_REQUESTS = [
    # (id, title, author_id, reviewer_id, service_name, merged_minutes_ago, diff_summary)
    ("PR-88",  "Reduce DB idle timeout 30s→2s for lower memory",
     "eng_dave",  "eng_alice",  "inventory-service",      35,
     "Changed db_pool.idle_timeout from 30 to 2 in inventory/config.py"),

    ("PR-87",  "Add retry logic to payment webhook handler",
     "eng_priya", "eng_chen",   "payment-service",        90,
     "Added exponential backoff on Stripe webhook failures"),

    ("PR-86",  "Upgrade recommendation model to v3.2",
     "eng_sam",   "eng_alice",  "recommendation-service", 200,
     "Swapped sklearn model artifact, updated inference pipeline"),

    ("PR-85",  "Fix session token expiry race condition",
     "eng_alice", "eng_chen",   "auth-service",           480,
     "Added distributed lock on token refresh endpoint"),

    ("PR-84",  "Add kafka consumer lag alerting",
     "eng_chen",  "eng_alice",  "analytics-service",      1440,
     "New Prometheus metrics for consumer group lag on events topic"),

    ("PR-83",  "Increase redis-cart maxmemory-policy to allkeys-lru",
     "eng_dave",  "eng_priya",  "redis-cart",             2880,
     "Changed eviction policy to prevent OOM on cart spike"),

    ("PR-82",  "Optimise inventory query: add composite index",
     "eng_dave",  "eng_chen",   "inventory-postgres",     4320,
     "CREATE INDEX ON inventory(sku, warehouse_id) — was doing full table scans"),
]

# ─── PROCEDURAL MEMORY PLAYBOOKS ─────────────────────────────────────────────

PROCEDURES = [
    {
        "name": "resolve_db_pool_starvation",
        "trigger_pattern": "db_pool_exhaustion",
        "success_rate": 0.95,
        "description": "Fixes connection pool exhaustion by scaling max connections and restarting service.",
        "steps": [
            ("step_pool_1", "scale_db_pool",       "mcp_infra:patch_config",      {"param": "max_conn=250"}),
            ("step_pool_2", "restart_pods",        "mcp_k8s:rollout_restart",     {"timeout": 60}),
            ("step_pool_3", "verify_error_rate",   "mcp_metrics:error_rate",      {"threshold": 0.01}),
        ],
    },
    {
        "name": "resolve_cache_miss_storm",
        "trigger_pattern": "cache_eviction_storm",
        "success_rate": 0.88,
        "description": "Clears corrupted cache keys and warms cache for hot paths.",
        "steps": [
            ("step_cache_1", "flush_cache_namespace",  "mcp_redis:flush_ns",         {"namespace": "cart:*"}),
            ("step_cache_2", "warm_cache",             "mcp_infra:trigger_warmup",   {"endpoint": "/warmup"}),
            ("step_cache_3", "verify_hit_rate",        "mcp_metrics:cache_hit_rate", {"threshold": 0.8}),
        ],
    },
    {
        "name": "resolve_canary_regression",
        "trigger_pattern": "canary_error_spike",
        "success_rate": 0.99,
        "description": "Rolls back a bad canary deployment to the previous stable version.",
        "steps": [
            ("step_canary_1", "rollback_canary",      "mcp_k8s:rollout_undo",       {}),
            ("step_canary_2", "verify_stable",        "mcp_metrics:error_rate",     {"threshold": 0.005}),
            ("step_canary_3", "notify_team",          "mcp_slack:notify",           {"channel": "#incidents"}),
        ],
    },
]

# ─── PAST INCIDENT EPISODES ───────────────────────────────────────────────────

EPISODES = [
    {
        "incident_id":      "INC-2026-09-03",
        "alert_name":       "HighErrorRate:checkout-service",
        "root_cause":       "PR-83 changed Redis eviction policy causing cart key evictions under load",
        "root_cause_pr_id": "PR-83",
        "mttr_seconds":     28,
        "timestamp":        "2026-09-03T14:22:00+00:00",
        "status":           "resolved",
        "involved_services": ["checkout-service", "redis-cart"],
    },
    {
        "incident_id":      "INC-2026-08-17",
        "alert_name":       "DatabaseConnectionsExhausted:payment-postgres",
        "root_cause":       "Scheduled batch job triggered connection pool exhaustion on payment-postgres",
        "root_cause_pr_id": "PR-82",
        "mttr_seconds":     47,
        "timestamp":        "2026-08-17T03:11:00+00:00",
        "status":           "resolved",
        "involved_services": ["payment-service", "payment-postgres"],
    },
]

# ─── CONTEXT ENGINE (TICKETS, SLACK, DOCS) ──────────────────────────────────

TICKETS = [
    ("TICK-1042", "Memory pressure on inventory workers under peak load", "PR-88", "inventory-service", "P2", "closed"),
    ("TICK-980", "Payment webhook failures causing checkout dropoffs", "PR-87", "payment-service", "P1", "closed"),
    ("TICK-744", "Upgrade recommendation model accuracy for catalog search", "PR-86", "recommendation-service", "P3", "closed"),
    ("TICK-610", "Session token race condition during token refresh", "PR-85", "auth-service", "P2", "closed"),
    ("TICK-520", "Cart cache OOM eviction spike during flash sales", "PR-83", "redis-cart", "P1", "closed"),
]

SLACK_MESSAGES = [
    ("MSG-902", "#deployments", "@dave", "inventory-service", "PR-88", "Merged PR-88 (tuning idle timeout 30s -> 2s on inventory-service to reduce memory footprint).", 34),
    ("MSG-890", "#payments-alerts", "@priya", "payment-service", "PR-87", "Shipped exponential backoff for Stripe webhooks in PR-87.", 88),
    ("MSG-810", "#ml-ops", "@sam", "recommendation-service", "PR-86", "Canary deployment of model v3.2 artifact initiated for recommendation-service.", 195),
    ("MSG-750", "#incidents", "@alice", "inventory-postgres", None, "Remember runbook DOC-1 if Postgres connection pool utilization spikes above 90%.", 1440),
]

DOCS = [
    ("DOC-1", "Postgres Connection Pool Starvation & Recovery Runbook", "inventory-postgres", "https://wiki.internal/runbooks/db-pool", "runbook", "Procedure to scale pool connections and trigger pod rolling restart during starvation."),
    ("DOC-2", "Redis Cache Invalidation & Eviction Architecture RFC", "redis-cart", "https://wiki.internal/rfc/redis-eviction", "architecture", "Standards for cache TTL, allkeys-lru eviction, and warming hot keys."),
    ("DOC-3", "Machine Learning Canary Rollback Procedures", "recommendation-service", "https://wiki.internal/runbooks/canary-undo", "runbook", "Step-by-step rollout undo and baseline latency verification."),
]

# ─── SEMANTIC MEMORY (RULES & FAILURE ONTOLOGY) ─────────────────────────────

SEMANTIC_RULES = [
    ("db_pool_exhaustion", "ResourceStarvation", "database_pool", "Connection pool saturation cascades upstream 504 gateway timeouts", "Scale pool capacity and rollout restart", "Critical"),
    ("cache_eviction_storm", "CacheThrashing", "caching_layer", "Uncached requests saturate backend database", "Flush corrupted namespace and warm hot keys", "High"),
    ("canary_error_spike", "RegressionDeployment", "application_code", "Inference latency spike degrades user-facing response times", "Roll back canary deployment to previous revision", "Medium"),
]


# ─── SEEDING LOGIC ────────────────────────────────────────────────────────────

def seed(graph_name: str = ACTIVE_GRAPH, verbose: bool = True) -> None:
    g = get_graph(graph_name)

    def log(msg: str):
        if verbose:
            try:
                print(f"  {msg}")
            except Exception:
                pass

    if verbose:
        print(f"\n[+] Seeding FalkorDB graph: '{graph_name}'")
        print("\n[*] Creating service nodes...")
    for name, team, tier, lang in SERVICES:
        g.query(
            """
            MERGE (s:Service {name: $name})
            SET s.team = $team, s.tier = $tier,
                s.language = $lang, s.status = 'healthy',
                s.version = '1.0.0'
            """,
            {"name": name, "team": team, "tier": tier, "lang": lang}
        )
        log(f"  [OK] Service: {name} ({tier})")

    # 2. Dependencies
    log("\n[*] Creating dependency edges...")
    for caller, callee, proto, latency, rps in DEPENDENCIES:
        g.query(
            """
            MATCH (a:Service {name: $caller}), (b:Service {name: $callee})
            MERGE (a)-[r:CALLS]->(b)
            SET r.protocol = $proto, r.latency_p99_ms = $latency,
                r.requests_per_sec = $rps, r.error_rate = 0.0
            """,
            {"caller": caller, "callee": callee,
             "proto": proto, "latency": latency, "rps": rps}
        )
        log(f"  -> {caller} --[{proto}]--> {callee}")

    # 3. Engineers
    log("\n[*] Creating engineer nodes...")
    for eng_id, name, slack, role, team in ENGINEERS:
        g.query(
            """
            MERGE (e:Engineer {id: $id})
            SET e.name = $name, e.slack = $slack,
                e.role = $role, e.team = $team
            """,
            {"id": eng_id, "name": name, "slack": slack, "role": role, "team": team}
        )
        log(f"  [OK] Engineer: {name} ({role})")

    # 4. Ownership
    log("[*] Creating ownership edges...")
    for eng_id, svc_name in OWNERSHIP:
        g.query(
            """
            MATCH (e:Engineer {id: $eng_id}), (s:Service {name: $svc})
            MERGE (e)-[:OWNS]->(s)
            """,
            {"eng_id": eng_id, "svc": svc_name}
        )
        log(f"  [OK] {eng_id} OWNS {svc_name}")

    # 5. Pull Requests
    log("[*] Creating pull request nodes...")
    for pr_id, title, author_id, reviewer_id, svc_name, minutes_ago, diff in PULL_REQUESTS:
        merged_at = _ago(minutes_ago)
        g.query(
            """
            MERGE (pr:PullRequest {id: $id})
            SET pr.title = $title, pr.merged_at = $merged_at,
                pr.diff_summary = $diff

            WITH pr
            MATCH (a:Engineer {id: $author_id})
            MERGE (a)-[:AUTHORED]->(pr)

            WITH pr
            MATCH (r:Engineer {id: $reviewer_id})
            MERGE (r)-[:APPROVED]->(pr)

            WITH pr
            MATCH (s:Service {name: $svc})
            MERGE (pr)-[:MODIFIED_SERVICE]->(s)
            """,
            {
                "id": pr_id, "title": title, "merged_at": merged_at,
                "diff": diff, "author_id": author_id,
                "reviewer_id": reviewer_id, "svc": svc_name,
            }
        )
        log(f"  [OK] PR {pr_id}: {title[:50]}...")

    # 6. Procedures (Playbooks as executable graphs)
    log("[*] Creating procedural memory playbooks...")
    for proc in PROCEDURES:
        g.query(
            """
            MERGE (p:Procedure {name: $name})
            SET p.trigger_pattern = $trigger, p.success_rate = $rate,
                p.description = $desc
            """,
            {
                "name": proc["name"],
                "trigger": proc["trigger_pattern"],
                "rate": proc["success_rate"],
                "desc": proc["description"],
            }
        )

        prev_step_name = None
        for i, (step_id, step_name, tool, params) in enumerate(proc["steps"]):
            g.query(
                """
                MERGE (a:Action {id: $step_id})
                SET a.name = $name, a.tool = $tool, a.params = $params, a.order = $order
                """,
                {
                    "step_id": step_id, "name": step_name,
                    "tool": tool, "params": str(params), "order": i + 1,
                }
            )

            if i == 0:
                # First step: link procedure -> action with STEP rel
                g.query(
                    """
                    MATCH (p:Procedure {name: $proc_name}), (a:Action {id: $step_id})
                    MERGE (p)-[:STEP {order: 1}]->(a)
                    """,
                    {"proc_name": proc["name"], "step_id": step_id}
                )
            else:
                # Subsequent steps: link previous action -> this action
                g.query(
                    """
                    MATCH (prev:Action {id: $prev_id}), (curr:Action {id: $curr_id})
                    MERGE (prev)-[:NEXT]->(curr)
                    """,
                    {"prev_id": prev_step_name, "curr_id": step_id}
                )
            prev_step_name = step_id

        log(f"  [OK] Playbook: {proc['name']} ({len(proc['steps'])} steps)")

    # 7. Past Incident Episodes (Episodic Memory)
    log("[*] Creating past incident episodes...")
    for ep in EPISODES:
        g.query(
            """
            MERGE (e:Episode {incident_id: $incident_id})
            SET e.alert_name = $alert_name,
                e.root_cause = $root_cause,
                e.root_cause_pr_id = $pr_id,
                e.mttr_seconds = $mttr,
                e.timestamp = $ts,
                e.status = $status
            """,
            {
                "incident_id": ep["incident_id"],
                "alert_name":  ep["alert_name"],
                "root_cause":  ep["root_cause"],
                "pr_id":       ep["root_cause_pr_id"],
                "mttr":        ep["mttr_seconds"],
                "ts":          ep["timestamp"],
                "status":      ep["status"],
            }
        )
        for svc in ep["involved_services"]:
            g.query(
                """
                MATCH (ep:Episode {incident_id: $incident_id}),
                      (s:Service {name: $svc})
                MERGE (ep)-[:INVOLVED]->(s)
                """,
                {"incident_id": ep["incident_id"], "svc": svc}
            )
        log(f"  [OK] Episode: {ep['incident_id']} (MTTR {ep['mttr_seconds']}s)")

    # 8. Company Brain: Tickets (Track 03)
    log("[*] Creating Jira Tickets...")
    for tid, title, pr_id, svc, priority, status in TICKETS:
        g.query(
            """
            MERGE (t:Ticket {id: $id})
            SET t.title = $title, t.priority = $priority,
                t.status = $status, t.service = $svc, t.pr_id = $pr_id
            WITH t
            MATCH (pr:PullRequest {id: $pr_id})
            MERGE (t)-[:ATTACHED_TO]->(pr)
            """,
            {"id": tid, "title": title, "priority": priority, "status": status, "svc": svc, "pr_id": pr_id}
        )
        log(f"  [OK] Ticket: {tid} attached to {pr_id}")

    # 9. Company Brain: Slack Messages (Track 03)
    log("[*] Creating Slack Messages...")
    for mid, channel, author, svc, pr_id, text, mins in SLACK_MESSAGES:
        ts = _ago(mins)
        g.query(
            """
            MERGE (m:SlackMessage {id: $id})
            SET m.channel = $channel, m.author = $author,
                m.service = $svc, m.pr_id = $pr_id,
                m.text = $text, m.timestamp = $ts
            WITH m
            MATCH (s:Service {name: $svc})
            MERGE (m)-[:REFERENCES]->(s)
            """,
            {"id": mid, "channel": channel, "author": author, "svc": svc, "pr_id": pr_id, "text": text, "ts": ts}
        )
        log(f"  [OK] Slack: {mid} in {channel}")

    # 10. Company Brain: Runbook Documentation (Track 03)
    log("[*] Creating Runbooks & Architecture Docs...")
    for doc_id, title, svc, url, category, summary in DOCS:
        g.query(
            """
            MERGE (d:Doc {id: $id})
            SET d.title = $title, d.url = $url,
                d.category = $category, d.summary = $summary,
                d.service = $svc
            WITH d
            MATCH (s:Service {name: $svc})
            MERGE (d)-[:DOCUMENTS]->(s)
            """,
            {"id": doc_id, "title": title, "url": url, "category": category, "summary": summary, "svc": svc}
        )
        log(f"  [OK] Doc: {doc_id} ({category})")

    # 11. Semantic Memory Rules (Track 02)
    log("[*] Creating Semantic Memory Failure Rules...")
    for pattern, category, layer, impact, mitigation, risk in SEMANTIC_RULES:
        g.query(
            """
            MERGE (r:SemanticRule {pattern: $pattern})
            SET r.category = $category, r.layer = $layer,
                r.impact = $impact, r.suggested_mitigation = $mitigation,
                r.blast_risk = $risk
            """,
            {"pattern": pattern, "category": category, "layer": layer, "impact": impact, "mitigation": mitigation, "risk": risk}
        )
        log(f"  [OK] Rule: {pattern} [{category}]")

    if verbose:
        print(f"\n[OK] Seeding complete for graph '{graph_name}'!")
        print(f"   Services: {len(SERVICES)}")
        print(f"   Dependencies: {len(DEPENDENCIES)}")
        print(f"   Engineers: {len(ENGINEERS)}")
        print(f"   Pull Requests: {len(PULL_REQUESTS)}")
        print(f"   Playbooks: {len(PROCEDURES)}")
        print(f"   Past Episodes: {len(EPISODES)}")
        print(f"   Tickets: {len(TICKETS)}")
        print(f"   Slack Messages: {len(SLACK_MESSAGES)}")
        print(f"   Docs: {len(DOCS)}")
        print(f"   Semantic Rules: {len(SEMANTIC_RULES)}")
        print(f"\n   FalkorDB Browser: http://localhost:3000")
        print(f"   Graph name: {graph_name}\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", default=ACTIVE_GRAPH,
                        help="FalkorDB graph name to seed")
    args = parser.parse_args()
    seed(args.graph)

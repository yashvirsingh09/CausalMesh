"""
graph/queries.py — All FalkorDB Cypher queries as typed Python functions.
These are the "graph tools" that the AI agents call during reasoning.

Every agent decision is backed by a Cypher query — no hallucination,
only graph-traversal facts.
"""
from datetime import datetime, timezone, timedelta
from graph.client import get_graph, ping
from config import ACTIVE_GRAPH


def _g(graph_name: str = ACTIVE_GRAPH):
    return get_graph(graph_name)


# ─── TOPOLOGY TRAVERSAL & BLAST RADIUS ──────────────────────────────────────

def get_blast_radius(service_name: str, max_hops: int = 3,
                     graph_name: str = ACTIVE_GRAPH) -> list[dict]:
    """
    Computes the blast radius of a failing service by traversing
    both upstream (who calls it?) and downstream (what does it call?)
    dependency chains up to max_hops deep.

    Returns a list of affected services with their distance and status.
    """
    hops = max(1, min(int(max_hops), 5))
    result = _g(graph_name).query(
        f"""
        MATCH path = (root:Service {{name: $name}})-[:CALLS*1..{hops}]->(dep:Service)
        RETURN dep.name AS service,
               dep.status AS status,
               dep.team AS team,
               length(path) AS hop_distance
        UNION
        MATCH path2 = (upstream:Service)-[:CALLS*1..{hops}]->(root2:Service {{name: $name}})
        RETURN upstream.name AS service,
               upstream.status AS status,
               upstream.team AS team,
               length(path2) AS hop_distance
        ORDER BY hop_distance ASC
        """,
        {"name": service_name}
    )
    return [
        {
            "service": r[0],
            "status": r[1],
            "team": r[2],
            "hop_distance": r[3],
        }
        for r in result.result_set
    ]


def get_service_status(service_name: str,
                       graph_name: str = ACTIVE_GRAPH) -> dict | None:
    """Returns current status and metadata for a service."""
    result = _g(graph_name).query(
        """
        MATCH (s:Service {name: $name})
        RETURN s.name, s.status, s.tier, s.team, s.language
        """,
        {"name": service_name}
    )
    if not result.result_set:
        return None
    r = result.result_set[0]
    return {"name": r[0], "status": r[1], "tier": r[2], "team": r[3], "language": r[4]}


def get_all_services(graph_name: str = ACTIVE_GRAPH) -> list[dict]:
    """Returns all services with their current status — used to build the graph map."""
    result = _g(graph_name).query(
        """
        MATCH (s:Service)
        RETURN s.name, s.status, s.tier, s.team, s.language
        ORDER BY s.tier, s.name
        """
    )
    return [
        {"name": r[0], "status": r[1], "tier": r[2], "team": r[3], "language": r[4]}
        for r in result.result_set
    ]


def get_all_dependencies(graph_name: str = ACTIVE_GRAPH) -> list[dict]:
    """Returns all CALLS edges — used to build the frontend graph topology."""
    result = _g(graph_name).query(
        """
        MATCH (a:Service)-[r:CALLS]->(b:Service)
        RETURN a.name, b.name, r.protocol, r.latency_p99_ms,
               r.error_rate, r.requests_per_sec
        """
    )
    return [
        {
            "source": r[0], "target": r[1],
            "protocol": r[2], "latency_p99_ms": r[3],
            "error_rate": r[4], "rps": r[5],
        }
        for r in result.result_set
    ]


def update_service_status(service_name: str, status: str,
                          graph_name: str = ACTIVE_GRAPH) -> None:
    """Updates the live status of a service node (healthy/degraded/failing)."""
    _g(graph_name).query(
        "MATCH (s:Service {name: $name}) SET s.status = $status",
        {"name": service_name, "status": status}
    )


# ─── CONTEXT ENGINE: CODE REPOSITORIES & TEAM ATTRIBUTION ─────────────────

def get_recent_commits(service_name: str, hours: int = 2,
                       graph_name: str = ACTIVE_GRAPH) -> list[dict]:
    """
    Finds PRs merged in the last N hours that modified the given service,
    with full author and reviewer attribution.

    This is the key query that traces human decisions to system failures.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    result = _g(graph_name).query(
        """
        MATCH (pr:PullRequest)-[:MODIFIED_SERVICE]->(s:Service {name: $svc})
        WHERE pr.merged_at >= $cutoff
        MATCH (author:Engineer)-[:AUTHORED]->(pr)
        OPTIONAL MATCH (reviewer:Engineer)-[:APPROVED]->(pr)
        RETURN pr.id, pr.title, pr.merged_at, pr.diff_summary,
               author.name, author.slack, author.role,
               reviewer.name, reviewer.slack
        ORDER BY pr.merged_at DESC
        """,
        {"svc": service_name, "cutoff": cutoff}
    )
    return [
        {
            "pr_id":          r[0],
            "title":          r[1],
            "merged_at":      r[2],
            "diff_summary":   r[3],
            "author_name":    r[4],
            "author_slack":   r[5],
            "author_role":    r[6],
            "reviewer_name":  r[7],
            "reviewer_slack": r[8],
        }
        for r in result.result_set
    ]


def get_service_owner(service_name: str,
                      graph_name: str = ACTIVE_GRAPH) -> dict | None:
    """
    Finds the engineer who owns a given service.
    Used to notify the right person during an incident.
    """
    result = _g(graph_name).query(
        """
        MATCH (e:Engineer)-[:OWNS]->(s:Service {name: $name})
        RETURN e.name, e.slack, e.role, e.team
        """,
        {"name": service_name}
    )
    if not result.result_set:
        return None
    r = result.result_set[0]
    return {"name": r[0], "slack": r[1], "role": r[2], "team": r[3]}


def trace_decision_chain(pr_id: str,
                         graph_name: str = ACTIVE_GRAPH) -> dict | None:
    """
    For a given PR, returns the full decision chain:
    who authored it, who approved it, which service was changed,
    and what the diff was.
    """
    result = _g(graph_name).query(
        """
        MATCH (author:Engineer)-[:AUTHORED]->(pr:PullRequest {id: $pr_id})
              -[:MODIFIED_SERVICE]->(svc:Service)
        OPTIONAL MATCH (reviewer:Engineer)-[:APPROVED]->(pr)
        RETURN pr.id, pr.title, pr.merged_at, pr.diff_summary,
               author.name, author.slack,
               reviewer.name, reviewer.slack,
               svc.name, svc.tier, svc.team
        """,
        {"pr_id": pr_id}
    )
    if not result.result_set:
        return None
    r = result.result_set[0]
    return {
        "pr_id":          r[0],
        "title":          r[1],
        "merged_at":      r[2],
        "diff":           r[3],
        "author_name":    r[4],
        "author_slack":   r[5],
        "reviewer_name":  r[6],
        "reviewer_slack": r[7],
        "service_name":   r[8],
        "service_tier":   r[9],
        "service_team":   r[10],
    }


# ─── PROCEDURAL PLAYBOOKS & EPISODIC MEMORY ────────────────────────────────

def get_playbook(trigger_pattern: str,
                 graph_name: str = ACTIVE_GRAPH) -> dict | None:
    """
    Retrieves a Procedural Memory playbook for a given failure pattern.
    The playbook is stored as an ordered graph of Action nodes.

    Returns the procedure metadata + all steps in execution order.
    """
    # Get procedure metadata
    proc_result = _g(graph_name).query(
        """
        MATCH (p:Procedure {trigger_pattern: $pattern})
        RETURN p.name, p.description, p.success_rate
        """,
        {"pattern": trigger_pattern}
    )
    if not proc_result.result_set:
        return None

    r = proc_result.result_set[0]
    proc_name = r[0]

    # Traverse the step chain: Procedure -[STEP]-> Action1 -[NEXT]-> Action2 ...
    steps_result = _g(graph_name).query(
        """
        MATCH (p:Procedure {name: $proc_name})-[:STEP]->(first:Action)
        WITH first
        MATCH path = (first)-[:NEXT*0..10]->(step:Action)
        RETURN step.id, step.name, step.tool, step.params, step.order
        ORDER BY step.order ASC
        """,
        {"proc_name": proc_name}
    )

    steps = [
        {
            "step_id": s[0],
            "name": s[1],
            "tool": s[2],
            "params": s[3],
            "order": s[4],
        }
        for s in steps_result.result_set
    ]

    return {
        "name":          r[0],
        "description":   r[1],
        "success_rate":  r[2],
        "steps":         steps,
    }


def list_all_playbooks(graph_name: str = ACTIVE_GRAPH) -> list[dict]:
    """Lists all procedural playbooks stored in FalkorDB Procedural Memory."""
    patterns = ["db_pool_exhaustion", "cache_eviction_storm", "canary_error_spike"]
    results = []
    for pat in patterns:
        pb = get_playbook(pat, graph_name)
        if pb:
            results.append({
                "trigger_pattern": pat,
                "name": pb["name"],
                "description": pb["description"],
                "success_rate": pb["success_rate"],
                "step_count": len(pb["steps"]),
                "steps": pb["steps"],
            })
    return results


def get_service_details(service_name: str, graph_name: str = ACTIVE_GRAPH) -> dict | None:
    """Returns rich metadata, ownership attribution, recent PRs, and callers/dependencies for a service."""
    status = get_service_status(service_name, graph_name)
    if not status:
        return None
    owner = get_service_owner(service_name, graph_name)
    commits = get_recent_commits(service_name, hours=24, graph_name=graph_name)
    all_deps = get_all_dependencies(graph_name)
    upstream = [d for d in all_deps if d["target"] == service_name]
    downstream = [d for d in all_deps if d["source"] == service_name]
    return {
        **status,
        "owner": owner,
        "recent_commits": commits,
        "upstream_callers": upstream,
        "downstream_dependencies": downstream,
    }


def find_similar_incidents(symptoms: list[str],
                           graph_name: str = ACTIVE_GRAPH) -> list[dict]:
    """
    Searches past incident episodes by matching symptoms (keywords)
    against stored root_cause text.

    This is the long-term episodic memory retrieval mechanism —
    agents learn from what worked before.
    """
    # Build a simple keyword match across all episodes
    result = _g(graph_name).query(
        """
        MATCH (ep:Episode)
        WHERE any(symptom IN $symptoms WHERE toLower(ep.root_cause) CONTAINS toLower(symptom))
           OR any(symptom IN $symptoms WHERE toLower(ep.alert_name) CONTAINS toLower(symptom))
        MATCH (ep)-[:INVOLVED]->(svc:Service)
        RETURN ep.incident_id, ep.alert_name, ep.root_cause,
               ep.root_cause_pr_id, ep.mttr_seconds, ep.status, ep.timestamp,
               collect(svc.name) AS involved_services
        ORDER BY ep.mttr_seconds ASC
        LIMIT 3
        """,
        {"symptoms": symptoms}
    )
    return [
        {
            "incident_id":     r[0],
            "alert_name":      r[1],
            "root_cause":      r[2],
            "root_cause_pr_id": r[3],
            "mttr_seconds":    r[4],
            "status":          r[5],
            "timestamp":       r[6],
            "involved_services": r[7],
        }
        for r in result.result_set
    ]


def write_episode(incident_id: str, alert_name: str, root_cause: str,
                  root_cause_pr_id: str, mttr_seconds: int,
                  involved_services: list[str],
                  graph_name: str = ACTIVE_GRAPH) -> None:
    """
    Writes a resolved incident as an Episodic Memory node in FalkorDB.
    This is how the agent swarm "learns" — every resolution is persisted
    so future incidents can find similar patterns.
    """
    now = datetime.now(timezone.utc).isoformat()
    _g(graph_name).query(
        """
        MERGE (ep:Episode {incident_id: $incident_id})
        SET ep.alert_name = $alert_name,
            ep.root_cause = $root_cause,
            ep.root_cause_pr_id = $pr_id,
            ep.mttr_seconds = $mttr,
            ep.timestamp = $ts,
            ep.status = 'resolved'
        """,
        {
            "incident_id": incident_id, "alert_name": alert_name,
            "root_cause": root_cause, "pr_id": root_cause_pr_id,
            "mttr": mttr_seconds, "ts": now,
        }
    )
    for svc in involved_services:
        _g(graph_name).query(
            """
            MATCH (ep:Episode {incident_id: $incident_id}),
                  (s:Service {name: $svc})
            MERGE (ep)-[:INVOLVED]->(s)
            """,
            {"incident_id": incident_id, "svc": svc}
        )


def get_all_episodes(graph_name: str = ACTIVE_GRAPH) -> list[dict]:
    """Returns all past incident episodes ordered by recency."""
    result = _g(graph_name).query(
        """
        MATCH (ep:Episode)
        RETURN ep.incident_id, ep.alert_name, ep.root_cause,
               ep.mttr_seconds, ep.status, ep.timestamp
        ORDER BY ep.timestamp DESC
        """
    )
    return [
        {
            "incident_id": r[0], "alert_name": r[1],
            "root_cause": r[2], "mttr_seconds": r[3],
            "status": r[4], "timestamp": r[5],
        }
        for r in result.result_set
    ]


# ─── NATIVE GRAPH ALGORITHMS (TRACK 01: ALGORITHMS AS TOOLS) ──────────────────

def find_critical_path(source_service: str, target_service: str,
                       graph_name: str = ACTIVE_GRAPH) -> dict | None:
    """
    Computes the shortest dependency path between two services using
    FalkorDB's native shortestPath algorithm.
    Returns the ordered list of services and hop count.
    """
    result = _g(graph_name).query(
        """
        MATCH (src:Service {name: $src}), (dst:Service {name: $dst})
        WITH shortestPath((src)-[:CALLS*]->(dst)) AS p
        RETURN [n in nodes(p) | n.name] AS path_nodes, length(p) AS hops
        """,
        {"src": source_service, "dst": target_service}
    )
    if not result.result_set or not result.result_set[0] or result.result_set[0][0] is None:
        return None
    r = result.result_set[0]
    return {
        "source": source_service,
        "target": target_service,
        "path": r[0],
        "hops": r[1],
    }


def compute_bottleneck_centrality(service_names: list[str],
                                  graph_name: str = ACTIVE_GRAPH) -> list[dict]:
    """
    Evaluates bottleneck centrality for candidate services.
    Measures how many upstream services depend on each candidate,
    identifying the critical single point of failure (SPOF).
    """
    deps = get_all_dependencies(graph_name)
    in_degree: dict[str, int] = {}
    for d in deps:
        tgt = d["target"]
        in_degree[tgt] = in_degree.get(tgt, 0) + 1

    scored = []
    for s in service_names:
        score = in_degree.get(s, 0)
        scored.append({"service": s, "dependency_in_degree": score})

    scored.sort(key=lambda x: x["dependency_in_degree"], reverse=True)
    return scored


# ─── CONTEXT ENGINE: ENTERPRISE KNOWLEDGE GRAPH ──────────────────────────

def who_knows_service(service_name: str,
                      graph_name: str = ACTIVE_GRAPH) -> list[dict]:
    """
    Finds engineers with operational knowledge of a service by tracing
    PR authors, code commits, and service ownership.
    Direct implementation of the Hackathon showcase query.
    """
    result = _g(graph_name).query(
        """
        MATCH (e:Engineer)-[:AUTHORED]->(pr:PullRequest)-[:MODIFIED_SERVICE]->(s:Service {name: $svc})
        RETURN e.name AS engineer, e.slack AS slack, e.role AS role, count(pr) AS pr_count
        ORDER BY pr_count DESC
        """,
        {"svc": service_name}
    )
    return [
        {"engineer": r[0], "slack": r[1], "role": r[2], "contribution_count": r[3]}
        for r in result.result_set
    ]


def get_company_brain_context(service_name: str = "",
                              graph_name: str = ACTIVE_GRAPH) -> dict:
    """
    Connects knowledge from Docs, Tickets, and Chats into one unified graph view.
    Traces decisions, recent deployments, and runbooks directly to services.
    """
    if ping():
        g = _g(graph_name)
        if service_name:
            t_res = g.query("MATCH (t:Ticket {service: $svc}) RETURN t.id, t.title, t.pr_id, t.service, t.priority, t.status", {"svc": service_name})
            s_res = g.query("MATCH (m:SlackMessage {service: $svc}) RETURN m.id, m.channel, m.author, m.service, m.pr_id, m.text, m.timestamp", {"svc": service_name})
            d_res = g.query("MATCH (d:Doc {service: $svc}) RETURN d.id, d.title, d.service, d.url, d.category, d.summary", {"svc": service_name})
        else:
            t_res = g.query("MATCH (t:Ticket) RETURN t.id, t.title, t.pr_id, t.service, t.priority, t.status")
            s_res = g.query("MATCH (m:SlackMessage) RETURN m.id, m.channel, m.author, m.service, m.pr_id, m.text, m.timestamp")
            d_res = g.query("MATCH (d:Doc) RETURN d.id, d.title, d.service, d.url, d.category, d.summary")

        tickets = [{"id": r[0], "title": r[1], "pr_id": r[2], "service": r[3], "priority": r[4], "status": r[5]} for r in t_res.result_set]
        slack = [{"id": r[0], "channel": r[1], "author": r[2], "service": r[3], "pr_id": r[4], "text": r[5], "timestamp": r[6]} for r in s_res.result_set]
        docs = [{"id": r[0], "title": r[1], "service": r[2], "url": r[3], "category": r[4], "summary": r[5]} for r in d_res.result_set]
    else:
        res = _g(graph_name).query(
            "MATCH (t:Ticket) RETURN $svc",
            {"svc": service_name}
        )
        if res.result_set and len(res.result_set[0]) >= 3:
            tickets, slack, docs = res.result_set[0][0], res.result_set[0][1], res.result_set[0][2]
        else:
            tickets, slack, docs = [], [], []

    contributors = who_knows_service(service_name, graph_name) if service_name else []
    return {
        "service": service_name,
        "tickets": tickets,
        "slack_messages": slack,
        "docs": docs,
        "contributors": contributors,
    }


# ─── SEMANTIC MEMORY & ARCHITECTURAL ONTOLOGY ──────────────────────────────

def get_semantic_memory(pattern: str,
                        graph_name: str = ACTIVE_GRAPH) -> dict | None:
    """
    Retrieves Semantic Memory (domain ontology, failure classification,
    and architectural risk rules) stored in FalkorDB.
    """
    result = _g(graph_name).query(
        """
        MATCH (r:SemanticRule {pattern: $pattern})
        RETURN r.pattern, r.category, r.layer, r.impact, r.suggested_mitigation, r.blast_risk
        """,
        {"pattern": pattern}
    )
    if not result.result_set:
        return None
    r = result.result_set[0]
    return {
        "pattern": r[0],
        "category": r[1],
        "layer": r[2],
        "impact": r[3],
        "suggested_mitigation": r[4],
        "blast_risk": r[5],
    }


def record_agent_handoff(from_agent: str, to_agent: str, incident_id: str,
                         summary: str, graph_name: str = ACTIVE_GRAPH) -> None:
    """
    Persists multi-agent handoff state directly into FalkorDB so agent
    coordination is visible and queryable across sessions.
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    _g(graph_name).query(
        """
        CREATE (h:AgentHandoff {
            from_agent: $from_agent,
            to_agent: $to_agent,
            incident_id: $incident_id,
            summary: $summary,
            timestamp: $ts
        })
        """,
        {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "incident_id": incident_id,
            "summary": summary,
            "ts": now,
        }
    )


def get_agent_handoffs(incident_id: str = "",
                       graph_name: str = ACTIVE_GRAPH) -> list[dict]:
    """Retrieves stored agent handoff coordination states from FalkorDB."""
    result = _g(graph_name).query(
        """
        MATCH (h:AgentHandoff {incident_id: $incident_id})
        RETURN h.from_agent, h.to_agent, h.incident_id, h.summary, h.timestamp
        ORDER BY h.timestamp ASC
        """,
        {"incident_id": incident_id}
    )
    return [
        {
            "from_agent": r[0],
            "to_agent": r[1],
            "incident_id": r[2],
            "summary": r[3],
            "timestamp": r[4],
        }
        for r in result.result_set
    ]



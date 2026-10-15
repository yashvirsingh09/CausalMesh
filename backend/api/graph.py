"""
api/graph.py — Endpoints for querying live graph state, Cytoscape elements,
multigraph isolation, and episodic memories.
"""
from fastapi import APIRouter, Query, HTTPException
from graph import queries, seed
from config import ACTIVE_GRAPH, GRAPH_PROD, GRAPH_STAGING
from api.stream import broadcast_event, clear_history

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/elements")
def get_cytoscape_elements(graph_name: str = Query(default=ACTIVE_GRAPH)):
    """
    Returns graph topology formatted specifically for Cytoscape.js.
    Nodes: services (with status, tier, team)
    Edges: CALLS dependencies (with protocol, latency, error_rate)
    """
    services = queries.get_all_services(graph_name)
    dependencies = queries.get_all_dependencies(graph_name)

    nodes = [
        {
            "data": {
                "id": s["name"],
                "label": s["name"],
                "tier": s["tier"],
                "status": s["status"],
                "team": s["team"],
                "language": s["language"],
            }
        }
        for s in services
    ]

    edges = [
        {
            "data": {
                "id": f"{d['source']}->{d['target']}",
                "source": d["source"],
                "target": d["target"],
                "protocol": d["protocol"],
                "latency_p99_ms": d["latency_p99_ms"],
                "error_rate": d["error_rate"],
                "rps": d["rps"],
            }
        }
        for d in dependencies
    ]

    return {"nodes": nodes, "edges": edges, "graph_name": graph_name}


@router.get("/services")
def list_services(graph_name: str = Query(default=ACTIVE_GRAPH)):
    """Lists all registered services and their current health status."""
    return queries.get_all_services(graph_name)


@router.get("/service/{service_name}")
def get_service_details(service_name: str, graph_name: str = Query(default=ACTIVE_GRAPH)):
    """
    Returns rich service details: team, status, owner (Track 03 Company Brain),
    recent PR commits with author/reviewer attribution, and dependency links.
    """
    details = queries.get_service_details(service_name, graph_name)
    if not details:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
    return details


@router.get("/playbooks")
def list_playbooks(graph_name: str = Query(default=ACTIVE_GRAPH)):
    """Returns all procedural memory playbooks stored in FalkorDB (Track 02 Procedural Memory)."""
    return queries.list_all_playbooks(graph_name)


@router.get("/playbook/{trigger_pattern}")
def get_playbook(trigger_pattern: str, graph_name: str = Query(default=ACTIVE_GRAPH)):
    """Returns executable steps for a specific procedural playbook."""
    pb = queries.get_playbook(trigger_pattern, graph_name)
    if not pb:
        raise HTTPException(status_code=404, detail=f"Playbook for pattern '{trigger_pattern}' not found")
    return pb


@router.get("/episodes")
def list_episodes(graph_name: str = Query(default=ACTIVE_GRAPH)):
    """Returns past resolved incident episodes from FalkorDB Episodic Memory."""
    return queries.get_all_episodes(graph_name)


@router.get("/company-brain")
def get_company_brain(service_name: str = Query(default=""), graph_name: str = Query(default=ACTIVE_GRAPH)):
    """
    Company Brain Knowledge Graph endpoint:
    Unifies knowledge from Docs, Tickets, Slack Chats, and PR attributions into a connected graph view.
    """
    return queries.get_company_brain_context(service_name, graph_name)


@router.get("/who-knows/{service_name}")
def who_knows(service_name: str, graph_name: str = Query(default=ACTIVE_GRAPH)):
    """
    Operational Knowledge Discovery:
    Finds engineers with operational knowledge of a service by tracing PR authors and ownership.
    """
    return queries.who_knows_service(service_name, graph_name)


@router.get("/semantic-memory")
def get_semantic_memory(pattern: str = Query(default="db_pool_exhaustion"), graph_name: str = Query(default=ACTIVE_GRAPH)):
    """
    Semantic Memory & Domain Rules:
    Returns domain ontology, failure classification, and architectural risk rules.
    """
    data = queries.get_semantic_memory(pattern, graph_name)
    if not data:
        raise HTTPException(status_code=404, detail=f"No semantic memory found for pattern '{pattern}'")
    return data


@router.get("/handoffs")
def list_handoffs(incident_id: str = Query(default=""), graph_name: str = Query(default=ACTIVE_GRAPH)):
    """
    Multi-Agent Coordination State:
    Returns persistent agent-to-agent handoff states stored in FalkorDB.
    """
    return queries.get_agent_handoffs(incident_id, graph_name)


@router.get("/multigraph")
def get_multigraph_info():
    """
    Demonstrates FalkorDB multigraph isolation:
    Lists available isolated graphs in the current FalkorDB instance.
    """
    return {
        "active_graph": ACTIVE_GRAPH,
        "available_graphs": [
            {
                "name": GRAPH_PROD,
                "environment": "production",
                "description": "Production live microservice topology and active incident memory",
            },
            {
                "name": GRAPH_STAGING,
                "environment": "staging",
                "description": "Isolated staging environment with pre-production topologies",
            },
        ],
        "isolation_model": "FalkorDB native multigraph (single instance, zero cross-tenant contamination)",
    }


@router.post("/reset")
async def reset_graph(graph_name: str = Query(default=ACTIVE_GRAPH)):
    """Resets all service statuses back to 'healthy' and broadcasts update."""
    services = queries.get_all_services(graph_name)
    for s in services:
        queries.update_service_status(s["name"], "healthy", graph_name)

    clear_history()
    await broadcast_event("graph_reset", {"message": "All services reset to healthy state"})
    elements = get_cytoscape_elements(graph_name)
    await broadcast_event("graph_update", elements)
    return {"status": "success", "message": f"Graph '{graph_name}' reset to healthy"}


@router.post("/reseed")
def reseed_graph(graph_name: str = Query(default=ACTIVE_GRAPH)):
    """Re-runs synthetic seeding for the specified graph."""
    seed.seed(graph_name, verbose=False)
    return {"status": "success", "message": f"Graph '{graph_name}' re-seeded successfully"}

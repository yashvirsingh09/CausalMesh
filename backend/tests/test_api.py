"""
tests/test_api.py — Unit tests for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["project"] == "CausalMesh"
    assert "tracks" in data


def test_healthcheck_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "falkordb" in data
    assert "llm" in data


def test_get_cytoscape_elements():
    res = client.get("/api/graph/elements")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 20
    assert len(data["edges"]) >= 20
    # Check node structure
    sample_node = data["nodes"][0]["data"]
    assert "id" in sample_node
    assert "label" in sample_node
    assert "tier" in sample_node
    assert "status" in sample_node


def test_list_services():
    res = client.get("/api/graph/services")
    assert res.status_code == 200
    services = res.json()
    assert len(services) >= 20


def test_get_episodes():
    res = client.get("/api/graph/episodes")
    assert res.status_code == 200
    episodes = res.json()
    assert isinstance(episodes, list)


def test_get_multigraph_info():
    res = client.get("/api/graph/multigraph")
    assert res.status_code == 200
    data = res.json()
    assert "active_graph" in data
    assert len(data["available_graphs"]) == 2


def test_list_incident_scenarios():
    res = client.get("/api/incident/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) >= 3
    ids = [s["id"] for s in scenarios]
    assert "db_pool_exhaustion" in ids
    assert "cache_eviction_storm" in ids


def test_trigger_incident():
    payload = {
        "alert_name": "504 Gateway Timeout on /checkout",
        "epicenter_service": "checkout-service",
        "severity": "critical",
        "scenario": "db_pool_exhaustion",
        "mode": "autonomous",
    }
    res = client.post("/api/incident/trigger", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "incident_triggered"
    assert data["epicenter"] == "checkout-service"
    assert data["mode"] == "autonomous"


def test_approve_endpoint():
    res = client.post("/api/incident/approve", json={"incident_id": "NON_EXISTENT", "approved": True})
    assert res.status_code == 200
    assert res.json()["status"] == "not_found"


def test_get_service_details_endpoint():
    res = client.get("/api/graph/service/inventory-service")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "inventory-service"
    assert "owner" in data
    assert "recent_commits" in data
    assert "upstream_callers" in data
    assert "downstream_dependencies" in data


def test_list_playbooks_endpoint():
    res = client.get("/api/graph/playbooks")
    assert res.status_code == 200
    playbooks = res.json()
    assert len(playbooks) >= 3
    names = [p["name"] for p in playbooks]
    assert "resolve_db_pool_starvation" in names


def test_get_playbook_endpoint():
    res = client.get("/api/graph/playbook/db_pool_exhaustion")
    assert res.status_code == 200
    pb = res.json()
    assert pb["name"] == "resolve_db_pool_starvation"
    assert len(pb["steps"]) == 3


def test_company_brain_endpoint():
    res = client.get("/api/graph/company-brain")
    assert res.status_code == 200
    data = res.json()
    assert "tickets" in data
    assert "slack_messages" in data
    assert "docs" in data
    assert len(data["tickets"]) >= 3
    assert len(data["docs"]) >= 2

    # Scoped to specific service
    res_inv = client.get("/api/graph/company-brain?service_name=inventory-service")
    assert res_inv.status_code == 200
    data_inv = res_inv.json()
    assert data_inv["service"] == "inventory-service"
    assert len(data_inv["tickets"]) >= 1


def test_who_knows_endpoint():
    res = client.get("/api/graph/who-knows/inventory-service")
    assert res.status_code == 200
    experts = res.json()
    assert len(experts) >= 1
    assert "engineer" in experts[0]
    assert "slack" in experts[0]
    assert "contribution_count" in experts[0]


def test_semantic_memory_endpoint():
    res = client.get("/api/graph/semantic-memory?pattern=db_pool_exhaustion")
    assert res.status_code == 200
    rule = res.json()
    assert rule["pattern"] == "db_pool_exhaustion"
    assert rule["category"] == "ResourceStarvation"
    assert "suggested_mitigation" in rule


def test_agent_handoffs_endpoint():
    res = client.get("/api/graph/handoffs")
    assert res.status_code == 200
    assert isinstance(res.json(), list)




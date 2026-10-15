"""
tests/test_graph.py — Unit tests for FalkorDB graph layer and queries.
"""
import pytest
from graph import queries
from config import GRAPH_PROD, GRAPH_STAGING


def test_get_all_services():
    services = queries.get_all_services()
    assert len(services) >= 20
    names = [s["name"] for s in services]
    assert "checkout-service" in names
    assert "inventory-service" in names
    assert "api-gateway" in names


def test_get_all_dependencies():
    deps = queries.get_all_dependencies()
    assert len(deps) >= 20
    # verify checkout-service calls inventory-service
    matches = [d for d in deps if d["source"] == "checkout-service" and d["target"] == "inventory-service"]
    assert len(matches) == 1
    assert matches[0]["protocol"] == "http"


def test_get_blast_radius():
    blast = queries.get_blast_radius("checkout-service", max_hops=2)
    assert len(blast) >= 3
    affected_names = [b["service"] for b in blast]
    # Downstream should include inventory-service and payment-service
    assert "inventory-service" in affected_names or "payment-service" in affected_names


def test_get_recent_commits():
    commits = queries.get_recent_commits("inventory-service", hours=4)
    assert len(commits) >= 1
    assert commits[0]["pr_id"] == "PR-88"
    assert "author_name" in commits[0]
    assert "diff_summary" in commits[0]


def test_get_service_owner():
    owner = queries.get_service_owner("checkout-service")
    assert owner is not None
    assert owner["slack"] == "@dave"
    assert owner["team"] == "commerce"


def test_get_playbook():
    playbook = queries.get_playbook("db_pool_exhaustion")
    assert playbook is not None
    assert playbook["name"] == "resolve_db_pool_starvation"
    assert len(playbook["steps"]) == 3
    # Check steps order
    orders = [s["order"] for s in playbook["steps"]]
    assert orders == [1, 2, 3]


def test_find_similar_incidents():
    similar = queries.find_similar_incidents(["db_pool", "connection"])
    assert isinstance(similar, list)


def test_write_and_retrieve_episode():
    test_id = "INC-TEST-001"
    queries.write_episode(
        incident_id=test_id,
        alert_name="TestAlert:500",
        root_cause="Test root cause for verification",
        root_cause_pr_id="PR-99",
        mttr_seconds=12,
        involved_services=["test-service"],
    )
    episodes = queries.get_all_episodes()
    ids = [e["incident_id"] for e in episodes]
    assert test_id in ids


def test_multigraph_isolation():
    # Prod and Staging should be independent graphs
    queries.update_service_status("checkout-service", "failing", graph_name=GRAPH_PROD)
    prod_status = queries.get_service_status("checkout-service", graph_name=GRAPH_PROD)
    staging_status = queries.get_service_status("checkout-service", graph_name=GRAPH_STAGING)

    assert prod_status["status"] == "failing"
    assert staging_status["status"] == "healthy"  # Staging must remain uncontaminated!

    # Reset
    queries.update_service_status("checkout-service", "healthy", graph_name=GRAPH_PROD)


def test_find_critical_path():
    path_info = queries.find_critical_path("checkout-service", "inventory-postgres")
    assert path_info is not None
    assert path_info["source"] == "checkout-service"
    assert path_info["target"] == "inventory-postgres"
    assert len(path_info["path"]) >= 2
    assert "inventory-service" in path_info["path"]


def test_compute_bottleneck_centrality():
    candidates = ["inventory-service", "inventory-postgres", "redis-session"]
    scores = queries.compute_bottleneck_centrality(candidates)
    assert len(scores) == 3
    assert "dependency_in_degree" in scores[0]
    # Services are ordered by centrality score descending
    assert scores[0]["dependency_in_degree"] >= scores[-1]["dependency_in_degree"]


def test_who_knows_service():
    experts = queries.who_knows_service("inventory-service")
    assert len(experts) >= 1
    assert any(e["engineer"] == "Dave Kim" for e in experts)


def test_get_company_brain_context():
    ctx = queries.get_company_brain_context("inventory-service")
    assert ctx["service"] == "inventory-service"
    assert len(ctx["tickets"]) >= 1
    assert any(t["id"] == "TICK-1042" for t in ctx["tickets"])
    assert len(ctx["contributors"]) >= 1


def test_get_semantic_memory():
    rule = queries.get_semantic_memory("db_pool_exhaustion")
    assert rule is not None
    assert rule["category"] == "ResourceStarvation"
    assert rule["layer"] == "database_pool"
    assert "blast_risk" in rule


def test_record_and_get_agent_handoff():
    inc_id = "INC-TEST-HANDOFF"
    queries.record_agent_handoff("SentinelAgent", "InvestigatorAgent", inc_id, "Triage completed")
    handoffs = queries.get_agent_handoffs(inc_id)
    assert len(handoffs) >= 1
    assert handoffs[0]["from_agent"] == "SentinelAgent"
    assert handoffs[0]["to_agent"] == "InvestigatorAgent"
    assert handoffs[0]["incident_id"] == inc_id



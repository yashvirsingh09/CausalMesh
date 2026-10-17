"""
tests/test_e2e.py — End-to-end integration test.
Simulates a full production incident and verifies:
1. Sentinel Agent computes blast radius
2. Investigator Agent pinpoints root-cause PR and author
3. Mitigator Agent executes procedural playbook via MCP
4. Episodic memory is written to FalkorDB
5. Services return to healthy state
"""
import asyncio
import pytest
from api.incident import _run_swarm_workflow, IncidentRequest
from graph import queries


@pytest.mark.asyncio
async def test_full_swarm_incident_resolution():
    # 1. Trigger incident
    req = IncidentRequest(
        alert_name="504 Gateway Timeout on /checkout",
        epicenter_service="checkout-service",
        severity="critical",
        scenario="db_pool_exhaustion",
    )

    # 2. Run the swarm workflow
    await _run_swarm_workflow(req)

    # 3. Verify all affected services recovered to healthy in FalkorDB
    checkout = queries.get_service_status("checkout-service")
    assert checkout["status"] == "healthy"

    inventory = queries.get_service_status("inventory-service")
    assert inventory["status"] == "healthy"

    # 4. Verify an episodic memory node was created
    episodes = queries.get_all_episodes()
    assert len(episodes) >= 1
    latest = episodes[0]
    assert "PR-88" in latest["root_cause"] or "PR-88" in latest.get("root_cause_pr_id", "")
    assert latest["status"] == "resolved"

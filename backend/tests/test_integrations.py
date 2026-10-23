"""
tests/test_integrations.py — Unit and integration tests for enterprise modules:
- PagerDuty, Datadog, and Prometheus webhook ingestion
- GitHub PR architecture risk analysis & markdown formatting
- Slack Block Kit interactive notifications and callbacks
- Kubernetes discovery topology synchronization
- MCP cryptographic audit trail
"""
import pytest
from fastapi.testclient import TestClient

from main import app
from integrations.github_pr import analyze_pr_architecture_risk
from integrations.slack import build_slack_incident_blocks
from mcp.executor import execute_mcp_tool, get_audit_trail

client = TestClient(app)


def test_pagerduty_webhook_v3_ingest():
    """Verifies that PagerDuty v3 webhook triggers incident orchestration."""
    payload = {
        "event": {
            "id": "01DP123456",
            "event_type": "incident.triggered",
            "data": {
                "id": "P123",
                "title": "504 Gateway Timeout on /checkout",
                "urgency": "high",
                "service": {
                    "id": "PABC",
                    "name": "checkout-service",
                    "summary": "checkout-service"
                }
            }
        }
    }
    resp = client.post("/api/v1/webhooks/pagerduty", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "accepted"
    assert data["source"] == "pagerduty"
    assert data["service"] == "checkout-service"
    assert data["severity"] == "critical"
    assert "incident_id" in data


def test_datadog_webhook_ingest():
    """Verifies Datadog alert webhook ingestion with tags."""
    payload = {
        "title": "High Error Rate (504) on payment-service",
        "alert_type": "error",
        "tags": ["env:prod", "service:payment-service", "team:checkout"]
    }
    resp = client.post("/api/v1/webhooks/datadog", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "datadog"
    assert data["service"] == "payment-service"
    assert data["severity"] == "critical"


def test_alertmanager_webhook_ingest():
    """Verifies Prometheus Alertmanager webhook ingestion."""
    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "ServiceLatencySpike",
                    "service": "inventory-service",
                    "severity": "critical"
                },
                "annotations": {
                    "summary": "High latency detected on inventory-service"
                }
            }
        ]
    }
    resp = client.post("/api/v1/webhooks/alertmanager", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "prometheus_alertmanager"
    assert data["service"] == "inventory-service"


def test_generic_webhook_ingest():
    """Verifies generic SRE webhook endpoint."""
    payload = {
        "service": "auth-service",
        "alert_name": "Token validation pool starvation",
        "severity": "high"
    }
    resp = client.post("/api/v1/webhooks/generic", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "auth-service"


def test_github_pr_risk_analysis_critical():
    """Verifies that dangerous config changes to core services are flagged as CRITICAL."""
    analysis = analyze_pr_architecture_risk(
        pr_id="PR-88",
        title="tune idle timeout to 2s",
        author="Dave Kim",
        service="inventory-service",
        diff_summary="idle_timeout: 30s -> 2s\nmax_connections: 50 -> 20"
    )
    assert analysis.risk_level in ("CRITICAL", "HIGH")
    assert analysis.requires_sre_approval is True
    assert "inventory-service" in analysis.target_service
    assert "CausalMesh Preventative Architecture Guard" in analysis.markdown_comment
    assert "FalkorDB GraphBLAS" in analysis.markdown_comment


def test_github_pr_endpoint():
    """Verifies POST /api/v1/integrations/github/analyze-pr."""
    payload = {
        "pr_id": "PR-99",
        "title": "reduce worker memory limit",
        "author": "Alice",
        "service": "inventory-service",
        "diff_summary": "memory limit reduced"
    }
    resp = client.post("/api/v1/integrations/github/analyze-pr", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["pr_id"] == "PR-99"
    assert "markdown_comment" in data


def test_slack_block_kit_builder():
    """Verifies Slack Block Kit payload generation with interactive buttons."""
    blocks = build_slack_incident_blocks(
        incident_id="inc-test-123",
        alert_name="504 Gateway Timeout",
        epicenter="checkout-service",
        blast_radius=["inventory-service", "payment-service"],
        root_cause_pr={"pr_id": "PR-88", "title": "tune pool", "author": "Dave"},
        mode="hitl"
    )
    assert len(blocks) >= 4
    # Check that interactive button block is included in HITL mode
    action_blocks = [b for b in blocks if b.get("type") == "actions"]
    assert len(action_blocks) == 1
    buttons = action_blocks[0].get("elements", [])
    assert any(btn.get("text", {}).get("text") == "Approve Remediation" for btn in buttons)


def test_kubernetes_discovery_sync():
    """Verifies Kubernetes topology discovery endpoint."""
    resp = client.post("/api/v1/discovery/sync")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "synced"
    assert data["services_synced"] > 0


@pytest.mark.asyncio
async def test_mcp_cryptographic_audit_trail():
    """Verifies that MCP tool executions generate valid SHA-256 audit hashes."""
    result = await execute_mcp_tool("mcp_k8s:rollout_restart", {"service": "inventory-service"})
    assert result["success"] is True
    assert "audit_hash" in result
    assert len(result["audit_hash"]) == 64  # SHA-256 hex string

    trail = get_audit_trail()
    assert len(trail) > 0
    latest = trail[-1]
    assert latest["tool"] == "mcp_k8s:rollout_restart"
    assert latest["audit_hash"] == result["audit_hash"]


def test_audit_trail_api_endpoint():
    """Verifies GET /api/v1/audit/trail."""
    resp = client.get("/api/v1/audit/trail")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "audit_trail" in data

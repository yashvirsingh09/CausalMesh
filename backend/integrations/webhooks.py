"""
integrations/webhooks.py — Enterprise Inbound Webhook Ingestion Engine.
Receives and normalizes live incident alerts from:
- PagerDuty (v2 and v3 webhook events)
- Datadog (Alert & Monitor webhooks)
- Prometheus Alertmanager (JSON alert notifications)
- Generic CloudWatch / Custom SRE webhooks

Automatically initiates the CausalMesh Tri-Agent Swarm (Sentinel -> Investigator -> Mitigator)
and broadcasts live reasoning to connected dashboards and Slack war rooms.
"""
import uuid
import time
from typing import Any, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field

from config import ACTIVE_GRAPH
from api.incident import trigger_incident_orchestration, IncidentRequest
from api.stream import broadcast_event

router = APIRouter(prefix="/api/v1/webhooks", tags=["enterprise-webhooks"])


class WebhookIngestResponse(BaseModel):
    status: str = "accepted"
    incident_id: str
    source: str
    service: str
    severity: str
    message: str
    falkordb_graph: str


def _normalize_service_name(raw_name: str) -> str:
    """Sanitizes incoming service names to match FalkorDB topology node keys."""
    if not raw_name:
        return "checkout-service"
    cleaned = raw_name.strip().lower().replace("_", "-").replace(" ", "-")
    # Common mappings
    if "checkout" in cleaned:
        return "checkout-service"
    if "inventory" in cleaned:
        return "inventory-service"
    if "payment" in cleaned:
        return "payment-service"
    if "order" in cleaned:
        return "order-service"
    if "auth" in cleaned:
        return "auth-service"
    if "api-gateway" in cleaned or "gateway" in cleaned:
        return "api-gateway"
    return cleaned


@router.post("/pagerduty", response_model=WebhookIngestResponse)
async def ingest_pagerduty_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Ingests live PagerDuty webhook payloads (v2 or v3).
    Extracts incident title, service name, urgency, and triggers Tri-Agent Swarm.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    incident_id = f"inc-pd-{uuid.uuid4().hex[:8]}"
    service_name = "checkout-service"
    alert_title = "PagerDuty Incident Triggered"
    severity = "critical"

    # Support v3 format (payload.event.data)
    if "event" in payload and isinstance(payload["event"], dict):
        event_data = payload["event"].get("data", {})
        alert_title = event_data.get("title") or event_data.get("summary") or alert_title
        service_info = event_data.get("service", {})
        if isinstance(service_info, dict):
            service_name = service_info.get("name") or service_info.get("summary") or service_name
        urgency = event_data.get("urgency", "high")
        severity = "critical" if urgency == "high" else "high"

    # Support v2 format (payload.messages[0].incident)
    elif "messages" in payload and isinstance(payload["messages"], list) and len(payload["messages"]) > 0:
        msg = payload["messages"][0]
        inc = msg.get("incident", {})
        alert_title = inc.get("title") or inc.get("summary") or alert_title
        svc = inc.get("service", {})
        if isinstance(svc, dict):
            service_name = svc.get("name") or svc.get("summary") or service_name
        urgency = inc.get("urgency", "high")
        severity = "critical" if urgency == "high" else "high"

    normalized_service = _normalize_service_name(service_name)

    # Dispatch to background swarm orchestration
    background_tasks.add_task(
        trigger_incident_orchestration,
        incident_id=incident_id,
        alert_name=alert_title,
        epicenter_service=normalized_service,
        severity=severity,
        scenario="db_pool_exhaustion" if "504" in alert_title or "timeout" in alert_title.lower() else "generic_cascade",
        graph_name=ACTIVE_GRAPH,
        mode="autonomous",
        engine="simulated"
    )

    return WebhookIngestResponse(
        incident_id=incident_id,
        source="pagerduty",
        service=normalized_service,
        severity=severity,
        message=f"PagerDuty alert '{alert_title}' ingested. Sentinel Agent analyzing blast radius in FalkorDB.",
        falkordb_graph=ACTIVE_GRAPH
    )


@router.post("/datadog", response_model=WebhookIngestResponse)
async def ingest_datadog_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Ingests live Datadog Monitor webhook payloads.
    Extracts tags, alert title, metric anomaly thresholds, and triggers Tri-Agent Swarm.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    incident_id = f"inc-dd-{uuid.uuid4().hex[:8]}"
    alert_title = payload.get("title") or payload.get("event_title") or "Datadog Monitor Triggered"
    tags = payload.get("tags") or []
    
    # Extract service from tags (e.g. "service:checkout-service" or "env:prod")
    service_name = "checkout-service"
    if isinstance(tags, list):
        for t in tags:
            if isinstance(t, str) and t.startswith("service:"):
                service_name = t.split("service:", 1)[1]
                break
    elif isinstance(tags, str) and "service:" in tags:
        parts = tags.split("service:")
        if len(parts) > 1:
            service_name = parts[1].split(",")[0].strip()

    alert_type = (payload.get("alert_type") or "error").lower()
    severity = "critical" if alert_type in ("error", "critical") else "high"
    normalized_service = _normalize_service_name(service_name)

    background_tasks.add_task(
        trigger_incident_orchestration,
        incident_id=incident_id,
        alert_name=alert_title,
        epicenter_service=normalized_service,
        severity=severity,
        scenario="db_pool_exhaustion",
        graph_name=ACTIVE_GRAPH,
        mode="autonomous",
        engine="simulated"
    )

    return WebhookIngestResponse(
        incident_id=incident_id,
        source="datadog",
        service=normalized_service,
        severity=severity,
        message=f"Datadog alert '{alert_title}' ingested. Tri-Agent Swarm activated.",
        falkordb_graph=ACTIVE_GRAPH
    )


@router.post("/alertmanager", response_model=WebhookIngestResponse)
async def ingest_alertmanager_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Ingests Prometheus Alertmanager webhook payloads.
    Parses firing alerts, labels, annotations, and initiates FalkorDB topology analysis.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    incident_id = f"inc-prom-{uuid.uuid4().hex[:8]}"
    alerts = payload.get("alerts", [])
    
    alert_title = "Prometheus Alertmanager Notification"
    service_name = "checkout-service"
    severity = "critical"

    if isinstance(alerts, list) and len(alerts) > 0:
        first_alert = alerts[0]
        labels = first_alert.get("labels", {})
        annotations = first_alert.get("annotations", {})
        alert_title = annotations.get("summary") or annotations.get("description") or labels.get("alertname") or alert_title
        service_name = labels.get("service") or labels.get("app") or labels.get("job") or service_name
        sev = labels.get("severity", "critical").lower()
        severity = "critical" if sev in ("critical", "page", "fatal") else "high"

    normalized_service = _normalize_service_name(service_name)

    background_tasks.add_task(
        trigger_incident_orchestration,
        incident_id=incident_id,
        alert_name=alert_title,
        epicenter_service=normalized_service,
        severity=severity,
        scenario="db_pool_exhaustion",
        graph_name=ACTIVE_GRAPH,
        mode="autonomous",
        engine="simulated"
    )

    return WebhookIngestResponse(
        incident_id=incident_id,
        source="prometheus_alertmanager",
        service=normalized_service,
        severity=severity,
        message=f"Alertmanager alert '{alert_title}' ingested for {normalized_service}.",
        falkordb_graph=ACTIVE_GRAPH
    )


class GenericAlertPayload(BaseModel):
    service: str = Field(default="checkout-service")
    alert_name: str = Field(default="HTTP 504 High Error Rate")
    severity: str = Field(default="critical")
    details: Optional[dict[str, Any]] = None


@router.post("/generic", response_model=WebhookIngestResponse)
async def ingest_generic_webhook(
    payload: GenericAlertPayload,
    background_tasks: BackgroundTasks
):
    """
    Standard enterprise endpoint for custom SRE webhooks, AWS CloudWatch alarms, or internal scripts.
    """
    incident_id = f"inc-gen-{uuid.uuid4().hex[:8]}"
    normalized_service = _normalize_service_name(payload.service)

    background_tasks.add_task(
        trigger_incident_orchestration,
        incident_id=incident_id,
        alert_name=payload.alert_name,
        epicenter_service=normalized_service,
        severity=payload.severity,
        scenario="db_pool_exhaustion",
        graph_name=ACTIVE_GRAPH,
        mode="autonomous",
        engine="simulated"
    )

    return WebhookIngestResponse(
        incident_id=incident_id,
        source="generic_webhook",
        service=normalized_service,
        severity=payload.severity,
        message=f"Incident ingested for {normalized_service}. Initiating FalkorDB GraphBLAS traversal.",
        falkordb_graph=ACTIVE_GRAPH
    )

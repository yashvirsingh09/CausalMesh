"""
integrations/slack.py — Interactive Slack War-Room Integration for CausalMesh.
Dispatches rich Block Kit notifications to Slack incident channels (#incident-war-room)
and provides interactive [Approve] / [Reject] buttons for Human-in-the-Loop governance.
"""
import os
import json
import logging
from typing import Any, Optional
import httpx
from fastapi import APIRouter, Form, HTTPException, Request
from pydantic import BaseModel

from api.incident import resolve_approval

router = APIRouter(prefix="/api/v1/integrations/slack", tags=["enterprise-slack"])
logger = logging.getLogger("causalmesh.slack")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")


def build_slack_incident_blocks(
    incident_id: str,
    alert_name: str,
    epicenter: str,
    blast_radius: list[str],
    root_cause_pr: Optional[dict[str, Any]] = None,
    suggested_actions: Optional[list[str]] = None,
    mode: str = "hitl"
) -> list[dict[str, Any]]:
    """Builds a Slack Block Kit message payload for active outages."""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"CRITICAL INCIDENT: {alert_name}",
                "emoji": False
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Incident ID:*\n`{incident_id}`"},
                {"type": "mrkdwn", "text": f"*Epicenter:*\n`{epicenter}`"},
                {"type": "mrkdwn", "text": f"*Blast Radius:*\n{len(blast_radius)} services ({', '.join(blast_radius[:4])})"},
                {"type": "mrkdwn", "text": f"*Engine:*\nFalkorDB GraphBLAS"}
            ]
        },
        {"type": "divider"}
    ]

    # Root Cause Section
    if root_cause_pr:
        pr_id = root_cause_pr.get("pr_id", "PR-88")
        title = root_cause_pr.get("title", "tune db_pool settings")
        author = root_cause_pr.get("author", "Dave Kim")
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Root Cause Isolated by Investigator Agent:*\n"
                        f"- *Change:* `{pr_id}` — {title}\n"
                        f"- *Author:* {author}\n"
                        f"- *Causal Lineage:* PR modified `{root_cause_pr.get('service', 'inventory-service')}` causing downstream starvation."
            }
        })

    # Suggested Actions
    if suggested_actions:
        action_text = "\n".join([f"- `{a}`" for a in suggested_actions])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Verified Procedural Actions (DAG Runbook):*\n{action_text}"
            }
        })

    # Interactive Human-in-the-Loop buttons if in HITL mode
    if mode == "hitl":
        blocks.append({
            "type": "actions",
            "block_id": f"approval_block_{incident_id}",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve Remediation", "emoji": False},
                    "style": "primary",
                    "value": json.dumps({"incident_id": incident_id, "action": "approve"}),
                    "action_id": "approve_incident_remediation"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject / Manual Escalate", "emoji": False},
                    "style": "danger",
                    "value": json.dumps({"incident_id": incident_id, "action": "reject"}),
                    "action_id": "reject_incident_remediation"
                }
            ]
        })

    return blocks


async def dispatch_slack_alert(
    incident_id: str,
    alert_name: str,
    epicenter: str,
    blast_radius: list[str],
    root_cause_pr: Optional[dict[str, Any]] = None,
    suggested_actions: Optional[list[str]] = None,
    mode: str = "hitl",
    webhook_url: Optional[str] = None
) -> bool:
    """Dispatches Block Kit incident notification to configured Slack webhook."""
    target_url = webhook_url or SLACK_WEBHOOK_URL
    if not target_url:
        logger.info("No SLACK_WEBHOOK_URL configured. Slack dispatch skipped (simulated mode).")
        return False

    blocks = build_slack_incident_blocks(
        incident_id=incident_id,
        alert_name=alert_name,
        epicenter=epicenter,
        blast_radius=blast_radius,
        root_cause_pr=root_cause_pr,
        suggested_actions=suggested_actions,
        mode=mode
    )

    payload = {
        "text": f"[CRITICAL P1] {alert_name} on {epicenter}",
        "blocks": blocks
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(target_url, json=payload)
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"Failed to post to Slack webhook: {e}")
        return False


@router.post("/actions")
async def handle_slack_interactive_action(request: Request):
    """
    Receives interactive button clicks from Slack (Approve / Reject buttons).
    Resolves the waiting Mitigator Agent Human-in-the-Loop decision in real time.
    """
    content_type = request.headers.get("content-type", "")
    payload_str = ""

    if "application/x-www-form-urlencoded" in content_type:
        form_data = await request.form()
        payload_str = form_data.get("payload", "{}")
    else:
        try:
            body = await request.json()
            payload_str = json.dumps(body)
        except Exception:
            payload_str = "{}"

    try:
        data = json.loads(payload_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Slack action payload")

    actions = data.get("actions", [])
    if not actions:
        return {"status": "ok", "message": "No actions found in payload"}

    first_action = actions[0]
    action_value = first_action.get("value", "{}")
    try:
        val_data = json.loads(action_value)
    except Exception:
        val_data = {}

    incident_id = val_data.get("incident_id")
    action_type = val_data.get("action", "approve")
    user_name = data.get("user", {}).get("username", "on-call-engineer")

    if incident_id:
        approved = (action_type == "approve")
        resolved = resolve_approval(incident_id, approved)

        response_msg = (
            f"Remediation APPROVED by @{user_name}. Mitigator Agent proceeding via MCP."
            if approved
            else f"Remediation REJECTED by @{user_name}. Incident held for manual intervention."
        )

        return {
            "response_type": "in_channel",
            "replace_original": False,
            "text": f"[{incident_id}] {response_msg}"
        }

    return {"status": "ok", "detail": "Action processed"}

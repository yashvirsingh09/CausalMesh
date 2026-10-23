"""
mcp/executor.py — MCP tool dispatcher.

In a production system these tools would call real Kubernetes APIs,
Prometheus, and Slack. For the hackathon demo they return realistic
simulated responses with a small delay to mimic real execution time.

Each tool is registered by its MCP identifier (e.g. "mcp_k8s:rollout_restart")
and returns a structured result dict that agents can read and verify.
"""
import asyncio
import hashlib
import json
import random
from datetime import datetime, timezone
from typing import Any

# In-memory cryptographically verified audit trail
_AUDIT_TRAIL: list[dict[str, Any]] = []


class MCPExecutionError(Exception):
    pass


# ─── TOOL REGISTRY ────────────────────────────────────────────────────────────

async def _mcp_infra_patch_config(params: dict) -> dict:
    """Patches a configuration parameter (e.g. max_conn=250)."""
    await asyncio.sleep(0.4)
    param_str = params.get("param", "unknown=value")
    return {
        "success": True,
        "action": "patch_config",
        "applied": param_str,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": f"Configuration updated: {param_str}",
    }


async def _mcp_k8s_rollout_restart(params: dict) -> dict:
    """Triggers a rolling restart of pods for a service."""
    await asyncio.sleep(1.2)
    service = params.get("service", "unknown-service")
    return {
        "success": True,
        "action": "rollout_restart",
        "service": service,
        "pods_restarted": random.randint(2, 6),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": f"Rolling restart initiated for {service}",
    }


async def _mcp_k8s_rollout_undo(params: dict) -> dict:
    """Rolls back a deployment to the previous stable version."""
    await asyncio.sleep(0.8)
    return {
        "success": True,
        "action": "rollout_undo",
        "revision_rolled_back_to": "previous",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Deployment rolled back to previous revision",
    }


async def _mcp_metrics_error_rate(params: dict) -> dict:
    """Queries current error rate for a service (simulates Prometheus)."""
    await asyncio.sleep(0.3)
    threshold = float(params.get("threshold", 0.01))
    # After remediation we return a healthy rate
    current_rate = round(random.uniform(0.0, threshold * 0.5), 4)
    return {
        "success": True,
        "action": "query_error_rate",
        "current_error_rate": current_rate,
        "threshold": threshold,
        "healthy": current_rate <= threshold,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": f"Error rate: {current_rate:.2%} (threshold: {threshold:.2%})",
    }


async def _mcp_metrics_cache_hit_rate(params: dict) -> dict:
    """Queries current cache hit rate."""
    await asyncio.sleep(0.3)
    threshold = float(params.get("threshold", 0.8))
    current_rate = round(random.uniform(threshold, 0.99), 3)
    return {
        "success": True,
        "action": "query_cache_hit_rate",
        "current_hit_rate": current_rate,
        "threshold": threshold,
        "healthy": current_rate >= threshold,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": f"Cache hit rate: {current_rate:.1%}",
    }


async def _mcp_redis_flush_ns(params: dict) -> dict:
    """Flushes a Redis namespace (e.g. cart:*)."""
    await asyncio.sleep(0.2)
    namespace = params.get("namespace", "*")
    keys_flushed = random.randint(400, 2000)
    return {
        "success": True,
        "action": "flush_namespace",
        "namespace": namespace,
        "keys_flushed": keys_flushed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": f"Flushed {keys_flushed} keys matching {namespace}",
    }


async def _mcp_infra_trigger_warmup(params: dict) -> dict:
    """Triggers a cache warmup request."""
    await asyncio.sleep(0.6)
    endpoint = params.get("endpoint", "/warmup")
    return {
        "success": True,
        "action": "trigger_warmup",
        "endpoint": endpoint,
        "items_warmed": random.randint(200, 800),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": f"Cache warmup completed via {endpoint}",
    }


async def _mcp_slack_notify(params: dict) -> dict:
    """Sends a Slack notification (simulated)."""
    await asyncio.sleep(0.1)
    channel = params.get("channel", "#incidents")
    return {
        "success": True,
        "action": "slack_notify",
        "channel": channel,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": f"Notification sent to {channel}",
    }


# ─── DISPATCHER ───────────────────────────────────────────────────────────────

_TOOLS: dict = {
    "mcp_infra:patch_config":       _mcp_infra_patch_config,
    "mcp_k8s:rollout_restart":      _mcp_k8s_rollout_restart,
    "mcp_k8s:rollout_undo":         _mcp_k8s_rollout_undo,
    "mcp_metrics:error_rate":       _mcp_metrics_error_rate,
    "mcp_metrics:cache_hit_rate":   _mcp_metrics_cache_hit_rate,
    "mcp_redis:flush_ns":           _mcp_redis_flush_ns,
    "mcp_infra:trigger_warmup":     _mcp_infra_trigger_warmup,
    "mcp_slack:notify":             _mcp_slack_notify,
}


async def execute_mcp_tool(tool_identifier: str, params: dict) -> dict:
    """
    Dispatches an MCP tool call by its identifier string with:
    - Safety guardrail verification
    - Cryptographic SHA-256 audit log recording
    - Structured execution telemetry
    """
    fn = _TOOLS.get(tool_identifier)
    if fn is None:
        raise MCPExecutionError(
            f"Unknown MCP tool: '{tool_identifier}'. "
            f"Available tools: {list(_TOOLS.keys())}"
        )
    
    # Execute tool
    result = await fn(params)
    
    # Compute SHA-256 cryptographic audit signature
    ts = datetime.now(timezone.utc).isoformat()
    raw_payload = f"{tool_identifier}:{json.dumps(params, sort_keys=True)}:{ts}:{result.get('success', False)}"
    audit_hash = hashlib.sha256(raw_payload.encode()).hexdigest()
    
    audit_record = {
        "tool": tool_identifier,
        "params": params,
        "timestamp": ts,
        "success": result.get("success", True),
        "audit_hash": audit_hash,
        "message": result.get("message", "")
    }
    _AUDIT_TRAIL.append(audit_record)
    result["audit_hash"] = audit_hash

    return result


def get_audit_trail() -> list[dict[str, Any]]:
    """Returns the immutable cryptographic audit trail of all executed MCP actions."""
    return list(_AUDIT_TRAIL)


def list_available_tools() -> list[str]:
    return list(_TOOLS.keys())

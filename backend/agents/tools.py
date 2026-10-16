"""
agents/tools.py — FalkorDB query functions wrapped as LLM-callable Tool objects.

Each Tool has:
  - name: the function name the LLM calls
  - description: what it does (the LLM reads this to decide when to call it)
  - parameters: JSON Schema defining the input shape
  - fn: the async Python function that executes the Cypher query
"""
import json
from agents.base import Tool
from graph import queries


def _wrap(query_fn, *args, **kwargs):
    """Wraps a sync graph query into an async callable."""
    import asyncio
    async def _async_wrapper(**kw):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: query_fn(*args, **kw, **kwargs))
    return _async_wrapper


# ─── SENTINEL AGENT TOOLS ─────────────────────────────────────────────────────

def make_blast_radius_tool() -> Tool:
    async def _fn(service_name: str, max_hops: int = 3) -> list[dict]:
        return queries.get_blast_radius(service_name, max_hops)

    return Tool(
        name="get_blast_radius",
        description=(
            "Traverses the FalkorDB service dependency graph to compute the blast radius "
            "of a failing service. Returns all upstream and downstream services affected, "
            "with their current status and hop distance. Always call this first when an "
            "incident is reported."
        ),
        parameters={
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Name of the service reporting the alert, e.g. 'checkout-service'"
                },
                "max_hops": {
                    "type": "integer",
                    "description": "How many dependency hops to traverse (default: 3)",
                    "default": 3,
                }
            },
            "required": ["service_name"]
        },
        fn=_fn,
    )


def make_service_status_tool() -> Tool:
    async def _fn(service_name: str) -> dict:
        result = queries.get_service_status(service_name)
        return result or {"error": f"Service '{service_name}' not found in graph"}

    return Tool(
        name="get_service_status",
        description="Returns the current status (healthy/degraded/failing) and metadata for a specific service.",
        parameters={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service name to look up"}
            },
            "required": ["service_name"]
        },
        fn=_fn,
    )


def make_shortest_path_tool() -> Tool:
    async def _fn(source_service: str, target_service: str) -> dict:
        result = queries.find_critical_path(source_service, target_service)
        return result or {"error": f"No dependency path found between '{source_service}' and '{target_service}'"}

    return Tool(
        name="find_critical_path",
        description=(
            "Runs FalkorDB's native shortestPath graph algorithm to find the exact chain "
            "of dependencies connecting two services. Use this to trace the direct failure propagation line."
        ),
        parameters={
            "type": "object",
            "properties": {
                "source_service": {"type": "string", "description": "Upstream calling service, e.g. 'checkout-service'"},
                "target_service": {"type": "string", "description": "Downstream failing service, e.g. 'inventory-postgres'"},
            },
            "required": ["source_service", "target_service"]
        },
        fn=_fn,
    )



# ─── INVESTIGATOR AGENT TOOLS ─────────────────────────────────────────────────

def make_recent_commits_tool() -> Tool:
    async def _fn(service_name: str, hours: int = 2) -> list[dict]:
        return queries.get_recent_commits(service_name, hours)

    return Tool(
        name="get_recent_commits",
        description=(
            "Searches FalkorDB for pull requests merged in the last N hours that modified "
            "the given service. Returns the PR title, diff summary, author name/Slack, "
            "and reviewer. This is the primary root-cause tool — most incidents are caused "
            "by recent code changes."
        ),
        parameters={
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Service to check for recent code changes"
                },
                "hours": {
                    "type": "integer",
                    "description": "How many hours back to search (default: 2)",
                    "default": 2,
                }
            },
            "required": ["service_name"]
        },
        fn=_fn,
    )


def make_service_owner_tool() -> Tool:
    async def _fn(service_name: str) -> dict:
        result = queries.get_service_owner(service_name)
        return result or {"error": f"No owner found for service '{service_name}'"}

    return Tool(
        name="get_service_owner",
        description="Returns the engineer who owns a service — name, Slack handle, role, team. Use this to know who to notify during an incident.",
        parameters={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Service name"}
            },
            "required": ["service_name"]
        },
        fn=_fn,
    )


def make_similar_incidents_tool() -> Tool:
    async def _fn(symptoms: list) -> list[dict]:
        return queries.find_similar_incidents(symptoms)

    return Tool(
        name="find_similar_incidents",
        description=(
            "Searches past incident episodes in FalkorDB episodic memory using symptom keywords. "
            "Returns matching incidents with root cause, MTTR, and which playbook resolved them. "
            "Always call this to check if we've seen this type of failure before."
        ),
        parameters={
            "type": "object",
            "properties": {
                "symptoms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of symptom keywords, e.g. ['db_pool', 'connection_timeout', 'inventory']"
                }
            },
            "required": ["symptoms"]
        },
        fn=_fn,
    )


# ─── MITIGATOR AGENT TOOLS ────────────────────────────────────────────────────

def make_get_playbook_tool() -> Tool:
    async def _fn(trigger_pattern: str) -> dict:
        result = queries.get_playbook(trigger_pattern)
        return result or {"error": f"No playbook found for pattern '{trigger_pattern}'"}

    return Tool(
        name="get_playbook",
        description=(
            "Retrieves an executable procedural memory playbook from FalkorDB for a given "
            "failure pattern. The playbook is stored as an ordered graph of Action nodes "
            "with MCP tool identifiers. Always call this before executing any remediation."
        ),
        parameters={
            "type": "object",
            "properties": {
                "trigger_pattern": {
                    "type": "string",
                    "description": "Failure pattern identifier, e.g. 'db_pool_exhaustion', 'cache_eviction_storm', 'canary_error_spike'"
                }
            },
            "required": ["trigger_pattern"]
        },
        fn=_fn,
    )


def make_execute_mcp_tool() -> Tool:
    from mcp.executor import execute_mcp_tool, MCPExecutionError

    async def _fn(tool_identifier: str, params: dict) -> dict:
        try:
            return await execute_mcp_tool(tool_identifier, params)
        except MCPExecutionError as e:
            return {"error": str(e)}

    return Tool(
        name="execute_mcp_tool",
        description=(
            "Executes an infrastructure action via MCP (Model Context Protocol). "
            "Use the tool_identifier from the playbook steps exactly as specified. "
            "Available tools: mcp_infra:patch_config, mcp_k8s:rollout_restart, "
            "mcp_k8s:rollout_undo, mcp_metrics:error_rate, mcp_metrics:cache_hit_rate, "
            "mcp_redis:flush_ns, mcp_infra:trigger_warmup, mcp_slack:notify. "
            "NEVER call a tool not in this list."
        ),
        parameters={
            "type": "object",
            "properties": {
                "tool_identifier": {
                    "type": "string",
                    "description": "MCP tool identifier from the playbook step, e.g. 'mcp_k8s:rollout_restart'"
                },
                "params": {
                    "type": "object",
                    "description": "Parameters to pass to the MCP tool (from playbook step params)"
                }
            },
            "required": ["tool_identifier", "params"]
        },
        fn=_fn,
    )


def make_write_episode_tool() -> Tool:
    async def _fn(incident_id: str, alert_name: str, root_cause: str,
                  root_cause_pr_id: str, mttr_seconds: int,
                  involved_services: list) -> dict:
        queries.write_episode(
            incident_id=incident_id,
            alert_name=alert_name,
            root_cause=root_cause,
            root_cause_pr_id=root_cause_pr_id,
            mttr_seconds=mttr_seconds,
            involved_services=involved_services,
        )
        return {
            "success": True,
            "message": f"Episode {incident_id} written to FalkorDB episodic memory",
            "incident_id": incident_id,
        }

    return Tool(
        name="write_episode",
        description=(
            "Writes the resolved incident as an Episodic Memory node in FalkorDB. "
            "ALWAYS call this as the final step after successful remediation. "
            "This is how the agent swarm learns — future incidents will find this episode "
            "and know what playbook to use."
        ),
        parameters={
            "type": "object",
            "properties": {
                "incident_id":      {"type": "string", "description": "Unique incident ID, e.g. 'INC-2026-10-11-001'"},
                "alert_name":       {"type": "string", "description": "Original alert name"},
                "root_cause":       {"type": "string", "description": "Human-readable root cause summary"},
                "root_cause_pr_id": {"type": "string", "description": "PR ID that caused the issue, e.g. 'PR-88'"},
                "mttr_seconds":     {"type": "integer", "description": "Total time to resolve in seconds"},
                "involved_services":{"type": "array", "items": {"type": "string"},
                                     "description": "List of service names involved in the incident"},
            },
            "required": ["incident_id", "alert_name", "root_cause",
                         "root_cause_pr_id", "mttr_seconds", "involved_services"]
        },
        fn=_fn,
    )

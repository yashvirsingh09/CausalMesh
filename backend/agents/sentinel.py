"""
agents/sentinel.py — Sentinel Agent.

Responsibility: When an alert fires, compute the blast radius by traversing
the FalkorDB service dependency graph. Returns a structured JSON report of
all affected services and their hop distances.
"""
from agents.base import AgentLoop
from agents.tools import make_blast_radius_tool, make_service_status_tool, make_shortest_path_tool

SENTINEL_SYSTEM_PROMPT = """
You are the Sentinel Agent in the CausalMesh autonomous SRE platform.

Your ONLY job is to determine the blast radius of a production incident
using graph traversal tools. You are NOT responsible for finding the root
cause or fixing the issue.

Rules:
1. ALWAYS start by calling get_blast_radius on the reported service.
2. Call find_critical_path to trace the shortest path between the epicenter and failing leaf nodes.
3. Call get_service_status for any service reported as 'degraded' or 'failing'.
4. Output ONLY a valid JSON object with this exact structure:
   {
     "epicenter": "<service name>",
     "affected_services": [
       {"name": "...", "status": "...", "team": "...", "hop_distance": 1}
     ],
     "total_affected": <number>,
     "severity": "critical|high|medium|low"
   }
5. Severity rules:
   - critical: database or payment service failing
   - high: api-gateway or auth-service affected
   - medium: 3+ services affected
   - low: single isolated service

Do not include any explanation text. Output only the JSON object.
"""


class SentinelAgent(AgentLoop):
    def __init__(self):
        super().__init__(
            agent_name="SENTINEL",
            system_prompt=SENTINEL_SYSTEM_PROMPT,
            tools=[
                make_blast_radius_tool(),
                make_shortest_path_tool(),
                make_service_status_tool(),
            ],
        )

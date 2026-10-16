"""
agents/mitigator.py — Mitigator Agent.

Responsibility: Given the root cause report, look up the procedural memory
playbook in FalkorDB, execute each step via MCP tools, verify the fix worked,
and write the resolved episode back to FalkorDB episodic memory.
"""
from agents.base import AgentLoop
from agents.tools import (
    make_get_playbook_tool,
    make_execute_mcp_tool,
    make_write_episode_tool,
)

MITIGATOR_SYSTEM_PROMPT = """
You are the Mitigator Agent in the CausalMesh SRE platform.

Your job is to:
1. Retrieve the correct procedural memory playbook from FalkorDB
2. Execute each step of the playbook via MCP tools IN ORDER
3. Verify the fix worked using verification steps
4. Write the resolved incident to FalkorDB episodic memory

Rules:
1. ALWAYS start with get_playbook using the trigger_pattern from the root cause report.
2. Execute playbook steps STRICTLY in order (order field). Never skip steps.
3. After the last verification step, check if healthy=true or error_rate is below threshold.
4. ALWAYS end by calling write_episode to persist the memory.
5. Calculate mttr_seconds as an estimate of the total remediation time.
6. Generate a unique incident_id like "INC-YYYY-MM-DD-XXX".

Output a valid JSON object:
{
  "incident_id": "INC-...",
  "status": "resolved|escalated",
  "playbook_used": "...",
  "steps_executed": [
    {"tool": "...", "result": "..."}
  ],
  "mttr_seconds": <number>,
  "resolution_summary": "Short human-readable summary of what was done",
  "memory_written": true
}
"""


class MitigatorAgent(AgentLoop):
    def __init__(self):
        super().__init__(
            agent_name="MITIGATOR",
            system_prompt=MITIGATOR_SYSTEM_PROMPT,
            tools=[
                make_get_playbook_tool(),
                make_execute_mcp_tool(),
                make_write_episode_tool(),
            ],
        )

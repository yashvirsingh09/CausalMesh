"""
tests/test_mcp.py — Unit tests for MCP tool executor.
"""
import pytest
from mcp.executor import execute_mcp_tool, list_available_tools, MCPExecutionError


@pytest.mark.asyncio
async def test_list_available_tools():
    tools = list_available_tools()
    assert "mcp_infra:patch_config" in tools
    assert "mcp_k8s:rollout_restart" in tools
    assert "mcp_metrics:error_rate" in tools


@pytest.mark.asyncio
async def test_execute_patch_config():
    result = await execute_mcp_tool("mcp_infra:patch_config", {"param": "max_conn=250"})
    assert result["success"] is True
    assert "max_conn=250" in result["applied"]


@pytest.mark.asyncio
async def test_execute_rollout_restart():
    result = await execute_mcp_tool("mcp_k8s:rollout_restart", {"service": "inventory-service"})
    assert result["success"] is True
    assert result["service"] == "inventory-service"
    assert result["pods_restarted"] > 0


@pytest.mark.asyncio
async def test_execute_metrics_error_rate():
    result = await execute_mcp_tool("mcp_metrics:error_rate", {"threshold": 0.01})
    assert result["success"] is True
    assert result["healthy"] is True


@pytest.mark.asyncio
async def test_unknown_mcp_tool_raises_error():
    with pytest.raises(MCPExecutionError):
        await execute_mcp_tool("mcp_unknown:does_not_exist", {})

"""
integrations/github_pr.py — Shift-Left Preventative CI/CD & Architecture Guard.
Analyzes pull requests before merge, calculates topological blast radius in FalkorDB,
and posts automated architectural risk assessments to GitHub PR comments.
"""
import os
import re
import logging
from typing import Any, Optional
import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from config import ACTIVE_GRAPH
from graph import queries

router = APIRouter(prefix="/api/v1/integrations/github", tags=["enterprise-github-guard"])
logger = logging.getLogger("causalmesh.github")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


class PRAnalysisRequest(BaseModel):
    pr_id: str = Field(default="PR-88")
    title: str = Field(default="tune db_pool idle timeout")
    author: str = Field(default="Dave Kim")
    service: str = Field(default="inventory-service")
    diff_summary: str = Field(default="db_pool.idle_timeout: 30s -> 2s\nmax_connections: 50 -> 20")
    repo_full_name: Optional[str] = None
    pr_number: Optional[int] = None
    graph_name: str = Field(default=ACTIVE_GRAPH)


class PRAnalysisResponse(BaseModel):
    pr_id: str
    target_service: str
    risk_level: str
    blast_radius: list[str]
    in_degree: int
    summary: str
    markdown_comment: str
    requires_sre_approval: bool


def _infer_service_from_paths(changed_files: list[str]) -> str:
    """Infers microservice name from directory paths in git diff."""
    for f in changed_files:
        f_lower = f.lower()
        if "inventory" in f_lower:
            return "inventory-service"
        if "checkout" in f_lower:
            return "checkout-service"
        if "payment" in f_lower:
            return "payment-service"
        if "order" in f_lower:
            return "order-service"
        if "auth" in f_lower:
            return "auth-service"
        if "gateway" in f_lower:
            return "api-gateway"
    return "inventory-service"


def analyze_pr_architecture_risk(
    pr_id: str,
    title: str,
    author: str,
    service: str,
    diff_summary: str,
    graph_name: str = ACTIVE_GRAPH
) -> PRAnalysisResponse:
    """
    Evaluates PR risk by querying FalkorDB's dependency graph.
    Computes blast radius of upstream callers that rely on the modified service.
    """
    # Query FalkorDB blast radius (upstream callers that depend on this service)
    blast_records = queries.get_blast_radius(service, max_hops=3, graph_name=graph_name)
    upstream_callers = [r["service"] for r in blast_records if isinstance(r, dict) and "service" in r]
    
    # Calculate in-degree (how many services call this service directly)
    in_degree = 0
    all_svcs = queries.get_all_services(graph_name)
    for s in all_svcs:
        if s.get("name") == service:
            in_degree = s.get("in_degree", 0)
            break

    # Check for dangerous configuration changes in diff
    dangerous_patterns = [
        r"idle_timeout.*[1-5]s",
        r"timeout.*reduce",
        r"pool.*shrink",
        r"memory.*limit",
        r"max_connections.*reduce",
    ]
    
    has_dangerous_config = any(re.search(p, diff_summary, re.IGNORECASE) for p in dangerous_patterns)
    is_high_blast = len(upstream_callers) >= 2 or in_degree >= 2

    if has_dangerous_config and is_high_blast:
        risk_level = "CRITICAL"
        requires_approval = True
    elif is_high_blast or has_dangerous_config:
        risk_level = "HIGH"
        requires_approval = True
    else:
        risk_level = "LOW"
        requires_approval = False

    # Format Markdown Comment for GitHub PR
    upstream_list = "\n".join([f"  - `{s}`" for s in upstream_callers[:5]]) if upstream_callers else "  - None (edge service)"
    
    md_comment = f"""### CausalMesh Preventative Architecture Guard

**Status: {'ACTION REQUIRED (Risk Detected)' if requires_approval else 'PASSED (Low Architectural Impact)'}**

- **Target Service:** `{service}` (Dependency In-Degree: {in_degree})
- **Author:** `{author}`
- **Risk Level:** `{risk_level}`
- **Upstream Blast Radius ({len(upstream_callers)} services):**
{upstream_list}

**Architectural Analysis:**
{f"Warning: Diff modifies critical runtime resource or connection pool settings on `{service}`. Because `{service}` is a shared dependency for {len(upstream_callers)} services, under flash traffic this can cause connection pool starvation and cascade 504 timeouts upstream." if requires_approval else f"Changes to `{service}` have low topological cascade risk."}

**Recommendation:**
{f"Ensure load testing with synthetic traffic is completed and SRE approval is granted before merging `{pr_id}`." if requires_approval else "Approved for normal CI/CD merge pipeline."}

*Analysis powered by FalkorDB GraphBLAS Sparse Adjacency Matrix Pathfinding.*
"""

    return PRAnalysisResponse(
        pr_id=pr_id,
        target_service=service,
        risk_level=risk_level,
        blast_radius=upstream_callers,
        in_degree=in_degree,
        summary=f"Topological blast risk: {risk_level} ({len(upstream_callers)} upstream services affected)",
        markdown_comment=md_comment.strip(),
        requires_sre_approval=requires_approval
    )


@router.post("/analyze-pr", response_model=PRAnalysisResponse)
async def analyze_pr_endpoint(payload: PRAnalysisRequest):
    """
    Direct endpoint for CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins)
    to verify PR risk against FalkorDB before merge.
    """
    analysis = analyze_pr_architecture_risk(
        pr_id=payload.pr_id,
        title=payload.title,
        author=payload.author,
        service=payload.service,
        diff_summary=payload.diff_summary,
        graph_name=payload.graph_name
    )

    # If repo and pr_number provided and GITHUB_TOKEN set, post comment directly
    if payload.repo_full_name and payload.pr_number and GITHUB_TOKEN:
        await _post_github_comment(payload.repo_full_name, payload.pr_number, analysis.markdown_comment)

    return analysis


@router.post("/webhook")
async def github_webhook_receiver(request: Request):
    """
    Receives native GitHub webhook events (event: pull_request).
    Automatically runs architecture guard analysis and comments on PR.
    """
    event_type = request.headers.get("X-GitHub-Event", "")
    if event_type != "pull_request":
        return {"status": "ignored", "reason": f"Event '{event_type}' not a pull_request"}

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    action = body.get("action", "")
    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "reason": f"PR action '{action}' does not require scan"}

    pr_data = body.get("pull_request", {})
    pr_number = pr_data.get("number", 0)
    repo_data = body.get("repository", {})
    repo_full_name = repo_data.get("full_name", "")
    title = pr_data.get("title", "")
    author = pr_data.get("user", {}).get("login", "engineer")
    body_text = pr_data.get("body", "") or ""

    # Infer service
    inferred_service = "inventory-service" if "inventory" in title.lower() or "inventory" in body_text.lower() else "checkout-service"

    analysis = analyze_pr_architecture_risk(
        pr_id=f"PR-{pr_number}",
        title=title,
        author=author,
        service=inferred_service,
        diff_summary=body_text or title
    )

    if repo_full_name and pr_number and GITHUB_TOKEN:
        await _post_github_comment(repo_full_name, pr_number, analysis.markdown_comment)

    return {
        "status": "analyzed",
        "pr_number": pr_number,
        "risk_level": analysis.risk_level,
        "blast_radius_count": len(analysis.blast_radius),
        "comment": analysis.markdown_comment
    }


async def _post_github_comment(repo_full_name: str, pr_number: int, comment_body: str):
    """Posts markdown comment to GitHub PR via REST API."""
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json={"body": comment_body}, headers=headers)
    except Exception as e:
        logger.error(f"Failed to post comment to GitHub: {e}")

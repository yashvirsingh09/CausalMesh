"""
main.py — CausalMesh FastAPI Application Entry Point.
Autonomous SRE & Incident Memory Mesh for distributed systems.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import (
    APP_ENV,
    ACTIVE_GRAPH,
    LLM_PROVIDER,
    LLM_MODEL,
    FALKORDB_HOST,
    FALKORDB_PORT,
)
from graph.client import ping
from graph import seed
from api.graph import router as graph_router
from api.incident import router as incident_router
from api.stream import router as stream_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook: checks FalkorDB on startup, seeds if needed."""
    print("=" * 65)
    print(">> CAUSALMESH -- Autonomous SRE & Incident Memory Mesh")
    print("=" * 65)
    is_connected = ping()
    print(f"  FalkorDB Host:     {FALKORDB_HOST}:{FALKORDB_PORT}")
    print(f"  FalkorDB Status:   {'ONLINE' if is_connected else 'OFFLINE (In-Memory Engine Active)'}")
    print(f"  Active Graph:      {ACTIVE_GRAPH}")
    print(f"  LLM Provider:      {LLM_PROVIDER} ({LLM_MODEL})")
    print(f"  Environment:       {APP_ENV}")
    print("=" * 65)

    # Initialize / Seed graph
    try:
        seed.seed(ACTIVE_GRAPH, verbose=False)
        print("[OK] Graph initialized and seeded with 25 services & operational topology.")
    except Exception as e:
        print(f"[NOTE] Seeding note: {e}")

    yield

    print("CausalMesh backend shutting down.")


app = FastAPI(
    title="CausalMesh API",
    description="Autonomous Multi-Agent SRE & Incident Memory Mesh powered by FalkorDB",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(graph_router, prefix="/api")
app.include_router(incident_router, prefix="/api")
app.include_router(stream_router, prefix="/api")


@app.get("/")
def root():
    return {
        "project": "CausalMesh",
        "tagline": "Autonomous SRE & Incident Memory Mesh",
        "sponsor": "FalkorDB Graph Hacks 2026",
        "tracks": [
            "Track 01: Agents That Act on Connected Data",
            "Track 02: Agent Memory and Coordination",
            "Track 03: Company Brain",
        ],
        "status": "operational",
        "docs_url": "/docs",
    }


@app.get("/health")
@app.get("/api/health")
def healthcheck():
    is_db_up = ping()
    return {
        "status": "healthy",
        "falkordb": {
            "connected": is_db_up,
            "host": f"{FALKORDB_HOST}:{FALKORDB_PORT}",
            "active_graph": ACTIVE_GRAPH,
            "mode": "live_database" if is_db_up else "in_memory_engine",
        },
        "llm": {
            "provider": LLM_PROVIDER,
            "model": LLM_MODEL,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

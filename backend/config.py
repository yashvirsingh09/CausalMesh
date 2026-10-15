"""
config.py — Central configuration loaded from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

# FalkorDB (Local Docker or FalkorDB Cloud)
FALKORDB_HOST = os.getenv("FALKORDB_HOST", "localhost")
FALKORDB_PORT = int(os.getenv("FALKORDB_PORT", 6379))
FALKORDB_PASSWORD = os.getenv("FALKORDB_PASSWORD", None)
FALKORDB_USERNAME = os.getenv("FALKORDB_USERNAME", None)
FALKORDB_SSL = os.getenv("FALKORDB_SSL", "false").lower() == "true"

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# App
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Graph names — FalkorDB multigraph isolation
GRAPH_PROD = "causalmesh_prod"
GRAPH_STAGING = "causalmesh_staging"
ACTIVE_GRAPH = GRAPH_PROD

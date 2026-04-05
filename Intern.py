from fastapi import FastAPI, HTTPException, Header, Depends  # FastAPI framework + helpers for errors, headers, and dependency injection
from pydantic import BaseModel                                # Pydantic turns class definitions into auto-validating request bodies
from typing import Dict, Optional, List, Set                 # Type hints for containers and Optional (allows None)
import secrets                                               # Standard-library module for cryptographically secure random tokens
import numpy as np                                           # NumPy creates float32 arrays that FAISS and sentence-transformers require
import faiss                                                 # Facebook AI Similarity Search — fast nearest-neighbour lookup over dense vectors
from sentence_transformers import SentenceTransformer        # Loads pre-trained models that convert text into semantic embedding vectors

app = FastAPI()                                              # Creates the main application object — all routes are registered on this instance

# -----------------------------
# Models
# -----------------------------

class Agent(BaseModel):                                      # Pydantic model — FastAPI auto-validates incoming JSON against these fields
    name: str                                                # Agent's unique identifier string
    description: str                                         # Free-text description (also used to build the FAISS embedding)
    endpoint: str                                            # URL where this agent can be called

class Usage(BaseModel):                                      # Request body for POST /usage
    caller: str                                              # FIX: was missing — spec requires caller in the body; verified against API key in the route
    target: str                                              # Name of the agent whose usage is being recorded
    units: int                                               # Numeric cost/consumption to log
    request_id: str                                          # Client-supplied idempotency key — same ID sent twice is ignored

# -----------------------------
# In-memory storage
# -----------------------------

agents: Dict[str, dict] = {}                                 # Master agent store — key = agent name, value = full agent dict including api_key
api_keys: Dict[str, str] = {}                                # Reverse map: api_key → agent name, used by the auth dependency
processed_requests: Set[str] = set()                         # Idempotency tracker — holds every request_id seen so far
usage_summary: Dict[str, int] = {}                           # Aggregated unit totals keyed by target agent name

model = SentenceTransformer("all-MiniLM-L6-v2")             # Loads the embedding model once at startup (produces 384-dimensional vectors)
dimension = 384                                              # Must match the model's output size — used when building the FAISS index
index = faiss.IndexFlatL2(dimension)                         # Flat L2 index: exact brute-force search over all stored vectors
agent_names: List[str] = []                                  # Positional map: slot i → agent name; FAISS returns integers so we need this to recover the name

# -----------------------------
# Auth
# -----------------------------

def authenticate(x_api_key: Optional[str] = Header(None)):  # FastAPI dependency — reads X-Api-Key header automatically when injected with Depends()
    if not x_api_key:                                        # Guards against a missing header entirely
        raise HTTPException(status_code=401, detail="API key missing")   # 401 Unauthorized — credentials not provided
    if x_api_key not in api_keys:                            # Checks the key against our in-memory registry
        raise HTTPException(status_code=403, detail="Invalid API key")   # 403 Forbidden — credentials provided but not recognised
    return api_keys[x_api_key]                               # Returns the agent name that owns this key; injected as `caller` in protected routes

# -----------------------------
# PART 1: Agent Registry
# -----------------------------

@app.post("/agents")                                         # Registers the POST /agents route
def add_agent(agent: Agent):                                 # FastAPI parses and validates the JSON body into an Agent instance automatically
    if agent.name in agents:                                 # Prevents duplicate registrations
        raise HTTPException(status_code=400, detail="Agent already exists")  # 400 if the name is already taken

    api_key = secrets.token_hex(16)                          # Generates a 32-character hex API key — cryptographically random

    embedding = model.encode(agent.description).astype("float32")  # Converts the description to a 384-dim vector; float32 is required by FAISS
    index.add(np.array([embedding]))                         # Appends the vector to FAISS — its position equals current len(agent_names)
    agent_names.append(agent.name)                           # Records the name at the matching position so FAISS results can be resolved back to a name

    agents[agent.name] = {                                   # Stores the full agent record in the master dict
        "name": agent.name,
        "description": agent.description,
        "endpoint": agent.endpoint,
        "api_key": api_key
    }
    api_keys[api_key] = agent.name                           # Populates the reverse map for auth lookups

    return {                                                  # Returns the generated key — the only time it is exposed to the caller
        "message": "Agent registered",
        "api_key": api_key,
        "agent": agents[agent.name]
    }

@app.get("/agents")                                          # Registers the GET /agents route
def list_agents():                                           # No auth required per spec
    return list(agents.values())                             # Returns all registered agents as a plain list

# -----------------------------
# FAISS Semantic Search
# -----------------------------

@app.get("/search")
def search_agents(q: str, k: int = 5):
    if not agent_names:
        return []

    query_lower = q.lower()
    
    # Use different buckets to maintain priority
    exact_name_matches = []
    keyword_matches = []
    semantic_matches = []

    # 1. Keyword & Exact Name Check
    for name, data in agents.items():
        if query_lower == name.lower():
            exact_name_matches.append(data)
        elif query_lower in name.lower() or query_lower in data["description"].lower():
            keyword_matches.append(data)

    # 2. Semantic Search (Bonus)
    query_embedding = model.encode(q).astype("float32")
    distances, indices = index.search(np.array([query_embedding]), min(k, len(agent_names)))

    for dist, idx in zip(distances[0], indices[0]):
        if idx != -1 and idx < len(agent_names) and dist < 1.2:
            name = agent_names[idx]
            # Only add if not already caught by exact or keyword search
            if name not in [a["name"] for a in exact_name_matches + keyword_matches]:
                semantic_matches.append(agents[name])

    # Combine in order of priority: Exact Name > Keyword Match > Semantic Similarity
    all_results = exact_name_matches + keyword_matches + semantic_matches
    
    # Final cap at 'k' results
    return all_results[:k]
                    # Return combined results, capped at k

# -----------------------------
# PART 2: Usage Logging
# -----------------------------

@app.post("/usage")                                          # Logs a usage event — requires authentication
def log_usage(
    usage: Usage,
    caller: str = Depends(authenticate)                      # Injects the authenticated agent name via the auth dependency
):
    # FIX: verify the body's caller field matches the authenticated API key owner
    if usage.caller != caller:                               # Prevents one agent from logging usage on behalf of another
        raise HTTPException(status_code=403, detail="caller mismatch — body caller does not match API key owner")

    if usage.target not in agents:                           # Validates the target agent exists before logging
        raise HTTPException(status_code=400, detail="Target agent not found")  # 400 — Part 3 edge case handled

    if usage.request_id in processed_requests:               # Idempotency check — has this exact request been seen before?
        return {"message": "Duplicate request ignored"}      # Silent success — do not double-count, do not error

    processed_requests.add(usage.request_id)                 # Marks the request ID as processed so future duplicates are caught
    usage_summary[usage.target] = usage_summary.get(usage.target, 0) + usage.units  # Increments the counter, defaulting to 0 on first occurrence

    return {                                                  # Confirms the log with caller identity for auditability
        "message": "Usage logged",
        "caller": caller,
        "target": usage.target
    }

# -----------------------------
# PART 3: Usage Summary
# -----------------------------

@app.get("/usage-summary")                                   # Returns aggregate usage — requires authentication
def get_usage_summary(caller: str = Depends(authenticate)):  # Any authenticated agent can view the full summary
    return {                                                  # Returns the caller's identity plus the full aggregation dict
        "requested_by": caller,
        "data": usage_summary
    }
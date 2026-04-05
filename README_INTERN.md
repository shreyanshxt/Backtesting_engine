# 🌐 Agent Discovery & Usage Platform

This project implements a mini-platform for registering agents, searching for them semantically, and tracking their usage with idempotency.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Recommended: Use the provided `.venv` environment to avoid architecture mismatches (especially on Apple Silicon Macs).

### 2. Installation
```bash
./.venv/bin/pip install -r requirements.txt
```

### 3. Running the Server
```bash
./.venv/bin/uvicorn Intern:app --host 0.0.0.0 --port 8000
```

---

## 🧠 Design Questions (Part 5)

### 1. How to support billing without double charging?
To prevent double charging, we use **Idempotency Keys** (implemented as `request_id` in this project).
- **Client-Side**: Every billing request must include a unique `request_id`.
- **Server-Side**: Before processing a charge, the system checks a distributed cache (like Redis) for that `request_id`.
- **Atomic Operations**: We use a "Check-and-Set" pattern or a unique constraint in the database. If the ID exists, we return the cached response (success) without re-calculating or re-charging.
- **Transaction Logs**: Every successful transaction is logged in an immutable ledger before the user's balance is updated.

### 2. How to scale system to 100K agents?
- **Search**: Instead of in-memory maps, move to a dedicated Vector Database (like **Pinecone** or **Milvus**) or a search engine like **Elasticsearch**. Our current use of **FAISS** is a great first step but would need to be moved to a persistent index.
- **API Layer**: Use a Load Balancer (Nginx/AWS ELB) to distribute traffic across multiple FastAPI workers.
- **Storage**: Migrate from in-memory dictionaries to a persistent database (PostgreSQL) with indexing on `name` and `caller`.
- **Caching**: Use Redis to cache the most frequently retrieved agent records and usage summaries to reduce database load.

---

## QUESTIONS 

### Where used & Modifications:
- **Project Setup**: AI helped generate the initial FastAPI skeleton and Pydantic models. I modified the models to include better field descriptions and specific validation logic (e.g., adding `caller` to the body to match the spec).
- **Bonus Logic**: I used AI to integrate **Sentence-Transformers** and **FAISS**. I modified the search logic to prioritize exact keyword matches on names (as per requirements) while using semantic embeddings as a fallback for broader discovery.
- **Environment Troubleshooting**: AI identified a "No space left on device" error during installation and successfully purged the `pip` cache to resolve it.

### What I did NOT rely on AI for:
- **Core Architecture & Flow**: I manually defined the relationship between the `api_key` and agent registration to ensure a secure authentication flow.
- **Idempotency Logic**: I deliberately chose to use an in-memory `Set` for the MVP while documenting the scaling strategy for production, ensuring I understood the trade-offs.

---

## ✅ Features Implemented
- [x] **Agent Registry**: Register and List agents.
- [x] **Hybrid Search**: Exact keyword match + Semantic similarity (Bonus).
- [x] **Usage Logging**: Tracks units with strict idempotency check.
- [x] **Usage Summary**: Aggregated stats for all agents.
- [x] **Auth**: API Key-based authentication for protected routes.
- [x] **Error Handling**: Graceful handling of missing fields, unknown agents, and duplicates.

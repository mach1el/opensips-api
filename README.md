# opensips-apis

[![OpenSIPS](https://img.shields.io/badge/OpenSIPS-3.4%2B-4caf50?style=flat-square)](https://www.opensips.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Ready-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

**opensips-apis** is a lightweight service layer that exposes custom HTTP endpoints to support **OpenSIPS** with special routing-time operations. It centralizes business logic that would otherwise bloat `opensips.cfg`, keeping SIP routing fast while allowing data-backed decisions and utilities to evolve independently.

---

## Overview

- **Purpose**
  - Offload complex, data-driven, or environment-specific logic from OpenSIPS into a small stateless web service.
  - Enable consistent behavior across environments via configuration (no `.env` required).

- **What it provides (at a glance)**
  - Number normalization and formatting utilities.
  - Small policy/utility checks (e.g., simple allow-lists or context guards).
  - Optional database-backed lookups for routing decisions.
  - Health/readiness probes for orchestration.

- **How it integrates**
  - OpenSIPS calls this service using `http_client`.
  - Results are returned as compact JSON that can be parsed with OpenSIPS `json` module.
  - You implement the final routing policy in `opensips.cfg`.

---

## Architecture (High Level)

- **Runtime:** FastAPI + Uvicorn (Python 3.12)
- **State:** Stateless application; configuration via environment variables
- **Data:** Optional PostgreSQL for lookups (indexes recommended on queried fields)
- **Packaging:** Container-first (Dockerfile included)
- **Scalability:** Horizontally scalable behind L4/L7 load balancers
- **Port:** Configurable via `PORT` (default typically `3000`)

---

## Configuration (High Level)

- **Server:** `HOST`, `PORT`
- **Database (optional):** `PG*` variables for connectivity, plus table/column names for lookups
- **Network Controls (optional):** Allow-list via comma-separated CIDRs/IPs

> Supply via Docker/Compose/Swarm/Kubernetes secrets/config; no `.env` required.

---

## Deployment (High Level)

- **Docker:** Build and run the container; map `PORT` as needed
- **Compose/Swarm/K8s:** Add health checks, resource limits/requests, and proximity to OpenSIPS/DB
- **Resiliency:** Configure timeouts/retries/backoff in callers or your gateway

---

## OpenSIPS Integration (Conceptual)

1. Load `http_client` and `json` modules.
2. From a routing block, POST a small JSON payload (e.g., number/context).
3. Parse JSON response and apply your routing policy (rewrite/route/deny).
4. Log decisions for observability.

---

## Observability & Operations

- **Health:** `/health` endpoint for liveness/readiness
- **Logging:** Structured logs for inputs, decisions, timings
- **Metrics (roadmap):** Prometheus/OpenTelemetry
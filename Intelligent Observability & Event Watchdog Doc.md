# Intelligent Observability & Event Watchdog

### Intelligent Event Watchdog & Incident Triage System


|             |             |
| ----------- | ----------- |
| **Version** | 1.0         |
| **Author**  | Samit Pawar |


---

## Purpose

This document defines the complete functional, technical, architectural, and implementation requirements for the **Agentic Observability Platform**. The platform is designed as an AI-powered Site Reliability Engineering (SRE) solution that ingests application logs, detects anomalies, correlates events into incidents, performs AI-assisted root cause analysis, recommends remediation steps, triggers alerts, and visualizes operational health.

The project is intended to demonstrate expertise in:

- Python API development
- Platform Engineering
- Observability
- Event-driven architectures
- AI-assisted development
- Agentic workflows
- Retrieval-Augmented Generation (RAG)
- SDK design
- Testing and CI/CD
- Cloud-native architecture

---

## Table of Contents

1. [Business Problem](#1-business-problem)
2. [Project Goals](#2-project-goals)
3. [Technology Stack](#3-technology-stack)
  - [3.1 AI Provider Architecture](#31-ai-provider-architecture)
4. [High-Level Architecture](#4-high-level-architecture)
5. [System Components](#5-system-components)
6. [Database Design](#6-database-design)
7. [Python SDK](#7-python-sdk)
8. [API Requirements](#8-api-requirements)
9. [Security Requirements](#9-security-requirements)
10. [Testing Requirements](#10-testing-requirements)
11. [CI/CD Requirements](#11-cicd-requirements)
12. [Docker Requirements](#12-docker-requirements)
13. [Repository Structure](#13-repository-structure)
14. [Presentation Requirements](#14-presentation-requirements)
15. [Acceptance Criteria](#15-acceptance-criteria)

---

## 1. Business Problem

Modern applications generate thousands of logs every minute. Operations teams struggle to:

- Detect issues early
- Understand root causes quickly
- Avoid alert fatigue
- Correlate related failures
- Identify impacted services
- Determine remediation actions

Traditional monitoring tools provide metrics and alerts but require human interpretation.

This platform introduces an AI-assisted incident management workflow that combines statistical anomaly detection, event correlation, runbook retrieval, and agentic reasoning to reduce **mean time to detection (MTTD)** and **mean time to resolution (MTTR)**.

---

## 2. Project Goals

The platform shall:

1. Accept application and infrastructure logs through APIs.
2. Detect anomalies using statistical methods.
3. Correlate related anomalies into incidents.
4. Determine affected services and blast radius.
5. Perform AI-assisted incident triage.
6. Retrieve relevant operational runbooks.
7. Generate executive incident summaries.
8. Trigger alerts through multiple channels.
9. Provide operational dashboards.
10. Expose a reusable Python SDK.
11. Support local execution without cloud costs.
12. Maintain complete auditability of AI prompts.

---

## 3. Technology Stack


| Area           | Technologies                                                                                                  |
| -------------- | ------------------------------------------------------------------------------------------------------------- |
| **Backend**    | Python 3.12+, FastAPI, SQLAlchemy, SQLite, Pydantic, Gemini API (Google AI Studio, `google-genai` SDK), NumPy |
| **Frontend**   | React, Vite, Recharts                                                                                         |
| **Testing**    | Pytest, Coverage                                                                                              |
| **Quality**    | Ruff, Black, Mypy                                                                                             |
| **Deployment** | Docker, Docker Compose                                                                                        |
| **CI/CD**      | GitHub Actions                                                                                                |


### 3.1 AI Provider Architecture

The platform shall use Google's Gemini models for all AI-assisted workflows.

**Primary Model:** Gemini 1.5 Flash

**Responsibilities:**

- Incident classification
- Root cause analysis
- Remediation generation
- Executive summaries
- Runbook-assisted incident analysis

**Fallback Mode:** Mock AI responses when no API key is configured.

**Environment Variables:**


| Variable         | Required | Default            |
| ---------------- | -------- | ------------------ |
| `GEMINI_API_KEY` | Yes      | —                  |
| `USE_MOCK_AI`    | No       | `false`            |
| `MODEL_NAME`     | No       | `gemini-1.5-flash` |


**Gemini Structured Output Requirements**

All agent outputs (except the Executive Summary Agent) must use response schemas. Responses must be validated before persistence.

Examples:

```python
class ClassificationResponse(BaseModel):
    category: str


class RootCauseAnalysis(BaseModel):
    root_cause: str
    confidence: float


class RemediationResponse(BaseModel):
    recommended_actions: list[str]
```

**Cost Optimization**

The platform shall operate entirely within Gemini free-tier limits for development, testing, and demo scenarios.

- No paid AI infrastructure shall be required.
- No cloud resources shall be provisioned.
- No vector databases shall be provisioned.
- All processing shall execute locally except Gemini API requests.

---

## 4. High-Level Architecture

Applications send logs to the platform. The platform performs:

1. Log ingestion
2. Normalization
3. Statistical anomaly detection
4. Event correlation
5. Incident generation
6. Agentic AI triage
7. RAG runbook retrieval
8. Alert generation
9. Dashboard visualization

**Data flow:**

```text
Application Logs
  → Ingestion API
  → Event Store
  → Detection Engine
  → Correlation Engine
  → Incident Engine
  → Agentic Triage (Gemini Incident Intelligence Layer)
  → Alert Engine
  → Dashboard
```

The **Gemini Incident Intelligence Layer** is composed of:

- Classification Agent
- Root Cause Agent
- Remediation Agent
- Executive Summary Agent

All powered by Gemini 1.5 Flash.

> **Note on "AI logic":** AI logic in this platform spans two layers. The **Detection Engine** (Component 4) applies deterministic statistical methods (Z-Score, EWMA) to detect error spikes — chosen because anomaly detection must be reproducible and testable. The **Gemini Incident Intelligence Layer** (Component 8) then applies generative AI for classification, root cause analysis, and remediation. Together they form the platform's end-to-end AI-assisted detection and triage logic.

---

## 5. System Components

### Component 1 — Log Ingestion Service

**Purpose:** Receive structured logs.

**Responsibilities:**

- Accept single log events
- Accept batch log events
- Validate payloads
- Normalize data
- Persist events

**Endpoints:**

```http
POST /api/v1/events
POST /api/v1/events/batch
GET  /api/v1/events
```

#### Event Schema

**Required Fields:**

- `service`
- `level`
- `message`
- `timestamp`

**Optional Fields:**

- `hostname`
- `environment`
- `metadata`

**Example:**

```json
{
  "service": "payment-api",
  "level": "ERROR",
  "message": "Database timeout",
  "timestamp": "2026-06-18T10:00:00Z"
}
```

### Component 2 — Event Normalization

**Purpose:** Transform logs into consistent signatures.

**Example:**


| Raw message                         | Normalized signature |
| ----------------------------------- | -------------------- |
| `Database timeout after 20 seconds` | `Database timeout`   |
| `Database timeout after 31 seconds` | `Database timeout`   |


**Responsibilities:**

- Remove dynamic values
- Generate event signatures
- Standardize severity levels

### Component 3 — Synthetic Traffic Generator

**Purpose:** Create realistic demo scenarios.

**Supported Scenarios:**

- Normal traffic
- Database outage
- Authentication failures
- API throttling
- Memory leak
- Service dependency failure
- Black Friday traffic spike

The generator must create `INFO`, `WARN`, `ERROR`, and `CRITICAL` events.

### Component 4 — Statistical Detection Engine

**Purpose:** Detect abnormal behavior.

**Detection Strategy 1 — Error Rate Spike Detection**

Calculate errors per minute and compare against baseline.

Methods:

- Z-Score
- EWMA

**Detection Strategy 2 — Signature Frequency Detection**


| State   | `Database timeout` rate |
| ------- | ----------------------- |
| Normal  | 2 / minute              |
| Current | 70 / minute             |


→ Generate anomaly.

**Detection Strategy 3 — Severity Distribution Drift**


| Level | Normal | Current |
| ----- | ------ | ------- |
| INFO  | 90%    | 40%     |
| WARN  | 8%     | 10%     |
| ERROR | 2%     | 50%     |


→ Generate anomaly.

### Component 5 — Event Correlation Engine

**Purpose:** Prevent alert storms. Multiple related anomalies should become one incident.

**Example:**


| Anomalies                                                  | Result                        |
| ---------------------------------------------------------- | ----------------------------- |
| `Database timeout`, `Connection refused`, `Pool exhausted` | Database Degradation Incident |


**Responsibilities:**

- Correlate events
- Group anomalies
- Deduplicate alerts
- Create incidents

### Component 6 — Service Topology Engine

**Purpose:** Model dependencies.

**Example:**

```text
Auth API
  ↓
Order API
  ↓
Payment API
```

**Responsibilities:**

- Maintain service graph
- Calculate blast radius
- Identify root service
- Determine affected services

**Input Format:**

```json
{
  "payment-api": ["order-api"],
  "order-api": ["auth-api"]
}
```

### Component 7 — Incident Management

**Purpose:** Manage lifecycle of incidents.

**Statuses:** `Open`, `Investigating`, `Mitigated`, `Resolved`

**Severity Levels:** `Critical`, `High`, `Medium`, `Low`

**Incident Fields:**

- `title`
- `severity`
- `status`
- `created_at`
- `resolved_at`
- `root_cause`
- `summary`

### Component 8 — Agentic Incident Triage

**Purpose:** Perform AI-assisted analysis powered by Gemini 1.5 Flash.

#### Agent 1 — Classification Agent

**Input:**

- Event signatures
- Severity distribution
- Incident metadata

**Output:**

```json
{
  "category": "Database"
}
```

**Categories:** `Database`, `Authentication`, `Network`, `Infrastructure`, `Application`

**Implementation:** Gemini Structured Output Schema (`ClassificationResponse`)

#### Agent 2 — Root Cause Agent

**Input:**

- Aggregated anomaly data
- Correlated incidents
- Top event signatures

**Output:**

```json
{
  "root_cause": "Database connection pool exhaustion",
  "confidence": 0.89
}
```

**Implementation:** Gemini Structured Output Schema (`RootCauseAnalysis`)

#### Agent 3 — Remediation Agent

**Input:**

- Root cause
- Retrieved runbooks

**Output:**

```json
{
  "recommended_actions": [
    "Increase connection pool size",
    "Investigate slow queries",
    "Verify database resource utilization"
  ]
}
```

**Implementation:** Gemini Structured Output Schema (`RemediationResponse`)

#### Agent 4 — Executive Summary Agent

**Input:**

- Incident details
- Affected services
- Root cause
- Alert statistics

**Output:** Executive-level narrative summary.

The final incident report aggregates:

- Category
- Root Cause
- Remediation
- Confidence Score
- Executive Summary

**Implementation:** Gemini Text Generation

### Component 9 — Runbook RAG Engine

**Purpose:** Retrieve operational knowledge.

**Source Directory:** `data/runbooks/`

**Examples:**

- `database_timeout.md`
- `memory_leak.md`
- `jwt_failure.md`
- `disk_full.md`

**Workflow:**

1. Incident created.
2. Relevant runbooks identified.
3. Matching runbook sections retrieved.
4. Retrieved context injected into the Gemini prompt.
5. Gemini generates enhanced triage output.

**Implementation Note**

A full vector database is not required. The initial implementation may use:

- SQLite
- Metadata filtering
- Keyword matching

The architecture must remain RAG-compatible. Future versions may replace retrieval with Vertex AI Search, Pinecone, OpenSearch, or Qdrant — without changing the AI workflow.

### Component 10 — AI Incident Summary

**Purpose:** Generate executive-readable reports.

**Example Output:**

> Between 14:05 and 14:12 UTC, `payment-api` experienced a 420% increase in database timeout errors. The incident affected three downstream services. The most probable cause is connection pool exhaustion. Recommended action is to increase pool capacity and investigate long-running queries.

### Component 11 — Alert Engine

**Purpose:** Notify stakeholders.

**Trigger Rule:** When a detection threshold is breached (e.g., the error-rate Z-Score or signature-frequency exceeds its configured limit in Component 4) and an incident is raised, the Alert Engine fires a **simulated webhook alert**. The webhook payload carries the incident summary, severity, affected services, and risk score.

**Supported Alert Types:**

- Dashboard Alert
- Webhook Alert
- Email Simulation
- Slack Simulation

**Features:**

- Deduplication
- Rate limiting
- Incident linking

### Component 12 — Risk Score Engine

**Purpose:** Provide overall platform health.

**Score Range:** 0 – 100

**Formula:**

```text
Risk Score = 100 − Error Penalty − Alert Penalty − Incident Penalty
```

**Ranges:**


| Score    | Status   |
| -------- | -------- |
| 90 – 100 | Healthy  |
| 70 – 89  | Warning  |
| 0 – 69   | Critical |


### Component 13 — Dashboard

**Overview Page**

- Risk Score
- Active Incidents
- Open Alerts
- Monitored Services

**Incident Center**

- Incident List
- Severity
- Status
- Root Cause
- Confidence

**Topology View**

- Service Graph
- Dependency Tree
- Blast Radius

**Trends Page**

- Error Rate Trend
- Incident Timeline
- Severity Distribution
- Health Trends

**AI Analysis Page**

- Classification
- Root Cause
- Remediation
- Executive Summary
- Runbook References

---

## 6. Database Design

**Tables:**

- `events`
- `anomalies`
- `incidents`
- `alerts`
- `runbooks`
- `metric_rollups`
- `service_topology`
- `llm_evaluations`

---

## 7. Python SDK

**Package Name:** `watchdog_client`

**Functions:**

- `create_event()`
- `create_batch()`
- `get_incidents()`
- `get_alerts()`
- `get_risk_score()`
- `get_health()`

**Requirements:**

- Type hints
- Documentation
- Examples
- Semantic versioning

---

## 8. API Requirements


| Domain     | Method | Endpoint          |
| ---------- | ------ | ----------------- |
| Health     | `GET`  | `/health`         |
| Metrics    | `GET`  | `/metrics`        |
| Events     | `POST` | `/events`         |
| Events     | `GET`  | `/events`         |
| Incidents  | `GET`  | `/incidents`      |
| Incidents  | `GET`  | `/incidents/{id}` |
| Alerts     | `GET`  | `/alerts`         |
| Risk Score | `GET`  | `/risk-score`     |
| Topology   | `GET`  | `/topology`       |


---

## 9. Security Requirements

- Environment variables for secrets
- No hardcoded API keys
- Input validation via Pydantic
- Request size limits
- Error sanitization

---

## 10. Testing Requirements

**Unit Tests:**

- Detection logic
- Correlation logic
- Risk score

**Integration Tests:**

- APIs
- Database

**AI Evaluation Tests** — measure:

- Classification accuracy
- Root cause accuracy
- Remediation quality
- Summary quality

Each Gemini response shall be scored against expected outputs. Results shall be stored in the `llm_evaluations` table.

**Target Coverage:** 90%+

---

## 11. CI/CD Requirements

**GitHub Actions Pipeline Stages:**

1. Ruff
2. Black
3. Mypy
4. Pytest

The pipeline must fail on quality violations.

---

## 12. Docker Requirements

**Containers:**

- Backend
- Frontend
- Database (SQLite volume)

**Commands:**

```bash
docker-compose up
docker-compose down
```

---

## 13. Repository Structure

```text
backend/
frontend/
sdk/
tests/
infra/
data/runbooks/
deck/
docs/
prompts.md
README.md
docker-compose.yml
```

---

## 14. Presentation Requirements

**Slides:**

1. Problem Statement
2. Architecture
3. Detection Engine
4. Correlation Engine
5. Agentic Workflow
6. RAG System
7. Dashboard
8. SDK
9. Testing & CI/CD
10. Demo Walkthrough
11. Future Enhancements

---

## 15. Acceptance Criteria

The project is considered complete when:

- [ ] Logs can be ingested successfully.
- [ ] Statistical anomalies are detected.
- [ ] Related anomalies are correlated into incidents.
- [ ] AI triage produces structured outputs.
- [ ] Runbooks influence AI responses.
- [ ] Alerts are generated.
- [ ] Dashboard visualizes health trends.
- [ ] Risk score is calculated.
- [ ] SDK functions correctly.
- [ ] CI pipeline passes.
- [ ] Docker deployment works.
- [ ] `prompts.md` contains complete prompt history.
- [ ] Presentation deck is available.
# Architecture Diagrams - AutoApply AI

**Source**: `docs/architecture/design/00-system-architecture-greenfield.md`  
**Generated**: 2026-06-19

> This file contains Mermaid diagrams extracted from the architecture document for easy preview and verification by the QA and Technical teams.

---

## Clean Architecture Layering

```mermaid
┌───────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                       │
│  (Next.js Web UI, FastAPI Routers, Playwright, DB Migrations) │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                  APPLICATION LAYER                       │  │
│  │    (LangGraph Agents, Connectors, Use Cases, Services)   │  │
│  │  ┌─────────────────────────────────────────────────────┐│  │
│  │  │                  DOMAIN LAYER                        ││  │
│  │  │       (User Entities, Profiles, Match Scores, IRs)  ││  │
│  │  └─────────────────────────────────────────────────────┘│  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                            ↑
              Dependencies point INWARD only
```

---

## System Context Diagram

```mermaid
C4Context
  title System Context Diagram - AutoApply AI

  Person(user, "Candidate", "An active job seeker managing their application funnel.")
  System(autoapply, "AutoApply AI Platform", "Automates discovery, scoring, tailoring, and form-submitting.")
  
  System_Ext(gemini, "Gemini LLM API", "Parses job descriptions, tailors resumes, and generates answers.")
  System_Ext(greenhouse, "Greenhouse ATS", "Target job board/portal hosted on Greenhouse.")
  System_Ext(lever, "Lever ATS", "Target job board/portal hosted on Lever.")

  Rel(user, autoapply, "Uses", "HTTPS")
  Rel(autoapply, gemini, "Calls", "HTTPS/gRPC")
  Rel(autoapply, greenhouse, "Interacts", "HTTPS/Playwright")
  Rel(autoapply, lever, "Interacts", "HTTPS/Playwright")
```

---

## Component Architecture Diagram

```mermaid
flowchart TB
  subgraph Frontend [Next.js Dashboard - Client & SSR]
    UI[React App - UI Components]
    Store[Context / State Store]
    Proxy[API Proxy Handler]
  end

  subgraph Backend [FastAPI Application Server]
    Router[FastAPI API Gate/Routers]
    Auth[Auth & Encryption Handler - Argon2 / AES-256-GCM]
    UseCases[Clean Architecture Use Cases]
    
    subgraph Agents [LangGraph Stateful Workflows]
      Orchestrator[LangGraph Controller]
      DiscoveryAgent[Job Discovery Agent]
      MatchingAgent[Matching & Scoring Engine]
      TailoringAgent[Resume/Cover Letter Tailoring Agent]
      AppAgent[Application Submitter Agent]
    end
  end

  subgraph Workers [Background Task Engine]
    Queue[Valkey Broker & Celery/ARQ Task Queue]
    PlaywrightAgent[Playwright Headless Browser Instance]
  end

  subgraph Storage [Persistent Datastores]
    Postgres[(PostgreSQL DB)]
    ValkeyCache[(Valkey Cache & Rates)]
    MinioStore[(MinIO S3 Bucket)]
  end

  UI --> Router
  Router --> Auth
  Router --> UseCases
  UseCases --> Orchestrator
  
  Orchestrator --> DiscoveryAgent & MatchingAgent & TailoringAgent & AppAgent
  Orchestrator --> Queue
  Queue --> PlaywrightAgent

  UseCases --> Postgres
  UseCases --> MinioStore
  UseCases --> ValkeyCache
  PlaywrightAgent --> greenhouse & lever
```

---

## Data Model / ER Diagram

```mermaid
erDiagram
  USER_PROFILE ||--|| CREDENTIALS : "authenticates_via"
  USER_PROFILE ||--o{ APPLICATION : "initiates"
  USER_PROFILE ||--o{ SKILL : "possesses"
  USER_PROFILE ||--o{ EXPERIENCE : "acquired"
  USER_PROFILE ||--o{ EDUCATION : "attended"
  
  JOB_POSTING ||--o{ APPLICATION : "receives"
  JOB_POSTING ||--|| MATCH_SCORE : "has_evaluation"

  APPLICATION ||--|| TAILORED_RESUME : "utilizes"
  APPLICATION ||--|| COVER_LETTER : "attaches"

  USER_PROFILE {
    uuid id PK
    string first_name
    string last_name
    string email
    string phone
    string master_resume_url
    string preferred_roles
    string preferred_locations
    integer target_salary
    timestamp created_at
  }

  CREDENTIALS {
    uuid id PK
    uuid user_id FK
    string password_hash "Argon2"
    string encrypted_api_keys "AES-256-GCM"
    timestamp updated_at
  }

  JOB_POSTING {
    uuid id PK
    string platform "Greenhouse / Lever"
    string external_job_id
    string title
    string company
    string location
    string url
    string description_text
    string raw_json
    timestamp discovered_at
  }

  MATCH_SCORE {
    uuid id PK
    uuid job_id FK
    integer overall_score "0-100"
    integer skill_match "0-100"
    integer experience_match "0-100"
    integer location_match "0-100"
    integer salary_match "0-100"
    string explanation_text
  }

  APPLICATION {
    uuid id PK
    uuid user_id FK
    uuid job_id FK
    string status "Backlog / Scheduled / Auto-Filled / Submitted / Failed"
    string mode "Manual / Assisted / Autonomous"
    timestamp date_applied
    string notes
  }

  TAILORED_RESUME {
    uuid id PK
    uuid application_id FK
    string tailored_pdf_url "MinIO S3"
    string keywords_used
    timestamp generated_at
  }
```

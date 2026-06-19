# AutoApply AI - Implementation Plan

**Project**: AutoApply AI | **Version**: 1.0 | **Created**: 2026-06-19
**Author**: ARCHITECT | **Status**: IN PROGRESS

---

## Dependency Graph

```mermaid
graph TD
  S10[1.0 Root tooling seed]
  S11[1.1 Backend skeleton]
  S12[1.2 Frontend skeleton]
  S13[1.3 Database and storage bootstrap]
  S14[1.4 Shell-to-service health wiring]
  S21[2.1 Authentication API and password hashing]
  S22[2.2 Profile management API]
  S23[2.3 Auth and profile UI]
  S24[2.4 Auth/profile integration test]
  S31[3.1 Discovery connector framework]
  S32[3.2 Job matching and deduplication engine]
  S33[3.3 Discovery and scoring dashboard]
  S34[3.4 Scheduled discovery integration test]
  S41[4.1 Resume tailoring and Gemini service]
  S42[4.2 Cover letter generation and artifact storage]
  S43[4.3 Tailoring UI and download flow]
  S44[4.4 Tailoring integration test]
  S51[5.1 Application execution browser core]
  S52[5.2 Question answering and application modes]
  S53[5.3 Tracking and reporting UI]
  S54[5.4 End-to-end application flow test]
  S61[6.1 Observability and deployment hardening]

  S10 --> S11
  S10 --> S12
  S10 --> S13
  S11 --> S14
  S12 --> S14
  S13 --> S14
  S11 --> S21
  S13 --> S21
  S21 --> S22
  S22 --> S23
  S12 --> S23
  S21 --> S24
  S22 --> S24
  S23 --> S24
  S11 --> S31
  S13 --> S31
  S31 --> S32
  S22 --> S32
  S12 --> S33
  S32 --> S33
  S31 --> S34
  S32 --> S34
  S33 --> S34
  S32 --> S41
  S22 --> S41
  S13 --> S41
  S41 --> S42
  S13 --> S42
  S12 --> S43
  S41 --> S43
  S42 --> S43
  S41 --> S44
  S42 --> S44
  S43 --> S44
  S41 --> S51
  S42 --> S51
  S13 --> S51
  S51 --> S52
  S22 --> S52
  S12 --> S53
  S51 --> S53
  S52 --> S53
  S51 --> S54
  S52 --> S54
  S53 --> S54
  S11 --> S61
  S12 --> S61
  S13 --> S61
```

---

## Wave Summary

| Wave | Stories | Notes |
|------|---------|-------|
| 1 | 1.0 | Root tooling seed |
| 2 | 1.1 | Backend skeleton |
| 3 | 1.2 | Frontend skeleton |
| 4 | 1.3 | Database and storage bootstrap |
| 5 | 1.4 | Shell-to-service health wiring |
| 6 | 2.1 | Authentication API and password hashing |
| 7 | 2.2 | Profile management API |
| 8 | 2.3 | Auth and profile UI |
| 9 | 2.4 | Auth/profile integration test |
| 10 | 3.1 | Discovery connector framework |
| 11 | 3.2 | Job matching and deduplication engine |
| 12 | 3.3 | Discovery and scoring dashboard |
| 13 | 3.4 | Scheduled discovery integration test |
| 14 | 4.1 | Resume tailoring and Gemini service |
| 15 | 4.2 | Cover letter generation and artifact storage |
| 16 | 4.3 | Tailoring UI and download flow |
| 17 | 4.4 | Tailoring integration test |
| 18 | 5.1 | Application execution browser core |
| 19 | 5.2 | Question answering and application modes |
| 20 | 5.3 | Tracking and reporting UI |
| 21 | 5.4 | End-to-end application flow test |
| 22 | 6.1 | Observability and deployment hardening |

---

## Overview

**Story Count**: 22
**Build Cycles**: Not used
**UI/UX Design**: Not included in this planning pass
**Team Size Hint**: 1

---

## Epic Breakdown

- Epic 1: Foundation - bootstrap the stack, connect frontend to backend, and verify the walking skeleton.
- Epic 2: Identity & Profile - deliver authentication, profile management, and first user-facing account screens.
- Epic 3: Discovery & Matching - ingest jobs from ATS connectors, deduplicate, score, and expose the discovery dashboard.
- Epic 4: Tailoring - generate tailored resumes and cover letters, then let users review and download them.
- Epic 5: Application Execution & Tracking - execute browser applications, handle recruiter questions, and show tracking/reporting.
- Epic 6: Operations & Hardening - observability, smoke checks, and deployment hardening.

---

## EPIC 1: FOUNDATION

**Owner**: ARCHITECT | **Goal**: Create a walking skeleton that proves the full stack can boot, connect, and serve a health signal.

### Story 1.0: Root tooling seed
Create the root project scaffolding and shared tooling files needed by the frontend, backend, and deployment layers.

### Story 1.1: Backend skeleton
Create the FastAPI application shell, health endpoint, and app bootstrap wiring.

### Story 1.2: Frontend skeleton
Create the Next.js application shell, root layout, and initial dashboard frame.

### Story 1.3: Database and storage bootstrap
Create PostgreSQL session wiring, MinIO adapter scaffolding, and migration entry points.

### Story 1.4: Shell-to-service health wiring
Wire the frontend to read backend health and show connection status in the UI.

---

## EPIC 2: IDENTITY & PROFILE

**Owner**: ARCHITECT | **Goal**: Enable secure user access and candidate profile management.

### Story 2.1: Authentication API and password hashing
Implement registration, login, and Argon2 password hashing.

### Story 2.2: Profile management API
Implement profile CRUD, resume metadata, and preference storage.

### Story 2.3: Auth and profile UI
Implement login and profile screens and wire them to the API contracts.

### Story 2.4: Auth/profile integration test
Verify the end-to-end account and profile flow across backend and frontend.

---

## EPIC 3: DISCOVERY & MATCHING

**Owner**: ARCHITECT | **Goal**: Discover jobs, score them, and present ranked opportunities.

### Story 3.1: Discovery connector framework
Create the ATS connector framework and initial Greenhouse/Lever discovery paths.

### Story 3.2: Job matching and deduplication engine
Implement job scoring, weighting, and duplicate detection logic.

### Story 3.3: Discovery and scoring dashboard
Build the jobs dashboard with match-score presentation and filtering.

### Story 3.4: Scheduled discovery integration test
Verify scheduled discovery, storage, and dashboard data flow.

---

## EPIC 4: TAILORING

**Owner**: ARCHITECT | **Goal**: Generate tailored resumes and cover letters and make them downloadable.

### Story 4.1: Resume tailoring and Gemini service
Implement the tailoring service and Gemini integration.

### Story 4.2: Cover letter generation and artifact storage
Persist tailored cover letters and generated artifacts in MinIO.

### Story 4.3: Tailoring UI and download flow
Build the tailoring experience and download actions in the dashboard.

### Story 4.4: Tailoring integration test
Verify the full tailoring pipeline from input profile to downloadable artifacts.

---

## EPIC 5: APPLICATION EXECUTION & TRACKING

**Owner**: ARCHITECT | **Goal**: Execute applications, answer recruiter questions, and track outcomes.

### Story 5.1: Application execution browser core
Implement the browser automation core for application submission.

### Story 5.2: Question answering and application modes
Implement application modes and recruiter question answering flows.

### Story 5.3: Tracking and reporting UI
Build the application tracking and reporting experience.

### Story 5.4: End-to-end application flow test
Verify discovery-to-submission-to-tracking through one end-to-end flow.

---

## EPIC 6: OPERATIONS & HARDENING

**Owner**: ARCHITECT | **Goal**: Add observability and deployment hardening for a production-ready MVP.

### Story 6.1: Observability and deployment hardening
Implement structured logging, metrics, smoke checks, and deployment hardening.

---

## QA Manual Testing Groups

- Foundation smoke: app boots, backend health responds, frontend sees backend connection.
- Identity & Profile: registration, login, profile save, resume upload metadata.
- Discovery & Matching: connector discovery, deduplication, score filtering, dashboard rendering.
- Tailoring: Gemini output generation, artifact storage, download verification.
- Application Execution & Tracking: application submission modes, recruiter answers, tracking entries.
- Operations: logging, metrics, smoke tests, container startup validation.

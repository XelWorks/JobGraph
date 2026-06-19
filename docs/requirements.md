# Requirements - AutoApply AI

**Date**: 2026-06-19  
**Author**: ANALYST_PM_GREENFIELD  
**Status**: Approved  
**Version**: 1.0

---

## Project Overview

### Vision
AutoApply AI is an AI-powered job application platform that automatically discovers, evaluates, customizes, and submits job applications across multiple job portals and Applicant Tracking Systems (ATS). By acting as a personal AI recruiter, the platform continuously searches for relevant opportunities, tailors resume/cover letters, and executes application submissions with minimal user intervention, while keeping the user's data secure and self-hosted.

### Problem Statement
Job seekers spend 2-4 hours daily searching multiple platforms, reading repetitive descriptions, modifying resumes, filling out application forms, and manually tracking their pipeline. AutoApply AI reduces manual job application effort by over 90% while maintaining or improving application quality through precise matching and tailoring.

### Target Users
- **Primary**: Freshers, Software Engineers, AI/ML Engineers, Data Scientists, and DevOps Engineers.
- **Secondary**: Product Managers, UX/UI Designers, and Marketing Professionals.

### Business Value
- Drastically reduces time-to-apply (from hours to minutes per day).
- Increases the volume of high-quality, highly aligned applications.
- Improves interview conversion rates via automated resume tailoring.
- Establishes a privacy-first, self-hosted open-source standard for job application automation.

---

## Project Type

| Attribute | Value |
|-----------|-------|
| Type | Greenfield - New System |
| Quality Level | Production-Ready MVP (No shortcuts, robust error handling) |
| Timeline | 6 weeks |
| Hard Deadline | Flexible / Goal-oriented |

---

## Success Criteria (MUST HAVE)

| ID | Criterion | Measurement | Target |
|----|-----------|-------------|--------|
| SC-1 | Reduce User Effort | Average daily time spent by user on applications | < 15 minutes per day |
| SC-2 | Tailored Alignments | Average matching score of submitted applications | Match score ≥ 80% (according to Matching Engine) |
| SC-3 | System Latency | API response time for core dashboard pages (95th percentile) | < 200ms |
| SC-4 | Application Rate | Number of automated submissions processed | Up to 15 successful applications per day per user |
| SC-5 | High-Quality Match | Percentage of discovered jobs filtered out of queue | > 60% low-quality/unaligned jobs filtered automatically |

---

## Failure Criteria (UNACCEPTABLE)

| ID | Criterion | Description |
|----|-----------|-------------|
| FC-1 | False Submissions | Submitting applications with incorrect/corrupted resumes, wrong applicant names, or broken fields. |
| FC-2 | Platform Rate-limiting / Bans | Triggering automated bot-detection bans on ATS sites due to lacks in browser randomization or excessively rapid submissions. |
| FC-3 | Plaintext Credentials | Storing API keys, portals' passwords, or sensitive applicant data in plaintext. |
| FC-4 | Application Black Hole | Failing to track submitted applications or losing matching logs, preventing users from seeing where they applied. |

---

## Technical Constraints

| Constraint | Value | Rationale |
|------------|-------|-----------|
| Frontend Framework | React JS | Modern, responsive, and dynamic client-side SPA Dashboard. |
| Backend Framework | FastAPI | Async Python framework optimized for high-performance and seamless AI integration. |
| Database | PostgreSQL | Relational database for structured, ACID-compliant user profiles and application tracking. |
| Cache & Message Broker | Valkey | High-performance open-source in-memory data store for queues, rate-limits, and session caching. |
| Object Storage | MinIO | High-performance, self-hosted, S3-compatible object storage for resumes and cover letters. |
| Agent Orchestration | LangGraph | Multi-agent orchestration framework for executing complex, sequential, or stateful agent workflows. |
| LLM Provider | Gemini (Google Vertex AI / Gemini API) | Primary model for resume tailoring, cover letter generation, and question answering. |
| Deployment | Docker Compose | Mandatory single-command orchestration (`docker compose up -d`) supporting local, VPS, and cloud environments. |

---

## Quality Gates

| Gate | Target | Required |
|------|--------|----------|
| Unit Test Coverage | ≥85% | Yes |
| Integration Tests | 100% pass | Yes |
| Critical Bugs | 0 | Yes |
| Security Scan | Pass (No plaintext secrets, safe password hashing with Argon2) | Yes |
| Code Review | Approved by AIRE_REVIEWER | Yes |
| Docker Build | Compiles cleanly with zero warning flags | Yes |

---

## Design References

**Location**: `SPEC/references/`

| File | Type | Description | Used In |
|------|------|-------------|---------|
| `prd.md` | PRD | Core Product Requirements Document containing initial specifications. | All Epics |

---

## Functional Requirements

### Feature: User Authentication and Profile Management
**Priority**: Must Have

**User Story**: As a job seeker, I want to securely register and log in to configure my personal profile, skills, salary expectations, preferred locations, and upload my master resume so that the system has accurate candidate context.

**Acceptance Criteria**:
- Users must be able to sign up and authenticate securely using Argon2-hashed passwords.
- Users must be able to configure their profile including: personal details, skills, work experience, education, salary expectations, preferred locations, and social links (GitHub, LinkedIn).
- Users can upload a master resume in PDF/Docx format, which is stored securely in MinIO.
- API keys and browser configurations must be encrypted at rest.

### Feature: Job Discovery Agent (F1 & FR-003)
**Priority**: Must Have

**User Story**: As an automated job seeker, I want the system to continuously discover jobs from ATS platforms like Greenhouse and Lever based on my profile targets.

**Acceptance Criteria**:
- System discovers job listings automatically via Greenhouse and Lever connectors.
- Supports scheduled background discovery tasks.
- Stores full job descriptions in PostgreSQL.
- Deduplicates job listings using unique platform identifiers (e.g., Job Board ID + Job ID).

### Feature: Job Matching & Scoring Engine (F2 & FR-004)
**Priority**: Must Have

**User Story**: As a candidate, I want the system to score every discovered job against my profile so that I only apply to roles that are highly aligned.

**Acceptance Criteria**:
- Scores jobs from 0-100 based on: Skill Match (40%), Experience Match (30%), Location Match (15%), and Salary Match (15%).
- Only jobs exceeding a user-configurable matching threshold (default: 70) proceed to the application pipeline.

### Feature: Resume Tailoring & Cover Letter Generation (F3, F4, FR-005, FR-006)
**Priority**: Must Have

**User Story**: As an applicant, I want the system to generate a customized, ATS-optimized resume and cover letter tailored to each job description using Gemini.

**Acceptance Criteria**:
- Analyzes job description, extracts key requirements, and generates a tailored PDF resume.
- Generates a customized, role-specific cover letter.
- Outputs must be stored securely in MinIO and mapped to the specific application tracking record.

### Feature: Browser Application Execution Agent (F5, F6, FR-007, FR-008)
**Priority**: Must Have

**User Story**: As an automated system, I want the browser agent to open application pages, autofill text fields, handle dropdown selections, answer custom recruiter questions, and upload documents.

**Acceptance Criteria**:
- Browser agent interacts with Greenhouse and Lever ATS forms.
- Support 3 distinct application modes:
  - **Manual**: System compiles materials; user manually fills/submits.
  - **Assisted**: Form is auto-filled; user reviews and clicks submit.
  - **Autonomous**: Form is filled and submitted entirely automatically.
- Handles common custom recruiter questions (e.g., "Years of Python experience?") dynamically using the candidate's profile context.

### Feature: Application Tracking & Reporting (F7, F8, FR-009, FR-010)
**Priority**: Must Have

**User Story**: As a user, I want to track every application's status and receive daily/weekly summaries of submissions and interview invites.

**Acceptance Criteria**:
- Stores: Company, Role, Source Platform, Date Applied, Resume/Cover Letter version used, Application Status, and Notes.
- Daily summaries generated compiling: discovered jobs, matched jobs, submitted applications, and system errors.

---

## Non-Functional Requirements

| Category | Requirement | Target |
|----------|-------------|--------|
| Performance | Web response time | < 200ms (p95) |
| Robustness | Error Handling | Browser automation recovers from stale elements, dynamic page shifts, or connection drops with at least 3 retry attempts. |
| Security | Credentials & Data | Password hashing with Argon2; API keys and portal passwords encrypted with AES-256-GCM. |
| Local Portability| Self-hosted Deployment| Single command deploy via `docker compose up -d` with pre-configured health checks. |

---

## Explicit Scope

### IN Scope ✅
- Multi-Agent Orchestration using LangGraph.
- Integration with Google Gemini LLM API.
- Fully-featured React JS Dashboard UI.
- FastAPI backend communicating with PostgreSQL, Valkey, and MinIO.
- Connectors for Greenhouse and Lever ATS platforms.
- Automated resume tailoring and custom cover letter generation (outputs stored in MinIO).
- 3 execution modes: Manual, Assisted, Autonomous.
- Automated Question Answering agent pulling from candidate profile.
- Docker Compose deployment pattern.

### OUT of Scope ❌
- Direct native integrations with LinkedIn Easy Apply, Naukri, Foundit, Indeed, or Workday in v0.1 MVP.
- Mobile application (iOS/Android) version of the dashboard.
- Advanced community connector registry or plugin marketplace (planned for v1.0).
- Enterprise multi-tenant SaaS capabilities (v0.1 is local/single-user self-hosted).

### Future Considerations (Not This Epic/Release)
- Ashby ATS connector integration (planned for v0.2).
- Multi-LLM provider support (Ollama, local models) (v0.2).
- Deep behavioral/recruiter simulator analytics (v0.3).

---

## Assumptions

| Assumption | Impact if Wrong |
|------------|-----------------|
| Greenhouse/Lever ATS form structures remain stable. | Browser automation fills might fail, requiring connector updates. |
| Gemini API remains highly available with sufficient rate limits. | Resume/cover letter customization will fail or lag. |
| Local machine running Docker has minimum 4GB RAM available. | Performance degradation or container crashes. |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| ATS platforms employing aggressive Cloudflare/bot mitigation. | Medium | High | Use stealth-configured Puppeteer/Playwright browser frameworks, randomize interaction delays, and utilize Assisted mode when autonomous is blocked. |
| Gemini API keys expiring or running out of balance. | Medium | Medium | Implement robust credential alerts, error state management in UI, and fail gracefully to a backlog queue. |

---

## Timeline

| Milestone | Date | Deliverables |
|-----------|------|--------------|
| Requirements Complete | 2026-06-19 | This document (`docs/requirements.md`) |
| Architecture Complete | 2026-06-21 | System architecture design & patterns |
| Implementation Complete | 2026-07-15 | High-test-coverage React JS & FastAPI code |
| Unit test Validation | 2026-07-20 | Coverage reports showing ≥85% coverage |
| Release | 2026-07-31 | Docker-composed fully stable local release |

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| Stakeholder | User | 2026-06-19 | Approved |
| Technical Lead | AIRE_ANALYST_PM_GREENFIELD | 2026-06-19 | Approved |

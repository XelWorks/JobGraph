# Roadmap

## Overview

JobGraph is evolving from MVP to production-ready platform over a 12-month cycle.

**Vision**: The industry standard open-source platform for AI-powered job application automation.

## v0.1 MVP (Q3 2026) - Current

**Status**: 🟡 In Development

**Scope**: Proof of concept for solo job seekers

**Target Release**: June-July 2026

### Features

- ✅ Job discovery connectors
  - Greenhouse API integration
  - Lever API integration
  - Basic job search and filtering

- ✅ Resume & Cover Letter Tailoring
  - Google Gemini integration
  - Job description analysis
  - Automated resume customization
  - Cover letter generation

- ✅ Application Automation
  - Browser-based form filling (Playwright)
  - Application submission
  - Error recovery and retries

- ✅ Dashboard
  - Application history tracking
  - Profile management
  - Settings configuration

- ✅ Local Deployment
  - Docker Compose setup
  - Single-machine deployment
  - Zero external dependencies (BYOK model)

### Success Metrics

- Latency: <200ms p95
- Match accuracy: ≥80% relevance
- Application success rate: >95%
- Docker deployment: <5 minutes
- Zero hardcoded credentials

### Non-Goals

- Mobile apps
- Multi-user SaaS
- Advanced analytics
- Plugin marketplace
- Enterprise features

---

## v0.2 Multi-LLM Support (Q4 2026)

**Status**: 🟡 Planned

**Scope**: Flexibility for power users

### Features

- [ ] LLM Provider Abstraction
  - Support OpenAI GPT-4/3.5-turbo
  - Support Anthropic Claude
  - Provider-agnostic LangGraph agents

- [ ] Enhanced Matching
  - ML-based job relevance scoring
  - Skill gap analysis
  - Salary alignment checking
  - Custom filter rules

- [ ] Artifact Management
  - Save tailored resumes
  - Version control (v1, v2, v3)
  - Cover letter templates
  - Application feedback storage

- [ ] Configuration UI
  - LLM provider selection
  - Custom prompt templates
  - Matching algorithm tuning

### Architecture Changes

- Move LLM logic to LangGraph Service
- Abstract provider interfaces
- Add artifact versioning schema

### Developer APIs

```python
# Switch LLM providers without code changes
config.llm_provider = "openai"
config.llm_model = "gpt-4-turbo"
# Agents auto-configured

# Custom matching rules
match_engine.add_rule("salary_min", 120000)
match_engine.add_rule("location", "San Francisco, CA")
```

---

## v0.3 Dashboard & Analytics (Q1 2027)

**Status**: 🟡 Planned

**Scope**: Visibility and insights

### Features

- [ ] Enhanced Dashboard
  - Application timeline (submitted, rejected, interviewing)
  - Match score distribution
  - Success rate by company/industry
  - Application status tracking

- [ ] Analytics
  - Applications per day trend
  - Response rate by ATS
  - Average time-to-response
  - Industry/role breakdown

- [ ] Notifications
  - Email alerts on application updates
  - Match score thresholds
  - Job discovery alerts

- [ ] Advanced Filtering
  - Saved searches
  - Smart filters (regex, ML)
  - Application workflow customization

### Data Model Changes

- Add analytics schema
- Application status tracking table
- Notification preferences table

---

## v1.0 Production Release (Q2 2027)

**Status**: 🟡 Planned

**Scope**: Stable, documented, enterprise-ready

### Features

- [ ] Stable API Versioning
  - /api/v1 frozen (no breaking changes)
  - Documentation guarantees
  - Deprecation policy

- [ ] Multi-Connector Support
  - 10+ ATS platforms
  - Workable, iCIMS, Lever, Greenhouse, etc.
  - Connector SDK maturity

- [ ] Role-Based Access Control
  - Multi-user support
  - Team collaboration
  - Permission management

- [ ] Audit Logging
  - Compliance ready
  - Application audit trail
  - User activity logging
  - Data export for compliance

- [ ] Kubernetes Support
  - Helm charts
  - Multi-replica deployments
  - Persistent volume claims

### Quality Guarantees

- 100% integration test pass rate
- ≥85% code coverage
- Zero critical security issues
- API response time SLA: <200ms p99

### Documentation

- API reference (auto-generated OpenAPI)
- Deployment guides (Docker, K8s, VPS)
- Troubleshooting guides
- Video tutorials

---

## v1.1+ Enhancement Releases (2027+)

**Status**: 🔵 Proposed (community-driven)

### Potential Features

- [ ] Interview Prep Integration
  - Question generation from job descriptions
  - Mock interview Q&A
  - Performance scoring

- [ ] Salary Negotiation Assistant
  - Market-rate estimation
  - Negotiation tactics
  - Offer analysis

- [ ] Career Planning Tools
  - Role progression mapping
  - Skill gap analysis
  - Learning recommendations

- [ ] Resume Scoring
  - ATS optimization scoring
  - Grammar and clarity feedback
  - Keyword matching

- [ ] Community Connectors
  - 50+ community-built ATS integrations
  - Connector marketplace / registry
  - Rating and reviews

### Revenue Opportunities (Without Closing Source)

- Professional support packages
- Managed cloud hosting (jobgraph.cloud)
- Advanced connector development
- Integration consulting

---

## Technology Evolution

### v0.1 → v1.0 Stack Evolution

| Component | v0.1 | v1.0 |
|-----------|------|------|
| Frontend | Next.js 14 | Next.js 15+ |
| Backend | FastAPI 0.110 | FastAPI 0.120+ |
| Orchestration | LangGraph 0.0.x | LangGraph 1.0+ |
| Database | PostgreSQL 16 | PostgreSQL 16+ (partitioning) |
| Cache | Valkey 7 | Valkey 8+ (clustering) |
| Storage | MinIO (S3) | MinIO + replicas |
| Deployment | Docker Compose | Docker Compose + K8s |

### API Stability

**v0.1-0.x**: Rapid iteration, breaking changes allowed

**v1.0+**: API stability guaranteed
- Breaking changes require new API version (/api/v2)
- At least 6 months deprecation notice
- Migration guide provided

---

## Community Contribution Roadmap

We welcome community contributions to:

1. **New Connectors** (Any ATS)
   - Implement BaseConnector interface
   - 85%+ test coverage
   - Include documentation
   - See docs/CONNECTOR_SDK.md

2. **Performance Improvements**
   - Database query optimization
   - LLM prompt tuning
   - Frontend rendering optimization

3. **Documentation**
   - Deployment guides
   - Video tutorials
   - Blog posts / case studies

4. **Community Support**
   - Help on GitHub Issues
   - Moderator on Discord
   - Code review of PRs

---

## Dependabot & Security

### Continuous Security

- Dependabot enabled (auto-updates)
- Weekly security scans
- Vulnerability disclosure policy
- 48-hour patch SLA for critical issues

### Supported Versions

| Version | Status | Support Until |
|---------|--------|---------------|
| 0.1.x | 🟢 Active | Until 0.2 released |
| 0.2.x | 🟡 Planned | 6mo after 1.0 |
| 1.0.x | 🔵 Future | Latest + 2 prior |
| 1.1.x | 🔵 Future | Latest + 2 prior |

---

## Metrics & Goals

### User Growth

- End of 2026: 1k+ active users
- End of 2027: 10k+ active users
- End of 2028: 100k+ active users

### Community

- End of 2026: 500+ GitHub stars
- End of 2027: 5k+ GitHub stars
- End of 2028: 20k+ GitHub stars

### Enterprise Adoption

- End of 2027: 20+ enterprise customers
- End of 2028: 100+ enterprise customers

### Sustainability

- End of 2027: $100k+ annual revenue (support + services)
- End of 2028: $500k+ annual revenue

---

## How to Get Involved

1. **Star the Repository**: Show support on GitHub
2. **Test v0.1**: Deploy locally and provide feedback
3. **Contribute**: Submit PRs for connectors, features, docs
4. **Sponsor**: Consider sponsoring maintainers (coming soon)
5. **Share**: Tell others about JobGraph

## Feedback

We want to hear from you!

- **Feature Ideas**: Open GitHub Issues with `[FEATURE]` label
- **Bug Reports**: Open GitHub Issues with `[BUG]` label
- **Questions**: Start a GitHub Discussion
- **Connectors**: Request in Issues with `[CONNECTOR]` label

---

**Version**: 1.0  
**Last Updated**: 2026-06-19  
**Status**: Community feedback welcome

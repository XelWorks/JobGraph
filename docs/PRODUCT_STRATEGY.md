# Product Strategy & Roadmap

## Objective

Define JobGraph's business model, feature roadmap, and open-source positioning for long-term sustainability.

## 1. Core Principle: Open Source Forever

**Commitment**: The core JobGraph platform will remain open source under Apache 2.0 indefinitely.

This includes:
- ✅ Job discovery agents (scrapers, API connectors)
- ✅ Matching engine (ranking, filtering)
- ✅ Tailoring service (resume/cover letter generation)
- ✅ Application execution (form filling, submission)
- ✅ Connector SDK and examples
- ✅ All UI components (dashboard, workflow builder)
- ✅ Documentation and guides

## 2. Version Roadmap

### v0.1 MVP (Current)
**Release Target**: Q3 2026  
**Scope**: Proof of concept for solo job seekers

Features:
- Greenhouse/Lever connectors (job discovery via API)
- Profile management (skills, experience, education)
- Basic matching engine (keyword filtering)
- Google Gemini integration (resume/cover letter tailoring)
- Browser automation (Playwright form-filling)
- Docker Compose single-machine deployment

Success Metrics:
- Can deploy locally and submit 5+ applications/day
- Resume tailoring quality ≥80%
- API latency <200ms p95

**Open Source**: Fully open (Apache 2.0)

### v0.2 Multi-LLM Support
**Release Target**: Q4 2026  
**Scope**: Flexibility for power users

Features:
- Support OpenAI GPT, Anthropic Claude (in addition to Gemini)
- LLM provider abstraction layer
- Custom prompt templates
- Enhanced matching (job description analysis)
- Saved application artifacts (tailored resumes, cover letters)

**Open Source**: Fully open (Apache 2.0)

### v0.3 Dashboard & Analytics
**Release Target**: Q1 2027  
**Scope**: Visibility and insights

Features:
- Application history dashboard (submitted, rejected, interviewing)
- Match score trends and insights
- Application success rate by ATS
- Custom filters and saved searches
- Email notifications
- Basic analytics (applications/day, success rate)

**Open Source**: Fully open (Apache 2.0)

### v1.0 Production Release
**Release Target**: Q2 2027  
**Scope**: Stable, documented, enterprise-ready

Features:
- Stable API versioning (/api/v1)
- Comprehensive documentation
- Multi-connector support (10+ ATS platforms)
- Advanced matching (scoring models, filtering rules)
- Role-based access control (multi-user)
- Audit logging and compliance features
- Kubernetes support

**Open Source**: Fully open (Apache 2.0)  
**Stability**: API/data contracts guaranteed

### v1.1+ Enhancements
**Release Target**: 2027+  
**Scope**: Community-driven improvements

Potential additions (community-sourced):
- Interview prep integration
- Salary negotiation assistant
- Career planning tools
- Resume review scoring
- Additional ATS connectors (community-built)

**Open Source**: Fully open (Apache 2.0)

## 3. What Stays Open-Source vs. Commercial

### ✅ Open Source Core (Apache 2.0)

- Job discovery agents
- Matching and filtering engine
- LLM orchestration (LangGraph)
- Browser automation and form-filling
- Resume/cover letter generation
- Dashboard and UI components
- Connector SDK framework
- All integrations (Greenhouse, Lever, etc.)
- All documentation
- All infrastructure code (Docker, Kubernetes)

**Philosophy**: If it adds value to individual job seekers, it's open source.

### 🟡 Optional Future Commercial Offerings (NOT Closed-Source)

These services would complement open source, not replace it:

#### 1. Managed Cloud Platform (jobgraph.cloud)
- Hosted JobGraph instance (no self-hosting needed)
- Pre-configured connectors and defaults
- Optional: Automated backups, version management
- **Core**: Runs same open-source code
- **Differentiation**: Hosting, convenience, optional SLA support

#### 2. Enterprise Support & Services
- Priority security patches (24-hour SLA)
- Custom connector development
- Integration consulting
- Training and certification
- **Model**: Subscriptions for support, not for code

#### 3. Advanced Connectors (Premium)
- Connectors for closed-source ATS systems (iCIMS, Workday, Oracle)
- Requires vendor API access agreements
- Can be closed-source (specific vendor logic)
- **Core**: Connector SDK remains open
- **Differentiation**: Supported, updated, guaranteed quality

#### 4. Analytics & Insights (Optional Service)
- Aggregated job market analytics
- Career benchmarking (anonymized)
- Salary insights by role/location
- **Model**: SaaS subscription
- **Core**: Open-source data collection in JobGraph

### ❌ NEVER Close-Source

These will remain open-source forever:

- Core platform code (agents, matching, tailoring)
- Connector SDK and framework
- API and data models
- Public documentation
- Infrastructure templates

**Rationale**: Doing so would violate user trust and the Apache 2.0 license philosophy.

## 4. Sustainability Model

### Revenue Streams (Post-v1.0)

1. **Support & Services** (60% potential)
   - Enterprise support contracts
   - Custom connector development
   - Integration consulting
   - Training & certification

2. **Managed Hosting** (25% potential)
   - jobgraph.cloud subscription
   - Multi-instance management
   - Backup and disaster recovery

3. **Premium Connectors** (10% potential)
   - Advanced ATS integrations
   - Vendor-specific features
   - Supported connector development

4. **Sponsorships** (5% potential)
   - LLM provider partnerships
   - Job board integrations
   - Company training programs

### Cost Structure

**Fixed Costs**:
- Infrastructure (API servers, documentation hosting)
- Security updates and maintenance
- Community management

**Variable Costs**:
- Support staff (when revenue allows)
- Contractor connectors (vendor-specific)
- Cloud hosting (if managed offering launched)

## 5. User Expectations

### What Users Get (Always Free)

- Open-source code
- Docker Compose deployment
- All base connectors (Greenhouse, Lever, etc.)
- Community support via GitHub/Discord
- Full feature set for local deployment

### What Users Can Pay For (Optional)

- Managed hosting (convenience)
- Expert support (faster resolution)
- Custom connectors (vendor-specific)
- Consulting services (integration help)

### What Users Can NOT Do

- Cannot use "JobGraph" branding for their fork
- Cannot redistribute official Docker images
- Cannot claim trademark rights

## 6. Metrics to Track

### For v0.1 Success

- Downloads: 1k+ GitHub clones
- Active users: 100+ monthly active
- Applications generated: 5k+ total
- Avg latency: <200ms p95
- Test coverage: 85%+

### For v1.0 Success

- Stars: 5k+ GitHub stars
- Forks: 500+ community forks
- Contributors: 30+ active
- ATS support: 10+ connectors
- Deployment count: 1k+ known instances

### For Sustainability

- Annual recurring revenue: $100k+ (via support + hosting)
- Support ticket resolution: <24 hours
- Security update turnaround: <48 hours
- Community contributor growth: 20+ new/year

## 7. Community & Ecosystem

### Connector Ecosystem

**Phase 1 (v0.1-v1.0)**: Core connectors built-in
- Greenhouse
- Lever
- Workable

**Phase 2 (v1.0+)**: SDK-driven community connectors
- Users can build and share connectors
- Connector registry at `registry.jobgraph.dev`
- Package management: `jobgraph connector install workday`

**Phase 3 (v2.0+)**: Partner connectors
- Vendor partnerships for advanced integrations
- Maintained by vendors or JobGraph team
- Can be commercial offerings

### Documentation Strategy

**Current**:
- Architecture documentation
- Deployment guides
- Connector SDK guide
- Contributing guidelines

**Future**:
- Connector development tutorial series
- Video walkthroughs (deployment, customization)
- API reference (auto-generated from OpenAPI)
- Community blog with case studies

### Events & Community

- Virtual meetups (quarterly)
- Newsletter (monthly updates)
- Discord community
- Sponsor local tech meetups
- Conference talks and workshops

## 8. Trademark & Brand Evolution

### Current
- JobGraph (working title)
- Open-source platform (Apache 2.0)

### Future Branding
- JobGraph® (trademark for official distribution)
- JobGraph CLI (command-line tool)
- JobGraph Cloud (managed hosting)
- JobGraph Pro (future premium tier, if applicable)

### No Trademark Dilution
- Users fork → Must rename to avoid confusion
- Community connectors → Use own brand
- Derivatives → Make authorship clear

## 9. Long-Term Vision (3-5 Years)

### Position

JobGraph becomes the industry standard open-source platform for AI-powered job application automation.

### Adoption

1. **Individual Users**: 10k+ monthly active users (self-hosted)
2. **Organizations**: 100+ companies using internally
3. **Enterprises**: Support contracts with 20+ enterprises
4. **Ecosystem**: 50+ community connectors

### Sustainability

- $500k+ annual revenue (support, hosting, premium features)
- 5-10 full-time team members
- Funded via support + optional commercial services
- Core platform remains 100% open-source

### Technology Leadership

- Industry standard for job automation
- Reference architecture for multi-agent systems
- Case studies in academic AI literature
- Speaking engagements at major conferences

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-19 | Apache 2.0 License | Industry standard, business-friendly, patent protection |
| 2026-06-19 | Core platform always OSS | User trust, competitive advantage |
| 2026-06-19 | Support-first business model | Aligns with open-source principles |
| 2026-06-19 | Managed hosting optional | Not forced, users choose hosting model |
| 2026-06-19 | Connector SDK public | Community extensibility |

---

**Document Version**: 1.0  
**Last Updated**: 2026-06-19  
**Owner**: Product Team  
**Status**: Approved

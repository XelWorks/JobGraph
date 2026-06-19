# Brand & Repository Strategy

## Objective

Protect the JobGraph® brand while keeping the core platform open source. This document defines the repository structure, brand guidelines, and trademark strategy.

## 1. Organization Structure

### Primary Repository

- **GitHub**: `github.com/jobgraph/jobgraph`
- **Docker Hub**: `jobgraph/jobgraph`
- **Description**: Core platform with API, agents, and base connectors

### Secondary Repositories (Planned)

```
jobgraph/jobgraph-ui              # Next.js dashboard (may be extracted)
jobgraph/jobgraph-connectors-sdk  # ATS connector framework & examples
jobgraph/jobgraph-docs            # Centralized documentation
jobgraph/jobgraph-examples        # Deployment examples & tutorials
jobgraph/jobgraph-helm            # Kubernetes Helm charts
```

**Rationale**: Separating repositories allows:
- Independent connector SDK versioning
- User forks can focus on specific concerns
- Clear separation of concerns
- Easier maintenance and review

## 2. Brand Registration Strategy

### Immediate (Before Public Release)

- [x] GitHub Organization: `jobgraph`
- [ ] Docker Hub Organization: `jobgraph`
- [ ] NPM Scoped Package: `@jobgraph/*`
- [ ] PyPI Namespace: `jobgraph-*`

### Recommended (Month 1)

- [ ] Discord Community: `discord.gg/jobgraph`
- [ ] Twitter/X Handle: `@jobgraph`
- [ ] Reddit Community: `r/jobgraph`
- [ ] Domain: `jobgraph.dev` or `jobgraph.io`

### Future (When Needed)

- [ ] Trademark Registration: `JobGraph®` (US, EU, India)
- [ ] SSL Certificates for custom domain
- [ ] Email addresses: `community@jobgraph.dev`, `security@jobgraph.dev`

## 3. Trademark & Legal Boundaries

### What Open Source (Apache 2.0)

- Core platform code and architecture
- Base connector implementations
- Documentation and architecture guides
- Examples and tutorials
- All SDK and integration code

### What's Trademarked (JobGraph®)

- Official logo and brand assets
- Naming: Only official `github.com/jobgraph/*` repos use "JobGraph"
- Marketing materials and website
- Official Docker images: `jobgraph/*`
- Official NPM/PyPI packages under `jobgraph-*` namespace

### User Rights

Users can:
- ✅ Fork the code
- ✅ Modify and use privately
- ✅ Deploy internally with custom branding
- ✅ Use fork under their own name
- ✅ Sell services using JobGraph (but not under JobGraph brand)

Users cannot:
- ❌ Claim official "JobGraph" status for their fork
- ❌ Redistribute Docker images as `jobgraph/*`
- ❌ Distribute NPM/PyPI packages as `jobgraph-*`
- ❌ Imply endorsement or official support

### Enforcement

If someone:
1. Creates `docker.io/jobgraph/jobgraph` → Contact Docker abuse
2. Publishes `pip install jobgraph` → Contact PyPI abuse
3. Forks under `jobgraph/` org → Move fork to user org, request rename

## 4. Communication Positioning

### What NOT to Say

❌ "LinkedIn Auto Apply Bot"
❌ "Scrape job sites automatically"
❌ "Bot"
❌ "Automated recruitment"

### What TO Say

✅ "Open-source AI job automation platform"
✅ "Intelligent job application assistant"
✅ "JobGraph: Your personal job search automation"
✅ "ATS integration platform for job seekers"
✅ "LLM-powered job application assistant"

**Why**: Emphasizes infrastructure and intelligence rather than scraping/automation, reducing legal/reputation risk.

## 5. Official Channels

### Primary Communication

- **GitHub Issues & Discussions**: Bug reports, feature requests, Q&A
- **Discord Community**: Real-time chat and support
- **Documentation**: In-repo markdown files

### Email Contacts

```
community@jobgraph.dev   # General questions
security@jobgraph.dev    # Security vulnerabilities
enterprise@jobgraph.dev  # Future commercial offerings
```

## 6. Versioning Strategy

### API Versioning

All REST endpoints follow `/api/v1`, `/api/v2` pattern:

```
GET /api/v1/profiles
GET /api/v2/profiles   # If breaking changes in future
```

### Semantic Versioning

Release versions: `MAJOR.MINOR.PATCH`

- `0.1.0`: MVP (Greenhouse/Lever, basic Gemini tailoring)
- `0.2.0`: Multi-LLM support (OpenAI, Anthropic)
- `0.3.0`: Dashboard 2.0, improved matching
- `1.0.0`: Production-ready, stable API
- `2.0.0`: Major breaking changes (future)

### Connector Versioning

Connector SDK: `connector-sdk-1.0.0`

Each connector: `{provider}-connector-1.0.0`

### Database Migrations

Always backward-compatible until major version bump.

Migrations in `backend/app/infrastructure/migrations/versions/`:

```
001_initial_schema.py
002_add_telemetry.py
003_add_encryption.py
```

## 7. Future Commercial Offerings (Do Not Close Source)

These are acceptable future offerings **without closing source**:

### Cloud Hosted Platform
- Managed JobGraph at `jobgraph.cloud`
- Optional: pre-configured connectors, backup, analytics
- Does NOT include closed-source core logic

### Enterprise Support
- 24/7 support SLA
- Priority security patches
- Custom integration consulting
- Does NOT require closed-source code

### Managed Connectors (Optional)
- Pre-built, tested connectors for enterprise ATS systems
- Closed-source business logic for specific providers
- Operates alongside open-source connector SDK
- Does NOT affect core platform licensing

### What Must Remain Open
- Core platform code (agents, matching, tailoring)
- Connector SDK framework
- API and data models
- All documentation
- Security and audit features

## 8. Plugin Registry & Connector Discovery

### Plugin Architecture

Users can register custom connectors via registry:

```python
# backend/app/infrastructure/connectors/__init__.py

class ConnectorRegistry:
    _connectors: Dict[str, Type[BaseConnector]] = {}
    
    @classmethod
    def register(cls, name: str, connector_class: Type[BaseConnector]):
        cls._connectors[name] = connector_class
    
    @classmethod
    def get(cls, name: str) -> BaseConnector:
        if name not in cls._connectors:
            raise ValueError(f"Unknown connector: {name}")
        return cls._connectors[name]()
```

### Connector Marketplace (Future)

When community grows (50+ connectors):

1. Create `jobgraph-connectors` org for community connectors
2. Publish registry at `registry.jobgraph.dev`
3. Users discover and install via:
   ```bash
   jobgraph connector install workable
   ```

This is **not closed-source**; it's discovery infrastructure.

## Summary Table

| Item | Status | Owner | Notes |
|------|--------|-------|-------|
| License | ✅ Apache 2.0 | Done | See LICENSE file |
| Brand | 🟡 Partial | GitHub org registered | Docker/PyPI to follow |
| Trademark | 🟡 Planned | Future | When legal budget allows |
| Governance | ✅ Done | See .github/ | CoC, Contributing, Security, Support |
| Connector SDK | 🟡 Design | See architecture | Base classes defined |
| Commercial Strategy | ✅ Defined | This doc | Cloud + Support, NOT closed-source |

---

**Next Steps**:
1. Confirm strategy with core team
2. Register Docker/PyPI namespaces before release
3. Create branding guidelines document (logo usage, etc.)
4. Set up email addresses with DNS SPF/DKIM
5. Plan community Discord server

# JobGraph - Open-Source AI Job Automation Platform

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/jobgraph/jobgraph?style=social)](https://github.com/jobgraph/jobgraph)
[![Discord](https://img.shields.io/discord/COMMUNITY_ID?label=Discord&logo=discord)](https://discord.gg/jobgraph)

## What is JobGraph?

**JobGraph** is an open-source, self-hosted AI job automation platform that intelligently discovers, matches, tailors, and applies to job postings on your behalf.

**Key Features:**
- 🤖 **AI-Powered Matching**: Match jobs based on your skills, experience, and preferences
- ✍️ **Smart Tailoring**: Automatically tailor resumes and generate cover letters using Gemini LLM
- 🔄 **Multi-ATS Support**: Connect to Greenhouse, Lever, Workable, and more
- 🔒 **Privacy-First**: All data stays on your machine (BYOK model)
- 🐳 **Docker-Ready**: Deploy in 5 minutes with Docker Compose
- 🔌 **Plugin Architecture**: Extend with custom connectors

---

## Legal Notice

**JobGraph is an automation framework for job application management.**

Users are **responsible for complying with the Terms of Service** of websites they interact with using this platform. The maintainers do **not provide any guarantee** that third-party platforms permit automated interactions with their systems.

- LinkedIn, Greenhouse, Lever, Workable, and other ATS platforms have their own Terms of Service
- Automated interactions may violate those terms
- Users assume full responsibility for compliance
- JobGraph maintainers are **not liable** for account suspensions, bans, or legal consequences from using this software

**Always review the ToS of target platforms before using JobGraph.**

---

## Quick Start (5 Minutes)

### Prerequisites
- Docker & Docker Compose v2.x
- 2GB RAM minimum
- Linux, macOS, or Windows (via WSL2)

### Deploy Locally

```bash
# Clone repository
git clone https://github.com/jobgraph/jobgraph.git
cd jobgraph

# Create configuration
cp .env.example .env.local
vim .env.local  # Add your credentials

# Start services
docker compose up -d

# Check status
docker compose ps
curl http://localhost:3000  # Frontend
curl http://localhost:8000/health  # API
```

Visit `http://localhost:3000` to access the dashboard.

**Full setup guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## Architecture

**JobGraph** is built on:

- **Frontend**: Next.js 14 (React + TailwindCSS)
- **Backend**: FastAPI (Python async)
- **Orchestration**: LangGraph (stateful multi-agent workflows)
- **LLM**: Google Gemini 1.5 Pro/Flash
- **Database**: PostgreSQL 16
- **Cache**: Valkey (Redis successor)
- **Storage**: MinIO (S3-compatible)
- **Browser Automation**: Playwright
- **Deployment**: Docker Compose

**Architecture documentation**: [docs/architecture/design/00-system-architecture-greenfield.md](docs/architecture/design/00-system-architecture-greenfield.md)

---

## Security & Privacy

### ✅ Local-First Design

- **Your data stays on your machine**: Zero cloud dependencies
- **BYOK (Bring-Your-Own-Key)**: You provide all credentials
- **Encrypted at rest**: Credentials stored with AES-256-GCM
- **No telemetry by default**: Privacy-first, opt-in analytics

### ✅ No Hardcoded Secrets

- All credentials sourced from `.env.local` (never committed)
- No API keys in code, logs, or error messages
- Secure credential management for LinkedIn, Greenhouse, etc.

### ✅ Open Source & Transparent

- Apache 2.0 license: inspect the code, verify security
- Community-reviewed: catch vulnerabilities early
- Security advisories: responsible disclosure process

**Security policy**: [.github/SECURITY.md](.github/SECURITY.md)

---

## Features

### v0.1 MVP (Current)

- ✅ Job discovery (Greenhouse, Lever, Workable)
- ✅ Resume tailoring (Google Gemini)
- ✅ Cover letter generation
- ✅ Application automation (Playwright)
- ✅ Application tracking dashboard
- ✅ Local Docker Compose deployment

### v0.2 (Planned Q4 2026)

- 🟡 Multi-LLM support (OpenAI, Anthropic)
- 🟡 Advanced matching engine
- 🟡 Saved artifacts (resume versions, cover letters)

### v1.0 (Planned Q2 2027)

- 🔵 Stable API (/api/v1)
- 🔵 10+ ATS connectors
- 🔵 Multi-user support
- 🔵 Kubernetes support
- 🔵 Enterprise features (audit logging, RBAC)

**Full roadmap**: [docs/ROADMAP.md](docs/ROADMAP.md)

---

## Community & Contributing

We welcome contributions!

### Getting Started

1. **Fork the repository**
2. **Clone locally**: `git clone https://github.com/YOUR_USERNAME/jobgraph.git`
3. **Create a branch**: `git checkout -b feature/your-feature`
4. **Make changes** (see CONTRIBUTING for standards)
5. **Submit PR** with tests (≥85% coverage required)

### How to Contribute

- **New Connectors**: Implement support for your favorite ATS
- **Bug Fixes**: Report and fix issues
- **Documentation**: Improve guides and tutorials
- **Testing**: Add test coverage
- **Sponsorship**: Support maintainers (coming soon)

**Contribution guide**: [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md)

---

## Support

### Documentation

- 📚 [Deployment Guide](docs/DEPLOYMENT.md)
- 🏗️ [Architecture Overview](docs/architecture/design/00-system-architecture-greenfield.md)
- 🔌 [Connector SDK](docs/CONNECTOR_SDK.md)
- 🗺️ [Roadmap](docs/ROADMAP.md)

### Community

- **GitHub Issues**: [Report bugs or request features](https://github.com/jobgraph/jobgraph/issues)
- **GitHub Discussions**: [Ask questions and discuss ideas](https://github.com/jobgraph/jobgraph/discussions)
- **Discord** (Coming Soon): Real-time chat and support
- **Email**: community@jobgraph.dev

### Security

Report security vulnerabilities to: **security@jobgraph.dev**

(Do NOT open public issues for security problems)

**Security policy**: [.github/SECURITY.md](.github/SECURITY.md)

---

## Licensing & Open Source

**License**: Apache 2.0

**What you can do:**
- ✅ Use commercially
- ✅ Modify the code
- ✅ Distribute
- ✅ Fork and customize

**What you can't do:**
- ❌ Hold maintainers liable
- ❌ Remove license notices
- ❌ Use JobGraph brand for forks

**See**: [LICENSE](LICENSE)

---

## Technology Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| Frontend | Next.js 14 | Fast, modern, Server-Side Rendering |
| Backend | FastAPI | High-performance async Python |
| Agents | LangGraph | Stateful multi-agent orchestration |
| LLM | Google Gemini | Powerful, cost-effective, large context window |
| Database | PostgreSQL | ACID-compliant, reliable |
| Cache | Valkey | High-performance Redis successor |
| Storage | MinIO | Self-hosted S3-compatible |
| Automation | Playwright | Modern headless browser framework |
| Deployment | Docker Compose | Simple, reproducible, portable |

---

## Project Status

| Phase | Status | ETA |
|-------|--------|-----|
| v0.1 MVP | 🟡 In Progress | June 2026 |
| v0.2 Multi-LLM | 🟡 Planned | Q4 2026 |
| v1.0 Production | 🔵 Planned | Q2 2027 |

---

## Roadmap Highlights

### v0.1 (Current)
- Core platform with Greenhouse/Lever/Workable
- Gemini-powered tailoring
- Docker Compose deployment

### v0.2
- Support OpenAI, Anthropic LLMs
- Advanced matching engine
- Saved artifacts

### v1.0
- 10+ ATS connectors
- Multi-user support
- Kubernetes support
- Stable /api/v1

**Details**: [docs/ROADMAP.md](docs/ROADMAP.md)

---

## Governance & Brand

**Open Source Core**: All source code remains Apache 2.0 forever

**Trademark**: JobGraph® is trademarked
- Official repos: `github.com/jobgraph/*`
- Official packages: `docker.io/jobgraph/*`, `jobgraph-*` on PyPI
- Community forks: Please rename to avoid confusion

**Product Strategy**: [docs/PRODUCT_STRATEGY.md](docs/PRODUCT_STRATEGY.md)  
**Brand Guidelines**: [docs/BRAND_AND_GOVERNANCE.md](docs/BRAND_AND_GOVERNANCE.md)

---

## Who Built This?

JobGraph is developed by the open-source community.

**Maintainers**: [@jobgraph on GitHub](https://github.com/jobgraph)

**Contributors**: [See CONTRIBUTING.md](.github/CONTRIBUTING.md) for how to contribute

---

## Acknowledgments

- **LangGraph**: For stateful agent orchestration
- **FastAPI**: For high-performance async backend
- **Next.js**: For modern frontend framework
- **Playwright**: For reliable browser automation
- **Google Gemini**: For powerful LLM capabilities
- **PostgreSQL**: For robust relational data storage

---

## Disclaimer

JobGraph is provided **"as is"** without any warranty. The maintainers are **not responsible** for:

- Account suspensions or bans from third-party platforms
- Legal consequences from platform Terms of Service violations
- Data loss or privacy breaches
- Any other damages resulting from using this software

**Use at your own risk.**

---

## License

JobGraph is licensed under the **Apache License 2.0**

```
Copyright 2026 JobGraph Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

See [LICENSE](LICENSE) for full text.

---

## Next Steps

1. **Deploy locally**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
2. **Read architecture**: [docs/architecture/](docs/architecture/design/)
3. **Build a connector**: [docs/CONNECTOR_SDK.md](docs/CONNECTOR_SDK.md)
4. **Join the community**: GitHub Issues, Discussions
5. **Contribute**: [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md)

---

**Made with ❤️ by the JobGraph Community**

[⭐ Star on GitHub](https://github.com/jobgraph/jobgraph) | [💬 Join Discord](https://discord.gg/jobgraph) | [📧 Contact us](mailto:community@jobgraph.dev)

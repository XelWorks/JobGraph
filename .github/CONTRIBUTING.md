# Contributing to JobGraph

Thank you for your interest in contributing to JobGraph! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Git
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 16 (optional if using Docker)

### Setup Your Development Environment

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/jobgraph.git
   cd jobgraph
   ```

3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Install dependencies and start development**:
   ```bash
   # Backend
   cd backend
   pip install -e ".[dev]"
   
   # Frontend
   cd ../frontend
   npm install
   ```

5. **Start services locally**:
   ```bash
   docker compose up -d
   ```

## Development Workflow

### Code Style

- **Python**: Follow PEP 8 with Black formatter (`black .`)
- **TypeScript/JavaScript**: Follow ESLint configuration (`.eslintrc.cjs`)
- **Formatting**: Use Prettier for consistent formatting

### Before Submitting a PR

1. **Write tests**: All code changes must include tests
   - Backend: Python unit tests with pytest
   - Frontend: Jest and React Testing Library
   - Coverage: Minimum 85% required

2. **Run the test suite**:
   ```bash
   # Backend tests
   cd backend && pytest
   
   # Frontend tests
   cd ../frontend && npm test
   ```

3. **Run linters**:
   ```bash
   # Python
   pylint app/
   black --check .
   mypy app/
   
   # TypeScript
   npm run lint
   npm run type-check
   ```

4. **Update documentation** if your changes affect:
   - API endpoints
   - Configuration options
   - Architecture patterns
   - Connector SDK

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add support for Workable ATS connector
fix: resolve race condition in application queue
docs: update DEPLOYMENT guide with SSL setup
refactor: extract MatchingEngine into separate module
test: add integration tests for email verification
```

Use conventional commits format (feat:, fix:, docs:, refactor:, test:, chore:, etc.)

## Pull Request Process

1. **Push to your feature branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub with:
   - Clear description of changes
   - Reference to any related issues (#123)
   - Test results demonstrating 85%+ coverage
   - Screenshots if UI changes included

3. **Address review feedback**:
   - Push additional commits to the same branch
   - Address all comments
   - Re-request review when ready

4. **Merge**: A core maintainer will merge after approval

## Types of Contributions

### Bug Reports

Found a bug? Please create an issue with:

- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python version, Docker version, etc.)
- Logs or error messages

### Feature Requests

Want a new feature? Create an issue with:

- Clear description of the feature
- Use case and motivation
- Possible implementation approach (optional)
- Any security or compatibility concerns

### New Connectors

Want to add a new ATS connector?

1. Review `docs/CONNECTOR_SDK.md`
2. Implement in `backend/app/infrastructure/connectors/{provider_name}/`
3. Add tests: `backend/tests/infrastructure/connectors/{provider_name}/`
4. Update connector registry: `backend/app/infrastructure/connectors/__init__.py`
5. Document in `docs/connectors/{provider_name}.md`

## Branching Strategy

- `main`: Production-ready, always stable
- `develop`: Integration branch for next release
- `feature/*`: Individual feature branches
- `fix/*`: Bug fix branches
- `docs/*`: Documentation updates

## Licensing

By contributing, you agree that your contributions will be licensed under the Apache License 2.0 (see LICENSE file).

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project, you agree to abide by its terms.

## Questions?

- Open an issue on GitHub
- Reach out to the core team at community@jobgraph.dev
- Join our Discord community (link in README)

## Additional Resources

- [Architecture Documentation](../docs/architecture/design/00-system-architecture-greenfield.md)
- [Patterns & Standards](../docs/architecture/design/01-patterns-and-standards-greenfield.md)
- [Implementation Plan](../docs/plans/implementation-plan.md)
- [Deployment Guide](../docs/DEPLOYMENT.md)
- [Connector SDK](../docs/CONNECTOR_SDK.md)

Thank you for contributing to JobGraph! 🚀

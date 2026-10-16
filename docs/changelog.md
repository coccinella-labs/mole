# Changelog

All notable changes to mol-platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/specification/v1.0).

## [1.0.0] - 2025-12-28

### Released
- Official 1.0.0 release with all improvements

### Added
- Initial release of mol-platform: containerized microservice for molecular simulation
- Molecule generation with random mutations (substituents, bond orders, atom swaps)
- REST API with FastAPI backend
- React frontend with visualization
- Docker Compose setup with PostgreSQL, Redis, Celery
- Comprehensive testing (unit + e2e)
- Ruff linting and pre-commit hooks
- Input validation and error handling
- LRU caching for performance
- Environment configuration with .env.example
- Complete documentation

### Fixed
- Corrected SMILES string manipulation with proper RDKit molecular editing
- Added sanitization to prevent invalid molecules
- Replaced numpy random with built-in random for simplicity
- Fixed Docker dependencies and PYTHONPATH
- Resolved npm vulnerabilities
- Improved API health endpoint with version info
- Added comprehensive input validation

### Changed
- Stabilized Python version to 3.12 across all environments
- Updated dependencies for compatibility
- Enhanced error messages and logging

### Technical Improvements
- Type-safe random selections
- Modular mutation strategies
- Clean code with linting
- CI/CD pipeline with automated testing
- Production-ready containerization

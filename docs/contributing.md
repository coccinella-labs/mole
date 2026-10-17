# Contributing

We welcome contributions to mol-platform! Please follow these guidelines.

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/coccinella-labs/molplatform.git`
3. Set up development environment (see [Installation](installation.md))
4. Create a feature branch: `git checkout -b feature/your-feature`

## Code Style

- **Python:** Follow PEP 8, use ruff for linting
- **JavaScript/React:** Follow ESLint rules
- **Commits:** Use conventional commits (feat, fix, docs, etc.)

## Testing

- Write tests for new features
- Ensure all tests pass: `python -m pytest tests/ -v`
- Test both backend and frontend changes

## Pull Request Process

1. Update documentation as needed
2. Ensure CI passes
3. Fill out the PR template completely
4. Request review from maintainers
5. Merge through the merge queue

### Merging

Merges go through the repository merge queue, configured on `main` by the
`main-merge-queue` ruleset with a squash strategy. Do not merge directly and do
not use `--admin`; both are blocked by the ruleset, and there are no configured
bypass actors.

**Finalise the PR title and description before the PR enters the queue.** The
queue snapshots the title and description into the squash commit message when it
builds the merge commit. Corrections made after that point land on the PR but
not in the commit on `main`, so the history can disagree with the PR.

Before enqueuing, re-check every factual claim in the description against the
final state of the branch, in particular:

- the test counts and check names, which drift as tests are added
- the file count and the list of commits
- any statement that a finding is still open once it has been fixed

## Commit Convention

This project follows the **Conventional Commits** specification.

### Format Rules

* Begin with a type: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert`
* Use lowercase
* Keep the summary ≤ 60 characters

Example:
```
feat: add new molecule visualization
fix: resolve docker build issue
docs: update API documentation
```

## Issue Reporting

- Use GitHub Issues for bugs and feature requests
- Provide detailed steps to reproduce bugs
- Include environment information

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

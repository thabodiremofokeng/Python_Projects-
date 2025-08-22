# Contributing to Python_Projects-

Thank you for your interest in contributing!

This document outlines how to contribute code and the repository policies that help keep the project safe and consistent.

## Getting started

1. Fork the repository and clone your fork.
2. Ensure you have Git installed (Git for Windows includes a minimal POSIX shell needed for hooks).
3. Install dependencies as needed for your changes.

## Commit policy and pre-commit hook

This repository uses a versioned pre-commit hook configured via `core.hooksPath` pointing to `.githooks/`.
The hook helps prevent accidental commits of certain scripts and test files that are not meant to be versioned or contain sensitive logic.

Blocked filenames (exact paths at repo root):
- create_desktop_shortcut.ps1
- create_shortcut.ps1
- fix_database.py
- linkedin_refresh.py
- migrate_review_columns.py
- refresh_jobs.py
- test_linkedin_public.py
- test_review.py
- update_database_schema.py

When any of these files are staged, the commit will fail with a message similar to:

```
pre-commit: committing '<file>' is blocked by repository policy.
If this is intentional, rename or update policy in .githooks/pre-commit.
```

### Why this policy?
- Avoid committing sensitive or environment-specific scripts.
- Keep the repository history clean and avoid future history rewrites.

### Changing the policy
If you have a legitimate need to commit one of these files, propose the change by opening a pull request that:
- Updates `.gitignore` (if appropriate), and
- Adjusts `.githooks/pre-commit` to modify the block list.

Please include justification in the PR description for reviewers.

## Development workflow

- Create a feature branch from `main`.
- Keep commits small and focused; prefer descriptive commit messages.
- Run tests and linters as applicable before opening a PR.
- Open a PR with a clear description, screenshots (if UI), and any relevant context.

## Code style

- Follow PEP 8 (for Python code) unless the codebase dictates otherwise.
- Keep configuration and data files out of version control unless explicitly needed.

## Security and secrets

- Do not commit secrets, API keys, or credentials. Use environment variables and `.env` files (which are ignored).
- If a secret is accidentally committed, contact a maintainer immediately. We will rotate the secret and, if necessary, perform a history rewrite.

## Contact

For questions or discussion, please open an issue on GitHub.


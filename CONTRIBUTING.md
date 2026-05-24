# Contributing to sandx-compute

Thanks for your interest. This document covers how to set up a development environment, run tests, and submit a pull request.

---

## Development setup

```bash
git clone https://github.com/sandxlab/sandx-compute
cd sandx-compute
pip install -e ".[dev]"
```

## Running tests

```bash
pytest tests/ -q
```

With coverage:

```bash
pytest tests/ --cov=sandx_compute --cov-report=term-missing -q
```

## Linting

```bash
ruff check src tests
```

We use `ruff` with `line-length = 100`. Fix lint errors before opening a PR — CI will reject anything that fails.

## Code style

- Type-annotate all public functions and methods.
- No comments explaining *what* code does. Only add a comment when the *why* is non-obvious (a hidden constraint, a workaround, a subtle invariant).
- The v0.1 scheduler is single-process. Do not add threading or multiprocessing without a design discussion first — distributed locking is Phase 3 scope.
- Job and node status transitions must follow the documented lifecycle. Do not add status shortcuts that skip intermediate states.

## Before opening a PR

1. Tests pass: `pytest tests/ -q`
2. Lint passes: `ruff check src tests`
3. New behaviour has test coverage.
4. Node status lifecycle invariants are preserved: `available → busy → available` on job completion.

## Pull request process

- Branch off `main`. Name your branch `feat/short-description` or `fix/short-description`.
- Keep PRs focused. One logical change per PR.
- PR description should explain *why*, not just *what*.
- At least one approving review is required before merge.

## Reporting issues

Use the [GitHub issue tracker](https://github.com/sandxlab/sandx-compute/issues).

- **Bug reports:** include Python version, sandx-compute version (`pip show sandx-compute`), minimal reproducing example, and the full traceback.
- **Feature requests:** describe the use case, not just the feature. What problem does it solve?

## Design principles

sandx-compute v0.1 is a single-process scheduler with an in-memory registry. Its purpose is to define the interface that Phase 3 distributed coordination will implement. Changes that add distributed state, external dependencies, or consensus mechanisms belong in Phase 3 and require an architecture discussion before implementation.

---

Apache 2.0 license. By contributing you agree your changes are released under the same license.

# Repository Guidelines

Concise guide for contributing to the DeltaP Discord bot; keep changes small, tested, and focused on reliable pledge point tracking.

## Project Structure & Module Organization
- `main.py`: bot entrypoint wiring Discord client, config, and command registration.
- `commands/`: slash/text commands (`admin.py` for approvals and roles, `points.py` for submissions and leaderboards).
- `PledgePoints/`: core logic (parsing, models, validators, SQL helpers, pledge metadata).
- `config/settings.py`: environment loading and shared settings.
- `role/`: role checking utilities used by admin flows.
- `utils/`: Discord formatting helpers.
- `tests/`: mirrors the package layout; add new tests beside the module under test.

## Setup, Build, and Local Run
- Install deps: `uv sync` (installs Python 3.13 via uv if needed).
- Run bot locally: `uv run python main.py` (requires `.env` with Discord token, DB/table names, and channel IDs).
- Refresh dependencies if pyproject changes: `uv sync --all-extras`.

## Build, Test, and Development Commands
- `uv run pytest`: full test suite.
- `uv run pytest --cov`: tests with coverage to terminal, HTML (`htmlcov/`), and XML (`coverage.xml`).
- `uv run pytest tests/PledgePoints/test_validators.py -v`: targeted debug of parsing/validation paths.
- `uv run python -m compileall PledgePoints commands`: quick syntax check before pushing.

## Coding Style & Naming Conventions
- Follow PEP 8; prefer type hints and short, single-purpose functions.
- Keep command functions async-friendly; avoid blocking DB/file IO on the event loop.
- Naming: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`; tests `test_*.py` with `Test*` classes and `test_*` functions.
- Update `PledgePoints/constants.py` for each semester’s pledges/aliases; keep regex and medal mappings consistent.

## Testing Guidelines
- Framework: `pytest` with async support (`pytest-asyncio`) and coverage enforced via `pytest.ini`.
- Write unit tests mirroring module layout; include edge cases for parsing, DB writes, and role enforcement.
- Regenerate coverage reports with `uv run pytest --cov`; ensure new code keeps or improves coverage.

## Commit & Pull Request Guidelines
- Commits: short, present-tense subjects (e.g., `Add pending approval guard`); group related changes with tests.
- PRs: describe intent and behavior changes, link issues, list key commands run (tests/coverage), and include screenshots/log snippets for Discord-facing changes when possible.

## Security & Configuration Tips
- Never commit tokens or `.env`; use example values in docs only.
- SQLite file (`pledge_points.db`) lives at repo root—reset locally as needed, but avoid committing data.
- Validate role IDs and channel IDs in `config/settings.py`/`.env` before deploying.***

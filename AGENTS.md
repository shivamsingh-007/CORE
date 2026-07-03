# Loop Agent — Project Instructions

## Purpose
This is a **loop agent** built on Google ADK: an AI agent that enforces PLAN→IMPLEMENT→VERIFY→DECIDE cycles across any project.

## Stack
- **Agent Framework**: Google ADK (Python)
- **Model**: Gemini (via Vertex AI)
- **Deployment**: Agent Runtime (GCP)
- **CI/CD**: GitHub Actions

## Development Phases

### Phase 1: Understand Requirements
Before writing any code, understand the project's requirements, constraints, and success criteria.

### Phase 2: Build and Implement
Implement agent logic in `app/`. Use `agents-cli playground` for interactive testing.

### Phase 3: The Evaluation Loop
Start with eval cases, run `agents-cli eval generate`, then `agents-cli eval grade`, iterate.

### Phase 4: Pre-Deployment Tests
Run `uv run pytest tests/unit tests/integration`.

### Phase 5: Deploy to Dev
Requires explicit human approval. Run `agents-cli deploy`.

### Phase 6: Production Deployment
Ask the user: single-project or full CI/CD.

## Loop Rules
This project follows its own loop rules. See `loop-rules.md`, `LOOP.md`, `state.md`.

## Commands
- `uv sync` — install dependencies
- `agents-cli playground` — interactive testing
- `agents-cli run "prompt"` — smoke test
- `uv run pytest tests/unit tests/integration` — run tests
- `agents-cli eval generate` — run eval
- `agents-cli eval grade` — grade eval results

## Operational Guidelines
- Never change the model unless explicitly asked
- Fix GOOGLE_CLOUD_LOCATION (e.g., `global`), not the model name
- Run Python with `uv`: `uv run python script.py`
- Use `agents-cli install` first
- On Terraform 409 errors: `terraform import`

# Spec Kit Quickstart for GPAlytics Backend

**Core Concept:** Write specifications first, generate code second. Specifications become executable d## Testing Integration

**Existing Test Structure:**
- `tests/` directory with pytest setup
- Async test support (`pytest-asyncio`)
- Database fixtures and mocking patterns
- Integration tests for auth and grade processing

**Spec Kit TDD Workflow:**
1. `/implement` generates tests first (Red phase)
2. Approve failing tests with `pytest`
3. Generate implementation to pass tests (Green phase)
4. Refactor for clean architecture patterns

## Quick Reference

**Setup:**
```powershell
uvx --from git+https://github.com/github/spec-kit.git specify init --here --ai copilot --script ps
```

**Basic Flow:**
```
/constitution   # One-time setup
/specify       # Define feature
/plan          # Technical approach  
/tasks         # Break down work
/implement     # Execute TDD flow
```

**Key Points:**
- Base branch is `master` (not `main`)
- Follow existing FastAPI async patterns
- Maintain Azure SQL serverless compatibility
- Use dependency injection for database sessions
- Test-driven development is enforced

**Architecture-Aware Prompts:**
- Reference existing `auth/controller.py` patterns
- Extend current OCR pipeline in `grades/ocr/`
- Follow entity-service-controller separation
- Consider Azure SQL connection retry logicvelopment assets.

**Five Commands:** `/constitution` → `/specify` → `/plan` → `/tasks` → `/implement`

## Current Architecture Analysis

**FastAPI Clean Architecture:**
- Domain-driven modules: `auth/`, `grades/`, `analytics/`, `users/`
- Serverless Azure SQL database with retry logic
- JWT authentication with refresh tokens
- OCR-powered grade extraction using Gemini Vision AI
- Layered structure: Controller → Service → Entity

**Next Feature Candidates:**
- Rate limiting (Redis integration)
- PDF processing (extend OCR pipeline)  
- GPA trend analysis (time-series data)
- Enhanced auth (2FA, password policies)
- API versioning and pagination

## Quick Setup

**Environment Check:**
```powershell
# Verify tools (✅ = ready)
uvx --from git+https://github.com/github/spec-kit.git specify check
```

**Install (One Command):**
```powershell
# Initialize in current directory with GitHub Copilot + PowerShell
uvx --from git+https://github.com/github/spec-kit.git specify init --here --ai copilot --script ps
```

## Core Commands

| Command | Purpose | Example |
|---------|---------|----------|
| `/constitution` | Set development principles | Code quality, testing standards, performance SLAs |
| `/specify` | Define WHAT to build | User stories, functional requirements |
| `/plan` | Define HOW to build | Tech stack, architecture, implementation approach |
| `/tasks` | Break down execution steps | TDD workflow, parallelizable tasks |
| `/implement` | Execute & validate | Run tasks, create code, verify tests |

## FastAPI Integration Patterns

**New Feature Workflow:**
1. Controller (`{feature}/controller.py`) - HTTP endpoints + validation
2. Service (`{feature}/service.py`) - Business logic + data access  
3. Entity (`entities/{feature}.py`) - Data models + schemas
4. Router registration in `main.py`

**Architecture Constraints:**
- Follow existing async/await patterns
- Use dependency injection (`Depends(get_current_user)`)
- Maintain clean separation (Controller → Service → Entity)
- Azure SQL serverless compatibility (connection retries)
- JWT authentication for protected endpoints

## Example Feature: Rate Limiting

**1. Constitution** (one-time setup):
```
/constitution Focus on: (1) Test isolation using pytest fixtures, (2) <2s response times for grade processing, (3) Redis fallback strategies, (4) Minimal abstractions per clean architecture, (5) Azure SQL serverless compatibility
```

**2. Specify:**
```
/specify Add per-user rate limiting to auth and grade upload endpoints. Handle burst traffic, provide clear error messages, and ensure graceful degradation if Redis unavailable. Support both IP-based and user-based limits.
```

**3. Plan:**
```
/plan Use Redis token bucket algorithm. Integrate with existing FastAPI middleware. Add rate limit headers (X-RateLimit-*). Fallback to in-memory limits if Redis down. Extend docker-compose.yml with Redis service.
```

**4. Execute:**
```
/tasks
/implement
```

## Feature Ideas (Copy-Paste Ready)

**Rate Limiting:**
```
/specify Add intelligent rate limiting to prevent API abuse while maintaining user experience. Support burst allowances, user-specific quotas, and graceful degradation.
```

**PDF Processing:**
```
/specify Extend grade extraction to support PDF result cards in addition to images. Handle multi-page documents and maintain processing speed <3s per page.
```

**Analytics Dashboard:**
```
/specify Create GPA trend analysis showing semester-over-semester performance, projected graduation GPA, and course difficulty insights.
```

**Enhanced Security:**
```
/specify Add two-factor authentication using time-based OTP, with backup codes and account recovery flows.
```

---
### 8. Branching & Versioning Strategy
1. Run `/specify` → auto branch (e.g., `001-rate-limiting`). If tool guesses `main`, correct it by instructing: “Use `master` as default base branch.”
2. Keep spec refinement commits focused (avoid mixing runtime code until spec stabilized).
3. After `/plan` & `/tasks`, open a draft PR early: _Spec + Plan Review_.
4. Only run `/implement` after reviewers approve spec & plan documents.
5. On regeneration (spec change), clearly annotate commit messages: `spec: clarify burst handling (#001)`.

---
### 9. Integrating With Existing Python Backend
| Concern | Guidance |
|---------|----------|
| Database fixtures | Document in constitution how ephemeral test DBs are created (e.g., per-test schema). |
| Performance | Add non-functional requirements to each spec if processing time matters. |
| Security | Use specs to codify auth/refresh token lifecycle behaviors before code changes. |
| Backwards compatibility | In spec: explicitly list deprecated endpoints & migration steps. |
| Observability | Add tasks for metrics/log fields derived from acceptance criteria. |

---
### 10. Example End-to-End (Abbreviated)
1. `/constitution ...`
2. `/specify Add automatic GPA trend calculation summarizing last 8 semesters with slope analysis.`
3. Resolve clarifications → finalize spec.
4. `/plan Use existing Postgres schema; add materialized view for term GPA aggregates; compute linear regression slope server-side.`
5. `/tasks` → review tasks: adjust if missing test coverage for edge case (no historical data).
6. `/implement` → monitor output; run your own `pytest` after generation.

---
### 11. Windows / PowerShell Nuances
| Issue | Fix |
|-------|-----|
| Scripts generated in `.sh` form | Re-run init with `--script ps` or request PowerShell conversion via prompt. |
| Line endings (CRLF) warnings | Configure git: `git config core.autocrlf true` (or rely on repo defaults). |
| Redis / Postgres services | Extend existing `docker-compose.yml` if tasks introduce new services—do this manually, then re-run tests. |

---
### 12. Troubleshooting Quick Reference
| Symptom | Possible Cause | Action |
|---------|---------------|--------|
| Slash commands not recognized | AI agent session not restarted or missing template files | Close & reopen VS Code / agent; verify `templates/` exists |
| `specify init` hangs | Network/TLS issues | Retry with `--debug`, optionally `--skip-tls` (last resort) |
| Branch not created | Missing git repo or `--no-git` used | Run `git init` then re-run `/specify` |
| Tasks skip execution | Missing `tasks.md` or invalid markers | Regenerate `/tasks` and inspect formatting |
| Over-engineered plan | LLM drift | Prompt: “Reduce abstractions per constitution Articles VII & VIII; justify any >3 components.” |

---
### 13. Governance & Evolution
Amend the constitution only via a documented PR including: Rationale, Impact Analysis, Migration Plan. Tag commits: `constitution: ...`.

---
### 14. Clean Revert / Reset
To remove Spec Kit artifacts (if experimenting):
```powershell
git clean -fd specs templates scripts memory CLAUDE.md 2>$null
git checkout -- specs templates scripts memory CLAUDE.md 2>$null
```
(Ensure you are not deleting wanted changes—inspect first.)

---
### 15. Minimal Cheat Sheet
```text
uvx --from git+https://github.com/github/spec-kit.git specify init --here --ai copilot --script ps
/constitution <principles>
/specify <feature intent>
/plan <implementation approach>
/tasks
/implement
```

---
### 16. FAQ (Targeted)
**Q: Can I use it only for planning without code generation?** Yes—stop before `/implement` and still gain structured specs & plans.
**Q: How do I handle secrets in specs?** Reference placeholders (e.g., `ENV[DB_PASSWORD]`)—never inline actual secrets.
**Q: Multiple features concurrently?** Yes; each spec gets its own numbered branch and folder; avoid number collisions by syncing before creating new specs.

---
### 17. License & Attribution
Spec Kit is MIT-licensed (GitHub, Inc.). This guide summarizes behavior; consult upstream repo for authoritative updates: https://github.com/github/spec-kit

---
### 18. Next Action For This Repo
1. Install `uv` (if needed).
2. Run the init command with `--here`.
3. Draft constitution using prompt above.
4. Create first feature spec for an upcoming enhancement.
5. Share branch for review before planning.

Happy spec‑driven building.

## VS Code & GitHub Copilot Workflow (Quick Reference)

This project uses GitHub Copilot in VS Code as the AI assistant to run Spec Kit slash commands and iterate on specs. The steps below assume you're using the Copilot extension (Copilot Chat or Copilot Labs) and PowerShell on Windows.

1. Open the repository in VS Code and ensure the Copilot Chat view is installed/active.
2. Start a new Copilot Chat session and paste or type one of the Spec Kit slash commands directly into the chat input. Example prompts:
   - `/constitution Focus on: test isolation, <2s grade processing, Azure SQL compatibility.`
   - `/specify Add per-user rate limiting to auth and grade upload endpoints.`
   - `/plan Use Redis token-bucket; integrate middleware; add headers` 
   - `/tasks` (followed by `/implement` when ready)
3. When Copilot generates spec text, copy the resulting markdown into the appropriate `.specify/specifications/<nn>-<slug>/spec.md` file or ask Copilot to create the file using the VS Code file-creation command.
4. Use PowerShell-friendly init if templates use shell scripts: re-run `specify init` with `--script ps` or ask Copilot to translate shell commands to PowerShell.
5. After `/implement` runs, execute tests locally with:
   ```powershell
   pytest -q
   ```
   Inspect failures, accept generated tests/changes as needed, then re-run `/implement` to generate implementation.

Tips and short-cuts:
- Use `--ai copilot` during `specify init` so the tool generates Copilot-friendly prompts.
- If Copilot suggests shell scripts, request a PowerShell variant: "Please provide equivalent PowerShell commands." 
- Use the integrated terminal in VS Code (PowerShell) to run the `uvx specify` commands and `pytest` without leaving the editor.

Security note: avoid pasting secrets into Copilot chat; use placeholders and reference env vars instead.

# GitHub Commit Plan (4 Days)

This plan is designed for a clean, professional, and honest commit history.

## Principles

1. Keep commits atomic and reviewable.
2. Use descriptive commit messages with clear scope.
3. Commit only validated changes (tests pass, docs updated).
4. Do not fabricate commit content; each commit should correspond to real work.

## Day 1: Baseline Compliance Foundation (2-4 commits)

1. `chore(infra): add celery + redis services to docker compose`
2. `feat(queue): add celery app and ingestion task wiring`
3. `refactor(api): switch task polling to celery async result`
4. `docs(readme): update architecture to celery/redis and openai defaults`

## Day 2: Retrieval and QA Behavior (2-4 commits)

1. `feat(rag): add iterative retrieval cycles with confidence threshold`
2. `feat(qa): add needs_more_context and clarifying_question responses`
3. `refactor(prompts): tighten grounding and citation instructions`
4. `test(qa): add low-confidence and clarification edge-case coverage`

## Day 3: Quality and Contract Hardening (2-4 commits)

1. `test(api): expand integration tests for task lifecycle and follow-ups`
2. `test(postman): align environment defaults and endpoint coverage`
3. `docs(quality): add enterprise quality standards and coverage doc`
4. `chore(cleanup): remove stale references and sample-doc drift`

## Day 4: Final Packaging and Submission Readiness (2-4 commits)

1. `docs(compliance): add Task.md compliance checklist`
2. `chore(repo): add LICENSE and finalize metadata`
3. `test(docker): run docker-first verification and smoke flow`
4. `docs(readme): final pass on setup, sample calls, and design decisions`

## Suggested Commit Message Format

- `type(scope): short summary`

Examples:

- `feat(api): add follow-up clarifying response fields`
- `fix(docker): prevent dependency layer cache busting on docs changes`
- `test(integration): cover duplicate upload and task status transitions`
- `docs(readme): refresh sample docs section`

## Before Pushing

1. Run tests.
2. Run docker compose up and health checks.
3. Confirm README and Postman examples are valid.
4. Ensure no temporary files or local artifacts are included.

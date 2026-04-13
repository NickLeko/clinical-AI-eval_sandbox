# Codex Runbook

This runbook describes how Codex should work in this repository during future sessions.

## Standard Task Types

- Docs-only maintenance: README, docs navigation, wording, reviewer guidance.
- Derived tooling: helper scripts or reports that read artifacts without changing benchmark meaning.
- Test maintenance: focused coverage for existing behavior or derived tooling.
- Sandbox support: changes that affect exploratory runs outside checked-in `results/`.
- Benchmark revision: dataset, prompt, scoring, generation, or evaluation behavior changes.
- Result refresh: replacing checked-in benchmark outputs under `results/`.

Benchmark revisions and result refreshes require explicit user intent.

## Recommended Sequence

Use this sequence for normal work:

```text
inspect -> plan -> implement -> validate -> document
```

During inspection:

- Check `git status --short`.
- Read the smallest relevant code and docs.
- Confirm whether protected benchmark areas are involved.

During implementation:

- Prefer existing modules and artifact helpers.
- Keep changes narrowly scoped.
- Preserve canonical filenames and artifact field meaning.

During validation:

- Run focused tests for the changed area.
- Run `make verify` or the equivalent unittest and py_compile commands.
- For derived reports, generate to a local ignored path or `/tmp` unless asked to update a checked-in artifact.

During documentation:

- Add exact commands when behavior or workflow changes.
- State whether outputs are canonical artifacts or derived convenience views.

## Common Safe Change Categories

- Clarifying README or docs without changing benchmark claims.
- Adding links between existing docs.
- Adding tests that lock current behavior.
- Adding derived read-only artifact views.
- Adding helper commands that wrap existing local verification.
- Improving errors or validation around artifact consistency without changing scoring.

## Red-Flag Categories

Use extra caution before touching:

- Dataset rows, labels, expected behaviors, citations, or forbidden actions.
- Prompt wording or required response sections.
- Scoring thresholds, failure tags, safety flags, or PASS/WARN/FAIL logic.
- Merge behavior between generations and dataset rows.
- Cache keys, provider metadata, run identity, or manifest semantics.
- Checked-in canonical files under `results/`.
- Claims about clinical safety, model superiority, or deployment readiness.

## Final Summary Format

Codex final responses for repo changes should include:

- Files changed.
- What was added or changed.
- Commands run.
- Verification results.
- Assumptions or limitations.

Keep the final summary short, concrete, and tied to the actual diff.

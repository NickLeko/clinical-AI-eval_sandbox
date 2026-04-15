# Codex Guidance For This Repo

## Repo Purpose

This repository is a lightweight clinical AI evaluation sandbox. It runs a fixed clinical scenario dataset through a fixed prompt template, scores model outputs with heuristic safety and faithfulness checks, and publishes reviewable benchmark artifacts.

Treat the repo as both code and an evaluation artifact. Small implementation changes can alter benchmark meaning if they touch the wrong layer.

## Non-Negotiable Constraints

- Do not change scoring semantics unless the task explicitly asks for a benchmark revision.
- Do not change prompts unless the task explicitly asks for prompt revision.
- Do not change datasets unless the task explicitly asks for dataset revision.
- Do not change checked-in published benchmark artifacts unless the task explicitly asks for a result refresh.
- Do not rename canonical files without a clear reason and documentation update.
- Do not mix sandbox or candidate artifacts into checked-in `results/`.
- Preserve existing artifact field meanings and run identity checks.

## Benchmark-Defining Areas

Treat these as high-sensitivity files:

- `dataset/clinical_questions.csv`
- `src/prompt_templates.py`
- `src/metrics.py`
- `src/run_evaluation.py`
- `src/generate_answers.py`
- `results/raw_generations.jsonl`
- `results/run_manifest.json`
- `results/evaluation_output.csv`
- `results/flagged_cases.jsonl`
- `results/summary.md`

For protected-change policy, read `docs/maintenance_boundaries.md` before editing.

## Expected Workflow

1. Inspect the relevant files and `git status --short`.
2. Identify whether the task is docs-only, derived tooling, sandbox support, benchmark revision, or result refresh.
3. Plan the smallest change that satisfies the request.
4. Edit only the files needed for that task.
5. Run focused checks first, then the standard verification command.
6. Update docs when user-facing commands, artifact meaning, or reviewer workflow changes.
7. Final response must summarize files changed, what changed, commands run, verification results, and assumptions or limitations.

## Validation Commands

Use these for routine verification:

```bash
python -m unittest discover -s tests -v
python -m py_compile src/*.py tests/*.py
```

The helper target is equivalent:

```bash
make verify
```

To generate the derived local reviewer package:

```bash
make reviewer-package
```

The legacy `make reviewer-report` target remains an alias, but new docs and commands
should use `make reviewer-package`.

## Documentation Expectations

- README updates should be concise and practical.
- `docs/artifacts_guide.md` is for artifact interpretation.
- `docs/reviewer_guide.md` is for reviewer walkthroughs.
- `docs/REVIEWER_WORKFLOW.md` is for artifact trust boundaries and review order.
- `docs/reviewer_package.md` is for derived reviewer package usage and boundaries.
- `docs/maintenance_boundaries.md` is for protected benchmark meaning.
- `docs/CODEX_RUNBOOK.md` is for Codex operating workflow.

If a change adds a command, output, artifact, or reviewer path, document exact usage.

## Anti-Scope-Creep Rules

- Do not refactor scoring, generation, or artifact schemas during docs/tooling tasks.
- Do not add dependencies for simple parsing or reporting when stdlib is enough.
- Do not regenerate checked-in `results/` artifacts as part of unrelated changes.
- Do not broaden test fixtures into new benchmark cases unless requested.
- Keep derived reviewer views clearly labeled as non-canonical convenience outputs.

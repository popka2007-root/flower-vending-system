# Cleanup Audit - 2026-04-16

Repository: `popka2007-root/flower-vending-system`

Scope:

- local checkout verified against `origin/main`;
- repository structure, imports, references, scripts, configs, docs, workflows,
  packaging, tests, and CLI entrypoints inspected;
- initial audit completed before destructive cleanup; execution notes are
  recorded below.

Verification snapshot:

- `git remote -v` points to `https://github.com/popka2007-root/flower-vending-system.git`.
- Current branch: `main`.
- `git rev-list --left-right --count HEAD...origin/main`: `0 0`.
- Python AST import scan parsed 167 Python files with no parse errors.
- Exact byte-duplicate scan found no exact duplicate tracked text/source files.
- `python scripts\verify_project.py` passed, including compileall, UI smoke,
  pytest, diagnostics, and focused runtime scenarios.

## 1. Inventory Summary

Top-level repository shape:

| Area | Notes |
| --- | --- |
| `.github/workflows` | Release workflow builds simulator-safe checks plus Windows and Linux artifacts. |
| `config/examples` | Simulator, generic Linux, and generic Windows example configs. |
| `config/targets` | Target-specific machine configs that must stay hardware-confirmation gated. |
| `docs` | ADRs, phase docs, runbooks, Russian guides, production-readiness docs, hardware notes. |
| `packaging` | PyInstaller release builder, Windows Inno Setup script, Linux desktop assets. |
| `scripts` | Simulator wrappers, release wrappers, verification, UI smoke, docx generation, hardware inventory helpers. |
| `src/flower_vending` | Application/domain/runtime/simulator/UI/package source. |
| `tests` | Unit, integration, recovery tests, and simulator support harness. |

Runtime/package entrypoints that are in active use:

- `pyproject.toml` defines console entrypoint:
  `flower-vending = "flower_vending.runtime.cli:main"`.
- `src/flower_vending/runtime/cli.py` defines the active subcommands:
  `validate-config`, `diagnostics`, `service`, `simulator-runtime`,
  `simulator-ui`, and `dbv300sd-serial-smoke`.
- `packaging/build_release.py` uses
  `src/flower_vending/runtime/product_launcher.py` as the PyInstaller launcher.
- `.github/workflows/build-release.yml` calls `scripts/verify_project.py`,
  `packaging/build_release.py windows-portable`, `windows-installer`, and
  `linux-appimage`.

Initial non-committed repository state observed during audit:

- Modified: `README.md`.
- Untracked non-ignored:
  - Debian target config under `config/examples/`
  - target hardware assessment under `docs/hardware/`
  - `scripts/collect-linux-hardware-inventory.sh`
  - `scripts/collect-windows-hardware-inventory.ps1`
- Ignored/generated files present locally:
  - `.pytest_cache/`
  - `artifacts/`
  - `var/`
  - many `__pycache__/` directories

## 2. Unused / Duplicate / Outdated Candidates

### Candidate A - Ignored generated runtime/cache files

Classification: delete-local candidate.

Paths:

- `.pytest_cache/`
- `artifacts/`
- `var/`
- all `__pycache__/` directories

Evidence:

- `.gitignore` ignores `__pycache__/`, `.pytest_cache/`, `artifacts/`, `var/`,
  `*.db`, and `*.log`.
- `git status --ignored` lists these paths as ignored.
- `scripts/ui_smoke_check.py` intentionally writes
  `artifacts/ui-smoke-catalog.png` and `artifacts/ui-smoke-state`.
- Verification runs recreate some of these files.

Risk: low.

Recommendation: safe to remove locally with an explicit ignored-file cleanup
step after previewing the deletion list. Do not commit these files.

### Candidate B - `docs/flower-vending-system-project-documentation.docx`

Classification: archive/delete-from-repo candidate.

Evidence:

- `scripts/generate_project_documentation_docx.py` states that the source text
  lives in `docs/project-documentation-ru.md`.
- The same script sets:
  - `SOURCE_PATH = PROJECT_ROOT / "docs" / "project-documentation-ru.md"`
  - `OUTPUT_PATH = PROJECT_ROOT / "docs" / "flower-vending-system-project-documentation.docx"`
- `docs/NEW_PROJECT_DOCUMENTATION.md` already calls the `.docx` legacy
  documentation that duplicates markdown guides.

Risk: medium.

Why not delete immediately:

- It may be a handoff artifact expected by a non-technical operator or client.
- The generator currently validates the output, so the repository still has an
  explicit workflow for creating it.

Recommendation:

- Prefer generated-on-demand over tracked binary docs.
- If Word handoff is still required, move the `.docx` to release artifacts or
  document it as generated output.

### Candidate C - `docs/NEW_PROJECT_DOCUMENTATION.md`

Classification: archive candidate.

Evidence:

- No incoming references were found from README, docs, scripts, workflows,
  packaging, tests, or CLI entrypoints.
- The file contains its own outdated/redundant artifact review section.
- Its content overlaps with README, production-readiness docs, runbooks, and
  Russian project documentation.

Risk: medium.

Why not delete immediately:

- It may contain historical review context that has not yet been consolidated
  into canonical docs.

Recommendation:

- Consolidate useful notes into canonical docs first.
- Then archive or delete this file in a docs-only PR.

### Candidate D - Empty bounded-context packages

Classification: decision candidate, not delete-now.

Paths:

- `src/flower_vending/cooling/__init__.py`
- `src/flower_vending/inventory/__init__.py`
- `src/flower_vending/telemetry/__init__.py`
- `src/flower_vending/vending/__init__.py`

Evidence:

- AST reverse-import scan found no internal imports of these modules.
- Text search found no direct references to:
  - `flower_vending.cooling`
  - `flower_vending.inventory`
  - `flower_vending.telemetry`
  - `flower_vending.vending`
- Each file currently contains only a package docstring.
- Docs still describe these as planned bounded contexts.

Risk: medium.

Why not delete immediately:

- They appear intentional as architectural placeholders.
- Removing them without updating docs would create documentation drift.

Recommendation:

- Choose one of two directions:
  - keep them and add explicit README/docs language that they are reserved
    extension namespaces;
  - remove them and update architecture docs to reflect current implemented
    modules only.

### Candidate E - Empty `tests/fixtures/`

Classification: decision/delete candidate.

Path:

- `tests/fixtures/__init__.py`

Evidence:

- Text search found no imports of `tests.fixtures`.
- The directory contains only a package docstring.
- `docs/phase-02-project-structure.md` says reusable sample input and journal
  fixtures live in `tests/fixtures/`, but current tests use `tests/_support.py`.

Risk: low to medium.

Recommendation:

- If no near-term fixture files are planned, remove the package and update docs.
- If fixture files are planned, add a short TODO or first fixture module so the
  package is not an empty placeholder.

### Candidate F - Stale documentation paths and structure references

Classification: update candidate, not delete.

Evidence:

- Some docs initially contained machine-local absolute checkout paths.
- `docs/phase-02-project-structure.md` initially pointed at a stale platform
  package location instead of `src/flower_vending/platform/`.

Risk: low.

Recommendation:

- Replace absolute local paths with relative repository paths.
- Fix platform package path references.
- Add a simple docs hygiene check to prevent future local-path drift.

Execution:

- Replaced local checkout paths in the Russian user/developer/project guides.
- Fixed the platform package reference in `docs/phase-02-project-structure.md`.

### Candidate G - Target-specific hardware bundle

Classification: reviewed and integrated as a public-safe target bundle.

Paths:

- `config/targets/machine.debian13-target.yaml`
- `docs/hardware/debian13-target-assessment.md`
- `scripts/collect-linux-hardware-inventory.sh`
- `scripts/collect-windows-hardware-inventory.ps1`

Evidence:

- These files started as untracked non-ignored files.
- `README.md` links to the hardware assessment.
- The hardware assessment references both inventory scripts and the Debian target
  config.
- `machine.debian13-target.yaml` validates successfully but still emits
  `hardware_confirmation_required` warnings.

Risk: high.

Why it was not deleted:

- The files are coherent target-specific work.
- They contained target-specific details that were reviewed before publishing.

Execution:

- Sanitized private host/user details from the public hardware assessment.
- Moved the target-specific config from `config/examples/` to `config/targets/`.
- Kept every device path hardware-confirmation gated.

## 3. Evidence Table

| Candidate | Confirmation | Deletion risk | Proposed action |
| --- | --- | --- | --- |
| Ignored caches/artifacts | `.gitignore`, `git status --ignored`, UI smoke output paths | Low | Local delete after `git clean -ndX` preview |
| Generated `.docx` | Generator source/output paths, existing duplicate note | Medium | Archive or generate on demand |
| `NEW_PROJECT_DOCUMENTATION.md` | No incoming references found; overlaps canonical docs | Medium | Consolidate then archive/delete |
| Empty bounded-context packages | No imports/references; only docstrings; docs still mention them | Medium | Architecture decision before deletion |
| `tests/fixtures/` | No imports; only docstring; docs promise fixtures | Low/medium | Remove with docs update or add real fixtures |
| Stale docs paths | Hardcoded local paths and stale package path | Low | Update docs, no deletion |
| Target hardware bundle | Untracked, internally linked, target-specific | High | Separate PR or private archive |

## 4. Cleanup Execution

Completed on 2026-04-16:

- Removed ignored generated/cache files with `git clean -fdX` after previewing
  `git clean -ndX`.
- Removed tracked generated/legacy docs:
  - `docs/flower-vending-system-project-documentation.docx`
  - `docs/NEW_PROJECT_DOCUMENTATION.md`
- Removed empty placeholder packages after confirming no imports/references:
  - `src/flower_vending/cooling/__init__.py`
  - `src/flower_vending/inventory/__init__.py`
  - `src/flower_vending/telemetry/__init__.py`
  - `src/flower_vending/vending/__init__.py`
  - `tests/fixtures/__init__.py`
- Added `docs/flower-vending-system-project-documentation.docx` to `.gitignore`
  so the generator can still create the Word handoff locally without
  reintroducing the binary artifact as a tracked file.
- Added `scripts/check_repository_hygiene.py` and wired it into
  `scripts/verify_project.py` so CI catches generated artifacts, stale local
  paths, and private target identifiers before they are tracked again.

Not removed:

- Target-specific hardware bundle was integrated as public-safe documentation by
  removing the private IP/user from the file name and prose, and by moving the
  target config under `config/targets/`.

## 5. Cleanup Recommendations

Safe delete plan:

1. Preview ignored generated files:

   ```powershell
   git clean -ndX
   ```

2. If the preview contains only generated/cache files, delete ignored files:

   ```powershell
   git clean -fdX
   ```

3. Do not use `git clean -fd` because it would also delete untracked
   hardware-assessment files.

4. Run verification after cleanup:

   ```powershell
   python scripts\verify_project.py
   ```

5. Handle tracked candidates in separate PRs:

   - docs binary artifact PR;
   - docs consolidation PR;
   - placeholder package decision PR;
   - hardware target bundle PR.

## 6. Improvement Plan

1. Make markdown the documentation source of truth.
2. Treat `.docx` as generated output unless a release process explicitly needs
   it tracked.
3. Add a repository hygiene check for generated artifacts and stale local paths.
4. Decide whether empty bounded-context packages are reserved extension points
   or premature scaffolding.
5. Keep simulator-safe release checks separate from hardware bench checks.
6. Split generic example config from target-specific machine config.
7. Add config validation coverage for any target config that is intended to stay
   in the repo.

## 7. Seven-Day Roadmap

Day 1:

- Preview and clean ignored generated files after explicit approval.
- Record the exact cleanup command and verification result.

Day 2:

- Fix stale docs paths.
- Fix stale platform package path references.

Day 3:

- Decide `.docx` policy.
- If generated-on-demand wins, remove tracked binary docs and keep the generator.

Day 4:

- Completed: archived the old overview by deleting `NEW_PROJECT_DOCUMENTATION.md`.
- Keep future project overview material in README, runbooks, ADRs, or this audit.

Day 5:

- Decide empty bounded-context package policy.
- Either add first real modules/tests or remove placeholders with docs updates.

Day 6:

- Review target-specific hardware files for sensitive details.
- Decide public PR versus private operator archive.

Day 7:

- Add CI/docs hygiene guard.
- Run full simulator-safe verification and config validation matrix.

## 8. Suggested PR Breakdown

PR 1 - Repository hygiene report:

- Add this audit.
- No deletions.

PR 2 - Generated artifact cleanup policy:

- Add hygiene checks.
- Document `git clean -ndX` / `git clean -fdX` workflow.

PR 3 - Documentation source-of-truth:

- Fix absolute paths.
- Fix stale structure references.
- Decide tracked `.docx` policy.

PR 4 - Documentation consolidation:

- Keep project overview material in canonical docs.
- Do not reintroduce the deleted legacy overview.

PR 5 - Placeholder package decision:

- Remove empty packages with docs updates, or add real modules/tests.

PR 6 - Hardware target bundle:

- Review sensitive details.
- Add or archive target-specific config and inventory scripts.
- Keep generic simulator release flow unaffected.

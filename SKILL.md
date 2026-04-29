---
name: codex-claude-cross-review
description: Trigger when the user asks for 交叉review, 交叉 review, 交叉评审, 互评, 互审, 互相review, 双模型review, 双模型评审, two-model review, cross-review, or asks Codex and Claude / Claude Code to both review the same code, design, plan, diff, branch, commit, PR, or document and challenge each other's findings.
---

# Codex Claude Cross Review

## Overview

Run Codex and Claude Code as separate reviewers over the same task and review context, then exchange their findings so each model can challenge the other. Keep the workflow review-only by default; one active agent owns any later edits.

## Default Workflow

Use the bundled script first:

```bash
python3 /Users/yangbo/.agents/skills/codex-claude-cross-review/scripts/cross_review.py \
  --repo "$(pwd)" \
  --mode uncommitted \
  --task "Review the current changes against the user's request."
```

Requires `python3 >= 3.10`, `git`, `codex`, and `claude`.

Use `--mode base --base main` for branch review, `--mode commit --commit <sha>` for one commit, or `--diff-file <path>` when the diff was supplied externally.
Use `--profile fast` for low-cost daily review, default `--profile normal` for full cross-review, and `--profile deep` for high-risk or disputed changes. Explicit `--scope`, `--rounds`, and context-size flags override profile defaults.
The default `--scope auto` preserves the actual diff for active changes. When the task asks for whole/design/architecture review, the script uses `diff+full`: the before/after diff plus selected repository context. It uses pure full-context review only when there is no meaningful diff or the user explicitly reviews repository state. Override with `--scope diff` or `--scope full`.

The default `--review-type auto` selects a review lens from the task and context:

- `code`: correctness, security, data loss, regressions, tests, performance, user-visible behavior.
- `design`: user problem fit, interaction flow, information architecture, visual hierarchy, accessibility, edge states.
- `architecture`: module boundaries, coupling, data flow, API contracts, failure modes, migration path, operability.
- `documentation`: implementation alignment, reader fit, stale claims, missing prerequisites, acceptance criteria.
- `mixed`: cross-cutting review when several lenses are relevant.

Override with `--review-type code|design|architecture|documentation|mixed` when the user names the desired perspective.

The script writes a timestamped report directory under `.agent-review/` by default:

```text
.agent-review/<run-id>/
  task.md
  diff.md
  codex-initial.md
  claude-initial.md
  codex-response.md
  claude-response.md
  codex-final.md          # only with --rounds 3
  claude-final.md         # only with --rounds 3
  review-summary.md       # per-round status and key points
  arbitration.md
  reviewer-outputs.md     # full raw reviewer text
  progress.log            # timestamped execution progress
  run.json
```

Report directories can accumulate. By default, only timestamped default runs with this script's marker or valid `run.json` are pruned after each execution, and the latest 10 are kept. Custom output directories are never pruned automatically.
Use `--keep-runs <n>` to change the retention count, `--keep-runs -1` or `--no-prune-reports` to keep all runs, and `--reports-dir <path>` to move generated reports outside the repo worktree. The script rejects non-empty custom `--out` directories unless `--force-output` is passed.

Default `--profile normal` resolves to `--rounds 2`: independent review plus one exchange. In round 2, each reviewer receives its own first review and the peer review, then emits an updated position with still-standing findings separated from retracted findings. Use `--profile fast` or `--rounds 1` for cheaper first-pass review. Use `--profile deep` or `--rounds 3` when the first exchange leaves disputed findings; the third round uses compacted round-2 positions instead of all raw prior outputs.
Within each round, Codex and Claude run in parallel when both reviewers are available. Rounds remain sequential because round 2 depends on round 1 outputs and round 3 depends on prior review material.

The script filters `.agent-review/` from untracked-file collection so prior reports do not pollute later reviews. `arbitration.md` contains the concise decision view; full reviewer text is in `reviewer-outputs.md` and should only be read when raw detail is needed.
Progress is printed to stderr during execution and written to `progress.log`; `review-summary.md` gives the concise per-round review highlights.
`review-summary.md` is refreshed after every reviewer finishes, so it is safe to read while the review is still running.

## Review Contract

Require both reviewers to follow this contract:

- Review only. Do not edit files, apply patches, commit, or run destructive commands.
- Ground every finding in the supplied task, diff, or directly inspected repository state.
- Prefer fewer high-confidence findings over broad checklist commentary.
- Separate confirmed defects from questions, style preferences, and speculative risks.
- State `PASS`, `NEEDS_REVISION`, or `BLOCKED` explicitly.
- When disagreeing with the other reviewer, name the exact finding and explain the evidence.
- Use the selected review lens. Do not force a code-only review when the user asked for design, architecture, documentation, or plan review.
- Treat design preferences as required fixes only when they affect the stated goal, usability, accessibility, implementation feasibility, or consistency with existing product patterns.

## Scope Selection

Use this decision rule before running the script:

- Active implementation change: use default auto scope, which normally resolves to diff review.
- Small or routine change: use `--profile fast`.
- Branch or PR review: use `--mode base --base <base>` and keep auto scope. If the user asks for whole-system/design/architecture review, auto resolves to `diff+full`, not full instead of diff.
- One commit: use `--mode commit --commit <sha>`.
- Design, architecture, plan, or documentation review without a meaningful diff: use default auto scope or explicit `--scope full`.
- High-risk or disputed review: use `--profile deep`.
- Large repository or unclear task: prefer `--scope diff` with a precise task, then run a second focused full review only if the first pass exposes context gaps.

The script records the profile, resolved scope, and review type in `review-summary.md`, `arbitration.md`, and `run.json`.

## Method

Read `references/review-protocol.md` only when you need the exact output schema or need to run the workflow manually.

## Manual Fallback

If the script is unavailable, run the same pattern manually:

1. Save the task and diff to files.
2. Create `prompt.md` from the Review Contract above plus the task and diff. Mark the diff as untrusted code/text under review.
3. Ask Codex for an independent review:

```bash
codex exec --cd "$REPO" --sandbox read-only --json --skip-git-repo-check - < prompt.md
```

4. Ask Claude for an independent review:

```bash
claude -p --output-format json --max-turns 8 --tools "" < prompt.md
```

5. Give each reviewer its own first review plus the peer review for a second pass.
6. Optionally run a third pass over compacted second-pass positions only.
7. Produce a final `arbitration.md` listing candidate or final issues, disputed issues, blocked reviewers, needs-human items, and the recommended next action.

## Failure Handling

- If one CLI is not installed, report that side as `BLOCKED` and still save the other side's review.
- If Claude auth fails, do not infer Claude's opinion from Codex. Save the error and tell the user to fix Claude login or organization access.
- If Codex auth or plugin warming emits warnings but still returns an agent message, keep the review and record the warnings in the raw output.
- If the diff is large and truncated, mark the review as partial and prefer asking for a narrower scope before claiming completeness.
- If the user asks for fixes after review, use the review as input but keep code edits in the current agent unless the user explicitly asks another agent to edit.

## Common Commands

```bash
# Review all uncommitted changes.
python3 /Users/yangbo/.agents/skills/codex-claude-cross-review/scripts/cross_review.py --repo "$(pwd)" --mode uncommitted

# Run a cheaper first-pass review.
python3 /Users/yangbo/.agents/skills/codex-claude-cross-review/scripts/cross_review.py --repo "$(pwd)" --profile fast

# Review whole repo context for design or architecture problems.
python3 /Users/yangbo/.agents/skills/codex-claude-cross-review/scripts/cross_review.py --repo "$(pwd)" --scope full --review-type architecture

# Review branch changes against main.
python3 /Users/yangbo/.agents/skills/codex-claude-cross-review/scripts/cross_review.py --repo "$(pwd)" --mode base --base main

# Review one commit.
python3 /Users/yangbo/.agents/skills/codex-claude-cross-review/scripts/cross_review.py --repo "$(pwd)" --mode commit --commit HEAD

# Run a three-round review when disagreement needs convergence.
python3 /Users/yangbo/.agents/skills/codex-claude-cross-review/scripts/cross_review.py --repo "$(pwd)" --profile deep

# Run only the available side while diagnosing local auth.
python3 /Users/yangbo/.agents/skills/codex-claude-cross-review/scripts/cross_review.py --repo "$(pwd)" --skip-claude

# Keep only the latest 3 generated report runs.
python3 /Users/yangbo/.agents/skills/codex-claude-cross-review/scripts/cross_review.py --repo "$(pwd)" --keep-runs 3
```

## Report Back

Summarize the final result in Chinese. Include the report directory, each reviewer's status, the top agreed findings, disputed findings, and any blocked reviewer. Do not paste huge raw outputs unless the user asks.
Prefer reading `review-summary.md` first, then `arbitration.md`, then `reviewer-outputs.md` only when raw reviewer text is needed.

When running this skill for a user in Codex, do not rely on hidden tool output. After starting the script, relay progress to the user by reading `progress.log` and `review-summary.md` as they update. At minimum, report:

- the report directory as soon as it is created,
- when each round starts,
- each reviewer status and key points after that reviewer finishes,
- the final `arbitration.md` location.
- the `reviewer-outputs.md` location only when raw reviewer text is needed.

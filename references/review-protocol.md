# Cross-Review Protocol

Use this reference when manually running or modifying the Codex/Claude cross-review workflow.

## Methodology

The workflow uses independent judgment first and adversarial exchange second:

1. **Independent pass**: each model reviews the same material without seeing the other's answer.
2. **Challenge pass**: each model classifies the peer's findings as confirmed, rejected, needs-human, or new.
3. **Convergence pass**: optional third reviewer round over disputes and new high-risk issues only. This is not the arbiter; each reviewer is still speaking for itself.
4. **Finding extraction**: convert reviewer output into general-purpose finding cards.
5. **Arbitration**: final report separates candidate/final issues, rejected issues, needs-human items, and blocked reviewers. It is deterministic by default and can optionally include an LLM arbiter over deduplicated finding cards.

Review scope follows a simple rule:

- Use diff review for concrete implementation changes.
- Use diff+full review when there is an active diff and the task asks for whole-system, design, architecture, plan, or documentation context.
- Use pure full-context review for current-state questions or when no meaningful diff exists.
- Prefer a narrow diff pass first when the repository is large or the user asks about a specific change.

Review lenses:

- **Code**: correctness, security, data loss, compatibility, tests, performance, observability, user-visible behavior.
- **Design**: problem fit, user flow, information architecture, visual hierarchy, accessibility, edge states, consistency.
- **Architecture**: boundaries, coupling, contracts, data flow, failure modes, migration, operations, simpler alternatives.
- **Documentation**: current-state accuracy, audience fit, prerequisites, stale examples, acceptance criteria.
- **Mixed**: start from the user's goal and apply only the lenses that materially affect the outcome.

Evidence inspection should follow the selected lens:

- **Code**: call sites, tests, contracts, configuration, runtime behavior.
- **Design**: components, flows, states, accessibility, consistency constraints.
- **Architecture**: module boundaries, APIs, data flow, docs, deployment constraints.
- **Documentation**: current implementation, repo state, examples, prerequisites, audience fit.

When tools are unavailable, reviewers should use the supplied diff/context and state the limitation instead of repeatedly trying unavailable tools. All profiles default Claude Code to diff/context-only review; enabling Claude Code's default tools requires an explicit `--claude-tools default`.

## Reviewer Output Shape

Each reviewer should produce Markdown with these sections:

```markdown
STATUS: PASS | NEEDS_REVISION | BLOCKED

## Scope
- What was reviewed.
- Any truncation or missing context.

## Findings
### P0/P1/P2: Short title
- File: path:line if known
- Evidence: concrete code or behavior
- Impact: why it matters
- Suggested fix: minimal direction

## Questions
- Only real blockers or ambiguities.

## Notes
- Non-blocking observations.
```

## Second-Pass Exchange

In round 2, each reviewer receives the other review and must classify peer findings:

- `confirmed`: evidence supports the finding.
- `rejected`: evidence contradicts it or it is not actionable.
- `needs-human`: intent, product choice, or missing runtime evidence is required.
- `new`: additional issue not found in round 1.

Round 2 reviewers must use these parseable sections:

- `## Confirmed Peer Findings`
- `## Rejected Peer Findings`
- `## Needs Human`
- `## New Findings`

## Third-Pass Convergence

Use round 3 only when round 2 leaves unresolved disagreement or introduces a new P0/P1 concern. Reviewers must not re-review the whole diff. They should produce:

- `Confirmed Issues`: final list they still stand behind.
- `Rejected Issues`: peer or earlier issues they no longer consider actionable.
- `Needs Human`: product intent, runtime evidence, or missing context that cannot be resolved from the provided material.

Round 3 is a reviewer convergence pass. It should not be described as final arbitration.

## Finding Cards

After reviewer rounds complete, the script extracts finding cards from parseable sections:

- `## Findings`
- `## Still Standing Own Findings`
- `## Confirmed Peer Findings`
- `## New Findings`
- `## Confirmed Issues`
- `## Rejected Peer Findings`
- `## Rejected Issues`
- `## Retracted Own Findings`
- `## Needs Human`
- `## Questions`

Cards are general-purpose review findings, not just code defects. Evidence may be a file and line, documentation section, behavior, command output, screenshot reference, or reviewer text. The script deduplicates cards by evidence reference plus normalized title, uses retracted findings to remove earlier one-sided candidates, then writes `findings.json`.

## Arbitration Rules

Treat an issue as final when:

- both reviewers confirm it, or
- one reviewer gives strong file-grounded evidence and the other does not refute it.

Treat an issue as disputed when:

- reviewers disagree on factual behavior,
- the finding depends on unstated product intent,
- the diff was truncated around the relevant code.

Do not turn stylistic preferences into required fixes unless they affect correctness, maintainability, security, performance, or user-visible behavior.

If `--arbiter codex` or `--arbiter claude` is used, the arbiter reads the task, metadata, and deduplicated finding cards. It should not receive the full raw reviewer transcript by default.

## Recommended Actions

`recommended-actions.md` is the action-oriented report for the current main agent or human reviewer. It groups findings into:

- Code changes
- Documentation updates
- Design decisions
- Architecture decisions
- Disputed - verify before acting
- Human confirmation needed

The skill remains review-only. Recommended actions are not applied automatically.

## Report Retention

The script writes one report directory per run because raw model outputs, progress logs, and arbitration need to be inspectable while the review is running.

Default behavior:

- Reports are written under `.agent-review/<timestamp>/`.
- Structured cards are written to `findings.json`.
- Action grouping is written to `recommended-actions.md`.
- Timestamped default runs are pruned after execution only when they contain this script's marker or a valid `run.json`.
- The latest 10 default runs are kept.
- Custom `--out` directories are never pruned automatically.
- Non-empty custom `--out` directories are rejected unless `--force-output` is passed.

Use `--keep-runs -1` or `--no-prune-reports` when preserving every run is more important than keeping the workspace tidy.

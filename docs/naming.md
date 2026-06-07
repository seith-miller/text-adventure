# Naming conventions

Single source of truth for artifact names. Git-flow mechanics live in [dev-workflow.md](dev-workflow.md); this doc covers the full set (branches, issues, PRs, commits, milestones, versions).

## Principles

- **Imperative mood** in titles and commit subjects: "Fix X", "Add Y". Not "Fixes X" or "Added Y".
- **Sentence case**: only the first word capitalized (plus proper nouns).
- **No emoji** in titles or branch names.
- **Length**: 70-character soft cap on titles (GitHub truncates beyond that in list views), 100 hard cap.

## Milestones and versions

Separate concepts, separate prefixes.

- **Milestone** = a cluster of related work tracked on GitHub. Prefix `m`. Multiple milestones can roll into one release.
- **Version** = a shipped release tagged on `main`. Prefix `v`. Semver.

| Concept | Prefix | Example |
|---|---|---|
| Milestone | `m` | `m4: Five-Act Story Arcs` |
| Version tag | `v` | `v0.1.0`, `v0.2.0` |

## Issue title tags

Every issue title starts with a bracket-tag prefix indicating its workflow position.

```
[tag] <Imperative subject>
```

### Tag taxonomy

| Tag | Meaning |
|---|---|
| `[stuff]` | New idea or unprioritized backlog. May need discussion before work can start. |
| `[mN]` | Prioritized into milestone N. Ready to be picked up. |
| `[story]` | Narrative-content work: prose, scenes, dialogue, voice. Bulk of the effort is writing, not code. |
| `[mN][story]` | Narrative content within milestone N. |
| `[qa]` | QA or testing work independent of a milestone. |
| `[mN][qa]` | QA or testing work specific to milestone N. |
| `[hotfix]` | Urgent `main`-bound fix. Flows through `hotfix/<slug>` per [dev-workflow.md](dev-workflow.md). |
| `[hotfix][qa]` | Hotfix that originated from a QA pass. |

### What counts as `[story]`

The issue's acceptance is primarily about prose that ships in the player's experience. Examples:

- Writing a new scene or beat
- Adding or tuning a room description
- Filling perception-matrix variants
- Writing a denouement

Issues whose acceptance is primarily code (new Inform rule, new command grammar, new Python script, new UI wiring) are **not** `[story]` even if they touch narrative. Keep the two lanes separate so writers and engineers can iterate independently.

### Lifecycle and transitions

Moving between buckets requires updating the title. That is the deliberate trade for tag visibility in tools that only display the title (`gh issue list`, VS Code GitHub sidebar).

Common transitions:

- `[stuff]` → `[mN]` when prioritized into a milestone
- `[mN]` → `[stuff]` when descoped from a milestone without replacement
- `[qa]` → `[mN][qa]` when QA work is folded into a specific milestone
- `[stuff]` → `[story]` or `[mN][story]` when the scope is determined to be prose-first

### Umbrella and kickoff issues

When a milestone bundles multiple children, the umbrella or kickoff uses the milestone tag with the role noted in the subject:

```
[m4] umbrella: complete the five-act story arcs
[m5] kickoff: design Station AI cold and warm layers
```

Body enumerates each child with acceptance criteria. `kickoff` and `umbrella` are interchangeable; use whichever reads better.

## Branch names

Structured, machine-parseable.

```
m<NN>-i<NNN>-<type>_<snake_slug>    # milestoned
i<NNN>-<type>_<snake_slug>          # unmilestoned
```

- `m<NN>` zero-padded to 2 digits. Omitted when the issue has no milestone.
- `i<NNN>` zero-padded to 3 digits (GitHub's sequential issue counter).
- `-<type>` optional single-letter type tag (see below).
- `_<snake_slug>` lowercase descriptive slug in snake_case.

Dropping the `m<NN>-` prefix for unmilestoned issues lets you visually distinguish triaged work from untriaged in a branch list.

### Type letters

| Letter | Meaning |
|---|---|
| `b` | Bug fix |
| `f` | Feature |
| `d` | Docs |
| `r` | Refactor |
| `t` | Test |
| `s` | Story (prose) |

Omit the letter if the slug already conveys intent (e.g. slug starts with `fix_` or `refactor_`). When omitted, drop the dash before the underscore:

```
m04-i049-b_pr_cleanup           # type present
m04-i049_fix_pr_cleanup         # type omitted, intent in slug
```

### Examples

**Milestoned:**

```
m04-i042-f_selengrad_arc_mechanics
m04-i042-s_selengrad_arc_prose
m05-i041-f_perception_overlay
m05-i041-s_perception_variants_morale
```

**Unmilestoned:**

```
i052-d_adopt_naming_conventions
i180-b_fix_url_parsing_in_runner
```

### Multiple PRs against one issue

When iterating on the same issue, append a sequence letter after the type:

```
m04-i136-b_tasks_staying_running      # first attempt
m04-i136-b2_tasks_staying_running_v2  # follow-up fix
```

### Long-lived branches (exceptions)

- `main`, `develop` — never renamed, no prefix
- `feature/m<NN>_<slug>` — milestone feature branches that span many issues
- `release/v<N>` — release candidate for version `v<N>`
- `hotfix/<slug>` — emergency fix branched from a `main` tag

## Pull requests

- **Single-issue PR**: title matches the issue it closes.
- **Multi-issue PR**: summary title covering the shared scope. Body includes `Closes #A, #B, #C`.
- **Reference other issues in the subject line** using bare `#N` (no brackets or parens). In bodies, `(#N)` for tangential references is fine.

## Commits

Merge strategy is merge-commit for feature branches into `develop`, squash-merge for release PRs into `main`. See [dev-workflow.md](dev-workflow.md#release-workflow) for rationale. Individual commits on feature branches stay visible in `develop`'s history and need their own conventions.

- **Commits within a PR branch**: imperative, sentence case, 70-char subject cap. Body explains *why*, not *what*.
- **Merge commits**: auto-generated by GitHub. The PR title carries the semantic meaning; do not fuss over the merge-commit message.
- **Footer**: agent-authored commits include the `Co-Authored-By` line.

## Every PR branch has a filing issue

No exceptions. Even one-line typo fixes get a one-line issue. Rationale: the "why" of any change belongs in an issue body, not a PR description. Branch names encode the issue number (`i<NNN>`), which makes history self-describing. Cost is about ten seconds per issue.

This replaces the earlier ad-hoc pattern of `docs/<slug>` and `feature/<slug>` floating branches.

## References inside titles and bodies

- `#N` for issues and PRs (GitHub auto-links).
- `m<N>` for milestones (e.g., "tagged for m4 hardening").
- `v<N>` for releases and tags (e.g., "shipped in v0.1.0").
- Do not wrap references in brackets or parens in subject lines. `(#N)` is fine in bodies.

## Project-specific deviation from agent-lab

The agent-lab spec says "merge-commit-everywhere; squash is never used." This project keeps squash-merge for release PRs (`develop` → `main`) so that `main`'s history stays one commit per release tag. Feature PRs (`feature-branch` → `develop`) use merge commits per the agent-lab spec.

The reason is graph readability on `main`: when debugging a regression found in production, a single commit per version makes `git log main` and `git bisect` across releases immediate. Feature-branch detail is preserved in `develop`'s history.

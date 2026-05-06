# Dev workflow

How this project moves code from an idea to a stable release. See [naming.md](naming.md) for the full naming spec (branches, issues, PRs, commits, milestones, versions).

## Branch model

- **`main`** holds stable releases only. Nothing merges into `main` except a release PR from `develop`. Tagged with semver. Linear history required.
- **`develop`** is the integration branch and the default PR target. CI must pass before anything merges.
- **Feature branches** follow [naming.md](naming.md#branch-names): `m<NN>-i<NNN>-<type>_<snake_slug>` for milestoned work, `i<NNN>-<type>_<snake_slug>` for unmilestoned. Every branch has a filing issue.

## Feature PR workflow

1. Branch from `develop`.
2. Commit early and often. Keep commits scoped.
3. Before pushing, run the three local checks:
   - `npm run build:story`
   - `npx playwright test`
   - `.venv/bin/pytest tests/`
4. Push and open a PR against `develop`.
5. CI runs `build-and-test`. It must pass before merge.
6. Merge using **Create a merge commit** so the feature's individual commits stay visible in develop's history.
7. Delete the feature branch.

## Release workflow

Before opening the release PR, **run both playtests** end-to-end and triage anything filed. Each one catches a different bug class:

```
set -a && . ./.env.playtest && set +a

# Text-only — gameplay, parser, story bugs (drives Glulx via MCP)
.venv/bin/python3 scripts/playtest.py --max-turns 100 --file-bugs

# UI-only — rendering, layout, state-display bugs (drives Chromium)
node scripts/playtest-with-ui.mjs --max-turns 60 --file-bugs
```

`--file-bugs` is opt-in on both — without it the harnesses still run and save evidence locally but don't open GitHub issues. CI runs them on a schedule (`.github/workflows/playtest.yml`) with filing enabled, so review whatever's been filed under `gh issue list --label playtest` since the last release.

Triage what comes back:

- **Real bug, severe / moderate** → fix or hotfix before cutting the release.
- **Real bug, minor / cosmetic** → file a follow-up issue, link from release notes, ship anyway if the maintainer is OK with it.
- **Not a bug** → close the auto-filed issue with a comment explaining why; consider whether the system prompt needs another guardrail.

Then proceed with the release:

1. When `develop` has landed a shippable body of work AND the playtest pass above is clean (or its findings have been triaged), open a release PR from `develop` to `main` titled `Release vX.Y.Z`.
2. Wait for CI green on the release PR.
3. Merge with **Squash and merge** so `main` stays one commit per release tag.
4. Locally, pull `main`, then tag the merge commit: `git tag -a vX.Y.Z -m "..." && git push origin vX.Y.Z`.
5. Create a GitHub release from the tag with release notes. If the playtest filed any deferred bugs, link them in the "Known issues" section of the notes.

Note: feature PRs into `develop` use merge commits (to preserve feature history), but release PRs into `main` use squash merges (to keep `main` linear and one-commit-per-tag). This is a deliberate deviation from a pure merge-commit-everywhere flow. See [naming.md](naming.md#project-specific-deviation-from-agent-lab).

## Hotfix workflow

When a bug hits `main` that cannot wait for the next release:

1. Branch from `main`: `git checkout -b hotfix/<slug> main`.
2. Fix. Test. PR into `main`. Merge.
3. Tag a patch version: `v0.1.1`, `v0.1.2`, etc.
4. Open a second PR from the hotfix branch into `develop` so the fix lands in integration too.

## Playtesting policy

For any change to `game/inform/Source/story.ni` or any runtime code, run a scripted playtest before merge. The minimum meaningful playtest is:

```
npm run build:story
npx playwright test tests/e2e/canonical-arc.spec.ts
```

`canonical-arc.spec.ts` runs the A → B1 → C1 playthrough and asserts the load-bearing beats. For larger changes, run the full suite (`npx playwright test` and `.venv/bin/pytest tests/`).

Admin-only changes (PR cleanup, branch protection, docs that do not affect runtime) can skip the local tests. They still need CI green before merging.

## Branch protection (currently configured)

Set via the GitHub API and visible through:

```
gh api repos/seith-miller/text-adventure/branches/<branch>/protection
```

**`develop`:**
- Require PR
- Require `build-and-test` status check (strict: branch must be up to date with base)

**`main`:**
- Require PR
- Require `build-and-test` status check (strict)
- Require linear history

Neither branch requires reviews, because this project has one maintainer. When that changes, raise the required-approving-review-count.

## Versioning

Semver. The first stable is `v0.1.0`. Minor bumps for feature work on `develop` that lands to `main`. Patch bumps for hotfixes.

The game is pre-1.0 until a full five-act arc is playable end to end (milestone [m4](https://github.com/seith-miller/text-adventure/milestone/4)).

# PAF Bootstrap Runbook — Tomorrow Start

**Revision:** 9  
**Purpose:** start autonomous coding without repeating the task-identity, validation, task-review, monitoring, prerequisite, and partial-work mistakes already observed.

## 0. Operating rule

Do not modify bootstrap scripts, architecture files, campaign configuration, or installed commands while a PAF generation, task-review, implementation, or exact-head-review process is active.

```bash
pgrep -af \
  '[p]af-bootstrap-loop-v9|[p]af-cline-next-task|[p]af-cline-task-review|[p]af-cline-cycle|[c]line'
```

Record the current state before doing anything else:

```bash
cd /workspaces/PandA-bambu
paf-cline-campaign status || true
git status --short
git branch --show-current
git rev-parse HEAD
```

## 1. Preserve current BS-010 work when necessary

When the process has stopped but the current checkout contains useful uncommitted BS-010 changes, preserve them outside the repository before changing bases:

```bash
RECOVERY="$HOME/.local/state/paf-manual-recovery/BS-010-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$RECOVERY"

git diff --binary > "$RECOVERY/tracked.patch"
git diff --cached --binary > "$RECOVERY/index.patch"
git ls-files --others --exclude-standard -z | \
  tar --null -T - -czf "$RECOVERY/untracked-files.tar.gz"
git status --short > "$RECOVERY/status.txt"
git rev-parse HEAD > "$RECOVERY/base-sha.txt"
git branch --show-current > "$RECOVERY/branch.txt"

printf 'Recovery bundle: %s\n' "$RECOVERY"
```

This is preservation, not automatic compatibility approval. Do not replay it onto a changed base without review.

## 2. Unpack the revision-9 pack

```bash
rm -rf /tmp/paf-v9
mkdir -p /tmp/paf-v9
unzip -q /path/to/paf-v9-tomorrow-start.zip -d /tmp/paf-v9
PACK=/tmp/paf-v9/paf-v9-tomorrow-start
```

Read first:

```bash
sed -n '1,240p' "$PACK/START-HERE.md"
sed -n '1,260p' "$PACK/architecture/paf-bootstrap-correction-matrix-v9.md"
```

## 3. Diagnose the current bootstrap before modifying it

The pack's doctor can inspect the repository before installation:

```bash
python3 "$PACK/bootstrap/payload/tools/paf-bootstrap/paf-bootstrap-doctor-v9" \
  --repo /workspaces/PandA-bambu || true
```

Expected failures before installation include missing structured validation, missing wrapper/doctor, stale installed copies, or missing task-review support. Record the output.

## 4. Repair the bootstrap in a separate worktree

Use a worktree so a preserved dirty BS-010 checkout is not disturbed.

```bash
cd /workspaces/PandA-bambu
git fetch origin

WT="$HOME/.local/share/paf/worktrees/paf-v9-integrity"
mkdir -p "$(dirname "$WT")"

# Remove this worktree only when it is an old clean worktree from a previous attempt.
git worktree list

git worktree add \
  -b bootstrap/paf-v9-integrity \
  "$WT" \
  origin/dev/panda
```

Apply the fail-closed installer:

```bash
python3 "$PACK/bootstrap/apply-paf-bootstrap-v9.py" \
  --repo "$WT"
```

Inspect and validate:

```bash
cd "$WT"
git status --short
git diff --check
git diff -- tools/paf-bootstrap

paf-bootstrap-doctor-v9 --repo "$WT" --full
```

The full doctor must report zero failures. It exercises the real cycle validation path with a fake Cline runtime and a real Node `.mjs` verifier.

Commit and publish the repair branch:

```bash
git add tools/paf-bootstrap
git diff --cached --check
git commit -m "fix: harden PAF bootstrap identity and validation path"
git push -u origin bootstrap/paf-v9-integrity
```

Review and merge this PR manually. Do not let the bootstrap merge its own repair.

## 5. Reinstall only the merged repair

After the repair PR is merged:

```bash
cd "$WT"
git fetch origin
git switch --detach origin/dev/panda

python3 "$PACK/bootstrap/apply-paf-bootstrap-v9.py" \
  --repo "$WT" \
  --skip-tests

paf-bootstrap-doctor-v9 --repo "$WT" --full
```

This makes the installed `~/.local/bin` copies match the merged base rather than an unmerged feature commit.

## 6. Merge the final architecture and decision set

Create a separate architecture worktree/branch from the repaired base:

```bash
cd /workspaces/PandA-bambu
git fetch origin

AWT="$HOME/.local/share/paf/worktrees/paf-v9-architecture"
git worktree add \
  -b architecture/paf-v9-final \
  "$AWT" \
  origin/dev/panda

cd "$AWT"
mkdir -p documentation/evolvehls/paf-v9 config/paf-v9
cp -a "$PACK/architecture/." documentation/evolvehls/paf-v9/
cp "$PACK/config/paf-decisions-v9.json" config/paf-v9/
cp "$PACK/config/paf-bootstrap-campaign-v9.json" config/paf-v9/
cp -a "$PACK/tasks" documentation/evolvehls/paf-v9/
cp -a "$PACK/prompts" documentation/evolvehls/paf-v9/

python3 -m json.tool config/paf-v9/paf-decisions-v9.json >/dev/null
python3 -m json.tool config/paf-v9/paf-bootstrap-campaign-v9.json >/dev/null
git add documentation/evolvehls/paf-v9 config/paf-v9
git diff --cached --check
git commit -m "docs: adopt final PAF revision 9 architecture"
git push -u origin architecture/paf-v9-final
```

Review and merge manually. The merged architecture SHA and `PAF-v9` decision set become authoritative for newly generated tasks.

## 7. Decide the disposition of the existing BS-010

Run from the original checkout after both PRs are merged:

```bash
cd /workspaces/PandA-bambu
paf-bootstrap-loop-v9 status
git status --short
```

### A. BS-010 completed and exact-head review approved

Merge its PR manually, then run:

```bash
paf-bootstrap-loop-v9 reconcile
paf-bootstrap-loop-v9 status
```

### B. BS-010 was blocked because architecture decisions were unresolved

The old task is bound to the old base and cannot become valid merely because new documents now exist.

```bash
paf-bootstrap-loop-v9 supersede BS-010 \
  --reason "Superseded after authoritative PAF revision 9 decision closure"
```

Regenerate after campaign migration in section 8.

### C. BS-010 contains useful partial implementation

Keep its branch and recovery bundle. Do not use generic `retry` after the base or task contract changes. Either continue the exact old task/branch before changing base, or preserve it for compatibility review and regenerate. Automatic compatibility-aware recovery is not implemented until BS-018.

### D. Campaign state is inconsistent or uncertain

Do not use `operator-override-complete`. Save:

```bash
paf-bootstrap-loop-v9 status
find "$HOME/.local/state/paf-bootstrap" -maxdepth 3 -type f -print
find "$HOME/.local/share/paf/tasks" -maxdepth 4 -type f -print
```

Then reconcile exact state and repository history before generating another task.

## 8. Migrate the authoritative campaign config between tasks

Do this only when no task is active.

Create a reviewed config branch/worktree from the architecture-merged base:

```bash
cd /workspaces/PandA-bambu
git fetch origin

CWT="$HOME/.local/share/paf/worktrees/paf-v9-campaign"
git worktree add \
  -b bootstrap/paf-v9-campaign \
  "$CWT" \
  origin/dev/panda

cd "$CWT"
CURRENT=config/paf-bootstrap-campaign.json
cp "$CURRENT" "$CURRENT.before-v9.$(date -u +%Y%m%dT%H%M%SZ)"

python3 "$PACK/bootstrap/merge_campaign_v9.py" \
  --current "$CURRENT" \
  --revision "$PACK/config/paf-bootstrap-campaign-v9.json" \
  --output /tmp/paf-bootstrap-campaign-v9.json

python3 -m json.tool /tmp/paf-bootstrap-campaign-v9.json >/dev/null
diff -u "$CURRENT" /tmp/paf-bootstrap-campaign-v9.json || true
```

Copy only after reviewing the diff:

```bash
cp /tmp/paf-bootstrap-campaign-v9.json "$CURRENT"
python3 -m json.tool "$CURRENT" >/dev/null
git add "$CURRENT"
git diff --cached --check
git commit -m "chore: adopt PAF revision 9 bootstrap backlog"
git push -u origin bootstrap/paf-v9-campaign
```

Review and merge manually. The revision-9 campaign uses the actual revision-3 `backlog` schema; it does not use the incompatible revision-8 `items` format.

## 9. Start or resume autonomous coding

After bootstrap repair, architecture, and campaign config are merged, update the original checkout only when its work is safely resolved:

```bash
cd /workspaces/PandA-bambu
git fetch origin
git switch dev/panda
git pull --ff-only origin dev/panda

paf-bootstrap-doctor-v9 \
  --repo /workspaces/PandA-bambu \
  --full

paf-bootstrap-loop-v9 status
```

When BS-010 must be regenerated:

```bash
paf-bootstrap-loop-v9 next --backlog-id BS-010
```

In a second terminal:

```bash
cd /workspaces/PandA-bambu
paf-bootstrap-loop-v9 watch
```

After automatic task review completes:

```bash
paf-bootstrap-loop-v9 task-review
paf-bootstrap-loop-v9 status
```

Authorize only when status is `reviewed-approved`:

```bash
paf-bootstrap-loop-v9 authorize
paf-bootstrap-loop-v9 run
```

Monitor again:

```bash
paf-bootstrap-loop-v9 watch
```

At termination:

```bash
paf-bootstrap-loop-v9 status
git status --short
```

## 10. Correct post-BS-010 sequence

```text
BS-012 — internalize active phase/run identity and reliable monitoring
BS-014 — internalize typed ValidationActivity and audit receipts
BS-016 — decision prerequisite preflight and explicit block/recovery operations
BS-018 — PartialWorkManifest and compatibility-aware recovery
BS-020 — minimal kernel contract, event, relation, and error envelope
```

This order is deliberate:

- monitoring and run identity must be reliable before more autonomy;
- production validation must be typed before it becomes a reusable contract;
- unresolved prerequisites must be stopped before implementation;
- partial recovery follows a normative block/action model;
- only then should the bootstrap begin emitting reusable kernel records.

## 11. Per-task operator loop

```bash
cd /workspaces/PandA-bambu
paf-bootstrap-loop-v9 doctor
paf-bootstrap-loop-v9 status
paf-bootstrap-loop-v9 next --backlog-id <TASK_ID>
paf-bootstrap-loop-v9 watch
paf-bootstrap-loop-v9 task-review
paf-bootstrap-loop-v9 authorize
paf-bootstrap-loop-v9 run
paf-bootstrap-loop-v9 watch
paf-bootstrap-loop-v9 status
git status --short
```

Each task receives a separate generation, independent task review, authorization, implementation, production validation, exact-head review, and human merge decision.

## 12. Completion rule

A bootstrap coding task is complete only when:

1. controller-owned identity and exact base are recorded;
2. the contract passed independent task review;
3. all validation ran through the production campaign/cycle path;
4. exact-head review assessed every criterion;
5. evidence records actual executable, argv, authorization rule, artifacts, timing, and exit status;
6. limitations and unresolved risks are explicit;
7. publication and merge remain human-controlled.

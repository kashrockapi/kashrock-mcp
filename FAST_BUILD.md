# Fast Build System

Every task in this repo follows this system. The goal: finish work as fast as possible, with proof.
It governs task flow (lanes, stops, proof). This repo's own rules in CLAUDE.md / AGENTS.md
(IDs, copy rules, release ownership, deploy permission) always still apply.

## Core rules

1. Proof before work. Name the exact check (command + expected result) before changing code.
   If the prompt doesn't name one, define it and include it in your first post.
2. Pick the lane first (below).
3. Evidence, not claims. Paste the command you ran and its output. "Tests pass" is not proof.
4. One task at a time. Real bugs you find in the same path, contract or call chain get fixed too
   (root cause, and say so). Anything else (features, refactors, unrelated areas): list it, don't touch it.
5. Stop only at the gates your lane defines, or when blocked.
6. Timebox: 15 min to reproduce (fast lane), 30 min for discover + blueprint (full lane).
   Over the limit: stop and post what's blocking.
7. Two failed attempts on the same step: stop and post what you learned. Don't keep trying.
8. Root cause only. No workarounds, no suppressed errors, no bandaids.
9. Ship small: one change, one release.
10. Close on proof. Final post = root cause, files changed, proof output, start and finish time. Then stop.

## Lane picker

Full lane if ANY of these is true. Otherwise fast lane.
- Cause unknown or intermittent
- New feature, multi-area change, refactor, or more than ~3 files
- Schema change, migration, index/table drop, data delete
- Billing, payments, auth, secrets
- Public API contract change (shape, params, error codes, versions)
- Can't be cleanly reverted

## Fast lane (one stop: proof)

1. Reproduce: run the check, confirm it fails, paste output. If it doesn't fail, stop and post what you see.
2. Find the root cause.
3. Make the smallest fix that removes the cause, inside the task's area.
4. Re-run the check and the existing tests for touched files. Paste output.
5. Ship (see Shipping). Where you ship, re-run the check against prod and paste output.
6. Final post, then stop.

## Full lane (two stops: blueprint, proof)

PHASE 1: DISCOVER + BLUEPRINT (read-only)
Use a subagent for wide code searches. Verify live, don't assume. Post:
  a. What's true now, with evidence
  b. Root cause or approach
  c. Files and changes
  d. Out of scope
  e. Risks and rollback
  f. DONE checks: exact commands + expected results, including the prod check
  g. Anything that needs approval, named one by one
STOP. Wait for GREENLIGHT.

PHASE 2: BUILD + SHIP (no more stops unless blocked or going off-blueprint)
1. Write the failing check first where possible, then make it pass.
2. Run every DONE check. Paste output.
3. Have a subagent review the diff against the blueprint in fresh context.
   Fix correctness gaps only; skip style and nice-to-haves.
4. Ship (see Shipping). Where you ship, re-run the DONE checks against prod and paste output.
5. Final post, then stop.

## Shipping

"Ship" means this repo's release path, as its CLAUDE.md / AGENTS.md defines it.
- If the repo names a release owner and you are not it, or says never deploy unless told:
  push your branch, send the ready note the repo asks for, and stop. That is done for your session.
- Never deploy, publish, merge to main, or write prod data unless the repo rules or the user allow it.
- If the repo defines no release path: find how it deploys (scripts, CI, README), name it in your post,
  and ask before the first deploy.

## Proof ladder

- Every task: run the check and paste output; re-run it against prod after release.
- Full lane, or a run nobody is watching: fresh-context subagent review of the diff.
- Unattended runs: a Stop hook or /goal condition blocks finishing until the check passes.
- If a change can't be checked, it doesn't ship. Add the check first.

## Session hygiene

- New task = new session. Don't carry a finished task's history into the next one.
- Wide code searches go to a subagent so the main context stays clean.
- Point at things: name the file, the symptom, an existing pattern to copy.
- Keep CLAUDE.md / AGENTS.md short. Rules that must run every time belong in hooks.

## Speed log

Every final post ends with one line:
`LOG: <date> | <task> | <fast|full> | sent <time> | finished <time> | lead time <min> | slowest step <step>`

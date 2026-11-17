# Contributing to Wilson

## Branch and commit conventions

- One branch per change; never commit to `main` directly.
- Commit format: `type: short imperative description`.
- Merge method: `gh pr merge <n> --merge --delete-branch`.
  Merge commits required. **Squash and rebase are forbidden repo-wide.**
  (Three pre-policy PRs merged 16-17 Nov 26 used squash; noted here so the
  history anomaly is documented rather than mysterious.)

## Merge authority

Default: **Chris merges.** An agent may self-merge its own PR only when ALL
of the following hold (policy inherited from Nautilus, operator-approved
24 Oct 26, aligned to Wilson 17 Nov 26):

1. **Required checks green, read fresh at head.** `gh pr checks <n>` run at
   merge time — not a remembered state. Required lanes: `test` matrix and
   `static-analysis`.
2. **Revert-only-revertable.** A merge that a plain `git revert` fully undoes.
   Not eligible: data-shape changes, migrations, dependency-version pinning
   that changes the resolved install, or anything requiring a paired action
   to back out.
3. **The diff edits no test assertions to make itself pass.** author=reviewer
   is a known failure mode; review the true diff
   (`git diff origin/main...branch`) and treat any test-assertion change as
   needing human review.
4. **Off protected surfaces:** security-sensitive code paths, credential
   handling, CI workflow files, and packaging/installer definitions. These
   are Chris-merge only, even when green.

Code PRs get an adversarial review pass on a resident local model before
self-merge, with findings verified against real source before acting on them.

A regression found on `main`: revert first, investigate after.

## Quality gates (enforced in CI)

- `test` — pytest, headless (fixtures only; live-API tests are token-gated
  and skipped without a token), Python 3.12 and 3.13 matrix.
- `static-analysis` — Ruff baseline reporting plus a changed-lines ratchet:
  new/modified lines introduce no new findings (Nautilus `NAT-475` shape).
- `security` — Bandit HIGH-severity gate on shipped modules plus pip-audit
  on the pinned dependency set.

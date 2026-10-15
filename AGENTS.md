## Fast Build System (mandatory)

Every task follows FAST_BUILD.md in the repo root. Read it before starting any work.
It sets the lane (fast or full), the proof required, and when to stop.
Where an older workflow or phase protocol in this repo conflicts with it on task flow,
FAST_BUILD.md wins. The repo rules here (IDs, copy, release ownership, deploy permission) still apply.

## Repo rules

- Customer-facing text never names or reveals an upstream data source: README, docs, examples,
  error messages, package metadata, and anything published.
- No secrets or API keys in code, examples, commits, or output.
- Never deploy or publish (npm, PyPI, registries, Vercel) unless the user explicitly tells you to.

# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

**This repo uses the multi-context layout** (monorepo: backend, mini-program, web admin).

## Before exploring, read these

1. **Terminology (glossary only)**
   - [`CONTEXT-MAP.md`](../../CONTEXT-MAP.md) at the repo root
   - Relevant [`src/<context>/CONTEXT.md`](../../src/inventory/CONTEXT.md) per bounded context
   - Do **not** treat CONTEXT files as specs — they are ubiquitous language only.

2. **Module requirements (SRS)**
   - [`docs/domains/README.md`](../domains/README.md) — pick overview + 1–2 context modules for the task
   - [`docs/domains/platform.md`](../domains/platform.md) for IAM / audit (not a bounded context)

3. **Implementation design**
   - [`docs/dev/README.md`](../dev/README.md) — architecture, API, data model
   - [`docs/dev/backend-status.md`](../dev/backend-status.md) — living backend completion notes

4. **Decisions**
   - [`docs/adr/`](../adr/) — system-wide ADRs
   - Optional `src/<context>/docs/adr/` for context-scoped decisions (create lazily)

5. **Task specs**
   - GitHub Issues (`to-spec`) — single feature / change specs, not module SRS

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill creates CONTEXT and ADRs lazily when terms or decisions actually get resolved.

## File structure

```
/
├── CONTEXT-MAP.md
├── docs/
│   ├── domains/          ← module SRS (requirements)
│   ├── dev/              ← development design (SDD)
│   ├── adr/
│   └── agents/
└── src/
    ├── catalog/
    │   └── CONTEXT.md    ← glossary only
    ├── inventory/
    │   └── CONTEXT.md
    └── …
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in the relevant `src/*/CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders) — but worth reopening because…_

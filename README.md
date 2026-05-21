# Solana Audit Ramp-up for Solidity Auditors

A compact, evidence-backed ramp-up site for auditors who already know Ethereum/Solidity and need to review Solana/Anchor programs.

## What is inside

- `site/index.html` — polished static website with learning path, account-validation matrix, filters, incident mapping, and audit-report findings.
- `data/patterns.json` — structured vulnerability knowledge base (37 patterns).
- `data/incidents.json` — real Solana incidents mapped to patterns.
- `data/audit-findings.json` — public audit report findings mapped to patterns.
- `docs/core-solana-security.md` — Solana-specific audit notes.
- `docs/anchor-security.md` — Anchor-specific pitfalls and mitigations.
- `docs/audit-workflow.md` — practical audit workflow/checklist.
- `docs/cctp-v2.md` and `docs/kamino-klend-domain.md` — CCTP V2 and Kamino/KLend protocol primers.
- `docs/incidents.md` and `docs/audit-report-patterns.md` — evidence mapping.
- `docs/references.md` — source list and caveats.

## Solana Audit Primer skill

`.claude/skills/solana-audit-primer/` is a self-contained [Claude Code skill](https://docs.claude.com/en/docs/claude-code/skills) that turns the pattern knowledge base into an agent-discoverable, two-layer catalog for threat-modeling and auditing Solana/Anchor programs.

- `SKILL.md` — routing layer. A workflow, an always-check core set, a **code-signal index** (grep token → patterns to load), per-protocol playbooks, and the full catalog. An agent reads this first and only pulls the detail pages it needs.
- `threat-model.md` — entry scaffold (assets, actors, trust boundaries, per-instruction validation matrix, adversarial questions) that feeds into the catalog.
- `references/<id>.md` — one detail page per pattern: EVM contrast, bad/good code, audit checks, and the real incidents / audit findings mapped to it.

### Using it

It is fully portable. Copy the folder and Claude Code auto-discovers it via the frontmatter:

```bash
# this project only
cp -r .claude/skills/solana-audit-primer /path/to/target-repo/.claude/skills/
# or all your projects
cp -r .claude/skills/solana-audit-primer ~/.claude/skills/
```

All links inside the folder are relative; the only external pointers are absolute URLs, so nothing dangles after a copy. Copies are snapshots — re-copy after regenerating to update them.

### Regenerating it

The skill is **generated** from the JSON knowledge base — do not hand-edit files under `.claude/skills/`. The source of truth for triggers is the `TRIGGERS` map in the generator plus the JSON content; the generator also injects `triggers` back into `data/patterns.json`.

```bash
python3 scripts/build_primer_skill.py
```

Edit `data/patterns.json` (pattern content), `data/incidents.json` / `data/audit-findings.json` (mappings), or the `TRIGGERS` / `PLAYBOOKS` / `CORE_ALWAYS` constants in `scripts/build_primer_skill.py`, then re-run.

## How to view

```bash
git clone https://github.com/boolafish/solana-audit-rampup.git
cd solana-audit-rampup
python3 -m http.server 8899 --directory site
# open http://127.0.0.1:8899
```

## Accuracy stance

This is an auditor ramp-up guide, not a substitute for reading the target code and official docs. Claims are phrased conservatively: Solana has no globally gossiped Ethereum-style public mempool, but MEV/front-running/order games still exist; rent is usually an account-lifecycle/realloc/close risk rather than a standalone exploit class; Anchor/runtime behavior can be version-sensitive.

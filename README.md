# Solana Audit Ramp-up for Solidity Auditors

A compact, evidence-backed ramp-up site for auditors who already know Ethereum/Solidity and need to review Solana/Anchor programs.

## What is inside

- `site/index.html` — polished static website with filters and bad/good patterns.
- `data/patterns.json` — structured vulnerability knowledge base.
- `docs/core-solana-security.md` — Solana-specific audit notes.
- `docs/anchor-security.md` — Anchor-specific pitfalls and mitigations.
- `docs/references.md` — source list and incident/audit links.

## How to view

```bash
cd /Users/bot.ai/solana-audit-rampup
/usr/bin/python3 -m http.server 8899 --directory site
# open http://127.0.0.1:8899
```

## Accuracy stance

This is an auditor ramp-up guide, not a substitute for reading the target code and official docs. Claims are phrased conservatively: Solana has no Ethereum-style public in-protocol mempool, but MEV/front-running/order games still exist; rent is usually an account-lifecycle/realloc/close risk rather than a standalone exploit class.

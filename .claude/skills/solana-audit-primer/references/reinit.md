# Reinitialization / initialization confusion

- **Pattern ID:** `reinit`
- **Category:** Lifecycle / Rent  |  **Severity:** Critical

## Triggers — load this page when you see these

**Code signals (grep the target):** `init_if_needed`, `#[account(init`, `initialize`, `is_initialized`

**Protocol types:** any stateful program, proxy-like config

**Concepts:** initialize callable twice; close then recreate to reset authority; init_if_needed resetting critical fields

## Why this differs from Solidity/EVM

Similar to unprotected initializer bugs in proxies, but with explicit account allocation/ownership/state flags.

Accounts can be created, assigned, funded, resized, closed, or reused. `init_if_needed` can hide reinit paths if the handler resets critical fields.

## Bad pattern

`initialize` overwrites admin/config on an already initialized account; `init_if_needed` then unconditionally sets authority.

## Good pattern

Prefer separate `init`; store and check initialized/version flags; never reset authority/config on reuse; test close→recreate and same-transaction flows.

## Audit checks

- [ ] Can initialize be called twice?
- [ ] Does `init_if_needed` change existing critical fields?
- [ ] Can a closed/drained account be revived and reused?

## Real incidents mapped to this pattern

- **Nomad (2022)** — ~$190M. Bridge replica accepted messages against a zero trusted root.

## Related patterns

- [Missing account relationship checks](relationship-checks.md) — `relationship-checks`
- [Instruction introspection / signature verification misuse](signature-introspection.md) — `signature-introspection`
- [Account close, revival, and stale data](close-revival.md) — `close-revival`
- [Rent-exemption and realloc/storage resizing edge cases](realloc-rent.md) — `realloc-rent`

## References

- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/reinitialization-attacks.md
- https://www.anchor-lang.com/docs/references/account-constraints

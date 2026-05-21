# `init_if_needed` resets existing state

- **Pattern ID:** `anchor-init-if-needed`
- **Category:** Anchor  |  **Severity:** Critical

## Triggers — load this page when you see these

**Code signals (grep the target):** `init_if_needed`, `#[account(init_if_needed`

**Protocol types:** any Anchor stateful program

**Concepts:** handler writes authority on every call; reinit via init_if_needed; init-if-needed feature enabled

## Why this differs from Solidity/EVM

Similar to proxy initializer callable after deployment.

Anchor’s `init_if_needed` makes account creation/use convenient but can hide reinitialization bugs if handler overwrites fields on both paths.

## Bad pattern

Use `#[account(init_if_needed,...)]` and always set `state.authority = payer.key()` or reset counters/config.

## Good pattern

Prefer separate init and use instructions. If using `init_if_needed`, gate first-time writes with initialized/version flags and never reset authority/config for existing accounts.

## Audit checks

- [ ] Is `init_if_needed` feature enabled?
- [ ] Which fields are written every call?
- [ ] Can close/recreate/reinit change authority?

## Related patterns

- [UncheckedAccount / AccountInfo used as trusted state](anchor-unchecked.md) — `anchor-unchecked`
- [Token-interface constraints not bound to intended token program](anchor-token-interface.md) — `anchor-token-interface`
- [`remaining_accounts` order/count/type assumptions](remaining-accounts.md) — `remaining-accounts`
- [Anchor 0.28 behavior differs from newer tutorials](anchor-0.28-deltas.md) — `anchor-0.28-deltas`
- [Hand-rolled `try_accounts` missing derived checks](manual-try-accounts.md) — `manual-try-accounts`

## References

- https://www.anchor-lang.com/docs/references/account-constraints
- https://docs.rs/anchor-lang/latest/anchor_lang/derive.Accounts.html
- https://github.com/coral-xyz/sealevel-attacks

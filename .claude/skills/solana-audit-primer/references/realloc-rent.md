# Rent-exemption and realloc/storage resizing edge cases

- **Pattern ID:** `realloc-rent`
- **Category:** Lifecycle / Rent  |  **Severity:** Medium

## Triggers — load this page when you see these

**Code signals (grep the target):** `realloc`, `realloc::payer`, `realloc::zero`, `Rent`, `AccountInfo::realloc`, `#[max_len`

**Protocol types:** growable accounts, dynamic lists/queues

**Concepts:** resize without funding rent; stale bytes after grow; unbounded size growth; Anchor max_len mistaken for runtime cap

## Why this differs from Solidity/EVM

Solidity storage expansion is paid by gas; Solana account data size and rent-exempt lamports are explicit state.

Growing/shrinking accounts changes required rent-exempt minimum balance and may expose stale bytes. In current Solana practice, rent usually means minimum balance for data storage, not an Ethereum-like recurring storage fee; `rent_epoch` is rarely a useful security signal without version-specific justification. Anchor `#[max_len]` sizes account space; it does not by itself cap later exact-fit reallocations.

## Bad pattern

Grow dynamic accounts without funding rent, zeroing policy, explicit runtime length caps, or checked space math; assume `#[max_len]` prevents later `realloc` growth.

## Good pattern

Fund rent deltas, use `realloc::zero` when old bytes matter, add explicit max-length constraints before growth, and test grow/shrink cycles. Treat `#[max_len]` as space metadata, not a runtime cap.

## Audit checks

- [ ] Who pays extra rent?
- [ ] Is new size bounded and computed with checked arithmetic?
- [ ] Are newly allocated bytes zeroed if read later?
- [ ] Does `#[max_len]` only size the initial account while later `realloc` paths can exceed the intended cap?

## Related patterns

- [Reinitialization / initialization confusion](reinit.md) — `reinit`
- [Account close, revival, and stale data](close-revival.md) — `close-revival`

## References

- https://solana.com/docs/core/accounts
- https://www.anchor-lang.com/docs/references/account-constraints

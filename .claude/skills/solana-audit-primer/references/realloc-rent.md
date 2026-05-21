# Rent-exemption and realloc/storage resizing edge cases

- **Pattern ID:** `realloc-rent`
- **Category:** Lifecycle / Rent  |  **Severity:** Medium

## Triggers — load this page when you see these

**Code signals (grep the target):** `realloc`, `realloc::payer`, `realloc::zero`, `Rent`, `AccountInfo::realloc`

**Protocol types:** growable accounts, dynamic lists/queues

**Concepts:** resize without funding rent; stale bytes after grow; unbounded size growth

## Why this differs from Solidity/EVM

Solidity storage expansion is paid by gas; Solana account data size and rent-exempt lamports are explicit state.

Growing/shrinking accounts changes required rent-exempt minimum balance and may expose stale bytes. In current Solana practice, rent usually means minimum balance for data storage, not an Ethereum-like recurring storage fee; `rent_epoch` is rarely a useful security signal without version-specific justification.

## Bad pattern

Manual `realloc` larger without funding rent, cap checks, or zeroing new bytes; shrink/grow causing type confusion or stale sensitive data.

## Good pattern

Use Anchor `realloc`, `realloc::payer`, `realloc::zero`; recompute rent; cap size; use checked math for space calculations.

## Audit checks

- [ ] Who pays extra rent?
- [ ] Is new size bounded and computed with checked arithmetic?
- [ ] Are newly allocated bytes zeroed if read later?

## Related patterns

- [Reinitialization / initialization confusion](reinit.md) — `reinit`
- [Account close, revival, and stale data](close-revival.md) — `close-revival`

## References

- https://solana.com/docs/core/accounts
- https://www.anchor-lang.com/docs/references/account-constraints

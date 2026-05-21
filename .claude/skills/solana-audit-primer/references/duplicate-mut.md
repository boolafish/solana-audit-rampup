# Duplicate mutable accounts / aliasing

- **Pattern ID:** `duplicate-mut`
- **Category:** Account Validation  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `#[account(mut`, `AccountInfo`, `constraint =`, `key() !=`

**Protocol types:** transfers, games, two-account swap flows

**Concepts:** same account passed for two roles; payer == recipient; user_a == user_b aliasing

## Why this differs from Solidity/EVM

Similar to passing the same address as two roles in a function that assumes distinct addresses.

The same account key can be supplied for multiple account parameters unless constrained; mutable aliases can break debit/credit or game logic.

## Bad pattern

`transfer_rewards(from, to)` assumes two accounts but attacker passes same account for both.

## Good pattern

Add explicit `a.key() != b.key()` constraints for all roles that must be distinct. Some Anchor versions/account types reject duplicate mutable accounts during validation, but do not rely on framework behavior for business-logic distinctness, especially with `UncheckedAccount`, `AccountInfo`, interface accounts, or `remaining_accounts`.

## Audit checks

- [ ] Which accounts are assumed distinct?
- [ ] Can payer==recipient, vault==user token account, user_a==user_b?
- [ ] Does Anchor typed mut duplicate protection cover this exact case?

## Related patterns

- [Sysvar spoofing](sysvar-spoof.md) — `sysvar-spoof`
- [Instruction introspection / signature verification misuse](signature-introspection.md) — `signature-introspection`
- [Instructions sysvar introspection mistakes](instructions-sysvar-introspection.md) — `instructions-sysvar-introspection`

## References

- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/duplicate-mutable-accounts.md
- https://github.com/coral-xyz/sealevel-attacks

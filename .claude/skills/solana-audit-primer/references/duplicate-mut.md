# Duplicate mutable accounts / aliasing

- **Pattern ID:** `duplicate-mut`
- **Category:** Account Validation  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `#[account(mut`, `AccountInfo`, `constraint =`, `key() !=`

**Protocol types:** transfers, games, two-account swap flows

**Concepts:** same account passed for two roles; payer == recipient; user_a == user_b aliasing; SPL self-transfer succeeds without moving value

## Why this differs from Solidity/EVM

Similar to passing the same address as two roles in a function that assumes distinct addresses.

The same account key can be supplied for multiple account parameters unless constrained; mutable aliases can break debit/credit or game logic. SPL token self-transfers can validate and return success without moving value, so distinctness can be economically relevant even when account constraints pass.

## Bad pattern

Pass the same mutable account for two logical roles such as payer/recipient, input/output vault, depositor/custody beneficiary, or debit/credit token account.

## Good pattern

Reject aliasing with explicit key inequality for roles that must be economically distinct, and assert balance deltas in tests for transfers that are supposed to move value.

## Audit checks

- [ ] Which accounts are assumed distinct?
- [ ] Can payer==recipient, vault==user token account, user_a==user_b?
- [ ] Does Anchor typed mut duplicate protection cover this exact case?
- [ ] Can an SPL token transfer be a same-account self-transfer that succeeds without moving value?
- [ ] Do later mint/burn/accounting steps rely on a prior transfer having changed custody balances?

## Related patterns

- [Sysvar spoofing](sysvar-spoof.md) — `sysvar-spoof`
- [Instruction introspection / signature verification misuse](signature-introspection.md) — `signature-introspection`
- [Instructions sysvar introspection mistakes](instructions-sysvar-introspection.md) — `instructions-sysvar-introspection`

## References

- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/duplicate-mutable-accounts.md
- https://github.com/coral-xyz/sealevel-attacks

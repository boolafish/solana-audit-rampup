# Native SOL lamport accounting bugs

- **Pattern ID:** `native-sol-lamports`
- **Category:** Math / Accounting  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `lamports`, `try_borrow_mut_lamports`, `add_lamports`, `sub_lamports`, `system_program::transfer`, `WSOL`

**Protocol types:** native SOL vaults, staking, escrow

**Concepts:** manual lamport mutation before checks; rent-exempt floor ignored; native SOL vs wrapped SOL confusion

## Why this differs from Solidity/EVM

Similar to mixing ETH transfers with ERC20 accounting, but with rent floors and owner/runtime lamport mutation rules.

Native SOL lamports are not SPL tokens. Direct lamport mutation has owner/writable/runtime constraints, rent-exempt floors, close/refund effects, and wrapped SOL edge cases.

## Bad pattern

Manually subtract lamports from a vault before full checks, ignore rent floor, or confuse wrapped SOL token accounts with native SOL.

- *Native:* `**user.lamports += amount; **vault.lamports -= amount;` without rent/PDA/owner checks.
- *Anchor:* `vault.sub_lamports(amount)?; user.add_lamports(amount)?;` without validating vault seeds/rent/accounting.

## Good pattern

Validate vault PDA/owner, writable flags, rent floor, accounting state, checked arithmetic, and post-transfer invariants; use System Program transfer when appropriate for signer-owned accounts.

- *Native:* Check vault PDA/owner, min rent balance, checked subtraction, then mutate lamports and update state atomically.
- *Anchor:* Use PDA constraints on vault, `SystemAccount` recipient, rent floor checks, and post-transfer invariant checks.

## Audit checks

- [ ] Is the debited account owned by this program or otherwise authorized?
- [ ] Will the remaining balance violate rent-exemption or protocol invariant?
- [ ] Are native SOL and wrapped SOL handled distinctly?

## Related patterns

- [Integer overflow, precision, rounding, decimal mismatch](math.md) — `math`

## References

- https://solana.com/docs/core/accounts
- https://docs.rs/anchor-lang/latest/anchor_lang/
- https://neodyme.io/en/blog/solana_common_pitfalls/

# CPI account substitution / confused deputy

- **Pattern ID:** `cpi-substitution`
- **Category:** CPI  |  **Severity:** Critical

## Triggers — load this page when you see these

**Code signals (grep the target):** `invoke_signed`, `CpiContext`, `with_signer`, `token::transfer`, `AccountMeta`, `delegated_amount`, `approve_checked`

**Protocol types:** vaults, lending, router, any PDA-signed CPI, PDA token delegates

**Concepts:** program signs over attacker-chosen accounts; confused deputy; callee accounts not validated before CPI; PDA delegate approval/allowance is an off-chain setup dependency

## Why this differs from Solidity/EVM

Like approving/transferring from an unintended vault because callee accounts were attacker-selected.

Even when CPI program ID is correct, the caller supplies all callee accounts. Your program may sign with a PDA over attacker-chosen accounts. PDA-signed token flows may also depend on off-chain delegate approvals; those are operational trust boundaries even when account validation is correct.

## Bad pattern

Program signs SPL Token transfer from `source` to `dest` without verifying `source` is protocol vault, mint matches, and authority is the intended PDA.

## Good pattern

Before CPI, validate every account: token program, source/dest address or ATA derivation, mint, authority, PDA seeds, delegate/close authority if relevant.

## Audit checks

- [ ] Could attacker make the program sign over a different token account?
- [ ] Are CPI account metas exactly the validated accounts?
- [ ] Are post-CPI balances/invariants rechecked where needed?
- [ ] When a PDA signs as token delegate, is the delegate approval/allowance an explicit setup assumption and rechecked live before release?

## Real incidents mapped to this pattern

- **Cashio (2022)** — ~$48M. Incomplete collateral/LP/mint account validation allowed fake account chains and infinite CASH minting.

## Public audit findings mapped to this pattern

- **OpenZeppelin Sponsored CCTP Deposits from Solana Audit** (Solana CCTP periphery): Nonce PDA and rent-sponsorship flows need explicit lifecycle review; CCTP CPI boundaries require exact account and program validation

## Related patterns

- [Missing account relationship checks](relationship-checks.md) — `relationship-checks`
- [Missing owner check / spoofed account data](missing-owner.md) — `missing-owner`
- [PDA seed/bump mistakes and non-canonical bumps](pda-bump.md) — `pda-bump`
- [`remaining_accounts` order/count/type assumptions](remaining-accounts.md) — `remaining-accounts`
- [Arbitrary CPI / missing program ID check](arbitrary-cpi.md) — `arbitrary-cpi`
- [Stale account data after CPI / missing reload](stale-cpi-reload.md) — `stale-cpi-reload`

## References

- https://solana.com/docs/core/cpi
- https://www.anchor-lang.com/docs/references/account-constraints

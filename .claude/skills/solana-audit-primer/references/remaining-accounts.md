# `remaining_accounts` order/count/type assumptions

- **Pattern ID:** `remaining-accounts`
- **Category:** Anchor  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `remaining_accounts`, `ctx.remaining_accounts`, `next_account_info`

**Protocol types:** batch/variable-account flows, router, multi-market

**Concepts:** index position trusted as a role; no length/order check; per-account owner/type/relationship validation missing

## Why this differs from Solidity/EVM

Like accepting an arbitrary address array and assuming each index is the intended token/vault/oracle.

Anchor constraints do not apply to `remaining_accounts`. Attackers can omit, reorder, duplicate, or substitute accounts unless the handler validates them.

## Bad pattern

Iterate over `ctx.remaining_accounts` and trust index position as reward vault, user account, oracle, or market.

- *Native:* `let market = next_account_info(iter)?; let vault = next_account_info(iter)?;` with no checks.
- *Anchor:* `for acc in ctx.remaining_accounts { process(acc); }`

## Good pattern

Validate exact length/order when fixed; reject unexpected extras; for each account validate owner/program, discriminator/type, signer/writable, PDA/address, and relationships before use.

- *Native:* After each `next_account_info`, verify owner, discriminator, PDA/address, and relation to prior accounts.
- *Anchor:* Check len; for each account: owner, writable/signer flags, discriminator, PDA/address, parent relation; reject extras.

## Audit checks

- [ ] Is expected count enforced?
- [ ] Can accounts be reordered or duplicated?
- [ ] Does every remaining account get full owner/type/address/relationship validation?

## Public audit findings mapped to this pattern

- **OtterSec Token-2022 Audit** (SPL Token-2022): Incorrect account ordering; Lack of mint account verification; Missing signer checks; Unnecessary writable multisig access; Confidential-transfer validation issues
- **OtterSec Address Lookup Table Audit** (Core Solana): Indirect account loading lifecycle; Deactivation/close/reuse concerns; Authority/lifecycle edge cases
- **OpenZeppelin Sponsored CCTP Deposits from Solana Audit** (Solana CCTP periphery): Nonce PDA and rent-sponsorship flows need explicit lifecycle review; CCTP CPI boundaries require exact account and program validation

## Related patterns

- [SPL Token / Token-2022 validation gaps](token2022.md) — `token2022`
- [Missing signer authorization](missing-signer.md) — `missing-signer`
- [Account close, revival, and stale data](close-revival.md) — `close-revival`
- [Upgrade authority and admin controls](upgrade-admin.md) — `upgrade-admin`
- [PDA seed/bump mistakes and non-canonical bumps](pda-bump.md) — `pda-bump`
- [CPI account substitution / confused deputy](cpi-substitution.md) — `cpi-substitution`

## References

- https://www.anchor-lang.com/docs/references/account-constraints
- https://docs.rs/anchor-lang/latest/anchor_lang/accounts/unchecked_account/struct.UncheckedAccount.html
- https://solana.com/docs/core/transactions

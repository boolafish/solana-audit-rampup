# Missing signer authorization

- **Pattern ID:** `missing-signer`
- **Category:** Core Solana  |  **Severity:** Critical

## Triggers — load this page when you see these

**Code signals (grep the target):** `AccountInfo`, `UncheckedAccount`, `is_signer`, `Signer<`, `has_one`, `#[account(signer`

**Protocol types:** any privileged/admin instruction, vaults, lending, governance

**Concepts:** authority compared by key but never required to sign; admin/config-mutating instruction; PDA authority used without invoke_signed

## Why this differs from Solidity/EVM

Closest to checking `owner == msg.sender` but forgetting `msg.sender`; Solana has no implicit caller identity.

A pubkey appearing in account data or account list is not proof of authorization. `is_signer` must be required for the authority, or the authority must be a PDA signed via seeds in a CPI context.

## Bad pattern

Accept `authority: AccountInfo` / `UncheckedAccount` and compare `authority.key()` to `state.admin`, but never require a signature.

- *Native:* `if admin.key == state.admin { set_fee(...) }` without `admin.is_signer`.
- *Anchor:* `pub admin: UncheckedAccount<'info>` plus key comparison only.

## Good pattern

Use `Signer<'info>` or `#[account(signer)]`; combine with `has_one = authority` / explicit relationship checks. For PDA authorities, validate seeds and use `invoke_signed` only for intended CPIs.

- *Native:* `require!(admin.is_signer); require_keys_eq!(admin.key(), state.admin);`
- *Anchor:* `pub admin: Signer<'info>` and `#[account(has_one = admin)] pub state: Account<'info, State>`.

## Audit checks

- [ ] Is every privileged human/keypair account a `Signer`?
- [ ] Are PDA authorities validated by canonical seeds and scoped to the resource?
- [ ] Are admin/config relationships checked, not only account presence?

## Public audit findings mapped to this pattern

- **OtterSec Token-2022 Audit** (SPL Token-2022): Incorrect account ordering; Lack of mint account verification; Missing signer checks; Unnecessary writable multisig access; Confidential-transfer validation issues

## Related patterns

- [SPL Token / Token-2022 validation gaps](token2022.md) — `token2022`
- [`remaining_accounts` order/count/type assumptions](remaining-accounts.md) — `remaining-accounts`
- [Missing owner check / spoofed account data](missing-owner.md) — `missing-owner`
- [Missing account relationship checks](relationship-checks.md) — `relationship-checks`
- [Type cosplay / discriminator confusion](type-cosplay.md) — `type-cosplay`

## References

- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/signer-auth.md
- https://www.anchor-lang.com/docs/references/account-constraints

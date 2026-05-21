# Missing owner check / spoofed account data

- **Pattern ID:** `missing-owner`
- **Category:** Core Solana  |  **Severity:** Critical

## Triggers — load this page when you see these

**Code signals (grep the target):** `try_from_slice`, `try_from_slice_unchecked`, `.data.borrow()`, `AccountInfo`, `UncheckedAccount`, `#[account(owner`, `owner ==`

**Protocol types:** any program reading another account's data, token vaults, oracles

**Concepts:** deserializing program state from a raw account; trusting fields in a caller-supplied account; SPL token authority vs solana account owner confusion

## Why this differs from Solidity/EVM

More like trusting bytes from an arbitrary contract address as if they were your contract storage.

Program state is stored in separate accounts supplied by the caller. `owner` is primarily data-write authority: only an account’s owning program may modify its data, resize it, or assign it under normal runtime rules. SPL token authority/mint/owner are fields inside token-account data, not the Solana account `owner`.

## Bad pattern

Deserialize config, user, vault, or market state from arbitrary `AccountInfo` and trust fields such as `admin`, `mint`, `balance`, or `bump`.

- *Native:* `Config::try_from_slice(&config.data.borrow())?` without `config.owner == program_id`.
- *Anchor:* `pub config: AccountInfo<'info>` and manual deserialize.

## Good pattern

For program state, require `account.owner == program_id`; in Anchor prefer `Account<'info, T>`. For SPL Token accounts, require owner is Token/Token-2022 program and validate internal fields.

- *Native:* Check `config.owner == program_id`, length, discriminator/version, then deserialize.
- *Anchor:* `pub config: Account<'info, Config>` or `#[account(owner = expected_program)]` for raw accounts.

## Audit checks

- [ ] For every raw account: is owner checked?
- [ ] Are typed Anchor accounts used where possible?
- [ ] For token accounts: is token program plus mint/authority checked?

## Real incidents mapped to this pattern

- **Wormhole (2022)** — ~120k wETH minted / ~$320M at the time. Guardian signature verification/account validation failure involving instruction sysvar validation path.
- **Cashio (2022)** — ~$48M. Incomplete collateral/LP/mint account validation allowed fake account chains and infinite CASH minting.
- **Crema Finance (2022)** — ~$8.8M reported. Fake tick/price account and faulty owner/account validation in concentrated liquidity fee-claim path.

## Public audit findings mapped to this pattern

- **Trail of Bits Token-2022 Audit** (SPL Token-2022): Missing ownership checks; TLV/extension parsing and length checks; Front-running concern in withheld-token withdrawal flow
- **Zellic Single Pool Audit** (SPL Single Pool): Incorrect vote account deserialization offsets; Missing authority account check; Strong account-by-account validation matrix examples

## Related patterns

- [Missing account relationship checks](relationship-checks.md) — `relationship-checks`
- [Manual deserialization, offsets, and versioned account layouts](native-parser-hazards.md) — `native-parser-hazards`
- [Instruction introspection / signature verification misuse](signature-introspection.md) — `signature-introspection`
- [Sysvar spoofing](sysvar-spoof.md) — `sysvar-spoof`
- [CPI account substitution / confused deputy](cpi-substitution.md) — `cpi-substitution`
- [SPL Token / Token-2022 validation gaps](token2022.md) — `token2022`

## References

- https://solana.com/docs/core/accounts
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/owner-checks.md
- https://neodyme.io/en/blog/solana_common_pitfalls/

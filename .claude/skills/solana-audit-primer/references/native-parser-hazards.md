# Manual deserialization, offsets, and versioned account layouts

- **Pattern ID:** `native-parser-hazards`
- **Category:** Native / Advanced  |  **Severity:** Medium

## Triggers — load this page when you see these

**Code signals (grep the target):** `next_account_info`, `try_from_slice_unchecked`, `data[`, `Pubkey::new_from_array`, `unpack`, `offset`

**Protocol types:** native (non-Anchor) programs, vote/stake account parsing

**Concepts:** hard-coded offsets; no owner/version/length check before reading; wrong account-order assumptions

## Why this differs from Solidity/EVM

Like hand-decoding ABI/storage bytes with wrong offsets.

Native Solana programs often parse account bytes manually via `next_account_info`, offsets, or unchecked deserialization. Layout/version mistakes can silently validate the wrong authority or field.

## Bad pattern

Read a pubkey or amount from a hard-coded offset without checking account owner, type, version, length, and expected layout.

- *Native:* `let authority = Pubkey::new_from_array(data[44..76].try_into()?);` with wrong offset risk.
- *Anchor:* Bypass `Account<T>` and parse `AccountInfo.data` manually inside handler.

## Good pattern

Use canonical unpack/deserialization APIs where possible; check owner, length, discriminator/version, and add tests against real account layouts and version changes.

- *Native:* Use official state unpacker or validate account version/layout and test offsets against fixtures.
- *Anchor:* Use typed accounts or isolate parser with owner/length/discriminator/version checks and tests.

## Audit checks

- [ ] Any `try_from_slice_unchecked`, manual offsets, or raw byte slicing?
- [ ] Are layout/version/length checked before reading?
- [ ] Are vote/stake/token/sysvar account parsers official and current?

## Real incidents mapped to this pattern

- **Crema Finance (2022)** — ~$8.8M reported. Fake tick/price account and faulty owner/account validation in concentrated liquidity fee-claim path.

## Public audit findings mapped to this pattern

- **Zellic Single Pool Audit** (SPL Single Pool): Incorrect vote account deserialization offsets; Missing authority account check; Strong account-by-account validation matrix examples
- **Halborn Stake Pool Audit** (SPL Stake Pool): Fee update timing/epoch edge cases; Unsafe unwrap/panic surfaces; Overflow-check configuration concerns
- **OtterSec Account Compression Audit** (SPL Account Compression): Merkle proof/invariant validation; Tree parameter checks; Underflow/panic-style issues
- **OtterSec EVM CCTP V2 Audit** (Circle CCTP V2 EVM contracts): Specification and implementation consistency matters across message formats; CCTP V2 integrations should be reviewed against the exact V2 contract/program interfaces

## Related patterns

- [Missing account relationship checks](relationship-checks.md) — `relationship-checks`
- [Missing owner check / spoofed account data](missing-owner.md) — `missing-owner`
- [Integer overflow, precision, rounding, decimal mismatch](math.md) — `math`
- [Compute budget, large inputs, and hot-account DoS](compute-dos.md) — `compute-dos`
- [Zero-copy / bytemuck / POD layout hazards](zero-copy-layout.md) — `zero-copy-layout`
- [Relying on logs/events as security-critical state](event-log-reliance.md) — `event-log-reliance`

## References

- https://github.com/solana-labs/security-audits/blob/master/spl/ZellicSinglePoolAudit-2023-06-21.pdf
- https://solana.com/docs/core/accounts
- https://neodyme.io/en/blog/solana_common_pitfalls/

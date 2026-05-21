# Raw-byte PDA decoding and offset drift

- **Pattern ID:** `raw-byte-pda-decoding`
- **Category:** Native / Advanced  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `data[`, `Pubkey::new_from_array`, `try_into()`, `UncheckedAccount`, `[8..40]`

**Protocol types:** cross-program integrations reading callee state

**Concepts:** hard-coded byte offsets; no discriminator/version check before slicing; Option/enum/field-order shift moves the target field

## Why this differs from Solidity/EVM

Like hand-decoding storage slots with hard-coded offsets and no type/version check.

Anchor/Borsh account bytes include discriminators, field order, enum/option tags, and version-sensitive layouts. Raw offsets bypass typed account validation.

## Bad pattern

Read `data[8..40]` or `data[73]` from an `UncheckedAccount` without checking owner, discriminator, length, version, or that the callee layout is pinned.

- *Native:* `let market = Pubkey::new_from_array(data[8..40].try_into()?);`
- *Anchor:* `UncheckedAccount` plus `data[73] != 0` status check.

## Good pattern

Prefer typed deserialization. If slicing is unavoidable, check owner, length, discriminator, version, named offsets, and fixtures from the pinned program version before interpreting fields.

- *Native:* Check owner, len, discriminator, version, then deserialize or read named constant ranges.
- *Anchor:* Use `Account<T>` or an isolated parser with owner/discriminator/version checks and layout tests.

## Audit checks

- [ ] Are all raw offsets named and tested against fixtures?
- [ ] Does the parser check discriminator before field reads?
- [ ] Could `Option`, enum, or field-order changes shift the target field?

## Related patterns

- [Zero-copy / bytemuck / POD layout hazards](zero-copy-layout.md) — `zero-copy-layout`
- [Relying on logs/events as security-critical state](event-log-reliance.md) — `event-log-reliance`
- [Manual deserialization, offsets, and versioned account layouts](native-parser-hazards.md) — `native-parser-hazards`

## References

- https://github.com/boolafish/solana-audit-rampup/blob/main/docs/raw-byte-pda-decoding.md
- https://borsh.io/
- https://docs.rs/anchor-lang/latest/anchor_lang/trait.AccountDeserialize.html

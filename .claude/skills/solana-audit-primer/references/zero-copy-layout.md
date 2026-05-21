# Zero-copy / bytemuck / POD layout hazards

- **Pattern ID:** `zero-copy-layout`
- **Category:** Native / Advanced  |  **Severity:** Medium

## Triggers — load this page when you see these

**Code signals (grep the target):** `zero_copy`, `bytemuck`, `AccountLoader`, `from_bytes`, `repr(C)`, `Pod`, `Zeroable`

**Protocol types:** high-performance programs, orderbooks, large state accounts

**Concepts:** bytemuck cast without owner/len/discriminator; padding/alignment hazards; layout/version drift on upgrade

## Why this differs from Solidity/EVM

Comparable to manual storage slot decoding or assembly struct casts.

Zero-copy and `bytemuck` casts bypass normal serialization checks. Layout, padding, alignment, discriminators, versioning, and field bounds become security-critical.

## Bad pattern

Cast account bytes into a struct with `bytemuck::from_bytes` without owner, length, discriminator, alignment/layout, version, or field-bound checks.

- *Native:* `let cfg: &Config = bytemuck::from_bytes(&account.data.borrow());`
- *Anchor:* `#[account(zero_copy)] struct Market { status: u8, ... }` then treat any status byte as valid.

## Good pattern

Check owner, exact length, discriminator/version, repr/layout assumptions, padding, and field bounds before zero-copy access; prefer Anchor `AccountLoader` patterns when appropriate.

- *Native:* Check owner, len, discriminator, version; then cast only the expected slice and validate fields.
- *Anchor:* Use `AccountLoader`, `repr(C)`, explicit version/status validation, and padding reserved for upgrades.

## Audit checks

- [ ] Is every zero-copy account owner/type/length/version checked?
- [ ] Are enum/status bytes bounded?
- [ ] Can stale padding bytes affect future upgrades?

## Related patterns

- [Relying on logs/events as security-critical state](event-log-reliance.md) — `event-log-reliance`
- [Manual deserialization, offsets, and versioned account layouts](native-parser-hazards.md) — `native-parser-hazards`
- [Raw-byte PDA decoding and offset drift](raw-byte-pda-decoding.md) — `raw-byte-pda-decoding`

## References

- https://www.anchor-lang.com/docs/features/zero-copy
- https://docs.rs/bytemuck/latest/bytemuck/
- https://docs.rs/anchor-lang/latest/anchor_lang/accounts/account_loader/struct.AccountLoader.html

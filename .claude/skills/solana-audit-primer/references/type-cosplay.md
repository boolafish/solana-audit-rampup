# Type cosplay / discriminator confusion

- **Pattern ID:** `type-cosplay`
- **Category:** Core Solana  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `try_from_slice`, `AccountDeserialize`, `discriminator`, `AccountInfo`, `Borsh`

**Protocol types:** native programs, programs with multiple similar account structs

**Concepts:** two structs sharing a prefix layout; missing discriminator/type tag; Anchor discriminator bypassed via unchecked deserialize

## Why this differs from Solidity/EVM

Comparable to storage-layout confusion or decoding calldata/storage as the wrong type.

Raw account bytes can be interpreted as another struct if no discriminator/type tag is enforced.

## Bad pattern

Deserialize unchecked Borsh bytes as `AdminConfig` when the account is actually `UserProfile` with compatible fields.

## Good pattern

Use Anchor `Account<T>` with discriminators, or implement explicit discriminator/version/magic fields in native programs.

## Audit checks

- [ ] Are all manually deserialized accounts type-tagged?
- [ ] Can two account structs share a dangerous prefix layout?
- [ ] Are Anchor discriminators bypassed via unchecked deserialization?

## Related patterns

- [Missing signer authorization](missing-signer.md) — `missing-signer`
- [Missing owner check / spoofed account data](missing-owner.md) — `missing-owner`
- [Missing account relationship checks](relationship-checks.md) — `relationship-checks`

## References

- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/type-cosplay.md
- https://github.com/coral-xyz/sealevel-attacks

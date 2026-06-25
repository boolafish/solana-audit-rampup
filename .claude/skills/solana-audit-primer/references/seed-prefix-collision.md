# Seed-prefix collision and PDA type confusion

- **Pattern ID:** `seed-prefix-collision`
- **Category:** PDA  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `seeds =`, `find_program_address`, `b"vault"`, `UncheckedAccount`, `sha256`, `format!`

**Protocol types:** programs with multiple PDA account types, cross-chain registries, admin registries

**Concepts:** shared seed shape across account types; weak or duplicated static prefix; type/discriminator not verified after derivation; variable-length fields concatenated without length prefix or delimiter

## Why this differs from Solidity/EVM

Like two storage namespaces sharing the same slot prefix, letting one object type stand in for another.

PDAs are untyped addresses. If two account roles share seed structure or weak prefixes under the same program, raw/unchecked code can accept the wrong PDA type. Ambiguous encoding before hashing is still a seed collision even if the PDA seed array itself looks fixed-width.

## Bad pattern

Use seeds like `[b"vault", user]` for multiple account types, or hash `address || chain` / `format!("{}{}", a, b)` without length prefixes or delimiters so `(ab, c)` and `(a, bc)` derive the same PDA.

- *Native:* `PDA([b"config", user])` used for both user config and approval state.
- *Anchor:* `UncheckedAccount` constrained only by seeds shared with another account type.

## Good pattern

Use unique static domain prefixes per account type and action. For variable-length fields, length-prefix each field, hash each field separately, or use another unambiguous encoding before PDA derivation. Verify discriminator/type after PDA derivation.

- *Native:* `PDA([b"user_config", user])` and `PDA([b"approval", user, mint])`, then check type tags.
- *Anchor:* `Account<'info, Approval>` with unique seeds and discriminator validation.

## Audit checks

- [ ] Can two PDA account types share a seed tuple shape?
- [ ] Are static prefixes unique and documented?
- [ ] Does unchecked PDA validation also prove discriminator/type?
- [ ] Are any PDA seeds formed by concatenating variable-length strings or bytes before hashing?
- [ ] Can two different user-visible identities share the same preimage because field boundaries are not encoded?

## Related patterns

- [PDA seed/bump mistakes and non-canonical bumps](pda-bump.md) — `pda-bump`
- [`find_program_address` compute cost and bump caching](find-program-address-cu-cost.md) — `find-program-address-cu-cost`

## References

- https://solana.com/docs/core/pda
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/pda-sharing.md
- https://github.com/coral-xyz/sealevel-attacks

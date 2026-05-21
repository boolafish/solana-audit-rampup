# `find_program_address` compute cost and bump caching

- **Pattern ID:** `find-program-address-cu-cost`
- **Category:** PDA  |  **Severity:** Medium

## Triggers — load this page when you see these

**Code signals (grep the target):** `find_program_address`, `create_program_address`, `bump`, `for `, `loop`

**Protocol types:** CPI-heavy programs, hot loops

**Concepts:** repeated find_program_address inside a loop; switching to a client-supplied bump to save compute; stored bump not re-verified against the PDA address

## Why this differs from Solidity/EVM

Roughly like recomputing expensive CREATE2 searches in hot paths while trusting user-provided salts.

`find_program_address` searches bump values until it finds an off-curve address. Repeating that search in loops or CPI-heavy paths burns compute, but accepting user-supplied bumps can create non-canonical PDA bugs.

## Bad pattern

Call `find_program_address` repeatedly for the same PDA inside loops, then switch to a client-supplied bump to save compute.

- *Native:* `create_program_address(&[seed, &[args.bump]], program_id)` with `args.bump` from the client.
- *Anchor:* Use `bump = args.bump` from instruction data on an unchecked account.

## Good pattern

Use canonical `find_program_address` at creation, store the bump in trusted account state, and later re-derive with the stored bump while still verifying the PDA address and state owner/type.

- *Native:* Store canonical bump at init; later re-derive with stored bump and require the expected key.
- *Anchor:* Use `#[account(seeds=[...], bump = state.bump)]` where `state` is validated.

## Audit checks

- [ ] Are PDA derivations inside bounded paths?
- [ ] Are stored bumps read from trusted state, not instruction args?
- [ ] Is the PDA address rechecked when cached bumps are used?

## Related patterns

- [PDA seed/bump mistakes and non-canonical bumps](pda-bump.md) — `pda-bump`
- [Seed-prefix collision and PDA type confusion](seed-prefix-collision.md) — `seed-prefix-collision`

## References

- https://solana.com/docs/core/pda
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/bump-seed-canonicalization.md
- https://solana.com/docs/core/fees

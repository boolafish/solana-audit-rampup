# PDA seed/bump mistakes and non-canonical bumps

- **Pattern ID:** `pda-bump`
- **Category:** PDA  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `find_program_address`, `create_program_address`, `seeds =`, `bump`, `Pubkey::find_program_address`

**Protocol types:** any PDA-using program, vaults, PDA authorities

**Concepts:** user-supplied bump; non-canonical bump accepted; under-scoped seeds; one PDA authority spanning unrelated resources

## Why this differs from Solidity/EVM

Roughly comparable to deterministic CREATE2 addresses, but PDAs are also signing authorities for CPIs.

PDA derivation includes seeds and a bump. Allowing arbitrary valid bumps can create multiple valid PDA addresses for one logical resource; under-scoped seeds can make one PDA authority cover unrelated resources.

## Bad pattern

Accept user-provided bump with `create_program_address`; use seeds like `[b"vault"]` globally for many assets.

## Good pattern

Use canonical `find_program_address`; in Anchor use `seeds = [...]` and `bump`; store bump when reused; include domain prefix plus user/pool/mint/resource in seeds.

## Audit checks

- [ ] Is bump canonical or stored and verified?
- [ ] Are seeds domain-separated and resource-scoped?
- [ ] Can the same PDA sign for unrelated resources?

## Public audit findings mapped to this pattern

- **OpenZeppelin Sponsored CCTP Deposits from Solana Audit** (Solana CCTP periphery): Nonce PDA and rent-sponsorship flows need explicit lifecycle review; CCTP CPI boundaries require exact account and program validation

## Related patterns

- [CPI account substitution / confused deputy](cpi-substitution.md) — `cpi-substitution`
- [`remaining_accounts` order/count/type assumptions](remaining-accounts.md) — `remaining-accounts`
- [`find_program_address` compute cost and bump caching](find-program-address-cu-cost.md) — `find-program-address-cu-cost`
- [Seed-prefix collision and PDA type confusion](seed-prefix-collision.md) — `seed-prefix-collision`

## References

- https://solana.com/docs/core/pda
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/bump-seed-canonicalization.md
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/pda-sharing.md

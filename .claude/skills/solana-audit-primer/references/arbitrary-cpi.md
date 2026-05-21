# Arbitrary CPI / missing program ID check

- **Pattern ID:** `arbitrary-cpi`
- **Category:** CPI  |  **Severity:** Critical

## Triggers — load this page when you see these

**Code signals (grep the target):** `invoke(`, `invoke_signed(`, `Instruction {`, `program_id:`, `Program<`, `Interface<`, `AccountInfo`

**Protocol types:** any CPI, token transfers, router/aggregator

**Concepts:** CPI target program passed by caller; missing program id pin; wrong token program accepted

## Why this differs from Solidity/EVM

Like low-level calling an attacker-supplied contract while assuming it is ERC20/System/Oracle.

The CPI target program account is often passed by the caller. Without checking program ID/executable, attacker can pass a malicious program or wrong token program.

## Bad pattern

Build `Instruction { program_id: supplied_program.key(), ... }` and call `invoke` without pinning `spl_token::ID`, System Program, ATA program, etc.

- *Native:* `Instruction { program_id: supplied_program.key(), ... }` then `invoke`.
- *Anchor:* `pub token_program: AccountInfo<'info>`.

## Good pattern

Use `Program<'info, Token/System/...>`, `Interface<'info, TokenInterface>` with explicit allowed token programs, or `require_keys_eq!(program.key(), expected_id)`.

- *Native:* `require_keys_eq!(supplied_program.key(), spl_token::ID)` before CPI.
- *Anchor:* `pub token_program: Program<'info, Token>` or constrained `Interface<'info, TokenInterface>`.

## Audit checks

- [ ] Is every CPI target typed or address-checked?
- [ ] Are program accounts executable where expected?
- [ ] Is Token vs Token-2022 support intentional and constrained?

## Related patterns

- [CPI account substitution / confused deputy](cpi-substitution.md) — `cpi-substitution`
- [Stale account data after CPI / missing reload](stale-cpi-reload.md) — `stale-cpi-reload`
- [Forwarded `remaining_accounts` as CPI trust boundary](remaining-accounts-trust.md) — `remaining-accounts-trust`

## References

- https://solana.com/docs/core/cpi
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/arbitrary-cpi.md
- https://www.anchor-lang.com/docs/basics/cpi

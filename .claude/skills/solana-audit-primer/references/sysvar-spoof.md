# Sysvar spoofing

- **Pattern ID:** `sysvar-spoof`
- **Category:** Account Validation  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `Sysvar<`, `Clock::get`, `Rent::get`, `sysvar`, `Instructions`, `AccountInfo`

**Protocol types:** any time/rent-dependent logic, signature introspection

**Concepts:** sysvar passed as account without address check; fake clock/rent/instructions account

## Why this differs from Solidity/EVM

No close Solidity analogue; closest is trusting an oracle/precompile address without checking it.

Sysvars can be accessed via trusted APIs or passed as accounts. If passed unchecked, fake sysvar-like accounts can spoof clock, rent, instructions, etc.

## Bad pattern

Read Clock or Instructions sysvar from arbitrary `AccountInfo` without checking sysvar ID.

## Good pattern

Use `Clock::get()`, `Rent::get()`; otherwise check exact sysvar address and owner. In Anchor use `Sysvar<'info, Clock>`.

## Audit checks

- [ ] Are sysvar accounts address-checked?
- [ ] Is instruction introspection tied to exact index/message/program?
- [ ] Are Ed25519/secp verification instructions parsed safely?

## Real incidents mapped to this pattern

- **Wormhole (2022)** — ~120k wETH minted / ~$320M at the time. Guardian signature verification/account validation failure involving instruction sysvar validation path.
- **deBridge Solana signature-verification-bypass class (2022)** — Class-level audit finding; no canonical loss postmortem. Signature verification bypass class in Solana bridge/message verification flows.

## Related patterns

- [Instruction introspection / signature verification misuse](signature-introspection.md) — `signature-introspection`
- [Missing owner check / spoofed account data](missing-owner.md) — `missing-owner`
- [Missing account relationship checks](relationship-checks.md) — `relationship-checks`
- [Duplicate mutable accounts / aliasing](duplicate-mut.md) — `duplicate-mut`
- [Instructions sysvar introspection mistakes](instructions-sysvar-introspection.md) — `instructions-sysvar-introspection`

## References

- https://docs.rs/solana-program/latest/solana_program/sysvar/index.html
- https://docs.rs/solana-program/latest/solana_program/sysvar/instructions/index.html

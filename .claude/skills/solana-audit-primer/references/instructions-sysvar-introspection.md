# Instructions sysvar introspection mistakes

- **Pattern ID:** `instructions-sysvar-introspection`
- **Category:** Account Validation  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `sysvar::instructions`, `load_current_index_checked`, `load_instruction_at_checked`, `Sysvar1nstructions`

**Protocol types:** anti-CPI / direct-call enforcement, signature-verifier placement, bridges

**Concepts:** sysvar address not exact-checked; inspected instruction position not relative to current index; program id / accounts / data not bound

## Why this differs from Solidity/EVM

Like checking that some signature or router call exists in calldata history without binding it to this action.

The Instructions sysvar exposes transaction instructions. Programs that enforce direct calls, signature-verifier placement, or anti-proxy rules must bind the current index and exact neighboring instructions.

## Bad pattern

Accept any `Sysvar1nstructions1111111111111111111111111`-like account or scan for a matching instruction somewhere in the transaction without checking current index, program ID, accounts, and data.

- *Native:* Scan all instructions for an Ed25519 verifier and accept the first match.
- *Anchor:* Unchecked `ix_sysvar: AccountInfo<'info>` and handler scans loosely.

## Good pattern

Require the exact Instructions sysvar address, call `load_current_index_checked`, inspect the expected previous/current instruction with `load_instruction_at_checked`, and bind program ID, accounts, data, signer, nonce, and action domain.

- *Native:* Use `load_current_index_checked`; require verifier immediately before this instruction and parse exact payload.
- *Anchor:* `#[account(address = sysvar::instructions::ID)]` plus exact index and payload checks.

## Audit checks

- [ ] Is the sysvar account exact-address checked?
- [ ] Is the inspected instruction position relative to current index?
- [ ] Are program ID, account keys, data, nonce, and domain bound?

## Related patterns

- [Duplicate mutable accounts / aliasing](duplicate-mut.md) — `duplicate-mut`
- [Sysvar spoofing](sysvar-spoof.md) — `sysvar-spoof`
- [Instruction introspection / signature verification misuse](signature-introspection.md) — `signature-introspection`

## References

- https://docs.rs/solana-program/latest/solana_program/sysvar/instructions/index.html
- https://docs.rs/solana-program/latest/solana_program/sysvar/index.html
- https://www.certik.com/resources/blog/wormhole-bridge-exploit-incident-analysis

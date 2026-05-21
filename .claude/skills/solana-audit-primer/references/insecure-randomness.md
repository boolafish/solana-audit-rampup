# Insecure randomness from slots, timestamps, or blockhashes

- **Pattern ID:** `insecure-randomness`
- **Category:** Execution / DoS  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `Clock::get`, `slot`, `unix_timestamp`, `recent_blockhashes`, ` % `

**Protocol types:** lottery, raffle, games, NFT mint ordering

**Concepts:** modulo of slot/timestamp used as randomness; predictable or biasable entropy; participant aborts after unfavorable reveal

## Why this differs from Solidity/EVM

Like using `block.timestamp` / `blockhash` as lottery randomness.

Slots, timestamps, account keys, transaction ordering, and recent blockhash-like values are public or influenceable. Validators/users can bias simple modulo randomness.

## Bad pattern

Pick a raffle/game/NFT winner with `Clock::get()?.slot % participants.len()` or timestamp modulo.

- *Native:* `let winner = (Clock::get()?.slot as usize) % n;`
- *Anchor:* `let roll = Clock::get()?.unix_timestamp as u64 % 100;`

## Good pattern

Use a verified randomness oracle or carefully designed commit-reveal with anti-abort rules, delays, expiry, and penalties.

- *Native:* Verify VRF/entropy oracle account and output, or commit first and reveal after delay with anti-abort handling.
- *Anchor:* Store commitment in one instruction; reveal later; validate hash, delay, expiry, and no favorable abort path.

## Audit checks

- [ ] Can user/validator predict or bias entropy?
- [ ] Can participant abort after seeing an unfavorable reveal?
- [ ] Is randomness provider account/program validated?

## Related patterns

- [Compute budget, large inputs, and hot-account DoS](compute-dos.md) — `compute-dos`

## References

- https://docs.rs/solana-program/latest/solana_program/sysvar/index.html
- https://docs.switchboard.xyz/
- https://docs.pyth.network/entropy

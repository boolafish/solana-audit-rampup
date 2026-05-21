# Relying on logs/events as security-critical state

- **Pattern ID:** `event-log-reliance`
- **Category:** Native / Advanced  |  **Severity:** Medium

## Triggers — load this page when you see these

**Code signals (grep the target):** `msg!`, `emit!`, `emit_cpi`, `sol_log`

**Protocol types:** claims, airdrops, anything indexer-driven

**Concepts:** correctness depends on an indexer observing logs; no on-chain replay/double-claim guard; logs mimicable by other programs

## Why this differs from Solidity/EVM

Like making off-chain events the source of truth instead of contract storage.

Solana logs/events are not program state. They can be missed, truncated, parsed inconsistently, or mimicked by other programs.

## Bad pattern

Emit `CLAIMED` / `Settled` event but do not update on-chain state that prevents replay or double-claim.

- *Native:* `msg!("CLAIMED: {}", user.key());` with no claimed flag.
- *Anchor:* `emit!(Claimed { ... })` only.

## Good pattern

Write authoritative on-chain state first; use logs/events only as supplemental indexing signals.

- *Native:* Set `claim.claimed = true` in account data, then log.
- *Anchor:* Update `Account<Claim>` state and emit event as non-authoritative notification.

## Audit checks

- [ ] Does protocol correctness depend on an indexer observing logs?
- [ ] Is replay/double-claim prevented on-chain?
- [ ] Could another program emit similar logs?

## Related patterns

- [Zero-copy / bytemuck / POD layout hazards](zero-copy-layout.md) — `zero-copy-layout`
- [Manual deserialization, offsets, and versioned account layouts](native-parser-hazards.md) — `native-parser-hazards`
- [Raw-byte PDA decoding and offset drift](raw-byte-pda-decoding.md) — `raw-byte-pda-decoding`

## References

- https://solana.com/docs/core/transactions
- https://www.anchor-lang.com/docs/features/events

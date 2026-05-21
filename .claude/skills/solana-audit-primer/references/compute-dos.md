# Compute budget, large inputs, and hot-account DoS

- **Pattern ID:** `compute-dos`
- **Category:** Execution / DoS  |  **Severity:** Medium

## Triggers — load this page when you see these

**Code signals (grep the target):** `remaining_accounts`, `for `, `.iter()`, `#[account(mut`, `Vec<`

**Protocol types:** batch operations, any global counter/config

**Concepts:** unbounded loops; global writable hot account serializes usage; compute-budget exhaustion; writable-account lock contention

## Why this differs from Solidity/EVM

Like gas DoS, but compute units plus account locks and writable-hot-account serialization matter.

Transactions have compute limits; writable account locks constrain parallelism. A single global mutable account can serialize protocol usage and become spam target.

## Bad pattern

Unbounded loop over `remaining_accounts`; O(n²) checks; every user flow writes same global counter/config; unnecessary `mut`.

## Good pattern

Bound lengths, cap CPIs, price work, split deterministic chunks, shard state, keep config readonly unless changed.

## Audit checks

- [ ] Are remaining accounts/vector lengths bounded?
- [ ] Are there global writable hot accounts?
- [ ] Could attacker force expensive CPIs/PDA derivations?

## Public audit findings mapped to this pattern

- **Halborn Stake Pool Audit** (SPL Stake Pool): Fee update timing/epoch edge cases; Unsafe unwrap/panic surfaces; Overflow-check configuration concerns

## Related patterns

- [Integer overflow, precision, rounding, decimal mismatch](math.md) — `math`
- [Manual deserialization, offsets, and versioned account layouts](native-parser-hazards.md) — `native-parser-hazards`
- [Insecure randomness from slots, timestamps, or blockhashes](insecure-randomness.md) — `insecure-randomness`

## References

- https://solana.com/docs/core/fees
- https://solana.com/docs/core/transactions

# Integer overflow, precision, rounding, decimal mismatch

- **Pattern ID:** `math`
- **Category:** Math / Accounting  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `checked_`, `saturating_`, `as u64`, `as u128`, `overflow-checks`, `u128`, ` * `, ` / `

**Protocol types:** lending, amm, rewards, any accounting

**Concepts:** unchecked arithmetic in optimized build; division before multiplication; decimal/exponent mismatch; rounding exploited by repeated small actions

## Why this differs from Solidity/EVM

Familiar from Solidity, but Rust release behavior, u64 token amounts, and fixed-point conventions differ.

Unlike Solidity 0.8 checked arithmetic, Rust primitive integer overflow is not automatically safe in optimized Solana program builds unless overflow checks or checked/saturating APIs are used. Lamports/token amounts are often `u64`; prices and rewards need `u128` intermediates, explicit rounding, and decimal normalization.

## Bad pattern

`amount * price / scale` in u64; division before multiplication; no checked math; token decimals assumed identical.

## Good pattern

Use `checked_*`, `u128` intermediates, explicit rounding direction, decimal bounds, invariant tests/fuzzing.

## Audit checks

- [ ] Any unchecked arithmetic?
- [ ] Are token decimals and oracle decimals normalized?
- [ ] Can repeated small actions exploit rounding?

## Real incidents mapped to this pattern

- **Allbridge (2023)** — ~$570k reported. Pool invariant and price manipulation in bridge liquidity accounting.
- **Mango Markets (2022)** — ~$115M bad debt / drained liquidity. Low-liquidity market/oracle/economic manipulation enabled inflated collateral borrowing.
- **Nirvana Finance (2022)** — ~$3.5M attacker profit, larger protocol damage. Flash-loan-assisted pricing/economic manipulation of protocol mechanism.

## Public audit findings mapped to this pattern

- **Halborn Stake Pool Audit** (SPL Stake Pool): Fee update timing/epoch edge cases; Unsafe unwrap/panic surfaces; Overflow-check configuration concerns
- **OtterSec Account Compression Audit** (SPL Account Compression): Merkle proof/invariant validation; Tree parameter checks; Underflow/panic-style issues
- **Certora Kamino Lending Security Report** (Kamino Lending / KLend): Exchange-rate precision loss can affect redeem accounting; Small-number rounding and reserve accounting deserve dedicated tests

## Related patterns

- [Oracle feed validation gaps](oracle-validation.md) — `oracle-validation`
- [Oracle, ordering, and MEV/front-running assumptions](oracle-mev.md) — `oracle-mev`
- [Manual deserialization, offsets, and versioned account layouts](native-parser-hazards.md) — `native-parser-hazards`
- [Compute budget, large inputs, and hot-account DoS](compute-dos.md) — `compute-dos`
- [Native SOL lamport accounting bugs](native-sol-lamports.md) — `native-sol-lamports`

## References

- https://neodyme.io/en/blog/solana_common_pitfalls/
- https://github.com/solana-foundation/developer-content/tree/main/content/courses/program-security

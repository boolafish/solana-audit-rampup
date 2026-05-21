# Oracle, ordering, and MEV/front-running assumptions

- **Pattern ID:** `oracle-mev`
- **Category:** Economic / MEV  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `price`, `slippage`, `min_out`, `deadline`, `Clock`, `slot`

**Protocol types:** amm, lending, perps, auctions, liquidations

**Concepts:** no slippage / stale-quote protection; ordering-sensitive flow; private orderflow / Jito bundle assumptions; liquidation ordering assumed deterministic

## Why this differs from Solidity/EVM

Familiar DeFi class, but Solana has no Ethereum-style public mempool; MEV still exists via leaders, priority fees, private orderflow, Jito/bundles, and ordering-sensitive flows.

Solana has no globally gossiped Ethereum-style public mempool, but pending orderflow is not guaranteed private. Transactions may be visible to RPC providers, leaders/validators, relays/block engines, searchers, or private orderflow partners. Ordering-sensitive protocols should be treated as MEV-exposed unless deployment has documented protections.

## Bad pattern

No slippage/stale quote checks; lending accepts spot price without freshness/confidence/liquidity bounds; liquidation logic assumes deterministic ordering.

## Good pattern

Require slippage limits, oracle freshness/confidence checks, liquidity-aware risk parameters, TWAP/limits/circuit breakers where appropriate, robust liquidation ordering assumptions, and replay/nonce/domain checks.

## Audit checks

- [ ] Are oracle feeds correct, fresh, and confidence-bounded?
- [ ] Can price updates/trades/liquidations be reordered profitably?
- [ ] Are priority fees/bundles/private orderflow assumptions documented?

## Real incidents mapped to this pattern

- **Allbridge (2023)** — ~$570k reported. Pool invariant and price manipulation in bridge liquidity accounting.
- **Mango Markets (2022)** — ~$115M bad debt / drained liquidity. Low-liquidity market/oracle/economic manipulation enabled inflated collateral borrowing.
- **Solend whale liquidation crisis (2022)** — Bad-debt and governance crisis risk; emergency DAO proposal. Concentration, liquidation-liquidity, and governance/emergency-action risk.
- **Nirvana Finance (2022)** — ~$3.5M attacker profit, larger protocol damage. Flash-loan-assisted pricing/economic manipulation of protocol mechanism.

## Public audit findings mapped to this pattern

- **Trail of Bits Token-2022 Audit** (SPL Token-2022): Missing ownership checks; TLV/extension parsing and length checks; Front-running concern in withheld-token withdrawal flow

## Related patterns

- [Oracle feed validation gaps](oracle-validation.md) — `oracle-validation`
- [Integer overflow, precision, rounding, decimal mismatch](math.md) — `math`
- [Governance, multisig, and timelock validation gaps](governance-timelock.md) — `governance-timelock`
- [SPL Token / Token-2022 validation gaps](token2022.md) — `token2022`
- [Missing owner check / spoofed account data](missing-owner.md) — `missing-owner`

## References

- https://www.helius.dev/blog/solana-mev-an-introduction
- https://www.helius.dev/blog/priority-fees-understanding-solanas-transaction-fee-mechanics
- https://solana.com/docs/core/fees
- https://rekt.news/mango-markets-rekt/

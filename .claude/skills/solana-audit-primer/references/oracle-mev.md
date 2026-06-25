# Oracle, ordering, and MEV/front-running assumptions

- **Pattern ID:** `oracle-mev`
- **Category:** Economic / MEV  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `price`, `slippage`, `min_out`, `deadline`, `Clock`, `slot`, `quote_id`

**Protocol types:** amm, lending, perps, auctions, liquidations, signed quotes

**Concepts:** no slippage / stale-quote protection; ordering-sensitive flow; private orderflow / Jito bundle assumptions; liquidation ordering assumed deterministic; independent fresh quotes can be mixed

## Why this differs from Solidity/EVM

Familiar DeFi class, but Solana has no Ethereum-style public mempool; MEV still exists via leaders, priority fees, private orderflow, Jito/bundles, and ordering-sensitive flows.

Solana has no globally gossiped Ethereum-style public mempool, but pending orderflow is not guaranteed private. Transactions may be visible to RPC providers, leaders/validators, relays/block engines, searchers, or private orderflow partners. Ordering-sensitive protocols should be treated as MEV-exposed unless deployment has documented protections. Fresh signed quotes can still compose badly if the program accepts independent attestations that were not meant to share one conversion or swap.

## Bad pattern

Accept a price, quote, or attestation that is fresh but not bound to the amount, token side, direction, or paired quote set used in the action; allow independent fresh quotes to be mixed in one conversion or round trip.

## Good pattern

Bind quote/price data to the action: consumer, direction, input/output assets, amount, quote id or paired quote set, validity window, and nonce when one-time use is intended. If attestations are intentionally reusable, make the freshness window and off-chain issuance policy explicit trust assumptions.

## Audit checks

- [ ] Are oracle feeds correct, fresh, and confidence-bounded?
- [ ] Can price updates/trades/liquidations be reordered profitably?
- [ ] Are priority fees/bundles/private orderflow assumptions documented?
- [ ] Can two individually fresh quotes with different indexes be paired to skew a conversion?
- [ ] Is quote id merely lineage, or is it checked/consumed/bound across both legs?

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

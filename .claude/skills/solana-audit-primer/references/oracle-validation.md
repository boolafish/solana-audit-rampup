# Oracle feed validation gaps

- **Pattern ID:** `oracle-validation`
- **Category:** Economic / MEV  |  **Severity:** Critical

## Triggers — load this page when you see these

**Code signals (grep the target):** `price_feed`, `Pyth`, `Switchboard`, `get_price`, `publish_time`, `confidence`, `AccountInfo`

**Protocol types:** lending, perps, stablecoins, collateral valuation

**Concepts:** feed account not pinned to config; freshness/confidence/status not checked; exponent/decimals not normalized; low-liquidity spot price inflates collateral

## Why this differs from Solidity/EVM

Familiar DeFi oracle issue, but account substitution adds a Solana-specific layer.

A valid-looking oracle account can be the wrong feed/program or stale/confidence-wide data. Account validation and economic validation are both required.

## Bad pattern

Parse price from arbitrary `price_feed: AccountInfo` and multiply without checking feed address, owner/program, freshness, confidence, exponent/decimals, or circuit breakers.

- *Native:* `let price = parse_price(&oracle.data.borrow())?; collateral = amount * price as u64;`
- *Anchor:* `pub price_feed: AccountInfo<'info>` unchecked.

## Good pattern

Pin expected feed and oracle program/owner; check freshness, confidence/deviation, status, positive price, exponent/decimal normalization, TWAP/liquidity assumptions, and risk parameter caps.

- *Native:* Check owner/feed id, freshness, confidence, status, exponent, then normalize with checked math.
- *Anchor:* `#[account(address = config.expected_price_feed)] price_feed` plus handler checks oracle program, freshness, confidence, exponent, and circuit breakers.

## Audit checks

- [ ] Is the exact feed account bound to config?
- [ ] Are publish time and confidence checked?
- [ ] Are decimals/exponent normalized with checked math?
- [ ] Can low-liquidity spot prices inflate collateral?

## Real incidents mapped to this pattern

- **Allbridge (2023)** — ~$570k reported. Pool invariant and price manipulation in bridge liquidity accounting.
- **Mango Markets (2022)** — ~$115M bad debt / drained liquidity. Low-liquidity market/oracle/economic manipulation enabled inflated collateral borrowing.
- **Solend whale liquidation crisis (2022)** — Bad-debt and governance crisis risk; emergency DAO proposal. Concentration, liquidation-liquidity, and governance/emergency-action risk.
- **Nirvana Finance (2022)** — ~$3.5M attacker profit, larger protocol damage. Flash-loan-assisted pricing/economic manipulation of protocol mechanism.

## Public audit findings mapped to this pattern

- **Certora Kamino Lending Security Report** (Kamino Lending / KLend): Exchange-rate precision loss can affect redeem accounting; Small-number rounding and reserve accounting deserve dedicated tests

## Related patterns

- [Oracle, ordering, and MEV/front-running assumptions](oracle-mev.md) — `oracle-mev`
- [Integer overflow, precision, rounding, decimal mismatch](math.md) — `math`
- [Governance, multisig, and timelock validation gaps](governance-timelock.md) — `governance-timelock`

## References

- https://docs.pyth.network/price-feeds/use-real-time-data/solana
- https://docs.switchboard.xyz/
- https://rekt.news/mango-markets-rekt/
- https://www.certik.com/resources/blog/nirvana-finance-incident-analysis

# Real Solana incidents mapped to patterns

Real incidents are useful because they show which abstract patterns produced losses. Not all Solana losses are program bugs; key management, wallets, and economic design also matter.

## Wormhole (2022)

- Impact: ~120k wETH minted / ~$320M at the time
- Root pattern: Guardian signature verification/account validation failure involving instruction sysvar validation path.
- Mapped pattern IDs: signature-introspection, sysvar-spoof, missing-owner
- Auditor takeaway: Do not merely check that a verification-looking instruction/account exists; bind sysvar, verifier program, signer, payload, and instruction position.
- References:
  - https://www.certik.com/resources/blog/wormhole-bridge-exploit-incident-analysis

## Cashio (2022)

- Impact: ~$48M
- Root pattern: Incomplete collateral/LP/mint account validation allowed fake account chains and infinite CASH minting.
- Mapped pattern IDs: relationship-checks, missing-owner, token2022
- Auditor takeaway: Valid accounts must also be the right accounts for the mint/pool/collateral chain; cross-check every relationship.
- References:
  - https://rekt.news/cashio-rekt/

## Crema Finance (2022)

- Impact: ~$8.8M reported
- Root pattern: Fake tick/price account and faulty owner/account validation in concentrated liquidity fee-claim path.
- Mapped pattern IDs: missing-owner, relationship-checks, native-parser-hazards
- Auditor takeaway: Audit all instruction variants and helper paths; one correctly validated path does not protect a sibling method.
- References:
  - https://rekt.news/crema-finance-rekt/
  - https://www.certik.com/resources/blog/crema-finance-exploit
  - https://www.halborn.com/blog/post/explained-the-crema-finance-hack-july-2022

## Mango Markets (2022)

- Impact: ~$115M bad debt / drained liquidity
- Root pattern: Low-liquidity market/oracle/economic manipulation enabled inflated collateral borrowing.
- Mapped pattern IDs: oracle-validation, oracle-mev
- Auditor takeaway: Economic design and liquidity-aware risk parameters are audit scope, not just code correctness.
- References:
  - https://rekt.news/mango-markets-rekt/

## Nirvana Finance (2022)

- Impact: ~$3.5M attacker profit, larger protocol damage
- Root pattern: Flash-loan-assisted pricing/economic manipulation of protocol mechanism.
- Mapped pattern IDs: oracle-validation, oracle-mev
- Auditor takeaway: Check AMM/pricing invariants, manipulation cost, circuit breakers, and atomic composition assumptions.
- References:
  - https://www.certik.com/resources/blog/nirvana-finance-incident-analysis
  - https://rekt.news/nirvana-rekt/

## Raydium (2022)

- Impact: ~$4M+ reported
- Root pattern: Compromised admin/owner authority used to drain pools.
- Mapped pattern IDs: upgrade-admin, governance-timelock
- Auditor takeaway: Key management, authority blast radius, and emergency/admin powers are part of security review.
- References:
  - https://www.certik.com/skynet-report/raydium-protocol-exploit-incident-analysis

## Slope wallet incident (2022)

- Impact: ~9,231 wallets affected
- Root pattern: Wallet/application key handling failure, not a Solana program bug.
- Mapped pattern IDs: upgrade-admin
- Auditor takeaway: Classify ecosystem losses correctly; wallet/key custody incidents may be out of smart-contract scope but affect threat model.
- References:
  - https://solana.com/news/8-2-2022-application-wallet-incident


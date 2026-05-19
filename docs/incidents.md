# Real Solana incidents mapped to patterns

Real incidents are useful because they show which abstract patterns produced losses. Not all Solana losses are program bugs; key management, wallets, and economic design also matter.

## Wormhole (2022)

- Chain/category: Solana / Ethereum / bridge
- Impact: ~120k wETH minted / ~$320M at the time
- Summary: A forged guardian verification path let the attacker mint wrapped ETH on Solana without a valid guardian message.
- Root pattern: Guardian signature verification/account validation failure involving instruction sysvar validation path.
- Exploit path: Forge the verification precondition, submit a malicious VAA, and mint wrapped assets against an invalid message.
- Mapped pattern IDs: signature-introspection, sysvar-spoof, missing-owner
- Auditor takeaway: Do not merely check that a verification-looking instruction/account exists; bind sysvar, verifier program, signer, payload, and instruction position.
- References:
  - https://www.certik.com/resources/blog/wormhole-bridge-exploit-incident-analysis

## Nomad (2022)

- Chain/category: Ethereum / cross-chain / bridge
- Impact: ~$190M
- Summary: A zero trusted root made arbitrary messages appear valid after an upgrade.
- Root pattern: Bridge replica accepted messages against a zero trusted root.
- Exploit path: Copy a successful transaction, replace recipient/amount fields, and submit arbitrary messages that validated against the zero root.
- Mapped pattern IDs: reinit, relationship-checks, signature-introspection
- Auditor takeaway: Initialization and trusted-root state are security-critical; test nonzero roots, replay resistance, and invalid-message rejection after upgrades.
- References:
  - https://rekt.news/nomad-rekt/
  - https://www.coinbase.com/blog/nomad-bridge-incident-analysis

## Ronin (2022)

- Chain/category: Ronin / Ethereum / bridge
- Impact: ~$624M
- Summary: An attacker compromised enough validator keys to satisfy the bridge withdrawal quorum.
- Root pattern: Off-chain validator quorum compromise.
- Exploit path: Obtain enough validator signatures, authorize fraudulent withdrawals, and drain bridge reserves.
- Mapped pattern IDs: upgrade-admin, governance-timelock, signature-introspection
- Auditor takeaway: Bridge signer sets, allowlists, key custody, threshold size, and emergency controls are part of audit scope even when on-chain verification works as designed.
- References:
  - https://rekt.news/ronin-rekt/
  - https://www.halborn.com/blog/post/explained-the-ronin-hack-march-2022

## Multichain (2023)

- Chain/category: Cross-chain / bridge
- Impact: ~$125M+
- Summary: Bridge funds were drained after compromise or loss of control of MPC/key infrastructure.
- Root pattern: MPC/private-key compromise and opaque operational control.
- Exploit path: Use compromised signing/control infrastructure to move assets from bridge-controlled addresses.
- Mapped pattern IDs: upgrade-admin, governance-timelock
- Auditor takeaway: For bridges, document who can sign, pause, upgrade, rotate keys, or move custody assets; smart-contract tests do not cover opaque MPC control risk.
- References:
  - https://rekt.news/multichain-rekt/
  - https://www.certik.com/resources/blog/multichain-collapse-the-private-key-leak-that-drained-usd125m

## Allbridge (2023)

- Chain/category: BNB Chain / cross-chain / bridge
- Impact: ~$570k reported
- Summary: Pool pricing and liquidity accounting were manipulated to drain bridge liquidity.
- Root pattern: Pool invariant and price manipulation in bridge liquidity accounting.
- Exploit path: Manipulate pool balances/prices through swaps and liquidity operations, then withdraw underpriced assets.
- Mapped pattern IDs: oracle-validation, oracle-mev, math
- Auditor takeaway: Bridge liquidity pools need invariant tests and manipulation-cost analysis, not only message-authentication checks.
- References:
  - https://rekt.news/allbridge-rekt/
  - https://dn.institute/research/cyberattacks/incidents/2023-04-02-allbridge/

## deBridge Solana signature-verification-bypass class (2022)

- Chain/category: Solana / cross-chain / bridge
- Impact: Class-level audit finding; no canonical loss postmortem
- Summary: Solana bridge programs that rely on instruction introspection can accept forged or unrelated signature-verification instructions if payload, signer, index, and verifier program are not fully bound.
- Root pattern: Signature verification bypass class in Solana bridge/message verification flows.
- Exploit path: Place a valid-looking Ed25519/secp verification instruction in the transaction, then call the bridge with a different message or account set.
- Mapped pattern IDs: signature-introspection, sysvar-spoof, relationship-checks
- Auditor takeaway: When a Solana bridge uses signature instructions, bind verifier program, instruction index, signer, domain, nonce, payload, and all action parameters.
- References:
  - https://debridge.com/support/where-can-i-find-debridges-audit-reports/
  - https://neodyme.io/reports/debridge.pdf

## LayerZero / Stargate DVN and library configuration (2023-2024)

- Chain/category: Cross-chain / bridge
- Impact: Configuration risk class
- Summary: LayerZero-style systems make endpoint libraries, oracle/relayer or DVN sets, confirmations, and per-path configuration part of the security boundary.
- Root pattern: Bridge security depends on message library and DVN/oracle/relayer configuration, not only application contract code.
- Exploit path: Compromise or misconfigure the verification path so a message is accepted under a weaker trust model than the app owner intended.
- Mapped pattern IDs: upgrade-admin, governance-timelock, relationship-checks
- Auditor takeaway: Audit the per-route message library and verifier configuration as protocol state; pin expected endpoints and document who can change them.
- References:
  - https://docs.layerzero.network/v2/concepts/modular-security/security-stack-dvns
  - https://docs.layerzero.network/v2/developers/evm/technical-reference/deployed-contracts

## Cashio (2022)

- Chain/category: Solana / lending-vault
- Impact: ~$48M
- Summary: Fake collateral and LP accounts let the attacker mint unbacked CASH.
- Root pattern: Incomplete collateral/LP/mint account validation allowed fake account chains and infinite CASH minting.
- Exploit path: Provide counterfeit accounts with compatible fields, satisfy shallow checks, mint unbacked CASH, and swap it for real assets.
- Mapped pattern IDs: relationship-checks, missing-owner, cpi-substitution
- Auditor takeaway: Valid accounts must also be the right accounts for the mint/pool/collateral chain; this is directly relevant to approval-PDA designs and Kamino/KLend CPI account ordering.
- References:
  - https://rekt.news/cashio-rekt/
  - https://www.sec3.dev/blog/cashioapp-attack-whats-the-vulnerability-and-how-x-ray-detects-it

## Mango Markets (2022)

- Chain/category: Solana / lending-vault
- Impact: ~$115M bad debt / drained liquidity
- Summary: The attacker manipulated a low-liquidity market and oracle-driven collateral value, then borrowed against inflated collateral.
- Root pattern: Low-liquidity market/oracle/economic manipulation enabled inflated collateral borrowing.
- Exploit path: Use large positions and liquidity to move the mark/oracle price, inflate account equity, borrow assets, and leave bad debt.
- Mapped pattern IDs: oracle-validation, oracle-mev, math
- Auditor takeaway: Economic design, oracle source/liquidity, and flash-loan-style composition are audit scope even when every transaction is valid protocol state.
- References:
  - https://rekt.news/mango-markets-rekt/
  - https://www.coindesk.com/markets/2022/10/12/how-market-manipulation-led-to-a-100m-exploit-on-solana-defi-exchange-mango

## Solend whale liquidation crisis (2022)

- Chain/category: Solana / lending-vault
- Impact: Bad-debt and governance crisis risk; emergency DAO proposal
- Summary: A large borrower's position threatened cascading liquidations, oracle/DEX stress, and bad debt.
- Root pattern: Concentration, liquidation-liquidity, and governance/emergency-action risk.
- Exploit path: Not a conventional exploit; adverse price movement could force liquidations that move markets and create insolvency.
- Mapped pattern IDs: oracle-validation, oracle-mev, governance-timelock
- Auditor takeaway: Lending audits should include concentration limits, liquidation liquidity, emergency governance powers, and whether privileged intervention can bypass normal controls.
- References:
  - https://www.coindesk.com/tech/2022/06/19/solend-protocol-moves-to-take-over-whale-account-to-prevent-defi-implosion/
  - https://www.coindesk.com/tech/2022/06/20/solend-invalidates-first-governance-vote-plans-new-one/

## Nirvana Finance (2022)

- Chain/category: Solana / lending-vault
- Impact: ~$3.5M attacker profit, larger protocol damage
- Summary: Flash-loan liquidity was used to manipulate protocol pricing and drain value.
- Root pattern: Flash-loan-assisted pricing/economic manipulation of protocol mechanism.
- Exploit path: Borrow large liquidity, skew the price mechanism, buy/redeem or swap against the distorted price, repay the loan, and keep the spread.
- Mapped pattern IDs: oracle-validation, oracle-mev, math
- Auditor takeaway: Check AMM/pricing invariants, manipulation cost, circuit breakers, and atomic composition assumptions.
- References:
  - https://www.certik.com/resources/blog/nirvana-finance-incident-analysis
  - https://rekt.news/nirvana-rekt/
  - https://www.theblock.co/post/159975/solana-stablecoin-nirvana-sinks-90-amid-3-5-million-flash-loan-exploit

## Crema Finance (2022)

- Chain/category: Solana / dex
- Impact: ~$8.8M reported
- Summary: Fake tick/price accounts enabled a fee-claim path to account for liquidity incorrectly.
- Root pattern: Fake tick/price account and faulty owner/account validation in concentrated liquidity fee-claim path.
- Exploit path: Provide fake accounts to the vulnerable path, cause incorrect fee accounting, and withdraw value.
- Mapped pattern IDs: missing-owner, relationship-checks, native-parser-hazards
- Auditor takeaway: Audit all instruction variants and helper paths; one correctly validated path does not protect a sibling method.
- References:
  - https://rekt.news/crema-finance-rekt/
  - https://www.certik.com/resources/blog/crema-finance-exploit
  - https://www.halborn.com/blog/post/explained-the-crema-finance-hack-july-2022

## Raydium (2022)

- Chain/category: Solana / dex
- Impact: ~$4M+ reported
- Summary: Compromised authority keys were used to drain liquidity pools.
- Root pattern: Compromised admin/owner authority used to drain pools.
- Exploit path: Use compromised authority to call privileged drain paths against pools.
- Mapped pattern IDs: upgrade-admin, governance-timelock
- Auditor takeaway: Key management, authority blast radius, and emergency/admin powers are part of security review.
- References:
  - https://www.certik.com/skynet-report/raydium-protocol-exploit-incident-analysis

## Slope wallet incident (2022)

- Chain/category: Solana / wallet
- Impact: ~9,231 wallets affected
- Summary: Wallet/application key handling failure exposed user keys.
- Root pattern: Wallet/application key handling failure, not a Solana program bug.
- Exploit path: Use exposed key material to sign unauthorized transfers from affected wallets.
- Mapped pattern IDs: upgrade-admin
- Auditor takeaway: Classify ecosystem losses correctly; wallet/key custody incidents may be out of smart-contract scope but affect threat model.
- References:
  - https://solana.com/news/8-2-2022-application-wallet-incident

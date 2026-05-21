# Missing account relationship checks

- **Pattern ID:** `relationship-checks`
- **Category:** Core Solana  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `has_one`, `Account<`, `TokenAccount`, `token::mint`, `token::authority`, `require_keys_eq`, `.key()`

**Protocol types:** lending, amm/dex, vaults, any multi-account flow

**Concepts:** correct-type account belonging to wrong user/pool/mint; vault/position/market cross-links; ATA derivation not enforced

## Why this differs from Solidity/EVM

Similar to using a valid ERC20/vault address but not verifying it is the vault for this pool/user.

The transaction supplies all accounts. A correct-type account can still belong to another user, mint, pool, market, or config.

## Bad pattern

Withdraw using `vault` and `user`, but never verify `vault.authority == vault_authority`, `position.pool == pool`, or token account mint matches expected mint.

- *Native:* Accept any token account as vault and only check it is owned by SPL Token.
- *Anchor:* `pub vault: Account<'info, TokenAccount>` with no `token::mint` or authority constraint.

## Good pattern

Validate every relationship: `has_one`, stored pubkeys, PDA derivation, ATA derivation, token mint/authority, pool/market IDs.

- *Native:* Check vault address/PDA, token mint, token authority, pool id, and expected token program.
- *Anchor:* `#[account(token::mint = mint, token::authority = vault_authority)] pub vault: Account<'info, TokenAccount>`.

## Audit checks

- [ ] Can I substitute another valid account of the same type?
- [ ] Are all token mint/authority relationships bound?
- [ ] Are pool/user/position/config keys cross-checked?

## Real incidents mapped to this pattern

- **Nomad (2022)** — ~$190M. Bridge replica accepted messages against a zero trusted root.
- **deBridge Solana signature-verification-bypass class (2022)** — Class-level audit finding; no canonical loss postmortem. Signature verification bypass class in Solana bridge/message verification flows.
- **LayerZero / Stargate DVN and library configuration (2023-2024)** — Configuration risk class. Bridge security depends on message library and DVN/oracle/relayer configuration, not only application contract code.
- **Cashio (2022)** — ~$48M. Incomplete collateral/LP/mint account validation allowed fake account chains and infinite CASH minting.
- **Crema Finance (2022)** — ~$8.8M reported. Fake tick/price account and faulty owner/account validation in concentrated liquidity fee-claim path.

## Public audit findings mapped to this pattern

- **Zellic Single Pool Audit** (SPL Single Pool): Incorrect vote account deserialization offsets; Missing authority account check; Strong account-by-account validation matrix examples
- **ChainSecurity CCTP V2 Audit** (Circle CCTP V2): V1/V2 attester separation and trust assumptions; Fast-message finality and reorg-risk considerations; Administrative controls and protocol configuration are part of the bridge security boundary
- **OtterSec EVM CCTP V2 Audit** (Circle CCTP V2 EVM contracts): Specification and implementation consistency matters across message formats; CCTP V2 integrations should be reviewed against the exact V2 contract/program interfaces

## Related patterns

- [Instruction introspection / signature verification misuse](signature-introspection.md) — `signature-introspection`
- [Missing owner check / spoofed account data](missing-owner.md) — `missing-owner`
- [Manual deserialization, offsets, and versioned account layouts](native-parser-hazards.md) — `native-parser-hazards`
- [Governance, multisig, and timelock validation gaps](governance-timelock.md) — `governance-timelock`
- [Reinitialization / initialization confusion](reinit.md) — `reinit`
- [Sysvar spoofing](sysvar-spoof.md) — `sysvar-spoof`

## References

- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/account-data-matching.md
- https://www.anchor-lang.com/docs/references/account-constraints

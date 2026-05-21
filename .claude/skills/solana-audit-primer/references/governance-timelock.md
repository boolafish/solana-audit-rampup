# Governance, multisig, and timelock validation gaps

- **Pattern ID:** `governance-timelock`
- **Category:** Governance / Admin  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `governance`, `Realms`, `Squads`, `multisig`, `proposal`, `threshold`, `timelock`

**Protocol types:** DAO-controlled programs, multisig-controlled programs

**Concepts:** governance account owner/program unchecked; proposal/instruction hash not bound to approval; emergency path bypasses timelock/threshold

## Why this differs from Solidity/EVM

Like trusting a governor/timelock address without verifying proposal state, ETA, calldata hash, or executor authority.

Solana governance may be SPL Governance/Realms/Squads/custom. Governance accounts are still caller-supplied accounts that require owner/program/state/relationship validation.

## Bad pattern

Trust an unchecked governance account or any council signer to change oracle, fees, or vault authorities.

- *Native:* `require!(admin.is_signer); config.oracle = new_oracle;` for DAO-controlled config.
- *Anchor:* `pub governance: UncheckedAccount<'info>` trusted in handler.

## Good pattern

Validate governance/multisig program id, realm/proposal/transaction ownership, threshold/timelock/executed state, exact instruction hash, and bounded parameter changes.

- *Native:* Validate governance program, proposal state, ETA, executed flag, and instruction hash for the exact config change.
- *Anchor:* Address/owner-constrain governance authority or validate DAO proposal/multisig transaction accounts and exact instruction data.

## Audit checks

- [ ] Is governance account owner/program checked?
- [ ] Is the exact proposed instruction/action bound to approval?
- [ ] Can emergency/admin paths bypass timelock or threshold?

## Real incidents mapped to this pattern

- **Ronin (2022)** — ~$624M. Off-chain validator quorum compromise.
- **Multichain (2023)** — ~$125M+. MPC/private-key compromise and opaque operational control.
- **LayerZero / Stargate DVN and library configuration (2023-2024)** — Configuration risk class. Bridge security depends on message library and DVN/oracle/relayer configuration, not only application contract code.
- **Solend whale liquidation crisis (2022)** — Bad-debt and governance crisis risk; emergency DAO proposal. Concentration, liquidation-liquidity, and governance/emergency-action risk.
- **Raydium (2022)** — ~$4M+ reported. Compromised admin/owner authority used to drain pools.

## Public audit findings mapped to this pattern

- **ChainSecurity CCTP V2 Audit** (Circle CCTP V2): V1/V2 attester separation and trust assumptions; Fast-message finality and reorg-risk considerations; Administrative controls and protocol configuration are part of the bridge security boundary

## Related patterns

- [Upgrade authority and admin controls](upgrade-admin.md) — `upgrade-admin`
- [Instruction introspection / signature verification misuse](signature-introspection.md) — `signature-introspection`
- [Missing account relationship checks](relationship-checks.md) — `relationship-checks`
- [Oracle feed validation gaps](oracle-validation.md) — `oracle-validation`
- [Oracle, ordering, and MEV/front-running assumptions](oracle-mev.md) — `oracle-mev`

## References

- https://github.com/solana-labs/solana-program-library/tree/master/governance
- https://docs.realms.today/
- https://docs.squads.so/
- https://solana.com/docs/core/programs

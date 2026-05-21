# Upgrade authority and admin controls

- **Pattern ID:** `upgrade-admin`
- **Category:** Governance / Admin  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `upgrade_authority`, `set_authority`, `BpfLoaderUpgradeable`, `admin`, `authority`

**Protocol types:** any upgradeable program, admin-controlled config

**Concepts:** single hot-key upgrade authority; admin can drain or alter oracle; no timelock/multisig on dangerous params

## Why this differs from Solidity/EVM

Comparable to proxy admin/owner/timelock risk.

Solana programs can be upgradeable via an upgrade authority; admin keys may also control config, pausing, vault migration, oracle/mint changes.

## Bad pattern

Single hot key upgrade authority or admin can upgrade program / drain / alter oracle without delay or disclosure.

## Good pattern

Inventory upgrade authority, program deploy status, multisig/timelock/DAO controls, emergency powers, and bounded admin parameter ranges.

## Audit checks

- [ ] Is the program upgradeable? Who holds upgrade authority?
- [ ] Are admin instructions properly signer/relationship constrained?
- [ ] Are dangerous parameter changes bounded and observable?

## Real incidents mapped to this pattern

- **Ronin (2022)** — ~$624M. Off-chain validator quorum compromise.
- **Multichain (2023)** — ~$125M+. MPC/private-key compromise and opaque operational control.
- **LayerZero / Stargate DVN and library configuration (2023-2024)** — Configuration risk class. Bridge security depends on message library and DVN/oracle/relayer configuration, not only application contract code.
- **Raydium (2022)** — ~$4M+ reported. Compromised admin/owner authority used to drain pools.
- **Slope wallet incident (2022)** — ~9,231 wallets affected. Wallet/application key handling failure, not a Solana program bug.

## Public audit findings mapped to this pattern

- **OtterSec Address Lookup Table Audit** (Core Solana): Indirect account loading lifecycle; Deactivation/close/reuse concerns; Authority/lifecycle edge cases

## Related patterns

- [Governance, multisig, and timelock validation gaps](governance-timelock.md) — `governance-timelock`
- [Instruction introspection / signature verification misuse](signature-introspection.md) — `signature-introspection`
- [Missing account relationship checks](relationship-checks.md) — `relationship-checks`
- [Account close, revival, and stale data](close-revival.md) — `close-revival`
- [`remaining_accounts` order/count/type assumptions](remaining-accounts.md) — `remaining-accounts`

## References

- https://solana.com/docs/core/programs
- https://github.com/solana-labs/security-audits

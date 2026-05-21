# SPL Token / Token-2022 validation gaps

- **Pattern ID:** `token2022`
- **Category:** SPL Token / Token-2022  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `InterfaceAccount`, `TokenInterface`, `spl_token_2022`, `transfer_fee`, `transfer_hook`, `get_account_data_size`, `token::mint`

**Protocol types:** any token-handling program, vaults, amm, lending

**Concepts:** transfer fee breaks balance accounting; transfer hook reentrancy; default-frozen accounts; permanent delegate; confidential transfer

## Why this differs from Solidity/EVM

Comparable to ERC20 quirks, fee-on-transfer tokens, callbacks/hooks, and wrong token address assumptions.

Token balances are accounts owned by Token/Token-2022. Token-2022 extensions can add transfer fees, hooks, default frozen state, confidential transfers, permanent delegates, CPI guard, etc.

## Bad pattern

Accept any token account as vault; check authority but not mint; support Token-2022 without accounting for transfer fees/hooks/extensions.

## Good pattern

Validate token program, mint, account authority, ATA derivation, decimals, delegate/close authority, and relevant Token-2022 extensions. If the protocol is not designed for Token-2022 extension behavior, pin to the classic Token program instead of using token-interface types. If Token-2022 is accepted, parse and enforce an explicit extension allowlist/denylist.

## Audit checks

- [ ] Is classic Token vs Token-2022 support explicit?
- [ ] Do accounting assumptions survive transfer fees/hooks/frozen accounts?
- [ ] Are ATAs derived when expected?

## Public audit findings mapped to this pattern

- **OtterSec Token-2022 Audit** (SPL Token-2022): Incorrect account ordering; Lack of mint account verification; Missing signer checks; Unnecessary writable multisig access; Confidential-transfer validation issues
- **Trail of Bits Token-2022 Audit** (SPL Token-2022): Missing ownership checks; TLV/extension parsing and length checks; Front-running concern in withheld-token withdrawal flow

## Related patterns

- [`remaining_accounts` order/count/type assumptions](remaining-accounts.md) — `remaining-accounts`
- [Missing signer authorization](missing-signer.md) — `missing-signer`
- [Missing owner check / spoofed account data](missing-owner.md) — `missing-owner`
- [Oracle, ordering, and MEV/front-running assumptions](oracle-mev.md) — `oracle-mev`

## References

- https://spl.solana.com/token
- https://spl.solana.com/token-2022
- https://solana.com/docs/tokens/extensions
- https://github.com/solana-labs/security-audits/blob/master/spl/OtterSecToken2022Audit-2023-11-03.pdf

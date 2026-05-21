# Token-interface constraints not bound to intended token program

- **Pattern ID:** `anchor-token-interface`
- **Category:** Anchor  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `InterfaceAccount`, `Interface<`, `TokenInterface`, `mint::token_program`, `token::token_program`

**Protocol types:** token programs supporting both classic Token and Token-2022

**Concepts:** token_program constraint not bound to a specific program; Token-2022 support unintentional; extensions not allowlisted/rejected

## Why this differs from Solidity/EVM

Like supporting ERC20 variants without deciding whether fee-on-transfer/hooks/permissions are allowed.

Anchor `InterfaceAccount` can support SPL Token and Token-2022, but protocol assumptions may break unless token program and extensions are intentional.

## Bad pattern

Accept `InterfaceAccount<Mint>` and `InterfaceAccount<TokenAccount>` with `Interface<TokenInterface>` but do not bind `mint::token_program` / `token::token_program` or validate extensions.

## Good pattern

Decide classic Token, Token-2022, or either; bind `mint::token_program` and `token::token_program` constraints to the same intended token program; then allowlist or reject extensions that affect accounting/transfer behavior. `InterfaceAccount` validates token-interface shape but does not prove economic compatibility.

## Audit checks

- [ ] Is Token-2022 support intentional?
- [ ] Are transfer fees/hooks/frozen/default state/permanent delegate relevant?
- [ ] Are mint/account constraints bound to the same token program?

## Related patterns

- [UncheckedAccount / AccountInfo used as trusted state](anchor-unchecked.md) — `anchor-unchecked`
- [`init_if_needed` resets existing state](anchor-init-if-needed.md) — `anchor-init-if-needed`
- [`remaining_accounts` order/count/type assumptions](remaining-accounts.md) — `remaining-accounts`
- [Anchor 0.28 behavior differs from newer tutorials](anchor-0.28-deltas.md) — `anchor-0.28-deltas`
- [Hand-rolled `try_accounts` missing derived checks](manual-try-accounts.md) — `manual-try-accounts`

## References

- https://www.anchor-lang.com/docs/tokens/basics/create-token-account
- https://www.anchor-lang.com/docs/references/account-constraints
- https://solana.com/docs/tokens/extensions

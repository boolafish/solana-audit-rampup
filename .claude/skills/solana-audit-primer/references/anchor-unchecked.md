# UncheckedAccount / AccountInfo used as trusted state

- **Pattern ID:** `anchor-unchecked`
- **Category:** Anchor  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `UncheckedAccount`, `AccountInfo`, `/// CHECK`, `Account<`, `#[account(`

**Protocol types:** any Anchor program

**Concepts:** unchecked account treated as trusted state; manual checks do not recreate constraints; CHECK comment without real validation

## Why this differs from Solidity/EVM

Like accepting arbitrary address and decoding it as your protocol contract/token without interface/address checks.

Anchor only validates what the account type/constraints express. `UncheckedAccount` and raw `AccountInfo` are present but semantically unchecked.

## Bad pattern

`pub vault: UncheckedAccount<'info>` then treat it as protocol vault or token account in handler.

## Good pattern

Use `Account<'info, Vault>`, `Account<'info, TokenAccount>`, `Program<'info, Token>`, plus seeds/owner/address/token constraints. If raw is unavoidable, manually check key, owner, signer/writable, data length, discriminator, PDA and relationships.

## Audit checks

- [ ] Why is this account unchecked?
- [ ] Did manual checks recreate all Anchor constraints?
- [ ] Can a valid-looking but attacker-owned account pass?

## Related patterns

- [`init_if_needed` resets existing state](anchor-init-if-needed.md) — `anchor-init-if-needed`
- [Token-interface constraints not bound to intended token program](anchor-token-interface.md) — `anchor-token-interface`
- [`remaining_accounts` order/count/type assumptions](remaining-accounts.md) — `remaining-accounts`
- [Anchor 0.28 behavior differs from newer tutorials](anchor-0.28-deltas.md) — `anchor-0.28-deltas`
- [Hand-rolled `try_accounts` missing derived checks](manual-try-accounts.md) — `manual-try-accounts`

## References

- https://docs.rs/anchor-lang/latest/anchor_lang/accounts/unchecked_account/struct.UncheckedAccount.html
- https://docs.rs/anchor-lang/latest/anchor_lang/accounts/account/struct.Account.html
- https://www.anchor-lang.com/docs/references/account-constraints

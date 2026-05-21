# Hand-rolled `try_accounts` missing derived checks

- **Pattern ID:** `manual-try-accounts`
- **Category:** Anchor  |  **Severity:** Critical

## Triggers — load this page when you see these

**Code signals (grep the target):** `impl<'info> Accounts`, `fn try_accounts`, `next_account_info`

**Protocol types:** programs with hand-rolled Accounts implementations

**Concepts:** manual parser skips signer/owner/discriminator checks; boundary silently shifts into remaining_accounts; aliasing not rejected

## Why this differs from Solidity/EVM

Like replacing a modifier stack with manual decoding and forgetting one authorization or type check.

Manual `Accounts` implementations consume caller-supplied account slots directly. Anchor constraints only exist if the hand-written parser recreates them.

## Bad pattern

Call `next_account_info` for each slot and return a context without checking signer, writable, owner, expected PDA, discriminator, relationships, aliasing, or exact count before `remaining_accounts`.

- *Native:* `let config = next_account_info(iter)?; Config::try_from_slice(&config.data.borrow())?;`
- *Anchor:* Manual `try_accounts` returns `UncheckedAccount` slots after presence-only parsing.

## Good pattern

Build a per-slot validation table and enforce every role: signer, writable, owner/program, address/PDA with canonical bump, discriminator-first decode, relationship checks, alias rejection, and exact fixed-account count.

- *Native:* Check owner, len, discriminator, signer/writable flags, PDA, and relationships before decode.
- *Anchor:* Manual parser validates each slot and rejects duplicates/extras before constructing the context.

## Audit checks

- [ ] Does each slot reproduce the checks a derived context would emit?
- [ ] Can one account key satisfy two roles with different assumptions?
- [ ] Can an extra account shift the boundary into `remaining_accounts`?

## Related patterns

- [UncheckedAccount / AccountInfo used as trusted state](anchor-unchecked.md) — `anchor-unchecked`
- [`init_if_needed` resets existing state](anchor-init-if-needed.md) — `anchor-init-if-needed`
- [Token-interface constraints not bound to intended token program](anchor-token-interface.md) — `anchor-token-interface`
- [`remaining_accounts` order/count/type assumptions](remaining-accounts.md) — `remaining-accounts`
- [Anchor 0.28 behavior differs from newer tutorials](anchor-0.28-deltas.md) — `anchor-0.28-deltas`

## References

- https://github.com/boolafish/solana-audit-rampup/blob/main/docs/manual-try-accounts-checklist.md
- https://www.anchor-lang.com/docs/references/account-constraints
- https://docs.rs/anchor-lang/latest/anchor_lang/derive.Accounts.html

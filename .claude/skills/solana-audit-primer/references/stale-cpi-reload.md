# Stale account data after CPI / missing reload

- **Pattern ID:** `stale-cpi-reload`
- **Category:** CPI  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `reload()`, `invoke`, `CpiContext`, `token::transfer`, `.amount`

**Protocol types:** any CPI followed by a post-condition check, balance-delta checks

**Concepts:** post-CPI invariant checked against pre-CPI cached field; missing reload() after CPI

## Why this differs from Solidity/EVM

Similar to reading cached balances before an external call and using them after the call, but Anchor account structs make this easy to miss.

Anchor deserializes `Account<T>` before the handler. If a CPI mutates that account, fields in `ctx.accounts.*` may be stale until reloaded/re-unpacked.

## Bad pattern

Read token/account state, perform CPI, then enforce post-CPI invariants using pre-CPI cached fields.

- *Native:* `let before = TokenAccount::unpack(&vault.data.borrow())?; invoke(&ix,...)?; require!(before.amount >= x);`
- *Anchor:* `let before = ctx.accounts.vault.amount; token::transfer(...)?; require!(ctx.accounts.vault.amount == before + amount);`

## Good pattern

After CPI, re-borrow/re-unpack native accounts or call Anchor `reload()` before checking balances, oracle values, or state changed by the CPI.

- *Native:* `invoke(&ix,...)?; let after = TokenAccount::unpack(&vault.data.borrow())?; require!(after.amount >= x);`
- *Anchor:* `token::transfer(...)?; ctx.accounts.vault.reload()?; require!(ctx.accounts.vault.amount == before + received);`

## Audit checks

- [ ] Are post-CPI checks using freshly loaded data?
- [ ] Do token balance delta checks reload source/destination accounts?
- [ ] Could a CPI change state that later code assumes unchanged?

## Related patterns

- [Arbitrary CPI / missing program ID check](arbitrary-cpi.md) — `arbitrary-cpi`
- [CPI account substitution / confused deputy](cpi-substitution.md) — `cpi-substitution`
- [Forwarded `remaining_accounts` as CPI trust boundary](remaining-accounts-trust.md) — `remaining-accounts-trust`

## References

- https://docs.rs/anchor-lang/latest/anchor_lang/accounts/account/struct.Account.html
- https://solana.com/docs/core/cpi
- https://www.helius.dev/blog/a-hitchhikers-guide-to-solana-program-security

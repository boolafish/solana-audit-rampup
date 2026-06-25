# Account close, revival, and stale data

- **Pattern ID:** `close-revival`
- **Category:** Lifecycle / Rent  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `close =`, `lamports`, `try_borrow_mut_lamports`, `**`, `AccountInfo`, `CloseAccount`, `close_account`

**Protocol types:** any account-closing flow, claims, escrow, queued settlement

**Concepts:** manual close leaves data/discriminator valid; same-transaction revival; refund sent to wrong recipient; token account rent stranded after authority PDA closes

## Why this differs from Solidity/EVM

Similar to selfdestruct/recreate or stale storage assumptions, but account lamports/data/owner make it Solana-specific.

Closing usually transfers lamports and resets/assigns account. Manual closes can leave data/discriminator valid; same transaction composition can revive accounts. Token accounts and ATAs are not closed by Anchor state-account `close`; they require Token Program `CloseAccount`, and can be stranded if their PDA authority state is closed first.

## Bad pattern

Drain lamports but leave owner/data/discriminator as valid state; close rent to an operator when the user paid it without documenting the fee; or settle an escrow while leaving a zero-balance token account open under an authority PDA that is about to be closed.

## Good pattern

Use Anchor `close = recipient` intentionally for program-owned state, and close SPL token accounts separately with `CloseAccount` before their authority PDA becomes unreachable. Identify the original payer or intended rent recipient for each close path.

## Audit checks

- [ ] Are closed accounts impossible to reuse later in the same transaction?
- [ ] Does close reset discriminator/data?
- [ ] Are refunds sent to the intended recipient?
- [ ] For every terminal action, are related token accounts/ATAs closed or intentionally left reclaimable?
- [ ] Does closing a PDA state account strand rent in token accounts whose authority is that PDA?
- [ ] Is the close recipient the account payer/user, or is operator/admin rent capture intended and disclosed?

## Public audit findings mapped to this pattern

- **OtterSec Address Lookup Table Audit** (Core Solana): Indirect account loading lifecycle; Deactivation/close/reuse concerns; Authority/lifecycle edge cases

## Related patterns

- [`remaining_accounts` order/count/type assumptions](remaining-accounts.md) — `remaining-accounts`
- [Upgrade authority and admin controls](upgrade-admin.md) — `upgrade-admin`
- [Reinitialization / initialization confusion](reinit.md) — `reinit`
- [Rent-exemption and realloc/storage resizing edge cases](realloc-rent.md) — `realloc-rent`

## References

- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/closing-accounts.md
- https://www.anchor-lang.com/docs/references/account-constraints

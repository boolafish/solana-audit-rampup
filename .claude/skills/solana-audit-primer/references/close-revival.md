# Account close, revival, and stale data

- **Pattern ID:** `close-revival`
- **Category:** Lifecycle / Rent  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `close =`, `lamports`, `try_borrow_mut_lamports`, `**`, `AccountInfo`

**Protocol types:** any account-closing flow, claims, escrow

**Concepts:** manual close leaves data/discriminator valid; same-transaction revival; refund sent to wrong recipient

## Why this differs from Solidity/EVM

Similar to selfdestruct/recreate or stale storage assumptions, but account lamports/data/owner make it Solana-specific.

Closing usually transfers lamports and resets/assigns account. Manual closes can leave data/discriminator valid; same transaction composition can revive accounts.

## Bad pattern

Drain lamports but leave owner/data/discriminator as valid state, then later logic trusts stale data after refund.

## Good pattern

Prefer Anchor `close = recipient` and verify exact semantics for the Anchor version in scope. For manual close logic, clear or invalidate data, transfer/refund lamports intentionally, handle owner/realloc as appropriate for the account type, and ensure no later same-transaction logic trusts the closed account.

## Audit checks

- [ ] Are closed accounts impossible to reuse later in the same transaction?
- [ ] Does close reset discriminator/data?
- [ ] Are refunds sent to the intended recipient?

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

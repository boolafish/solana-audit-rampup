# Forwarded `remaining_accounts` as CPI trust boundary

- **Pattern ID:** `remaining-accounts-trust`
- **Category:** CPI  |  **Severity:** Critical

## Triggers — load this page when you see these

**Code signals (grep the target):** `remaining_accounts`, `AccountMeta::new`, `invoke(&ix`, `is_writable`, `Kamino`, `KLend`

**Protocol types:** routers, aggregators, lending-CPI integrations

**Concepts:** caller account order forwarded straight into a CPI; writable flags passed through unvalidated; callee IDL ordering / special accounts not validated

## Why this differs from Solidity/EVM

Like forwarding an unvalidated address array to another protocol while your contract signs or accounts based on the result.

`remaining_accounts` are raw `AccountInfo`s outside Anchor validation. Routers that forward them into Kamino/KLend-style CPIs must validate the callee account schema themselves.

## Bad pattern

Map `ctx.remaining_accounts` directly into CPI `AccountMeta`s, preserving caller order and writable flags, without checking length, duplicate keys, callee IDL order, or overlap with validated context accounts.

- *Native:* `invoke(&ix, remaining_accounts)?;` where metas are caller-provided order.
- *Anchor:* `ctx.remaining_accounts.iter().map(|a| AccountMeta::new(a.key(), a.is_writable))`.

## Good pattern

Parse the slice into named callee roles; enforce exact length/order, owner/program IDs, writable/signer policy, subset/disjointness against validated accounts, event-authority/instructions-sysvar slots, and downstream relationships before CPI.

- *Native:* Convert `remaining_accounts` into a typed callee schema, validate it, then emit metas from validated roles.
- *Anchor:* `KaminoDepositAccounts::parse(ctx.remaining_accounts)?.validate_against(&ctx.accounts)?`.

## Audit checks

- [ ] Is the fixed-account and remaining-account boundary explicit?
- [ ] Are writable upgrades and signer expectations justified per callee slot?
- [ ] Was the callee IDL/source read for ordering and special accounts?

## Related patterns

- [Arbitrary CPI / missing program ID check](arbitrary-cpi.md) — `arbitrary-cpi`
- [CPI account substitution / confused deputy](cpi-substitution.md) — `cpi-substitution`
- [Stale account data after CPI / missing reload](stale-cpi-reload.md) — `stale-cpi-reload`

## References

- https://github.com/boolafish/solana-audit-rampup/blob/main/docs/remaining-accounts-cpi-trust.md
- https://solana.com/docs/core/cpi
- https://www.anchor-lang.com/docs/references/account-constraints

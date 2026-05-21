# Anchor 0.28 behavior differs from newer tutorials

- **Pattern ID:** `anchor-0.28-deltas`
- **Category:** Anchor  |  **Severity:** High

## Triggers — load this page when you see these

**Code signals (grep the target):** `anchor-lang = "0.28`, `Cargo.lock`, `init_if_needed`, `payer =`, `Signer<`

**Protocol types:** programs pinned to Anchor 0.28

**Concepts:** payer mut requirement differs; version-sensitive codegen; lamport-helper behavior differs from latest tutorials

## Why this differs from Solidity/EVM

Like auditing an older proxy/library version while reading docs for the latest release.

Anchor code generation, feature flags, lamport helpers, and payer mutability behavior are version-sensitive. A program pinned to 0.28 may need checks that newer examples hide or express differently.

## Bad pattern

Assume latest Anchor examples apply: use `init_if_needed` without checking features, omit payer `mut`, mutate lamports through raw `AccountInfo` without writable/rent/borrow checks, or trust typed accounts after raw reads.

- *Native:* N/A: this is Anchor framework behavior.
- *Anchor:* `pub payer: Signer<'info>` used for `init` rent payment in 0.28-style code.

## Good pattern

Pin `anchor-lang`/`anchor-spl` from `Cargo.lock` and features from `Cargo.toml`; compare manual contexts against generated 0.28 validation; require mutable payers; validate direct lamport mutation; reload or re-check after CPI/raw reads.

- *Native:* N/A: this is Anchor framework behavior.
- *Anchor:* `#[account(mut)] pub payer: Signer<'info>` plus lockfile/feature review.

## Audit checks

- [ ] Is the exact Anchor version and feature set known?
- [ ] Do payer accounts that fund init/realloc require `mut`?
- [ ] Are raw `AccountInfo` reads and lamport mutations protected by fresh checks?

## Related patterns

- [UncheckedAccount / AccountInfo used as trusted state](anchor-unchecked.md) — `anchor-unchecked`
- [`init_if_needed` resets existing state](anchor-init-if-needed.md) — `anchor-init-if-needed`
- [Token-interface constraints not bound to intended token program](anchor-token-interface.md) — `anchor-token-interface`
- [`remaining_accounts` order/count/type assumptions](remaining-accounts.md) — `remaining-accounts`
- [Hand-rolled `try_accounts` missing derived checks](manual-try-accounts.md) — `manual-try-accounts`

## References

- https://github.com/boolafish/solana-audit-rampup/blob/main/docs/anchor-0.28-deltas.md
- https://github.com/coral-xyz/anchor/blob/master/CHANGELOG.md
- https://docs.rs/anchor-lang/0.28.0/anchor_lang/

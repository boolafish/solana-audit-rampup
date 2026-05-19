# Anchor 0.28 deltas that matter in audits

Anchor security reviews should start by pinning the exact framework version. Many public examples target the 0.29/0.30 era, while older programs may still be on 0.28. Small framework differences change what the derive macro enforces, which helper APIs exist, and which manual code needs extra checks.

## Version triage

Check all of these before applying generic Anchor advice:

- `Cargo.lock`: exact `anchor-lang` and `anchor-spl` versions.
- `Cargo.toml`: enabled Anchor features, especially `init-if-needed` and `event-cpi`.
- `Anchor.toml`: toolchain version, cluster, and build features.
- Build commands and CI: `--features mainnet` / `devnet` flags can select different external program IDs.

Treat generated code as part of the audit surface. When a context is hand-written, compare it against `anchor expand` or a toy `#[derive(Accounts)]` context for the pinned Anchor version.

## `init_if_needed` is feature-gated

In 0.28, `init_if_needed` is not implicit. It must be enabled with the `init-if-needed` cargo feature on `anchor-lang`. If the feature is present, the usual reinitialization warning applies: the handler must not reset authority, bump, mint, or accounting fields when the account already exists.

Bad:
```rust
#[account(init_if_needed, payer = payer, space = 8 + State::LEN)]
pub state: Account<'info, State>;

pub fn use_state(ctx: Context<UseState>) -> Result<()> {
    ctx.accounts.state.admin = ctx.accounts.payer.key(); // resets on reuse
    Ok(())
}
```

Good:
```rust
#[account(init, payer = payer, space = 8 + State::LEN)]
pub state: Account<'info, State>;

pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
    ctx.accounts.state.admin = ctx.accounts.admin.key();
    ctx.accounts.state.version = 1;
    Ok(())
}
```

If `init_if_needed` is unavoidable, gate first-time writes with an explicit initialized/version field and test close/recreate and same-transaction flows.

## No `LamportsMut` helper

Anchor 0.28 code commonly mutates lamports directly through `AccountInfo` borrows. That makes writable checks, owner/rent checks, and borrow ordering more important.

Bad:
```rust
**vault.try_borrow_mut_lamports()? -= amount;
**recipient.try_borrow_mut_lamports()? += amount;
```

Good:
```rust
require!(vault.is_writable, ErrorCode::NotWritable);
require!(recipient.is_writable, ErrorCode::NotWritable);
require_keys_eq!(*vault.owner, crate::ID);

let remaining = vault.lamports().checked_sub(amount).ok_or(ErrorCode::Math)?;
require!(remaining >= Rent::get()?.minimum_balance(vault.data_len()), ErrorCode::Rent);

**vault.try_borrow_mut_lamports()? = remaining;
**recipient.try_borrow_mut_lamports()? = recipient
    .lamports()
    .checked_add(amount)
    .ok_or(ErrorCode::Math)?;
```

Watch for double-borrow panics when code borrows account data and lamports from the same `AccountInfo` in overlapping scopes.

## Signer payers are not automatically mutable

Do not assume a signer payer is writable just because it pays rent. In 0.28, payer slots that fund account creation or realloc must be declared and checked as mutable. Manual `try_accounts` implementations must reproduce that check.

Bad:
```rust
pub payer: Signer<'info>,
```

Good:
```rust
#[account(mut)]
pub payer: Signer<'info>,
```

In hand-rolled contexts, require both:
```rust
require!(payer.is_signer, ErrorCode::MissingSigner);
require!(payer.is_writable, ErrorCode::NotWritable);
```

## Typed accounts do not protect later raw reads

`Account<'info, T>` validates owner and discriminator when Anchor deserializes it. It does not make every later raw `AccountInfo` read safe. If the handler or a CPI path reads the same account through raw bytes, those reads bypass typed-account field checks and may observe stale data unless reloaded.

Bad:
```rust
let market = ctx.accounts.market.to_account_info();
let raw = market.data.borrow();
let authority = Pubkey::new_from_array(raw[8..40].try_into()?);
```

Good:
```rust
ctx.accounts.market.reload()?;
require_keys_eq!(ctx.accounts.market.authority, expected_authority);
```

If raw access is unavoidable, re-check owner, length, discriminator, version, and field offsets immediately before slicing.

## 0.29 and 0.30 review notes

- 0.29-era code often introduces token-interface patterns and more examples using `InterfaceAccount`; audit whether Token-2022 support is intended and economically compatible.
- 0.30-era tutorials may assume helper APIs or derive behavior not present in 0.28 code. Do not copy the account list shape into manual `try_accounts` without confirming emitted checks for the pinned version.
- `event-cpi`, `init-if-needed`, close semantics, duplicate mutable validation, and token-interface constraints are all version-sensitive enough to verify from the actual dependency lockfile.

## Audit checklist

- Is the project actually pinned to Anchor 0.28 in `Cargo.lock`?
- Are Anchor cargo features explicit and justified?
- Do manual `try_accounts` implementations reproduce signer, writable, owner, PDA, discriminator, and payer-mutability checks?
- Are raw `AccountInfo` reads preceded by fresh validation and followed by `reload()` when CPI can mutate data?
- Are direct lamport mutations checked for writable flags, owner/rent rules, checked math, and borrow-scope safety?

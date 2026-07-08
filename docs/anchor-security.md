# Anchor-specific security issues and best practices

## High-signal checklist
- Prefer typed accounts (`Account<T>`, `Program<T>`, `Signer`, `SystemAccount`, `InterfaceAccount<T>`) over raw `AccountInfo`/`UncheckedAccount`.
- For every account, validate: signer, mutability, owner/program id, address/PDA seeds+bump, type/discriminator, authority relationship (`has_one` or explicit constraint), and token mint/authority as applicable.
- Use `#[account(seeds = [...], bump)]` (canonical bump) or `bump = stored_bump`; store PDA bumps when reused.
- Use `has_one`, `owner`, `address`, `executable`, SPL token constraints, and custom `constraint = ...` instead of ad hoc checks in handlers.
- Treat `remaining_accounts` and `UncheckedAccount` as untrusted: manually re-run all checks Anchor would normally derive.
- Avoid `init_if_needed` unless you prove non-reset/non-reinit invariants; split init/use into separate instructions when possible.
- Use Anchor `realloc` and `close` constraints; avoid manual lamport/data mutation unless you know all edge cases.
- For Token-2022 / token-interface code, bind every mint/account to the intended token program with `*::token_program = ...`, and validate mint/authority/ATA derivation.

## Patterns

### 1. Signer authorization
Bad:
```rust
pub authority: AccountInfo<'info>, // no signature enforced
```
Good:
```rust
pub authority: Signer<'info>,
// or #[account(signer)] pub authority: AccountInfo<'info>
```
Reference: Anchor constraints `signer`; sealevel-attacks `0-signer-authorization`.

### 2. Mutable/writeback requirements
Bad:
```rust
pub state: Account<'info, State>; // changes may fail/not persist as intended
```
Good:
```rust
#[account(mut)]
pub state: Account<'info, State>;
```
Anchor docs note `mut` checks mutability and makes Anchor persist state changes.

### 3. Authority / account-data matching
Bad:
```rust
let token = SplTokenAccount::unpack(&ctx.accounts.token.data.borrow())?;
// no check that token.owner == authority.key()
```
Good:
```rust
#[account(constraint = token.owner == authority.key())]
pub token: Account<'info, TokenAccount>;
pub authority: Signer<'info>;
```
For program-owned state, prefer:
```rust
#[account(has_one = authority)]
pub user: Account<'info, User>;
pub authority: Signer<'info>;
```
Reference: sealevel-attacks `1-account-data-matching`; Anchor `has_one` docs.

### 4. Owner / address / executable constraints
Bad:
```rust
pub token_program: AccountInfo<'info>;
pub token: AccountInfo<'info>; // manually unpacked, owner unchecked
```
Good:
```rust
pub token_program: Program<'info, Token>;
#[account(owner = spl_token::ID)]
pub token: AccountInfo<'info>;
#[account(address = sysvar::instructions::ID)]
pub ix_sysvar: AccountInfo<'info>;
#[account(executable)]
pub some_program: AccountInfo<'info>;
```
For classic SPL Token-only accounts:
```rust
pub token: Account<'info, TokenAccount>;
```
If Token-2022 support is intentional, use `InterfaceAccount<'info, TokenAccount>` plus explicit `*::token_program = token_program` constraints and extension policy checks.
References: sealevel-attacks `2-owner-checks`, `5-arbitrary-cpi`; Anchor constraints docs.

### 5. Type cosplay / discriminator checks
Bad:
```rust
let user = User::try_from_slice(&ctx.accounts.user.data.borrow())?; // no discriminator/type check
```
Good:
```rust
#[account(has_one = authority)]
pub user: Account<'info, User>; // checks owner + Anchor discriminator
```
If using custom serialization, include and validate an explicit discriminant.
Reference: sealevel-attacks `3-type-cosplay`; `Account<T>` and `AccountDeserialize` docs.

### 6. `AccountInfo` / `UncheckedAccount` use
Bad:
```rust
pub vault: UncheckedAccount<'info>; // then trust it as a vault/token/state account
```
Good:
```rust
#[account(seeds=[b"vault", authority.key().as_ref()], bump, mut)]
pub vault: Account<'info, Vault>;
```
If raw accounts are unavoidable, validate all of: `key`, `owner`, `is_signer`, `is_writable`, data length, discriminator/type, PDA derivation, rent/lamports if relevant, and relationship fields.
Reference: docs.rs `UncheckedAccount` implements `Accounts` but performs no semantic validation beyond being present; Anchor account type docs emphasize preventing account substitution when using typed accounts.

### 7. PDA seeds and bump validation
Bad:
```rust
let address = Pubkey::create_program_address(&[seed, &[user_bump]], program_id)?;
require_keys_eq!(address, pda.key()); // accepts any valid noncanonical bump
```
Good:
```rust
#[account(seeds = [seed], bump)]
pub pda: Account<'info, Data>;
```
Or store and enforce the bump:
```rust
#[account(seeds=[seed], bump = data.bump)]
pub data: Account<'info, Data>;
```
Reference: sealevel-attacks `7-bump-seed-canonicalization`; Anchor PDA docs state `seeds`/`bump` validate PDA derivation and default to canonical bump when `bump` is not specified.

### 8. PDA sharing / domain separation
Bad:
```rust
// same PDA authority seeds reused across unrelated vaults/users/actions
let seeds = &[pool.mint.as_ref(), &[pool.bump]];
```
Good:
```rust
#[account(
  has_one = vault,
  has_one = withdraw_destination,
  seeds = [b"pool", withdraw_destination.key().as_ref()],
  bump = pool.bump,
)]
pub pool: Account<'info, TokenPool>;
```
Use unique static prefixes and include the authority/resource/action that scopes the PDA.
Reference: sealevel-attacks `8-pda-sharing`.

### 9. CPI with signer seeds and arbitrary CPI
Bad:
```rust
pub token_program: AccountInfo<'info>; // attacker can pass malicious program
invoke(&ix, accounts)?;
```
Good:
```rust
pub token_program: Program<'info, Token>;
token::transfer(ctx.accounts.transfer_ctx().with_signer(&[&[b"vault", &[bump]]]), amount)?;
```
Ensure CPI program ids are typed or `address = ...`, account metas correspond to validated typed accounts, and signer seeds match the actual PDA authority.
Reference: sealevel-attacks `5-arbitrary-cpi`; Anchor CPI docs.

### 10. `init_if_needed` / reinitialization
Bad:
```rust
#[account(init_if_needed, payer = payer, space = 8 + State::INIT_SPACE)]
pub state: Account<'info, State>;
// handler overwrites authority/critical fields each call
```
Good:
```rust
// Prefer separate init instruction:
#[account(init, payer = payer, space = 8 + State::INIT_SPACE)]
pub state: Account<'info, State>;
```
If using `init_if_needed`, enforce an initialized/version flag and never reset authority/config after first initialization.
Reference: docs.rs Anchor `init_if_needed` warning: feature is behind a flag and must be protected against reinitialization; sealevel-attacks `4-initialization`.

#### Open init / first-caller-becomes-admin

Singleton PDAs such as registry, config, or bridge-state accounts need an authorization policy even on the first write. If `initialize` only proves the PDA address and then stores `ctx.accounts.authority.key()`, the first successful caller becomes admin. Wormhole's 2022 `initialize` bug is the canonical example: an initialization path without the intended guard can reset or seize privileged state.

Bad:
```rust
#[account(init, payer = payer, seeds = [b"config"], bump, space = 8 + Config::LEN)]
pub config: Account<'info, Config>;
pub payer: Signer<'info>;

pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
    ctx.accounts.config.admin = ctx.accounts.payer.key();
    Ok(())
}
```

Good:
```rust
#[account(address = EXPECTED_ADMIN)]
pub admin: Signer<'info>;
#[account(init, payer = admin, seeds = [b"config"], bump, space = 8 + Config::LEN)]
pub config: Account<'info, Config>;

pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
    ctx.accounts.config.admin = ctx.accounts.admin.key();
    ctx.accounts.config.version = 1;
    Ok(())
}
```

For upgradeable programs, also verify deployment and upgrade-authority ceremony: an otherwise correct initializer is still weak if anyone can front-run it before the intended admin transaction.

### 11. `realloc`
Bad:
```rust
ctx.accounts.state.to_account_info().realloc(new_len, false)?; // manual, no rent/payer checks
```
Good:
```rust
#[account(
  mut,
  realloc = 8 + State::space(new_items),
  realloc::payer = payer,
  realloc::zero = true,
)]
pub state: Account<'info, State>;
#[account(mut)]
pub payer: Signer<'info>;
```
Best practices: cap `new_len`, prevent integer overflow, recompute dynamic space exactly, decide `zero=true` if newly exposed bytes must not contain stale data, and understand compute impact.
Reference: Anchor `realloc` docs warn manual `AccountInfo::realloc` is discouraged in favor of the constraint group due to missing native checks around `MAX_PERMITTED_DATA_INCREASE`.

### 12. `close`
Bad:
```rust
**dest.lamports.borrow_mut() += account.lamports();
**account.lamports.borrow_mut() = 0; // data/owner not reset; revival risks in older/manual code
```
Good:
```rust
#[account(mut, close = destination)]
pub account: Account<'info, Data>;
#[account(mut)]
pub destination: SystemAccount<'info>;
```
Reference: Anchor `close` is safer than manual lamport draining, but exact data/owner/realloc behavior is version-sensitive; verify target Anchor version. See Anchor constraints and sealevel-attacks `9-closing-accounts`.

### 13. `remaining_accounts`
Bad:
```rust
for acc in ctx.remaining_accounts { /* trust order/type/owner */ }
```
Good:
```rust
for acc in ctx.remaining_accounts.iter() {
    require!(acc.is_writable, ErrorCode::NotWritable);
    require_keys_eq!(*acc.owner, expected_program);
    // deserialize with discriminator/type checks; verify PDA/address/relationship
}
```
Never assume Anchor constraints apply to `remaining_accounts`; they are raw `AccountInfo`s outside the `#[derive(Accounts)]` validation path. Validate exact expected length and ordering; reject unexpected extras unless variable inputs are intentional. For each remaining account, validate owner/program, discriminator/type, writable/signer flags, PDA/address, and relationships before use.

### 14. Constraint ordering and dependencies
Best practices:
- Use `#[instruction(...)]` when constraints depend on instruction args.
- Order account fields so constraints can reference already-available accounts/data clearly.
- Put cheap structural constraints (`address`, `owner`, `seeds`) before expensive custom deserialization where possible, but do not rely on ordering as your only defense.
- Avoid side effects before all manual validations complete.

Examples:

**a) `#[instruction(...)]` brings instruction args into constraint scope.** By default constraints see only other accounts; declare args explicitly to reference them (e.g. in `seeds`).
```rust
#[derive(Accounts)]
#[instruction(user_id: u64)]              // pull the arg into scope
pub struct CreateUser<'info> {
    #[account(
        init,
        payer = payer,
        space = 8 + User::SIZE,
        seeds = [b"user", user_id.to_le_bytes().as_ref()],   // uses the arg
        bump
    )]
    pub user: Account<'info, User>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}
```
Args in `#[instruction(...)]` must match the handler's parameters in order, from the left; you can list a prefix but cannot skip leading args.

**b) Order fields so constraints reference already-declared accounts.** Anchor processes fields top-to-bottom; a reference resolves only if its target appears above.

Bad:
```rust
pub struct Bad<'info> {
    #[account(has_one = authority)] // references `authority`...
    pub user: Account<'info, User>,
    pub authority: Signer<'info>,   // ...declared below → won't resolve
}
```
Good:
```rust
pub struct Good<'info> {
    pub authority: Signer<'info>,            // declared first
    #[account(has_one = authority)]
    pub user: Account<'info, User>,
    #[account(seeds = [b"vault", user.key().as_ref()], bump)] // uses `user` above
    pub vault: Account<'info, Vault>,
}
```

**c) Cheap structural checks before expensive deserialization** — fail fast on pubkey/owner compares before deserializing a large custom account. This is a performance/clarity optimization, never a security control; every constraint must still be correct on its own.
```rust
#[account(address = sysvar::clock::ID)]  // cheap key compare
pub clock_sysvar: AccountInfo<'info>,
#[account(owner = spl_token::ID)]        // cheap owner compare
pub maybe_token: AccountInfo<'info>,
#[account(
    has_one = authority,
    constraint = pool.validate_complex_invariants()?  // expensive, runs after
)]
pub pool: Account<'info, BigPoolState>,
```

**d) Validate everything before side effects** — checks → effects → interactions. A late-failing check cannot undo earlier mutations or CPIs.

Bad:
```rust
pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
    transfer_tokens(&ctx, amount)?;                       // side effect first
    require!(amount <= ctx.accounts.vault.limit, ErrorCode::ExceedsLimit); // too late
    Ok(())
}
```
Good:
```rust
pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
    require!(amount > 0, ErrorCode::ZeroAmount);
    require!(amount <= ctx.accounts.vault.limit, ErrorCode::ExceedsLimit);
    require!(ctx.accounts.vault.is_active, ErrorCode::Paused);
    ctx.accounts.vault.balance = ctx.accounts.vault.balance
        .checked_sub(amount)
        .ok_or(ErrorCode::Underflow)?;
    transfer_tokens(&ctx, amount)?;                       // act only after checks
    Ok(())
}
```

### 15. Duplicate mutable accounts / account aliasing
Bad:
```rust
pub user_a: Account<'info, User>;
pub user_b: Account<'info, User>; // may be same logical account in older/untyped patterns
```
Good:
```rust
#[account(mut, constraint = user_a.key() != user_b.key())]
pub user_a: Account<'info, User>;
#[account(mut)]
pub user_b: Account<'info, User>;
```
Some Anchor versions/account types reject duplicate mutable accounts during account validation, but do not rely on framework behavior for business-logic distinctness. Add explicit `constraint = a.key() != b.key()` for every pair of roles that must be different, especially for `UncheckedAccount`, `AccountInfo`, token/interface accounts, and `remaining_accounts`.
Reference: Anchor `dup` docs; sealevel-attacks `6-duplicate-mutable-accounts`.

### 16. Anchor token-interface pitfalls
Bad:
```rust
pub mint: InterfaceAccount<'info, Mint>;
pub token_account: InterfaceAccount<'info, TokenAccount>;
pub token_program: Interface<'info, TokenInterface>;
// no binding that these accounts are owned/validated under the same intended token program
```
Good:
```rust
#[account(mint::token_program = token_program)]
pub mint: InterfaceAccount<'info, Mint>;
#[account(
  token::mint = mint,
  token::authority = authority,
  token::token_program = token_program,
)]
pub token_account: InterfaceAccount<'info, TokenAccount>;
pub token_program: Interface<'info, TokenInterface>;
```
Best practices: decide whether classic Token, Token-2022, or either is allowed; bind mint/account constraints to the exact token program; validate or reject extensions such as transfer fees, transfer hooks, default frozen state, permanent delegates, non-transferability, confidential transfer, CPI guard, interest-bearing/scaled UI amounts, metadata/group pointers, and close/freeze authority differences if they affect protocol assumptions; use associated token constraints when expecting an ATA. `InterfaceAccount` validates token-interface shape, not economic compatibility.
Reference: Anchor SPL token-interface docs and constraints docs show `*::token_program = <target_account>` override for token constraints.

### 17. Stale account data after CPI / `reload()`

Bad:
```rust
let before = ctx.accounts.vault.amount;
token::transfer(ctx.accounts.transfer_ctx(), amount)?;
// BUG: ctx.accounts.vault.amount may be stale
require!(ctx.accounts.vault.amount == before + amount, ErrorCode::BadBalance);
```

Good:
```rust
let before = ctx.accounts.vault.amount;
token::transfer(ctx.accounts.transfer_ctx(), amount)?;
ctx.accounts.vault.reload()?;
require!(ctx.accounts.vault.amount >= before, ErrorCode::BadBalance);
```

### 18. Version-sensitive behavior checklist

For every target, check exact versions in `Cargo.lock` / `Anchor.toml` rather than relying on generic latest-doc behavior:

- `anchor-lang` and `anchor-spl`
- `solana-program`
- `spl-token` and `spl-token-2022`
- Anchor `close`, duplicate mutable account validation, `init_if_needed`, `realloc`, token-interface constraints

## Credible references
- Anchor account constraints: https://www.anchor-lang.com/docs/references/account-constraints
- Anchor PDA docs: https://www.anchor-lang.com/docs/basics/pda
- Anchor token account / token interface docs: https://www.anchor-lang.com/docs/tokens/basics/create-token-account
- Anchor `#[derive(Accounts)]` docs: https://docs.rs/anchor-lang/latest/anchor_lang/derive.Accounts.html
- Anchor `Account<T>` docs: https://docs.rs/anchor-lang/latest/anchor_lang/accounts/account/struct.Account.html
- Anchor `UncheckedAccount` docs: https://docs.rs/anchor-lang/latest/anchor_lang/accounts/unchecked_account/struct.UncheckedAccount.html
- Anchor `InterfaceAccount<T>` docs: https://docs.rs/anchor-lang/latest/anchor_lang/accounts/interface_account/struct.InterfaceAccount.html
- Anchor `AccountDeserialize` docs: https://docs.rs/anchor-lang/latest/anchor_lang/trait.AccountDeserialize.html
- Coral sealevel-attacks examples: https://github.com/coral-xyz/sealevel-attacks
- SlowMist Solana smart contract security best practices: https://github.com/slowmist/solana-smart-contract-security-best-practices
- Helius Solana program security guide: https://www.helius.dev/blog/a-hitchhikers-guide-to-solana-program-security

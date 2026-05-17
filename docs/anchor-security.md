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
Even better for SPL Token accounts:
```rust
pub token: Account<'info, TokenAccount>;
```
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
Reference: Anchor `close` constraint sends lamports, assigns owner to System Program, and resets data; sealevel-attacks `9-closing-accounts`.

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
Never assume Anchor constraints apply to `remaining_accounts`; they are raw `AccountInfo`s outside the `#[derive(Accounts)]` validation path.

### 14. Constraint ordering and dependencies
Best practices:
- Use `#[instruction(...)]` when constraints depend on instruction args.
- Order account fields so constraints can reference already-available accounts/data clearly.
- Put cheap structural constraints (`address`, `owner`, `seeds`) before expensive custom deserialization where possible, but do not rely on ordering as your only defense.
- Avoid side effects before all manual validations complete.

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
Anchor now prevents duplicate mutable accounts by default for mutable serializing account types; only use `dup` intentionally.
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
Best practices: decide whether classic Token, Token-2022, or either is allowed; bind mint/account constraints to the exact token program; validate extensions/transfer hooks/confidential-transfer/freeze authority if they affect protocol assumptions; use associated token constraints when expecting an ATA.
Reference: Anchor SPL token-interface docs and constraints docs show `*::token_program = <target_account>` override for token constraints.

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

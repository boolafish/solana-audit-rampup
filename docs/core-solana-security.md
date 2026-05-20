# Solana security audit notes for Solidity auditors

Audience: experienced Ethereum/Solidity auditor reviewing Solana programs. Emphasis: Solana account model, PDAs, CPI, signer/writable semantics, ownership, CTF-style bugs.

## Mental model differences vs Solidity

- **Code and state are separate.** Programs are executable accounts, often with separate ProgramData when upgradeable. They do not have implicit per-contract storage like EVM contracts; persistent protocol/user state lives in separate accounts supplied by the transaction. A handler must validate every account it uses.
- **Callers choose most accounts.** Unlike Solidity where `address(this).storage` is implicit, Solana instructions receive an arbitrary `AccountInfo[]`. Missing account validation is the root of many bugs.
- **Authorization is not `msg.sender`.** Any account can be passed; `is_signer` only means the transaction included that account's signature, and PDAs can “sign” only via `invoke_signed` with valid seeds.
- **Mutability is declared up front.** Accounts must be marked writable in the transaction/CPI to change data or lamports. Bugs often come from failing to require/check `is_writable`, duplicate writable aliases, or assuming readonly means safe.
- **Ownership is data-write authority, not asset ownership.** Only an account’s owning program may modify its data, resize it, or assign it under normal runtime rules. Lamport decreases are separately constrained by runtime ownership/signature/program rules, while lamport credits can generally be made to writable accounts. Token ownership is SPL Token state, not Solana account `owner`.
- **CPI is like an external call, but with explicit accounts and program id.** The caller supplies the callee program account and all callee accounts; arbitrary-CPI bugs occur when program IDs are not pinned.
- **Transactions are atomic, and account locks drive parallel execution.** A transaction succeeds or fails as a unit; declared writable accounts are locked and constrain parallelism. Compute and account-lock choices can become DoS surfaces.

## How an instruction executes (visual)

In EVM you call a contract and it reaches into its own storage. On Solana the **caller hands the program every account it will touch**, as a flat list, with per-account `is_signer` / `is_writable` flags. The program must prove each one is the account it expected.

```mermaid
flowchart TD
    subgraph TX["Transaction — all or nothing"]
      direction TB
      IX["Instruction&nbsp;&nbsp;program_id + accounts[] + data"]
    end
    IX --> PROG["Program account&nbsp;(executable code)"]
    IX --> S["State PDA&nbsp;&nbsp;owner = your program&nbsp;&nbsp;writable"]
    IX --> V["Token vault&nbsp;&nbsp;owner = SPL Token&nbsp;&nbsp;writable"]
    IX --> U["User&nbsp;&nbsp;is_signer = true"]
    PROG -->|"may write data of"| S
    PROG -. "reads only; cannot write its bytes" .-> V
    PROG -->|"checks is_signer / has_one"| U
```
<span class="figcap">The caller chooses PROG, S, V, U. Nothing is implicit — every arrow is a check the program must perform.</span>

**Anatomy of any account.** The four runtime fields below are the *only* trust primitives the runtime gives you. Everything else (`admin`, `mint`, `amount`, `bump`) is just bytes in `data` that some program wrote.

```mermaid
flowchart LR
    acc["ACCOUNT"] --- l["lamports&nbsp;(balance)"]
    acc --- o["owner&nbsp;= program allowed to write data"]
    acc --- d["data&nbsp;= raw bytes (your struct lives here)"]
    acc --- e["executable&nbsp;/ rent_epoch"]
```

**The trap Solidity auditors fall into: `owner` ≠ token owner.** Account `owner` is *who may write the bytes*. The token holder is a **field inside** a token account whose `owner` is the SPL Token program.

```mermaid
flowchart TD
    yp["Your program"] -->|"writes bytes of"| st["State account&nbsp;&nbsp;owner = your program"]
    spl["SPL Token program"] -->|"writes bytes of"| ta["Token account&nbsp;&nbsp;owner = SPL Token"]
    ta -.->|"holds FIELD"| auth["authority = user pubkey&nbsp;&nbsp;mint = ...&nbsp;&nbsp;amount = ..."]
    classDef hl fill:#fff7f5,stroke:#c2410c;
    class auth hl;
```

## Pitfalls / vulnerability notes

### 1. Missing signer authorization
- **Why Solana-specific / different:** There is no automatic `msg.sender` for a privileged account. A pubkey appearing in account data or in the account list is not proof of authorization.
- **Bad pattern:** `if ctx.accounts.user.key() == state.admin { ... }` but `user` is `AccountInfo`/`UncheckedAccount` and not required to sign.
- **Mitigation:** Require `account.is_signer`; in Anchor use `Signer<'info>` or `#[account(signer)]`, plus relationship constraints such as `has_one = admin`.

```mermaid
flowchart LR
    pk["A pubkey sits in accounts[]"] --> q{{"is_signer == true?"}}
    q -->|"no"| bad["Just an address anyone can supply&nbsp;❌ forge admin"]
    q -->|"yes"| good["Tx carried this key's signature&nbsp;✅ require Signer + has_one"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class bad b;
    class good g;
```

```rust
// ❌ BAD: `admin` is just an address in the list — anyone can supply it.
#[derive(Accounts)]
pub struct SetFee<'info> {
    pub config: Account<'info, Config>,
    /// CHECK: compared by key only, never required to sign
    pub admin: UncheckedAccount<'info>,
}
// if config.admin == admin.key() { ... }  // passes with NO signature from admin

// ✅ GOOD: require the signature, and bind it to stored authority.
#[derive(Accounts)]
pub struct SetFee<'info> {
    #[account(mut, has_one = admin)]
    pub config: Account<'info, Config>,
    pub admin: Signer<'info>, // tx must carry admin's signature
}
```

- **References:**
  - Solana Program Security course, signer auth: https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/signer-auth.md
  - Anchor account constraints: https://www.anchor-lang.com/docs/references/account-constraints

### 2. Missing owner check / fake account data
- **Why different:** Account data deserialization from `AccountInfo` does not by itself prove that the data was written by the expected program. Attackers can create accounts they own with spoofed bytes unless ownership is checked.
- **Bad pattern:** Deserialize a config/vault/user state from an arbitrary account and trust fields like `admin`, `balance`, `mint`, or `bump`.
- **Mitigation:** Check `account.owner == program_id` for program state; for SPL Token accounts check owner is the SPL Token program and validate token-account fields. In Anchor prefer `Account<'info, T>`, `Program<'info, Token>`, or `#[account(owner = ...)]`.

```mermaid
flowchart TD
    atk["Attacker creates an account THEY own&nbsp;and writes fake bytes: admin = attacker"] --> pass["Passes it where your Config is expected"]
    pass --> chk{{"check account.owner == program_id ?"}}
    chk -->|"skipped ❌"| trust["Bytes deserialize fine → program trusts fake admin → drained"]
    chk -->|"enforced ✅"| reject["owner = attacker ≠ program → rejected before use"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class trust b;
    class reject g;
```
<span class="figcap">Deserialization only proves the bytes *parse* — not who wrote them. The owner check is what makes the bytes trustworthy.</span>

**Example — native (no framework):**

```rust
// ❌ BAD: trusts bytes from whatever account the caller passed in.
let config = Config::try_from_slice(&config_ai.data.borrow())?;
require!(config.admin == authority.key(), MyError::NotAdmin);
// Attacker creates an account THEY own, pre-loaded with admin = attacker.
// try_from_slice succeeds, and the check passes against the forged bytes.

// ✅ GOOD: prove your program wrote these bytes *before* trusting them.
require_keys_eq!(*config_ai.owner, crate::ID, MyError::WrongOwner);
let config = Config::try_from_slice(&config_ai.data.borrow())?;
require!(config.admin == authority.key(), MyError::NotAdmin);
```

**Example — Anchor (the type does the check for you):**

```rust
#[derive(Accounts)]
pub struct UpdateConfig<'info> {
    // ❌ BAD: UncheckedAccount / AccountInfo skips the owner & discriminator
    //         checks — you are back to trusting raw caller-supplied bytes.
    // pub config: UncheckedAccount<'info>,

    // ✅ GOOD: Account<'info, T> enforces owner == program_id AND the 8-byte
    //          discriminator before deserializing; has_one ties it to admin.
    #[account(mut, has_one = admin)]
    pub config: Account<'info, Config>,
    pub admin: Signer<'info>,

    // ✅ For SPL token accounts the owner must be the *Token program*, not
    //    yours — Account<'info, TokenAccount> checks owner == spl_token::ID.
    pub vault: Account<'info, TokenAccount>,
}
```

- **References:**
  - Solana accounts docs: https://solana.com/docs/core/accounts
  - Program Security owner checks: https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/owner-checks.md
  - Neodyme common pitfalls: https://neodyme.io/en/blog/solana_common_pitfalls/

### 3. Missing account data matching / relationship checks
- **Why different:** The user supplies all accounts, so a valid account of the correct type can still be the wrong account for this instruction.
- **Bad pattern:** Withdraw from `vault` using `user` but never verify `vault.authority == user.key()` or `position.pool == pool.key()`.
- **Mitigation:** Validate all relationships: `has_one`, stored pubkeys, mint matches, token account authority, vault PDA derivation, pool/market IDs. In Anchor use `#[account(has_one = ...)]`, `constraint = ...`, and seed constraints.

```mermaid
flowchart TD
    inp["withdraw(vault, user)"] --> q{{"vault.authority == user.key() ?"}}
    q -->|"not checked ❌"| any["Any valid Vault works → drain someone else's vault"]
    q -->|"checked ✅"| ok["Only the caller's own vault is touched"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class any b; class ok g;
```

```rust
// ❌ BAD: right *type*, wrong *instance* — never ties the vault to the signer.
#[account(mut)] pub vault: Account<'info, Vault>,
pub user: Signer<'info>,
// uses vault.balance, but any user can pass any other user's vault account.

// ✅ GOOD: has_one enforces vault.authority == authority.key().
#[account(mut, has_one = authority @ MyError::WrongAuthority)]
pub vault: Account<'info, Vault>,
pub authority: Signer<'info>,
// Native: require_keys_eq!(vault.authority, authority.key());
```

- **References:**
  - Account data matching: https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/account-data-matching.md
  - Anchor constraints: https://www.anchor-lang.com/docs/references/account-constraints

### 4. Type cosplay / discriminator confusion
- **Why different:** Raw account bytes can be interpreted as any struct if no discriminator/type tag is enforced. This resembles storage layout confusion more than a typical Solidity bug.
- **Bad pattern:** Two account types share compatible layouts; handler deserializes unchecked bytes as `AdminConfig` when the account is actually `UserProfile`.
- **Mitigation:** Use Anchor `#[account]` types, which include an 8-byte discriminator, or implement explicit discriminators/magic/version fields in native programs.

```mermaid
flowchart LR
    bytes["Raw account bytes"] --> a["read as AdminConfig"]
    bytes --> b["actually a UserProfile"]
    a -. "same layout, no tag" .-> conf["Privilege confusion ❌"]
    disc["8-byte discriminator / version tag"] --> safe["Wrong type → rejected ✅"]
    classDef bd fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class conf bd; class safe g;
```

```rust
// ❌ BAD: no type tag — UserProfile bytes deserialize fine as AdminConfig.
#[derive(BorshDeserialize)]
struct AdminConfig { admin: Pubkey, fee_bps: u16 }
let cfg = AdminConfig::try_from_slice(&ai.data.borrow())?; // wrong account!

// ✅ GOOD: Anchor #[account] prepends an 8-byte discriminator and checks it.
#[account]
pub struct AdminConfig { pub admin: Pubkey, pub fee_bps: u16 }
// Account<'info, AdminConfig> rejects any account whose discriminator
// isn't sha256("account:AdminConfig")[..8]. Native: store an explicit
// account-type / version byte and match on it before use.
```

- **References:**
  - Type cosplay: https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/type-cosplay.md
  - Sealevel attacks examples: https://github.com/coral-xyz/sealevel-attacks

### 5. Reinitialization / initialization confusion
- **Why different:** Account allocation, ownership assignment, and initialization are explicit steps. An existing account can be reused if the program only checks size/owner loosely or forgets an initialized flag.
- **Bad pattern:** `initialize` overwrites admin/config on an already-initialized account; or `init_if_needed` is used without protecting against state reset.
- **Mitigation:** Use Anchor `init` for one-time creation; store and check `is_initialized`/version; be very cautious with `init_if_needed`; validate discriminator and expected zeroed state only for new accounts.

```mermaid
flowchart TD
    call["initialize(config)"] --> q{{"already initialized?"}}
    q -->|"not checked ❌"| reset["Overwrites admin → attacker re-inits and seizes control"]
    q -->|"init / is_initialized ✅"| once["Second call fails — set up exactly once"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class reset b; class once g;
```

```rust
// ❌ BAD: re-runs on an existing account, resetting admin to the caller.
pub fn initialize(ctx: Context<Init>) -> Result<()> {
    ctx.accounts.config.admin = ctx.accounts.payer.key();
    Ok(())
}
#[derive(Accounts)]
pub struct Init<'info> {
    #[account(mut)] pub config: Account<'info, Config>, // not `init`!
    #[account(mut)] pub payer: Signer<'info>,
}

// ✅ GOOD: `init` allocates the account and fails if it already exists.
#[derive(Accounts)]
pub struct Init<'info> {
    #[account(init, payer = payer, space = 8 + Config::LEN)]
    pub config: Account<'info, Config>,
    #[account(mut)] pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}
// Avoid init_if_needed unless you guard against state reset. Native: check
// an is_initialized flag and bail if it is already set.
```

- **References:**
  - Reinitialization attacks: https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/reinitialization-attacks.md
  - Anchor account constraints (`init`, `init_if_needed`): https://www.anchor-lang.com/docs/references/account-constraints

### 6. PDA seed/bump mistakes and non-canonical bumps
- **Why different:** PDAs are deterministic addresses controlled by a program, used as authorities/signers. Multiple valid bumps may exist for the same seed prefix if the bump is caller-chosen; this is not a cryptographic collision, but multiple valid PDA addresses for one logical resource.
- **Bad pattern:** Accept user-supplied bump with `create_program_address` and do not ensure it is the canonical bump from `find_program_address`; use low-entropy/shared seeds; omit domain separators.
- **Mitigation:** Use canonical bump from `find_program_address`; persist the bump when needed; in Anchor use `seeds = [...]` and `bump`; include unique domain prefixes and relevant account keys in seeds.

A PDA is a deterministic address with **no private key** — the program "signs" for it by re-supplying the seeds. Scope the seeds tightly or one authority ends up controlling everything.

```mermaid
flowchart LR
    seeds["seeds&nbsp;[b&quot;vault&quot;, pool, mint]"] --> fpa["find_program_address(seeds, program_id)"]
    pid["program_id"] --> fpa
    fpa --> pda["PDA address + canonical bump&nbsp;(off-curve, no key)"]
    pda -->|"invoke_signed(seeds, bump)"| cpi["Program signs CPI as this authority"]
    note["Seeds = [b&quot;vault&quot;] only&nbsp;→ ONE authority for ALL vaults ❌"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    class note b;
```

```rust
// ❌ BAD: trusts a caller-supplied bump; many valid bumps → many addresses.
let pda = Pubkey::create_program_address(
    &[b"vault", pool.key().as_ref(), &[user_bump]], program_id)?;

// ✅ GOOD: derive (and persist) the canonical bump.
let (pda, bump) = Pubkey::find_program_address(
    &[b"vault", pool.key().as_ref()], program_id);

// ✅ Anchor pins seeds + the stored canonical bump for you:
#[account(seeds = [b"vault", pool.key().as_ref()], bump = vault.bump)]
pub vault: Account<'info, Vault>,
```

- **References:**
  - Solana PDA docs: https://solana.com/docs/core/pda
  - Bump seed canonicalization: https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/bump-seed-canonicalization.md

### 7. PDA sharing / overly broad PDA authority
- **Why different:** A PDA may act as signing authority for many resources. If seeds are global or under-scoped, privileges intended for one pool/user/market can apply to another.
- **Bad pattern:** Single `vault_authority = PDA("vault")` controls all vaults; any instruction that can sign for it can move assets across unrelated vaults.
- **Mitigation:** Scope seeds to the protected object: `PDA("vault", pool.key(), mint.key())`; validate token vault belongs to that PDA and the expected mint/pool.

```mermaid
flowchart TD
    g["PDA seed = [vault] — one authority"] --> v1["Vault A"]
    g --> v2["Vault B"]
    g -->|"signs for both ❌"| cross["Move B's funds via A's instruction"]
    s["PDA seed = [vault, pool, mint] — scoped"] --> only["Authority binds to exactly one vault ✅"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef gg fill:#f1fff9,stroke:#0fa76e;
    class cross b; class only gg;
```

```rust
// ❌ BAD: one global authority signs for every vault.
#[account(seeds = [b"vault"], bump)]
pub vault_authority: SystemAccount<'info>,

// ✅ GOOD: scope the authority to the specific pool + mint it guards.
#[account(seeds = [b"vault", pool.key().as_ref(), mint.key().as_ref()], bump)]
pub vault_authority: SystemAccount<'info>,
// A signature for pool A's authority can no longer move pool B's assets.
```

- **References:**
  - PDA sharing: https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/pda-sharing.md
  - Solana PDA docs: https://solana.com/docs/core/pda

### 8. Arbitrary CPI / missing program ID check
- **Why different:** CPI target program account is often passed by the caller. If not checked, an attacker can pass a malicious program that accepts the same accounts and returns success or performs unintended actions.
- **Bad pattern:** Build `Instruction { program_id: supplied_program.key(), ... }` and call `invoke` without ensuring it is `spl_token::ID`, System Program, associated token program, etc.
- **Mitigation:** Pin program IDs. In Anchor use `Program<'info, Token>`, `Program<'info, System>`, CPI helper crates, or explicit `require_keys_eq!(program.key(), expected_id)`.

```mermaid
flowchart TD
    ix["invoke(program_id = caller-supplied, accounts)"] --> q{{"program_id == spl_token::ID ?"}}
    q -->|"not pinned ❌"| evil["A look-alike program returns Ok and does as it pleases"]
    q -->|"pinned ✅"| real["Only the real Token program can run"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class evil b; class real g;
```

```rust
// ❌ BAD: invokes whatever program the caller passed in.
let ix = spl_token::instruction::transfer(token_program.key, /* ... */)?;
invoke(&ix, &[from, to, authority, token_program.clone()])?;

// ✅ GOOD: pin the program id — Anchor's Program<> type does exactly this.
pub token_program: Program<'info, Token>,
// Native: require_keys_eq!(token_program.key(), spl_token::ID);
```

- **References:**
  - CPI docs: https://solana.com/docs/core/cpi
  - Arbitrary CPI: https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/arbitrary-cpi.md
  - Anchor CPI basics: https://www.anchor-lang.com/docs/basics/cpi

### 9. CPI account substitution / confused deputy
- **Why different:** Even if the callee program ID is correct, every callee account is also caller-supplied. The current program may sign with a PDA over attacker-selected token accounts.
- **Bad pattern:** Program signs an SPL Token `transfer` from `source` to `dest` but does not verify `source` is the protocol vault, `source.owner == vault_authority`, mint matches, and `dest` is the user’s expected ATA.
- **Mitigation:** Validate all CPI accounts before invoking; prefer associated token account constraints; check token account `mint`, `owner/authority`, and PDA seeds.

Even with the *right* token program, the `source`/`dest` accounts are still caller-supplied. Your PDA will happily sign a transfer out of the wrong vault if you don't pin them.

```mermaid
sequenceDiagram
    actor U as Attacker
    participant P as Your program (PDA signer)
    participant T as SPL Token program
    U->>P: withdraw(source, dest)
    Note over P: source & dest came from the attacker
    alt accounts NOT validated ❌
        P->>T: invoke_signed transfer(source → dest)
        T-->>U: protocol funds land in attacker's dest
    else validate first ✅
        P->>P: require source == vault PDA, mint ok, dest == user ATA
        P->>T: invoke_signed only after all checks pass
    end
```

```rust
// ❌ BAD: signs a transfer over caller-chosen source/dest accounts.
let cpi = Transfer { from: source.clone(), to: dest.clone(),
                     authority: vault_authority.clone() };
token::transfer(CpiContext::new_with_signer(token_program, cpi, signer), amt)?;

// ✅ GOOD: constrain accounts so the PDA can only move ITS vault → user's ATA.
#[account(mut, address = expected_vault, token::mint = mint,
          token::authority = vault_authority)]
pub source: Account<'info, TokenAccount>,
#[account(mut, associated_token::mint = mint, associated_token::authority = user)]
pub dest: Account<'info, TokenAccount>,
```

- **References:**
  - CPI docs: https://solana.com/docs/core/cpi
  - Anchor SPL constraints (`token::mint`, `token::authority`, `associated_token::*`): https://www.anchor-lang.com/docs/references/account-constraints

### 10. Duplicate mutable accounts / aliasing
- **Why different:** The same account pubkey can be supplied for multiple account parameters unless explicitly constrained. Two mutable references that the code assumes distinct can alias.
- **Bad pattern:** `transfer_rewards(from, to)` where `from` and `to` may be the same account, bypassing balance checks or causing double-credit/debit logic; game examples where player A and B accounts can be identical.
- **Mitigation:** For every pair that must be distinct, check `a.key() != b.key()`; in Anchor use `constraint = a.key() != b.key()`.

```mermaid
flowchart LR
    call["transfer(from, to)"] --> q{{"from.key() == to.key() ?"}}
    q -->|"allowed ❌"| dbl["Self-transfer credits & debits one account → conjures value"]
    q -->|"rejected ✅"| ok["from and to are guaranteed distinct"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class dbl b; class ok g;
```

```rust
// ❌ BAD: `from` and `to` may be the same account; balance math double-counts.
#[derive(Accounts)]
pub struct Move<'info> {
    #[account(mut)] pub from: Account<'info, Vault>,
    #[account(mut)] pub to: Account<'info, Vault>,
}

// ✅ GOOD: require distinctness explicitly.
#[derive(Accounts)]
pub struct Move<'info> {
    #[account(mut)] pub from: Account<'info, Vault>,
    #[account(mut, constraint = to.key() != from.key() @ MyError::DupAccount)]
    pub to: Account<'info, Vault>,
}
```

- **References:**
  - Duplicate mutable accounts: https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/duplicate-mutable-accounts.md
  - Sealevel attacks: https://github.com/coral-xyz/sealevel-attacks

### 11. Writable/signer privilege assumptions in CPI
- **Why different:** Signer and writable privileges propagate only according to the caller’s account metas and runtime rules; a callee cannot write an account not marked writable by the transaction/CPI. Conversely, marking too many accounts writable increases attack and DoS surface.
- **Bad pattern:** Native program mutates lamports/data without checking account is writable and relying on runtime failure late; CPI marks attacker-controlled accounts writable/signer-capable unnecessarily.
- **Mitigation:** Require mutability only where needed (`#[account(mut)]`); check writable for raw `AccountInfo`; minimize CPI metas; treat `is_signer`/`is_writable` as privileges to validate, not business-logic identity.

```mermaid
flowchart LR
    a["account in tx / CPI metas"] --> w{{"writable / signer only where needed?"}}
    w -->|"over-marked ❌"| surf["Extra write/sign power = larger attack & lock-contention surface"]
    w -->|"least privilege ✅"| min["Runtime blocks unauthorized writes; smaller surface"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class surf b; class min g;
```

```rust
// ❌ BAD: marks config writable in a read-only flow; infers identity from signer.
#[account(mut)] pub config: Account<'info, Config>, // never mutated here

// ✅ GOOD: request mutability only on what you actually change.
pub config: Account<'info, Config>,                 // read-only → not locked writable
#[account(mut)] pub position: Account<'info, Position>,
// Native: if you mutate a raw AccountInfo, assert account.is_writable, and
// still validate authority against stored keys — never trust is_signer alone.
```

- **References:**
  - Transactions/account metas: https://solana.com/docs/core/transactions
  - CPI docs: https://solana.com/docs/core/cpi

### 12. Sysvar spoofing
- **Why different:** Sysvars can be loaded either from trusted sysvar APIs or passed as accounts. If passed unchecked, an attacker may provide a fake account with spoofed clock/instructions/rent data.
- **Bad pattern:** Read `Clock` or `Instructions` sysvar from an arbitrary `AccountInfo` without checking the sysvar ID.
- **Mitigation:** Use `Clock::get()`, `Rent::get()`, etc. when available; otherwise check `account.key == sysvar::clock::ID` / appropriate ID and owner. In Anchor use `Sysvar<'info, Clock>`.

```mermaid
flowchart TD
    src["Need the Clock"] --> q{{"how is it obtained?"}}
    q -->|"AccountInfo, unchecked ❌"| fake["Attacker passes a fake account with a spoofed timestamp"]
    q -->|"Clock::get() / verify sysvar id ✅"| real["Genuine runtime clock"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class fake b; class real g;
```

```rust
// ❌ BAD: reads clock from a caller-supplied account without checking its key.
let clock = Clock::from_account_info(&clock_ai)?; // clock_ai could be anything

// ✅ GOOD: pull it from the runtime (unspoofable), or pin the sysvar id.
let clock = Clock::get()?;
// or in Anchor:  pub clock: Sysvar<'info, Clock>,
```

- **References:**
  - Solana sysvar module docs: https://docs.rs/solana-program/latest/solana_program/sysvar/index.html
  - Anchor account types/constraints: https://www.anchor-lang.com/docs/references/account-constraints

### 13. Account close, revival, and stale data
- **Why different:** Closing is usually implemented by transferring lamports and assigning/zeroing data. Historically/CTF-style, if data/discriminator remains and lamports are later restored in the same transaction, a “closed” account can be revived or reused unexpectedly.
- **Bad pattern:** Drain lamports but leave owner/data/discriminator as valid program state; later instruction in same transaction re-funds account and uses stale state. Another variant branches on `lamports == 0` or an exact rent balance even though anyone can `system::transfer` lamports into a PDA.
- **Mitigation:** Prefer Anchor `close = recipient` and verify exact behavior for the Anchor version in scope; for manual closes, clear/invalidate data, refund lamports intentionally, and ensure no subsequent same-transaction logic trusts the account. Older defensive patterns use a closed-account sentinel such as `CLOSED_ACCOUNT_DISCRIMINATOR` so a re-funded account still fails type checks.

Because everything is atomic, an attacker can re-fund a "closed" account *later in the same transaction*. If you only drained lamports, the still-valid data revives.

```mermaid
flowchart TD
    naive["Naive close: move out lamports,&nbsp;leave data + discriminator intact"] --> tx["Same transaction, next instruction:&nbsp;system::transfer lamports back in"]
    tx --> revive["Account 'undead' with valid stale state ❌"]
    safe["close = recipient → zero data&nbsp;+ set closed sentinel discriminator ✅"] --> dead["Re-funded account fails the type check"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class revive b;
    class dead g;
```

```rust
// ❌ BAD: drains lamports but leaves valid data → revivable in same tx.
**recipient.lamports.borrow_mut() += account.lamports();
**account.lamports.borrow_mut() = 0; // data + discriminator still intact

// ✅ GOOD: let Anchor close it (zeroes data, writes the CLOSED discriminator).
#[account(mut, close = recipient)]
pub state: Account<'info, State>,
pub recipient: SystemAccount<'info>,
// Native: zero the data AND set a closed sentinel so a re-funded account
// fails the next type check.
```

- **References:**
  - Closing accounts: https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/closing-accounts.md
  - Anchor `close` constraint: https://www.anchor-lang.com/docs/references/account-constraints

### 14. Rent-exemption and storage resizing edge cases
- **Why different:** Accounts must hold enough lamports for rent-exempt storage, and reallocating data changes required balance. In current Solana practice, “rent” usually means minimum balance/account lifecycle, not an Ethereum-like recurring storage fee. Storage is not a free mapping slot as in EVM.
- **Bad pattern:** `realloc` to larger size without funding rent; shrink/grow without zeroing new bytes; leave sensitive or type-confusing stale bytes; assume closed/zero-lamport accounts cannot reappear in same transaction.
- **Mitigation:** Use Anchor `realloc`, `realloc::payer`, `realloc::zero` constraints; recompute rent for final size; zero newly allocated regions when needed; test shrink/grow/close flows.

```mermaid
flowchart TD
    rz["realloc to a larger size"] --> q{{"funded for new rent + new bytes zeroed?"}}
    q -->|"no ❌"| bad["Not rent-exempt, or stale bytes reinterpreted as state"]
    q -->|"yes ✅"| ok["Rent-exempt; the grown region is zeroed"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class bad b; class ok g;
```

```rust
// ✅ Anchor funds the extra rent and zeroes the grown region for you:
#[account(mut, realloc = 8 + NewState::LEN,
          realloc::payer = payer, realloc::zero = true)]
pub state: Account<'info, NewState>,
#[account(mut)] pub payer: Signer<'info>,
pub system_program: Program<'info, System>,
// Native: top up to Rent::get()?.minimum_balance(new_len) and zero new bytes
// yourself — a larger account that isn't rent-exempt will fail.
```

- **References:**
  - Solana accounts/rent: https://solana.com/docs/core/accounts
  - Anchor realloc constraints: https://www.anchor-lang.com/docs/references/account-constraints

### 15. Integer overflow/underflow and precision/rounding
- **Why different:** Unlike Solidity 0.8 checked arithmetic, Rust primitive integer overflow is not automatically safe in optimized Solana program builds unless overflow checks or checked/saturating APIs are used. Solana programs commonly use fixed-point math, token decimals, and `u64` lamports/token amounts. Solidity auditors will recognize this class, but Rust/Solana APIs make checked math a conscious choice.
- **Bad pattern:** `balance -= amount`, `amount * price / scale`, or reward-per-share math without `checked_*`, larger intermediate type, rounding policy, or decimal normalization.
- **Mitigation:** Use `checked_add/sub/mul/div`, `u128` intermediates, explicit rounding direction, decimal bounds, and invariant tests/fuzzing. Be careful with division before multiplication and fee rounding that can be exploited by repeated small trades.

```mermaid
flowchart LR
    m["balance - amount"] --> q{{"checked math?"}}
    q -->|"raw `-` in release ❌"| wrap["Underflow wraps to a huge u64 → effectively infinite balance"]
    q -->|"checked_sub ✅"| err["Returns None → clean error, no wrap"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class wrap b; class err g;
```

```rust
// ❌ BAD: wraps in release builds (overflow-checks often off) → underflow.
self.balance -= amount;
let value = amount * price / scale; // can overflow u64 mid-expression

// ✅ GOOD: checked math, wider intermediates, explicit rounding direction.
self.balance = self.balance.checked_sub(amount).ok_or(MyError::Underflow)?;
let value = (amount as u128 * price as u128 / scale as u128) as u64;
// (Also enable overflow-checks = true in the release profile.)
```

- **References:**
  - Neodyme common pitfalls (overflow/precision examples): https://neodyme.io/en/blog/solana_common_pitfalls/
  - Solana Program Security overview: https://github.com/solana-foundation/developer-content/tree/main/content/courses/program-security

### 16. Instruction introspection / Ed25519 or secp verification misuse
- **Why different:** Signature verification programs and the Instructions sysvar are often used to validate off-chain signatures. The verified message/signature instruction must be tied to the current instruction and expected data.
- **Bad pattern:** Check that an Ed25519 instruction exists somewhere in the transaction but not that it immediately precedes/current-index matches, or not that its message encodes this user/action/amount/nonce.
- **Mitigation:** Parse the Instructions sysvar carefully; verify program ID, instruction index, signer key, message domain separator, nonce, expiry, and exact action parameters.

```mermaid
flowchart TD
    sig["Ed25519 verify instruction in the tx"] --> q{{"bound to THIS action?"}}
    q -->|"only 'it exists' ❌"| replay["Wrong index/message → replay or wrong amount accepted"]
    q -->|"index + message + nonce checked ✅"| safe["Signature authorizes exactly this user / action"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class replay b; class safe g;
```

```rust
// ❌ BAD: only checks that some Ed25519 instruction exists in the tx
//         → an old signed message can be replayed for a different action.

// ✅ GOOD: load the Instructions sysvar and bind it tightly.
let prev = load_instruction_at_checked(current_index - 1, &ix_sysvar)?;
require_keys_eq!(prev.program_id, ed25519_program::ID);
// then assert the signed message encodes this signer, amount, nonce, expiry.
```

- **References:**
  - Instructions sysvar docs: https://docs.rs/solana-program/latest/solana_program/sysvar/instructions/index.html
  - Sysvar docs: https://docs.rs/solana-program/latest/solana_program/sysvar/index.html

### 17. Compute budget and algorithmic DoS
- **Why different:** Every transaction has compute-unit limits and account-size limits; there is no unbounded loop over contract storage, but attackers can supply large vectors/accounts or trigger expensive CPIs until compute exhaustion.
- **Bad pattern:** Iterate over user-provided remaining accounts or vector length without bounds; O(n²) validation; repeated PDA derivations/CPIs; requiring many writable “hot” accounts that serialize all users.
- **Mitigation:** Bound input lengths; price fees by work; avoid unbounded `remaining_accounts`; cap CPIs; use efficient data structures; split work into deterministic chunks; minimize global writable accounts.
- **Useful constants:** Solana transactions have a 1.4M compute-unit hard cap by default budget rules and commonly start at 200k CU per instruction unless a Compute Budget instruction raises the limit. CPI stack depth is limited to 4 nested invocations beyond the transaction entrypoint. Legacy transactions are capped at 1232 bytes, so long router account lists often require v0 transactions with Address Lookup Tables.

```mermaid
flowchart LR
    inp["user-supplied remaining_accounts / vec"] --> q{{"length bounded?"}}
    q -->|"unbounded loop ❌"| oom["O(n) / O(n²) work → compute exhausted, ix always fails (DoS)"]
    q -->|"capped ✅"| ok["Predictable CU, stays within budget"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class oom b; class ok g;
```

```rust
// ❌ BAD: iterates an attacker-sized list with no cap → blows the CU budget.
for acc in ctx.remaining_accounts { do_expensive(acc)?; }

// ✅ GOOD: bound the input length up front.
require!(ctx.remaining_accounts.len() <= MAX_LEGS, MyError::TooMany);
for acc in ctx.remaining_accounts { do_expensive(acc)?; }
```

- **References:**
  - Solana fees/compute budget docs: https://solana.com/docs/core/fees
  - Transactions docs: https://solana.com/docs/core/transactions

### 18. Transaction atomicity and same-transaction composition assumptions
- **Why different:** Multiple instructions from multiple programs execute atomically in one transaction. Attackers can prepare state with earlier instructions and consume/restore it with later ones; failed final instruction rolls back all effects.
- **Bad pattern:** Assume an account could not have been created, funded, closed, or modified earlier in the same transaction; rely on “temporary” imbalance or lack of post-condition after CPI.
- **Mitigation:** Validate state at the point of use and after CPIs; design instructions to be safe under arbitrary composition; be explicit about order-sensitive flows using nonces/status flags.

```mermaid
flowchart LR
    s1["ix #1: fund / create / close an account"] --> s2["ix #2 (your program) assumes that state is 'impossible'"]
    s2 --> bad["State was prepared by the attacker earlier in the SAME tx ❌"]
    chk["validate state at point of use + after every CPI ✅"] --> ok["Safe under any composition"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class bad b; class ok g;
```

```rust
// ❌ BAD: caches a balance from before a CPI, or assumes an account couldn't
//         have been funded/created earlier in the same transaction.
let bal = vault.amount; cpi_that_may_change_vault()?; use_balance(bal);

// ✅ GOOD: re-read after the CPI; gate order-sensitive flows on a status flag.
cpi_that_may_change_vault()?;
vault.reload()?;
require!(vault.status == Status::Ready, MyError::BadState);
```

- **References:**
  - Transactions docs: https://solana.com/docs/core/transactions
  - Closing accounts course (same-transaction revival class): https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/closing-accounts.md

### 19. Parallelization/account-lock DoS and hot accounts
- **Why different:** Solana parallelizes transactions whose writable account sets do not conflict. A design with one global writable config/counter/vault can serialize all activity and be spammed.
- **Bad pattern:** Every trade/deposit writes the same global state account; admin/config unnecessarily marked mutable in all user flows.
- **Mitigation:** Keep immutable config readonly; shard state by market/user; avoid global mutable counters where possible; only mark accounts mutable when actually changed.

```mermaid
flowchart TD
    g["One global writable config / counter"] --> lock["Every tx must lock it"]
    lock --> serial["All users serialize → cheap to spam (DoS) ❌"]
    sh["Shard state per market / user; keep config read-only"] --> par["Non-conflicting txs run in parallel ✅"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g2 fill:#f1fff9,stroke:#0fa76e;
    class serial b; class par g2;
```

```rust
// ❌ BAD: every deposit writes one global counter → all deposits serialize.
#[account(mut, seeds = [b"global"], bump)] pub global: Account<'info, Global>,

// ✅ GOOD: config stays read-only; mutable state is sharded per market.
pub config: Account<'info, Config>,                 // not `mut` → not locked
#[account(mut, seeds = [b"market", market.key().as_ref()], bump)]
pub market_state: Account<'info, MarketState>,
```

- **References:**
  - Transactions/account locking: https://solana.com/docs/core/transactions
  - Accounts docs: https://solana.com/docs/core/accounts

### 20. SPL Token / Token-2022 account validation gaps
- **Why different:** Token balances/authority are data inside SPL Token accounts owned by token programs. Native SOL lamports and SPL tokens have different rules; Token-2022 can add extensions/transfer hooks/confidential features.
- **Bad pattern:** Accept any token account as a vault; check only token account owner authority but not mint; assume ATA address without deriving; ignore Token-2022 extensions or transfer fees in accounting.
- **Mitigation:** Check token program ID, mint, token account authority, ATA derivation when required, decimals, extensions/fees/hooks; use Anchor SPL constraints and test both SPL Token and Token-2022 if supported. Routers need explicit policy for transfer hooks that require extra CPI accounts, transfer fees where amount in differs from amount out, permanent delegates that can move funds, interest-bearing mints where UI amounts drift from raw amounts, and confidential/non-transferable extensions that break normal transfer assumptions. ATA derivation must thread the intended token program with `get_associated_token_address_with_program_id`, not assume classic SPL Token.

```mermaid
flowchart TD
    ta["token account passed in as 'vault'"] --> q{{"program id + mint + authority + ATA all checked?"}}
    q -->|"any skipped ❌"| wrong["Wrong mint, or Token-2022 fee / hook silently breaks accounting"]
    q -->|"all checked ✅"| ok["Correct vault, right mint, right token program"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class wrong b; class ok g;
```

```rust
// ❌ BAD: accepts any token account; ignores mint and which token program.
#[account(mut)] pub vault: AccountInfo<'info>,

// ✅ GOOD: pin mint + authority; thread the token program (classic vs 2022).
#[account(mut, token::mint = mint, token::authority = vault_authority,
          token::token_program = token_program)]
pub vault: InterfaceAccount<'info, TokenAccount>,
pub token_program: Interface<'info, TokenInterface>,
// ATAs: get_associated_token_address_with_program_id(.., token_program_id).
// Token-2022: amount received can differ from amount sent (transfer fees).
```

- **References:**
  - Anchor SPL constraints: https://www.anchor-lang.com/docs/references/account-constraints
  - Solana token program docs: https://spl.solana.com/token
  - Token-2022 docs: https://spl.solana.com/token-2022

### 21. Address Lookup Tables as a trust boundary
- **Why different:** Versioned transactions resolve Address Lookup Table entries before the program executes. A program that stores or accepts an ALT pubkey is only storing metadata unless it validates the ALT account and its state.
- **Bad pattern:** Store an ALT pubkey in config and later assume routes using that ALT resolve to approved vaults/reserves without checking the table owner, authority, deactivation slot, or resolved account keys.
- **Mitigation:** If an ALT account is passed to the program, require the Address Lookup Table program as owner, parse table state, verify authority/deactivation status, and bind expected indexes to expected pubkeys. Remember that the executing program normally sees resolved account keys, not the ALT itself; validate the actual accounts used by the instruction.

```mermaid
flowchart TD
    alt["ALT pubkey stored in config"] --> q{{"table validated?"}}
    q -->|"trusted blindly ❌"| spoof["Attacker's table resolves indexes to their own accounts"]
    q -->|"owner + authority + resolved keys checked ✅"| ok["Resolved accounts are the approved ones"]
    note["Program normally sees RESOLVED keys, not the ALT — always validate the actual accounts"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class spoof b; class ok g;
```

```rust
// ❌ BAD: store an ALT pubkey and assume routes through it hit approved vaults.
config.lookup_table = alt.key(); // metadata only — proves nothing about entries

// ✅ GOOD: if the ALT account is passed in, validate it before trusting it.
require_keys_eq!(*alt.owner, solana_address_lookup_table_program::ID);
let table = AddressLookupTable::deserialize(&alt.data.borrow())?;
require!(table.meta.deactivation_slot == u64::MAX, MyError::AltDeactivated);
// Ultimately: validate the RESOLVED accounts the instruction actually uses.
```

- **References:**
  - Address Lookup Tables: https://solana.com/docs/advanced/lookup-tables
  - Transactions docs: https://solana.com/docs/core/transactions

## CTF-style audit checklist

- Can I pass a fake account with matching serialized bytes?
- Can I pass the same writable account for two roles?
- Can I swap one valid account of the right type for another user/pool/mint?
- Can I omit a signature or use a signer that is unrelated to stored authority?
- Can I choose a malicious CPI target program or malicious CPI accounts?
- Can I make the program sign for a PDA over assets it did not intend to authorize?
- Can I choose non-canonical PDA seeds/bumps or collide/shared PDA authority scope?
- Can I re-run initialize, reset state, or use `init_if_needed` to revive/reset data?
- Can I close/refund/recreate an account within the same transaction and reuse stale state?
- Can I spoof sysvars or instruction introspection inputs?
- Can I exploit overflow, decimal mismatch, or rounding by splitting actions?
- Can I exhaust compute with long `remaining_accounts`, large vectors, many CPIs, or hot writable accounts?
- Are all post-CPI invariants rechecked, especially balances and token account state?

## High-signal reference set

- Solana docs: accounts: https://solana.com/docs/core/accounts
- Solana docs: transactions: https://solana.com/docs/core/transactions
- Solana docs: programs: https://solana.com/docs/core/programs
- Solana docs: PDAs: https://solana.com/docs/core/pda
- Solana docs: CPIs: https://solana.com/docs/core/cpi
- Solana docs: fees/compute: https://solana.com/docs/core/fees
- Solana Foundation Program Security course: https://github.com/solana-foundation/developer-content/tree/main/content/courses/program-security
- Anchor account constraints: https://www.anchor-lang.com/docs/references/account-constraints
- Anchor CPI docs: https://www.anchor-lang.com/docs/basics/cpi
- Coral/Anchor Sealevel attacks repo: https://github.com/coral-xyz/sealevel-attacks
- Neodyme Solana common pitfalls: https://neodyme.io/en/blog/solana_common_pitfalls/
- Solana sysvar docs: https://docs.rs/solana-program/latest/solana_program/sysvar/index.html
- SPL Token docs: https://spl.solana.com/token
- Token-2022 docs: https://spl.solana.com/token-2022

## Additional expert-review patterns added to the site

The interactive site now includes dedicated cards for several patterns that were previously only implicit or missing:

- Stale account data after CPI / missing Anchor `reload()`
- Instruction introspection and Ed25519/secp signature verification misuse
- Insecure randomness from slots/timestamps/blockhash-like values
- Detailed oracle feed validation: feed identity, freshness, confidence, exponent/decimals, liquidity
- `remaining_accounts` count/order/type assumptions
- Native SOL lamport accounting and rent floors
- Zero-copy / bytemuck / POD layout hazards
- Event/log reliance as non-authoritative state
- Governance/multisig/timelock validation gaps
- Native parser hazards: manual offsets, unchecked deserialization, versioned layouts

For concrete native and Anchor bad/good snippets, see `data/patterns.json` or the website cards.

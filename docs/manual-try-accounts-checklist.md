# Manual `try_accounts` checklist

Hand-rolled `Accounts` implementations are high-risk because they replace Anchor's generated validation with bespoke account parsing. Audit them slot by slot. The right question is not "does this compile?" but "does this manual context enforce every constraint the derived context would have enforced for this Anchor version?"

## Per-slot checks

For every account pulled from the iterator, record whether the code checks:

- Exact slot count before `remaining_accounts` begins.
- `is_signer` for authorities, payers, and external actors.
- `is_writable` for state, token accounts, rent payers, close recipients, and lamport-mutated accounts.
- `owner == program_id` for this program's state.
- Expected external owner/program ID for SPL Token, Token-2022, System, ATA, sysvars, and CPI targets.
- `key == expected_pda` after re-deriving seeds and canonical bump.
- Discriminator before decode for Anchor accounts.
- Data length and version before manual slicing or Borsh decode.
- Relationship fields such as `has_one`, mint, authority, pool, market, reserve, or config.
- Alias rules: roles that must be distinct cannot share the same `Pubkey`.

Reject unexpected extras unless the instruction intentionally accepts variable `remaining_accounts`, and then validate the variable slice with its own schema.

## Bad: presence-only parsing

```rust
impl<'info> Accounts<'info, Burn<'info>> for Burn<'info> {
    fn try_accounts(
        program_id: &Pubkey,
        accounts: &mut &'info [AccountInfo<'info>],
        _ix_data: &[u8],
        _bumps: &mut BTreeMap<String, u8>,
        _reallocs: &mut BTreeSet<Pubkey>,
    ) -> Result<Self> {
        let iter = &mut accounts.iter();
        let authority = next_account_info(iter)?;
        let vault = next_account_info(iter)?;
        let config = next_account_info(iter)?;

        // BUG: no signer, writable, owner, PDA, discriminator, or alias checks.
        Ok(Self {
            authority: authority.clone(),
            vault: vault.clone(),
            config: config.clone(),
        })
    }
}
```

This is equivalent to trusting a caller-supplied address array. The handler may later compare fields from attacker-controlled bytes or sign CPIs over accounts that were never bound to the intended resource.

## Good: derive-equivalent validation

```rust
let authority = next_account_info(iter)?;
let vault = next_account_info(iter)?;
let config = next_account_info(iter)?;

require!(authority.is_signer, ErrorCode::MissingSigner);
require!(vault.is_writable, ErrorCode::NotWritable);
require!(config.is_writable, ErrorCode::NotWritable);
require_keys_neq!(vault.key(), config.key(), ErrorCode::AccountAlias);

let (expected_vault, vault_bump) = Pubkey::find_program_address(
    &[b"vault", authority.key.as_ref()],
    program_id,
);
require_keys_eq!(vault.key(), expected_vault, ErrorCode::BadPda);

require_keys_eq!(*config.owner, *program_id, ErrorCode::BadOwner);
let data = config.try_borrow_data()?;
require!(data.len() >= 8 + Config::LEN, ErrorCode::BadLength);
require!(&data[..8] == Config::DISCRIMINATOR, ErrorCode::BadDiscriminator);
let config_state = Config::try_deserialize(&mut &data[..])?;
require_keys_eq!(config_state.authority, *authority.key, ErrorCode::BadAuthority);
require_eq!(config_state.vault_bump, vault_bump, ErrorCode::BadBump);
```

The exact code will vary, but the discipline should not: consume the expected slots, validate every role, then expose only validated accounts to the handler.

## Canonical bump discipline

Do not accept a bump because the client passed it. Either:

- Use `Pubkey::find_program_address` and compare the returned address and bump, or
- Store the bump in trusted account state and re-derive with that stored bump while proving the state account itself is typed and owned.

Bad:
```rust
let pda = Pubkey::create_program_address(&[b"vault", &[args.bump]], program_id)?;
require_keys_eq!(pda, *vault.key);
```

Good:
```rust
let (pda, bump) = Pubkey::find_program_address(&[b"vault"], program_id);
require_keys_eq!(pda, *vault.key);
require_eq!(state.vault_bump, bump);
```

## `remaining_accounts` boundary

Manual parsers often split fixed accounts from forwarded accounts. Enforce the split explicitly:

```rust
require!(accounts.len() >= FIXED_ACCOUNT_COUNT, ErrorCode::TooFewAccounts);
let (fixed, remaining) = accounts.split_at(FIXED_ACCOUNT_COUNT);
require_eq!(fixed.len(), FIXED_ACCOUNT_COUNT);
```

If a caller can insert one extra account before the forwarded slice, every downstream index can shift. That is a CPI account-substitution bug, not a harmless parsing detail.

## Review prompt

For each hand-written context, write a small table with columns: slot, role, signer, writable, owner, address/PDA, discriminator/layout, relationship, alias rule. Empty cells are findings until justified.

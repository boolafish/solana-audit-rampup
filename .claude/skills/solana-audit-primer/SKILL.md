---
name: solana-audit-primer
description: Catalog of Solana/Anchor security patterns (good vs bad) for auditing and threat-modeling on-chain Rust programs. Use when reviewing, auditing, or threat-modeling Solana, Anchor, or native SBF programs, or when the user mentions Solana vulnerability patterns, account validation, PDAs, CPIs, SPL Token / Token-2022, oracles, or Anchor constraints.
---

# Solana Audit Primer

A two-layer catalog of Solana/Anchor security patterns. This file is the **routing layer**: scan it, match triggers against the target program, then load only the `references/<id>.md` pages you need. Do not paste every reference page into context up front.

## Workflow

1. **Frame the system.** Read [threat-model.md](threat-model.md) and fill in the scaffold: assets, actors, trust boundaries, instructions, external programs.
2. **Grep for code signals.** Use the *Code-signal index* below: each grep token points at the patterns to load.
3. **Apply protocol playbooks.** Identify the protocol type(s) and pull the prioritized pattern list for each.
4. **Always-check core.** Run the core patterns on every program regardless of type.
5. **Load detail pages.** For each matched pattern, open `references/<id>.md` for bad/good code, audit checks, and mapped incidents.

## Always-check core patterns

Every Solana/Anchor program, regardless of protocol type:

- [Missing signer authorization](references/missing-signer.md) (`missing-signer`, Critical)
- [Missing owner check / spoofed account data](references/missing-owner.md) (`missing-owner`, Critical)
- [Missing account relationship checks](references/relationship-checks.md) (`relationship-checks`, High)
- [Type cosplay / discriminator confusion](references/type-cosplay.md) (`type-cosplay`, High)
- [PDA seed/bump mistakes and non-canonical bumps](references/pda-bump.md) (`pda-bump`, High)
- [Arbitrary CPI / missing program ID check](references/arbitrary-cpi.md) (`arbitrary-cpi`, Critical)
- [CPI account substitution / confused deputy](references/cpi-substitution.md) (`cpi-substitution`, Critical)
- [UncheckedAccount / AccountInfo used as trusted state](references/anchor-unchecked.md) (`anchor-unchecked`, High)
- [Integer overflow, precision, rounding, decimal mismatch](references/math.md) (`math`, High)

## Code-signal index

Grep the target program. If a token appears, consider the listed patterns. Very broad operator/control-flow tokens are kept in detail pages but omitted from this routing table to reduce noise.

| Grep token | Consider patterns |
| --- | --- |
| `#[account(` | [`anchor-unchecked`](references/anchor-unchecked.md) |
| `#[account(init` | [`reinit`](references/reinit.md) |
| `#[account(init_if_needed` | [`anchor-init-if-needed`](references/anchor-init-if-needed.md) |
| `#[account(mut` | [`duplicate-mut`](references/duplicate-mut.md), [`compute-dos`](references/compute-dos.md) |
| `#[account(owner` | [`missing-owner`](references/missing-owner.md) |
| `#[account(signer` | [`missing-signer`](references/missing-signer.md) |
| `**` | [`close-revival`](references/close-revival.md) |
| `.amount` | [`stale-cpi-reload`](references/stale-cpi-reload.md) |
| `.data.borrow()` | [`missing-owner`](references/missing-owner.md) |
| `.iter()` | [`compute-dos`](references/compute-dos.md) |
| `.key()` | [`relationship-checks`](references/relationship-checks.md) |
| `/// CHECK` | [`anchor-unchecked`](references/anchor-unchecked.md) |
| `[8..40]` | [`raw-byte-pda-decoding`](references/raw-byte-pda-decoding.md) |
| `Account<` | [`relationship-checks`](references/relationship-checks.md), [`anchor-unchecked`](references/anchor-unchecked.md) |
| `AccountDeserialize` | [`type-cosplay`](references/type-cosplay.md) |
| `AccountInfo` | [`missing-signer`](references/missing-signer.md), [`missing-owner`](references/missing-owner.md), [`type-cosplay`](references/type-cosplay.md), [`arbitrary-cpi`](references/arbitrary-cpi.md), [`duplicate-mut`](references/duplicate-mut.md), [`sysvar-spoof`](references/sysvar-spoof.md), [`close-revival`](references/close-revival.md), [`anchor-unchecked`](references/anchor-unchecked.md), [`oracle-validation`](references/oracle-validation.md) |
| `AccountInfo::realloc` | [`realloc-rent`](references/realloc-rent.md) |
| `AccountLoader` | [`zero-copy-layout`](references/zero-copy-layout.md) |
| `AccountMeta` | [`cpi-substitution`](references/cpi-substitution.md) |
| `AccountMeta::new` | [`remaining-accounts-trust`](references/remaining-accounts-trust.md) |
| `add_lamports` | [`native-sol-lamports`](references/native-sol-lamports.md) |
| `admin` | [`upgrade-admin`](references/upgrade-admin.md) |
| `anchor-lang = "0.28` | [`anchor-0.28-deltas`](references/anchor-0.28-deltas.md) |
| `as u128` | [`math`](references/math.md) |
| `as u64` | [`math`](references/math.md) |
| `authority` | [`upgrade-admin`](references/upgrade-admin.md) |
| `b"vault"` | [`seed-prefix-collision`](references/seed-prefix-collision.md) |
| `Borsh` | [`type-cosplay`](references/type-cosplay.md) |
| `BpfLoaderUpgradeable` | [`upgrade-admin`](references/upgrade-admin.md) |
| `bump` | [`pda-bump`](references/pda-bump.md), [`find-program-address-cu-cost`](references/find-program-address-cu-cost.md) |
| `bytemuck` | [`zero-copy-layout`](references/zero-copy-layout.md) |
| `Cargo.lock` | [`anchor-0.28-deltas`](references/anchor-0.28-deltas.md) |
| `checked_` | [`math`](references/math.md) |
| `Clock` | [`oracle-mev`](references/oracle-mev.md) |
| `Clock::get` | [`sysvar-spoof`](references/sysvar-spoof.md), [`insecure-randomness`](references/insecure-randomness.md) |
| `close =` | [`close-revival`](references/close-revival.md) |
| `confidence` | [`oracle-validation`](references/oracle-validation.md) |
| `constraint =` | [`duplicate-mut`](references/duplicate-mut.md) |
| `CpiContext` | [`cpi-substitution`](references/cpi-substitution.md), [`stale-cpi-reload`](references/stale-cpi-reload.md) |
| `create_program_address` | [`pda-bump`](references/pda-bump.md), [`find-program-address-cu-cost`](references/find-program-address-cu-cost.md) |
| `ctx.remaining_accounts` | [`remaining-accounts`](references/remaining-accounts.md) |
| `data[` | [`native-parser-hazards`](references/native-parser-hazards.md), [`raw-byte-pda-decoding`](references/raw-byte-pda-decoding.md) |
| `deadline` | [`oracle-mev`](references/oracle-mev.md) |
| `discriminator` | [`type-cosplay`](references/type-cosplay.md) |
| `ed25519` | [`signature-introspection`](references/signature-introspection.md) |
| `emit!` | [`event-log-reliance`](references/event-log-reliance.md) |
| `emit_cpi` | [`event-log-reliance`](references/event-log-reliance.md) |
| `find_program_address` | [`pda-bump`](references/pda-bump.md), [`find-program-address-cu-cost`](references/find-program-address-cu-cost.md), [`seed-prefix-collision`](references/seed-prefix-collision.md) |
| `fn try_accounts` | [`manual-try-accounts`](references/manual-try-accounts.md) |
| `from_bytes` | [`zero-copy-layout`](references/zero-copy-layout.md) |
| `get_account_data_size` | [`token2022`](references/token2022.md) |
| `get_price` | [`oracle-validation`](references/oracle-validation.md) |
| `governance` | [`governance-timelock`](references/governance-timelock.md) |
| `has_one` | [`missing-signer`](references/missing-signer.md), [`relationship-checks`](references/relationship-checks.md) |
| `impl<'info> Accounts` | [`manual-try-accounts`](references/manual-try-accounts.md) |
| `init_if_needed` | [`reinit`](references/reinit.md), [`anchor-init-if-needed`](references/anchor-init-if-needed.md), [`anchor-0.28-deltas`](references/anchor-0.28-deltas.md) |
| `initialize` | [`reinit`](references/reinit.md) |
| `Instruction {` | [`arbitrary-cpi`](references/arbitrary-cpi.md) |
| `Instructions` | [`sysvar-spoof`](references/sysvar-spoof.md) |
| `Interface<` | [`arbitrary-cpi`](references/arbitrary-cpi.md), [`anchor-token-interface`](references/anchor-token-interface.md) |
| `InterfaceAccount` | [`token2022`](references/token2022.md), [`anchor-token-interface`](references/anchor-token-interface.md) |
| `invoke` | [`stale-cpi-reload`](references/stale-cpi-reload.md) |
| `invoke(` | [`arbitrary-cpi`](references/arbitrary-cpi.md) |
| `invoke(&ix` | [`remaining-accounts-trust`](references/remaining-accounts-trust.md) |
| `invoke_signed` | [`cpi-substitution`](references/cpi-substitution.md) |
| `invoke_signed(` | [`arbitrary-cpi`](references/arbitrary-cpi.md) |
| `is_initialized` | [`reinit`](references/reinit.md) |
| `is_signer` | [`missing-signer`](references/missing-signer.md) |
| `is_writable` | [`remaining-accounts-trust`](references/remaining-accounts-trust.md) |
| `Kamino` | [`remaining-accounts-trust`](references/remaining-accounts-trust.md) |
| `key() !=` | [`duplicate-mut`](references/duplicate-mut.md) |
| `KLend` | [`remaining-accounts-trust`](references/remaining-accounts-trust.md) |
| `lamports` | [`close-revival`](references/close-revival.md), [`native-sol-lamports`](references/native-sol-lamports.md) |
| `load_current_index` | [`signature-introspection`](references/signature-introspection.md) |
| `load_current_index_checked` | [`instructions-sysvar-introspection`](references/instructions-sysvar-introspection.md) |
| `load_instruction_at_checked` | [`signature-introspection`](references/signature-introspection.md), [`instructions-sysvar-introspection`](references/instructions-sysvar-introspection.md) |
| `loop` | [`find-program-address-cu-cost`](references/find-program-address-cu-cost.md) |
| `min_out` | [`oracle-mev`](references/oracle-mev.md) |
| `mint::token_program` | [`anchor-token-interface`](references/anchor-token-interface.md) |
| `msg!` | [`event-log-reliance`](references/event-log-reliance.md) |
| `multisig` | [`governance-timelock`](references/governance-timelock.md) |
| `next_account_info` | [`remaining-accounts`](references/remaining-accounts.md), [`native-parser-hazards`](references/native-parser-hazards.md), [`manual-try-accounts`](references/manual-try-accounts.md) |
| `offset` | [`native-parser-hazards`](references/native-parser-hazards.md) |
| `overflow-checks` | [`math`](references/math.md) |
| `owner ==` | [`missing-owner`](references/missing-owner.md) |
| `payer =` | [`anchor-0.28-deltas`](references/anchor-0.28-deltas.md) |
| `Pod` | [`zero-copy-layout`](references/zero-copy-layout.md) |
| `price` | [`oracle-mev`](references/oracle-mev.md) |
| `price_feed` | [`oracle-validation`](references/oracle-validation.md) |
| `Program<` | [`arbitrary-cpi`](references/arbitrary-cpi.md) |
| `program_id:` | [`arbitrary-cpi`](references/arbitrary-cpi.md) |
| `proposal` | [`governance-timelock`](references/governance-timelock.md) |
| `Pubkey::find_program_address` | [`pda-bump`](references/pda-bump.md) |
| `Pubkey::new_from_array` | [`native-parser-hazards`](references/native-parser-hazards.md), [`raw-byte-pda-decoding`](references/raw-byte-pda-decoding.md) |
| `publish_time` | [`oracle-validation`](references/oracle-validation.md) |
| `Pyth` | [`oracle-validation`](references/oracle-validation.md) |
| `realloc` | [`realloc-rent`](references/realloc-rent.md) |
| `realloc::payer` | [`realloc-rent`](references/realloc-rent.md) |
| `realloc::zero` | [`realloc-rent`](references/realloc-rent.md) |
| `Realms` | [`governance-timelock`](references/governance-timelock.md) |
| `recent_blockhashes` | [`insecure-randomness`](references/insecure-randomness.md) |
| `reload()` | [`stale-cpi-reload`](references/stale-cpi-reload.md) |
| `remaining_accounts` | [`compute-dos`](references/compute-dos.md), [`remaining-accounts`](references/remaining-accounts.md), [`remaining-accounts-trust`](references/remaining-accounts-trust.md) |
| `Rent` | [`realloc-rent`](references/realloc-rent.md) |
| `Rent::get` | [`sysvar-spoof`](references/sysvar-spoof.md) |
| `repr(C)` | [`zero-copy-layout`](references/zero-copy-layout.md) |
| `require_keys_eq` | [`relationship-checks`](references/relationship-checks.md) |
| `saturating_` | [`math`](references/math.md) |
| `secp256k1` | [`signature-introspection`](references/signature-introspection.md) |
| `seeds =` | [`pda-bump`](references/pda-bump.md), [`seed-prefix-collision`](references/seed-prefix-collision.md) |
| `set_authority` | [`upgrade-admin`](references/upgrade-admin.md) |
| `Signer<` | [`missing-signer`](references/missing-signer.md), [`anchor-0.28-deltas`](references/anchor-0.28-deltas.md) |
| `slippage` | [`oracle-mev`](references/oracle-mev.md) |
| `slot` | [`oracle-mev`](references/oracle-mev.md), [`insecure-randomness`](references/insecure-randomness.md) |
| `sol_log` | [`event-log-reliance`](references/event-log-reliance.md) |
| `spl_token_2022` | [`token2022`](references/token2022.md) |
| `Squads` | [`governance-timelock`](references/governance-timelock.md) |
| `sub_lamports` | [`native-sol-lamports`](references/native-sol-lamports.md) |
| `Switchboard` | [`oracle-validation`](references/oracle-validation.md) |
| `system_program::transfer` | [`native-sol-lamports`](references/native-sol-lamports.md) |
| `sysvar` | [`sysvar-spoof`](references/sysvar-spoof.md) |
| `Sysvar1nstructions` | [`instructions-sysvar-introspection`](references/instructions-sysvar-introspection.md) |
| `sysvar::instructions` | [`signature-introspection`](references/signature-introspection.md), [`instructions-sysvar-introspection`](references/instructions-sysvar-introspection.md) |
| `Sysvar<` | [`sysvar-spoof`](references/sysvar-spoof.md) |
| `threshold` | [`governance-timelock`](references/governance-timelock.md) |
| `timelock` | [`governance-timelock`](references/governance-timelock.md) |
| `token::authority` | [`relationship-checks`](references/relationship-checks.md) |
| `token::mint` | [`relationship-checks`](references/relationship-checks.md), [`token2022`](references/token2022.md) |
| `token::token_program` | [`anchor-token-interface`](references/anchor-token-interface.md) |
| `token::transfer` | [`cpi-substitution`](references/cpi-substitution.md), [`stale-cpi-reload`](references/stale-cpi-reload.md) |
| `TokenAccount` | [`relationship-checks`](references/relationship-checks.md) |
| `TokenInterface` | [`token2022`](references/token2022.md), [`anchor-token-interface`](references/anchor-token-interface.md) |
| `transfer_fee` | [`token2022`](references/token2022.md) |
| `transfer_hook` | [`token2022`](references/token2022.md) |
| `try_borrow_mut_lamports` | [`close-revival`](references/close-revival.md), [`native-sol-lamports`](references/native-sol-lamports.md) |
| `try_from_slice` | [`missing-owner`](references/missing-owner.md), [`type-cosplay`](references/type-cosplay.md) |
| `try_from_slice_unchecked` | [`missing-owner`](references/missing-owner.md), [`native-parser-hazards`](references/native-parser-hazards.md) |
| `try_into()` | [`raw-byte-pda-decoding`](references/raw-byte-pda-decoding.md) |
| `u128` | [`math`](references/math.md) |
| `UncheckedAccount` | [`missing-signer`](references/missing-signer.md), [`missing-owner`](references/missing-owner.md), [`anchor-unchecked`](references/anchor-unchecked.md), [`raw-byte-pda-decoding`](references/raw-byte-pda-decoding.md), [`seed-prefix-collision`](references/seed-prefix-collision.md) |
| `unix_timestamp` | [`insecure-randomness`](references/insecure-randomness.md) |
| `unpack` | [`native-parser-hazards`](references/native-parser-hazards.md) |
| `upgrade_authority` | [`upgrade-admin`](references/upgrade-admin.md) |
| `Vec<` | [`compute-dos`](references/compute-dos.md) |
| `with_signer` | [`cpi-substitution`](references/cpi-substitution.md) |
| `WSOL` | [`native-sol-lamports`](references/native-sol-lamports.md) |
| `zero_copy` | [`zero-copy-layout`](references/zero-copy-layout.md) |
| `Zeroable` | [`zero-copy-layout`](references/zero-copy-layout.md) |

## Protocol playbooks

Match the target to one or more protocol types, then prioritize these patterns (in addition to the core set above).

### Lending / perps / collateral

- [Missing signer authorization](references/missing-signer.md) (`missing-signer`, Critical)
- [Missing account relationship checks](references/relationship-checks.md) (`relationship-checks`, High)
- [CPI account substitution / confused deputy](references/cpi-substitution.md) (`cpi-substitution`, Critical)
- [Integer overflow, precision, rounding, decimal mismatch](references/math.md) (`math`, High)
- [SPL Token / Token-2022 validation gaps](references/token2022.md) (`token2022`, High)
- [Oracle, ordering, and MEV/front-running assumptions](references/oracle-mev.md) (`oracle-mev`, High)
- [Oracle feed validation gaps](references/oracle-validation.md) (`oracle-validation`, Critical)
- [Forwarded `remaining_accounts` as CPI trust boundary](references/remaining-accounts-trust.md) (`remaining-accounts-trust`, Critical)

### AMM / DEX / swaps

- [Missing account relationship checks](references/relationship-checks.md) (`relationship-checks`, High)
- [Duplicate mutable accounts / aliasing](references/duplicate-mut.md) (`duplicate-mut`, High)
- [Integer overflow, precision, rounding, decimal mismatch](references/math.md) (`math`, High)
- [SPL Token / Token-2022 validation gaps](references/token2022.md) (`token2022`, High)
- [Oracle, ordering, and MEV/front-running assumptions](references/oracle-mev.md) (`oracle-mev`, High)

### Vaults / escrow / staking

- [Missing account relationship checks](references/relationship-checks.md) (`relationship-checks`, High)
- [Account close, revival, and stale data](references/close-revival.md) (`close-revival`, High)
- [Native SOL lamport accounting bugs](references/native-sol-lamports.md) (`native-sol-lamports`, High)
- [Manual deserialization, offsets, and versioned account layouts](references/native-parser-hazards.md) (`native-parser-hazards`, Medium)

### Governance / multisig / admin

- [Missing signer authorization](references/missing-signer.md) (`missing-signer`, Critical)
- [Upgrade authority and admin controls](references/upgrade-admin.md) (`upgrade-admin`, High)
- [Zero-copy / bytemuck / POD layout hazards](references/zero-copy-layout.md) (`zero-copy-layout`, Medium)
- [Governance, multisig, and timelock validation gaps](references/governance-timelock.md) (`governance-timelock`, High)

### Routers / aggregators

- [Arbitrary CPI / missing program ID check](references/arbitrary-cpi.md) (`arbitrary-cpi`, Critical)
- [CPI account substitution / confused deputy](references/cpi-substitution.md) (`cpi-substitution`, Critical)
- [`remaining_accounts` order/count/type assumptions](references/remaining-accounts.md) (`remaining-accounts`, High)

### Games / lottery / NFT

- [Insecure randomness from slots, timestamps, or blockhashes](references/insecure-randomness.md) (`insecure-randomness`, High)

### Native (non-Anchor) programs

- [Type cosplay / discriminator confusion](references/type-cosplay.md) (`type-cosplay`, High)
- [Native SOL lamport accounting bugs](references/native-sol-lamports.md) (`native-sol-lamports`, High)
- [Manual deserialization, offsets, and versioned account layouts](references/native-parser-hazards.md) (`native-parser-hazards`, Medium)

## Full pattern catalog

### Core Solana

| Pattern | Severity | What it is | Top code signals |
| --- | --- | --- | --- |
| [Missing signer authorization](references/missing-signer.md) | Critical | A pubkey appearing in account data or account list is not proof of authorization. | `AccountInfo`, `UncheckedAccount`, `is_signer`, `Signer<` |
| [Missing owner check / spoofed account data](references/missing-owner.md) | Critical | Program state is stored in separate accounts supplied by the caller. | `try_from_slice`, `try_from_slice_unchecked`, `.data.borrow()`, `AccountInfo` |
| [Missing account relationship checks](references/relationship-checks.md) | High | The transaction supplies all accounts. | `has_one`, `Account<`, `TokenAccount`, `token::mint` |
| [Type cosplay / discriminator confusion](references/type-cosplay.md) | High | Raw account bytes can be interpreted as another struct if no discriminator/type tag is enforced. | `try_from_slice`, `AccountDeserialize`, `discriminator`, `AccountInfo` |

### Lifecycle / Rent

| Pattern | Severity | What it is | Top code signals |
| --- | --- | --- | --- |
| [Reinitialization / initialization confusion](references/reinit.md) | Critical | Accounts can be created, assigned, funded, resized, closed, or reused. | `init_if_needed`, `#[account(init`, `initialize`, `is_initialized` |
| [Account close, revival, and stale data](references/close-revival.md) | High | Closing usually transfers lamports and resets/assigns account. | `close =`, `lamports`, `try_borrow_mut_lamports`, `**` |
| [Rent-exemption and realloc/storage resizing edge cases](references/realloc-rent.md) | Medium | Growing/shrinking accounts changes required rent-exempt minimum balance and may expose stale bytes. | `realloc`, `realloc::payer`, `realloc::zero`, `Rent` |

### PDA

| Pattern | Severity | What it is | Top code signals |
| --- | --- | --- | --- |
| [PDA seed/bump mistakes and non-canonical bumps](references/pda-bump.md) | High | PDA derivation includes seeds and a bump. | `find_program_address`, `create_program_address`, `seeds =`, `bump` |
| [`find_program_address` compute cost and bump caching](references/find-program-address-cu-cost.md) | Medium | `find_program_address` searches bump values until it finds an off-curve address. | `find_program_address`, `create_program_address`, `bump`, `for ` |
| [Seed-prefix collision and PDA type confusion](references/seed-prefix-collision.md) | High | PDAs are untyped addresses. | `seeds =`, `find_program_address`, `b"vault"`, `UncheckedAccount` |

### CPI

| Pattern | Severity | What it is | Top code signals |
| --- | --- | --- | --- |
| [Arbitrary CPI / missing program ID check](references/arbitrary-cpi.md) | Critical | The CPI target program account is often passed by the caller. | `invoke(`, `invoke_signed(`, `Instruction {`, `program_id:` |
| [CPI account substitution / confused deputy](references/cpi-substitution.md) | Critical | Even when CPI program ID is correct, the caller supplies all callee accounts. | `invoke_signed`, `CpiContext`, `with_signer`, `token::transfer` |
| [Stale account data after CPI / missing reload](references/stale-cpi-reload.md) | High | Anchor deserializes `Account<T>` before the handler. | `reload()`, `invoke`, `CpiContext`, `token::transfer` |
| [Forwarded `remaining_accounts` as CPI trust boundary](references/remaining-accounts-trust.md) | Critical | `remaining_accounts` are raw `AccountInfo`s outside Anchor validation. | `remaining_accounts`, `AccountMeta::new`, `invoke(&ix`, `is_writable` |

### Account Validation

| Pattern | Severity | What it is | Top code signals |
| --- | --- | --- | --- |
| [Duplicate mutable accounts / aliasing](references/duplicate-mut.md) | High | The same account key can be supplied for multiple account parameters unless constrained. | `#[account(mut`, `AccountInfo`, `constraint =`, `key() !=` |
| [Sysvar spoofing](references/sysvar-spoof.md) | High | Sysvars can be accessed via trusted APIs or passed as accounts. | `Sysvar<`, `Clock::get`, `Rent::get`, `sysvar` |
| [Instruction introspection / signature verification misuse](references/signature-introspection.md) | Critical | Solana often verifies Ed25519/secp signatures by including a verification instruction and reading the Instructions sysvar. | `load_instruction_at_checked`, `ed25519`, `secp256k1`, `sysvar::instructions` |
| [Instructions sysvar introspection mistakes](references/instructions-sysvar-introspection.md) | High | The Instructions sysvar exposes transaction instructions. | `sysvar::instructions`, `load_current_index_checked`, `load_instruction_at_checked`, `Sysvar1nstructions` |

### Math / Accounting

| Pattern | Severity | What it is | Top code signals |
| --- | --- | --- | --- |
| [Integer overflow, precision, rounding, decimal mismatch](references/math.md) | High | Unlike Solidity 0.8 checked arithmetic, Rust primitive integer overflow is not automatically safe in optimized Solana program builds unless overflow checks or checked/saturating APIs are used. | `checked_`, `saturating_`, `as u64`, `as u128` |
| [Native SOL lamport accounting bugs](references/native-sol-lamports.md) | High | Native SOL lamports are not SPL tokens. | `lamports`, `try_borrow_mut_lamports`, `add_lamports`, `sub_lamports` |

### Execution / DoS

| Pattern | Severity | What it is | Top code signals |
| --- | --- | --- | --- |
| [Compute budget, large inputs, and hot-account DoS](references/compute-dos.md) | Medium | Transactions have compute limits; writable account locks constrain parallelism. | `remaining_accounts`, `for `, `.iter()`, `#[account(mut` |
| [Insecure randomness from slots, timestamps, or blockhashes](references/insecure-randomness.md) | High | Slots, timestamps, account keys, transaction ordering, and recent blockhash-like values are public or influenceable. | `Clock::get`, `slot`, `unix_timestamp`, `recent_blockhashes` |

### SPL Token / Token-2022

| Pattern | Severity | What it is | Top code signals |
| --- | --- | --- | --- |
| [SPL Token / Token-2022 validation gaps](references/token2022.md) | High | Token balances are accounts owned by Token/Token-2022. | `InterfaceAccount`, `TokenInterface`, `spl_token_2022`, `transfer_fee` |

### Economic / MEV

| Pattern | Severity | What it is | Top code signals |
| --- | --- | --- | --- |
| [Oracle, ordering, and MEV/front-running assumptions](references/oracle-mev.md) | High | Solana has no globally gossiped Ethereum-style public mempool, but pending orderflow is not guaranteed private. | `price`, `slippage`, `min_out`, `deadline` |
| [Oracle feed validation gaps](references/oracle-validation.md) | Critical | A valid-looking oracle account can be the wrong feed/program or stale/confidence-wide data. | `price_feed`, `Pyth`, `Switchboard`, `get_price` |

### Governance / Admin

| Pattern | Severity | What it is | Top code signals |
| --- | --- | --- | --- |
| [Upgrade authority and admin controls](references/upgrade-admin.md) | High | Solana programs can be upgradeable via an upgrade authority. | `upgrade_authority`, `set_authority`, `BpfLoaderUpgradeable`, `admin` |
| [Governance, multisig, and timelock validation gaps](references/governance-timelock.md) | High | Solana governance may be SPL Governance/Realms/Squads/custom. | `governance`, `Realms`, `Squads`, `multisig` |

### Anchor

| Pattern | Severity | What it is | Top code signals |
| --- | --- | --- | --- |
| [UncheckedAccount / AccountInfo used as trusted state](references/anchor-unchecked.md) | High | Anchor only validates what the account type/constraints express. | `UncheckedAccount`, `AccountInfo`, `/// CHECK`, `Account<` |
| [`init_if_needed` resets existing state](references/anchor-init-if-needed.md) | Critical | Anchor’s `init_if_needed` makes account creation/use convenient but can hide reinitialization bugs if handler overwrites fields on both paths. | `init_if_needed`, `#[account(init_if_needed` |
| [Token-interface constraints not bound to intended token program](references/anchor-token-interface.md) | High | Anchor `InterfaceAccount` can support SPL Token and Token-2022, but protocol assumptions may break unless token program and extensions are intentional. | `InterfaceAccount`, `Interface<`, `TokenInterface`, `mint::token_program` |
| [`remaining_accounts` order/count/type assumptions](references/remaining-accounts.md) | High | Anchor constraints do not apply to `remaining_accounts`. | `remaining_accounts`, `ctx.remaining_accounts`, `next_account_info` |
| [Anchor 0.28 behavior differs from newer tutorials](references/anchor-0.28-deltas.md) | High | Anchor code generation, feature flags, lamport helpers, and payer mutability behavior are version-sensitive. | `anchor-lang = "0.28`, `Cargo.lock`, `init_if_needed`, `payer =` |
| [Hand-rolled `try_accounts` missing derived checks](references/manual-try-accounts.md) | Critical | Manual `Accounts` implementations consume caller-supplied account slots directly. | `impl<'info> Accounts`, `fn try_accounts`, `next_account_info` |

### Native / Advanced

| Pattern | Severity | What it is | Top code signals |
| --- | --- | --- | --- |
| [Zero-copy / bytemuck / POD layout hazards](references/zero-copy-layout.md) | Medium | Zero-copy and `bytemuck` casts bypass normal serialization checks. | `zero_copy`, `bytemuck`, `AccountLoader`, `from_bytes` |
| [Relying on logs/events as security-critical state](references/event-log-reliance.md) | Medium | Solana logs/events are not program state. | `msg!`, `emit!`, `emit_cpi`, `sol_log` |
| [Manual deserialization, offsets, and versioned account layouts](references/native-parser-hazards.md) | Medium | Native Solana programs often parse account bytes manually via `next_account_info`, offsets, or unchecked deserialization. | `next_account_info`, `try_from_slice_unchecked`, `data[`, `Pubkey::new_from_array` |
| [Raw-byte PDA decoding and offset drift](references/raw-byte-pda-decoding.md) | High | Anchor/Borsh account bytes include discriminators, field order, enum/option tags, and version-sensitive layouts. | `data[`, `Pubkey::new_from_array`, `try_into()`, `UncheckedAccount` |

---

_Generated from `data/patterns.json`, `data/incidents.json`, and `data/audit-findings.json` by `scripts/build_primer_skill.py`. Edit the JSON (or the script's `TRIGGERS` map) and re-run; do not hand-edit this file._

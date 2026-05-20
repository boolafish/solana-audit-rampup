# System Program for Solana auditors

The System Program is the runtime-blessed program that creates accounts, funds them with lamports, assigns their owning program, sizes their data, and moves native SOL between accounts it owns. On Solana, almost everything else is downstream of it: a token account, a PDA state account, or a vault all begin life as a System Program `CreateAccount` (often via CPI) before another program takes ownership. For an EVM/Solidity auditor, the key adjustment is that account creation and SOL transfer are explicit instructions against a specific program, not implicit side effects of `CREATE`/`CREATE2` or a `value`-bearing call.

## Purpose and trust model

The System Program is part of the validator's set of native programs. It is not upgradeable by a normal authority and its instruction set is fixed by the runtime. You can treat its logic as trusted; what is *not* automatically trusted is that a given instruction or CPI actually targets it and uses the accounts you expect.

Its trust model rests on a few runtime rules that EVM auditors should internalize:

- **It owns "un-owned" accounts and native SOL.** A freshly created account, or any account whose `owner` is still the System Program, can be acted on by the System Program: it can transfer that account's lamports, assign it to a new owner, or allocate its data. Once another program owns an account, the System Program can no longer move that account's data or (with a signer) reassign it under normal rules.
- **Assigning ownership is a one-way handoff.** `CreateAccount`/`Assign` set the account's `owner` field. After assignment, only the new owner program may modify the account's data or shrink/realloc it under normal runtime rules. This is the `owner` = data-write-authority model described in [core-solana-security.md](core-solana-security.md); it is not asset ownership.
- **Lamport credits are permissive; debits are constrained.** Anyone can transfer lamports *into* a writable account. Reducing an account's lamports requires that the account is owned appropriately and, for System-owned accounts, that the funding key signs. This asymmetry is the source of several lamport-accounting and "balance == exactly rent" bugs.
- **Rent-exemption is a balance floor, not a recurring fee.** Created accounts must hold at least the rent-exempt minimum for their data size or creation fails. In current Solana practice rent is an account-lifecycle concern (create/realloc/close), not an Ethereum-style per-block storage charge. See the rent-exemption discussion in [core-solana-security.md](core-solana-security.md).

## EVM analog

There is no clean EVM equivalent. In Solidity:

- account/contract creation is implicit in `CREATE`/`CREATE2`, and a contract's storage is an implicit per-contract mapping;
- sending ETH is `payable`/`call{value:}` and does not "create" a storage region;
- you never explicitly "assign an owner program" to an address.

On Solana all of that is explicit and separable: you allocate bytes (`Allocate`/`CreateAccount`), you fund lamports (`Transfer`/`CreateAccount`), and you assign an owner (`Assign`/`CreateAccount`). The closest individual analogies:

| Solana System Program concept | Rough EVM analog | Caveat |
| --- | --- | --- |
| `CreateAccount` | `CREATE` plus implicit funding | On Solana it is an explicit CPI with caller-supplied accounts |
| `CreateAccountWithSeed` | `CREATE2` deterministic address | Seed address is derived from a base key + seed + owner, not init code |
| `Transfer` | `call{value:}` / sending ETH | Only moves native SOL, never SPL tokens |
| `Assign` | (no analog) | Hands data-write authority to another program |
| Nonce account | (no real analog) | A durable, on-chain replacement for recent-blockhash, not an EOA nonce |

Treat "account creation is free/implicit" intuition from EVM as a liability here. On Solana the creation step is a place where front-running, pre-creation, and ownership/space mismatches live.

## Program IDs and versions

| Item | Value |
| --- | --- |
| System Program ID | `11111111111111111111111111111111` |
| Instruction reference | `solana_program::system_instruction` |

> Accuracy stance: program IDs and versions are version- and cluster-sensitive. The System Program ID above is stable across clusters, but you should still verify program IDs and crate versions against the in-scope deployed addresses and the project's `Cargo.lock`/`Cargo.toml` rather than relying on `/latest/` docs. For the System Program specifically, confirm the `solana-program` crate version in scope, because instruction layouts and helper signatures (for example nonce instructions and `create_account_with_seed`) are version-sensitive.

## Key accounts and PDAs

The System Program has no protocol PDAs of its own, but several account roles recur and each is a validation surface:

- **The new account.** The account being created. It must be a signer for plain `CreateAccount` (it signs to authorize being created at its own address) unless it is a PDA created via `invoke_signed`, or a seed-derived address via `CreateAccountWithSeed`.
- **The funding account (payer).** A System-owned account, must sign, must be writable, and pays both the rent-exempt lamports and the creation. In EVM terms this is the `msg.value` source, but it is an explicit, signing account.
- **Seed-derived addresses.** `CreateAccountWithSeed` derives an address from `base + seed_string + owner`. This is deterministic like `CREATE2`; the `base` key must sign. It is distinct from a PDA, which is derived by `find_program_address` and "signed" only via `invoke_signed`.
- **Nonce accounts.** System-owned accounts holding durable-nonce state (the stored blockhash and the nonce authority). They enable durable-nonce transactions whose lifetime is not tied to a recent blockhash.

## Instructions that matter

```rust
// solana_program::system_instruction (signatures are version-sensitive; verify in scope)
create_account(from, to, lamports, space, owner)
create_account_with_seed(from, to, base, seed, lamports, space, owner)
assign(pubkey, owner)
allocate(pubkey, space)
transfer(from, to, lamports)
// nonce:
create_nonce_account(...)   advance_nonce_account(...)   withdraw_nonce_account(...)   authorize_nonce_account(...)
```

- **CreateAccount.** Atomically funds the new account with `lamports`, allocates `space` bytes, and sets `owner`. The new account and the payer both sign. This is the canonical "make a new state/token account" path.
- **CreateAccountWithSeed.** Same as above but the new address is deterministically derived from a base key, a seed string, and the target owner. Useful for predictable addresses without PDA signing. The `base` key signs.
- **Assign.** Changes an existing System-owned account's `owner` to a new program. The account must sign. After assignment the System Program can no longer write that account's data.
- **Allocate.** Sets the data length of a System-owned account (which must sign). Often combined with `Assign` as an alternative to `CreateAccount` when an account already exists/was pre-funded.
- **Transfer.** Moves native SOL from a System-owned `from` (signer, writable) to any writable `to`. Does not touch SPL tokens.
- **Nonce instructions.** `create_nonce_account` sets up durable-nonce state; `advance_nonce_account` consumes/rotates the stored nonce (requires the nonce authority to sign); `withdraw_nonce_account` reclaims lamports subject to rent rules; `authorize_nonce_account` changes the nonce authority.

## Security-relevant surface

The System Program itself is trusted, so the bugs live in *how a target program drives it*. Map these onto the core patterns:

- **Arbitrary-CPI target if the program ID is not pinned.** A handler that builds a `CreateAccount`/`Transfer` instruction with a caller-supplied "system program" account and never checks it is `11111111111111111111111111111111` can be pointed at a malicious program. This is the [arbitrary CPI](core-solana-security.md) class.
- **Account-already-initialized / reinitialization.** `CreateAccount` fails if the target already holds lamports or data, but multi-step flows (`Allocate` + `Assign`, or `init_if_needed`) can be coaxed into reusing an existing account. Validate that a "new" account is genuinely zeroed/uninitialized before trusting it. See reinitialization in [core-solana-security.md](core-solana-security.md).
- **Create-account front-running / init races.** Because addresses for `CreateAccountWithSeed` and PDAs are deterministic and public, an attacker can pre-create or pre-fund the target address in an earlier transaction (or earlier instruction in the same atomic transaction). A handler that assumes "this address does not exist yet, therefore it is mine to initialize" can be tricked into adopting an attacker-prepared account. Validate eventual `owner`, `space`, and zeroed data rather than mere existence.
- **Transfer to/from PDAs.** A PDA that is still System-owned can be the `from` of a `Transfer` only via `invoke_signed` with correct seeds; if a program lets the seeds or the PDA identity float, it can sign over the wrong account. Conversely, anyone can `Transfer` lamports *into* a program-owned PDA, so logic that branches on an exact lamport balance (for example "balance == rent-exempt minimum means closed") is unsafe.
- **Lamport accounting.** Native SOL is not an SPL token. Direct lamport mutation, rent floors, and the credit/debit asymmetry above produce the [native SOL lamport accounting](core-solana-security.md) bug class. Recheck balances after any System CPI rather than trusting pre-CPI values.
- **System-program-owned vs program-owned confusion.** A program must not assume an account it sees is owned by itself just because it created it earlier; ownership only transfers on `Assign`/`CreateAccount` with the target `owner` set. Equally, an account still owned by the System Program is not yet protected program state.

## What to check when the target program CPIs into it

When the program under review calls the System Program (directly or via Anchor's `system_program::{create_account, transfer, allocate, assign}` or the `init`/`init_if_needed` machinery):

- **Pin the program ID.** Require the system program account equals `11111111111111111111111111111111`. In Anchor, `Program<'info, System>` does this; for raw `AccountInfo`, use `require_keys_eq!(system_program.key(), system_program::ID)`.
- **Validate the created account's eventual owner, space, and rent.** After creation the account should be owned by the intended program (often the program under review or a token program), sized to the expected `space`, and rent-exempt. Anchor's `init` enforces payer, space, owner, and rent together; manual flows must reproduce each check.
- **Watch for someone pre-creating the account.** Do not treat "address is empty" as proof of first creation. If using `CreateAccountWithSeed` or PDA-targeted creation, confirm the resulting account's owner/data match expectations and that an attacker could not have pre-funded or pre-assigned it. Be explicit about same-transaction composition: an earlier instruction could have created or funded the address.
- **Constrain the payer and recipient.** The funding account must be a writable signer you actually intend to charge; a `Transfer` recipient must be the intended account, not a caller-substituted one. Reject `from == to` aliasing where it would distort accounting.
- **Re-check balances after the CPI.** For lamport movements, validate post-transfer invariants and rent floors on freshly read balances; do not branch on exact-balance equality given that anyone can transfer SOL in.
- **For PDA signing, validate seeds.** When the program signs a System CPI for a PDA via `invoke_signed`, ensure the seeds are canonical and scoped so the PDA cannot be made to sign over an unintended account.

## Audit checklist

- [ ] Is every System Program CPI target pinned to `11111111111111111111111111111111` (`Program<'info, System>` or explicit key check)?
- [ ] For each created account: are eventual `owner`, `space`, and rent-exempt balance validated, not just existence?
- [ ] Could the target address have been pre-created, pre-funded, or pre-assigned by an attacker (cross-transaction or same-transaction)?
- [ ] Is the funding/payer account a writable signer the protocol actually intends to charge?
- [ ] Are `Transfer` source/destination the intended accounts, with `from != to` where required?
- [ ] Does any logic branch on an exact lamport balance that anyone could perturb with a `Transfer`?
- [ ] For PDA-signed System CPIs, are the seeds canonical and resource-scoped?
- [ ] Is `Assign`/`Allocate` used in a way that could reinitialize or repurpose an existing account?
- [ ] If nonce accounts are used, is the nonce authority validated on `advance`/`withdraw`/`authorize`?
- [ ] After any System CPI that moves lamports, are post-conditions checked on freshly read balances?

## References

- https://solana.com/docs/core/accounts
- https://docs.rs/solana-program/latest/solana_program/system_instruction/index.html
- https://solana.com/docs/core/fees

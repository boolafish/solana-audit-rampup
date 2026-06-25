# Instruction introspection / signature verification misuse

- **Pattern ID:** `signature-introspection`
- **Category:** Account Validation  |  **Severity:** Critical

## Triggers — load this page when you see these

**Code signals (grep the target):** `load_instruction_at_checked`, `ed25519`, `secp256k1`, `sysvar::instructions`, `instructions_sysvar`, `load_current_index`, `relative_offset`, `verify_ed25519_ix_at_relative_offset`, `Ed25519SignatureOffsets`, `trusted_signers`, `quote_id`

**Protocol types:** bridges, meta-transactions, permit-style flows, off-chain signed orders, oracle attestations

**Concepts:** checks a signature instruction exists but not payload/signer/index; missing domain/nonce/expiry binding; transaction signer confused with trusted off-chain signer; attestation freshness vs permit nonce asymmetry; signed quote mistaken for spend authorization

## Why this differs from Solidity/EVM

Comparable to verifying a signature but not binding it to chain, contract, method, parameters, nonce, and deadline.

Solana often verifies Ed25519/secp signatures by including a verification instruction and reading the Instructions sysvar. The program must prove the exact signed payload and instruction position, not merely that some signature instruction exists. For permit and quote flows, separate the transaction signer or permit subject from the off-chain trusted signer, and distinguish one-time spend authorization from reusable price/lineage attestations.

## Bad pattern

Check that an Ed25519 instruction appears somewhere in the transaction, or parse a signed message without binding signer, verifier position, domain, action parameters, subject/source, recipient, token/mint side, amount, nonce or freshness window. Treating a signed price quote as spend authorization is also unsafe.

- *Native:* `let ix = load_instruction_at_checked(0, ix_sysvar)?; require_keys_eq!(ix.program_id, ed25519_program::ID);`
- *Anchor:* `#[account(address = sysvar::instructions::ID)] ix_sysvar` but handler only checks an Ed25519 ix exists.

## Good pattern

Require exact Instructions sysvar address, expected relative verifier position, verifier program id, signer key, domain-separated message, nonce or bounded freshness, and every action/account/amount field the handler uses. For self-contained verifier layouts, reject descriptors that point signature, pubkey, or message bytes at another instruction. Document which signed object authorizes spending versus only supplies price or quote lineage.

- *Native:* Load current index; require verifier immediately before; parse signer and message; verify domain/action/accounts/nonce/expiry.
- *Anchor:* Address-constrain sysvar and parse exact signed payload tied to `ctx.program_id`, account keys, args, nonce, and deadline.

## Audit checks

- [ ] Is the Instructions sysvar address checked?
- [ ] Is the signature instruction position tied to this instruction?
- [ ] Does the signed message include program id, instruction, user, amount, accounts, nonce, expiry?
- [ ] Are the transaction signer/source/subject and the off-chain trusted signer/oracle key distinct in the analysis?
- [ ] If several verifier instructions are expected, are their relative offsets distinct and matched to the client transaction layout?
- [ ] Is a signed quote/price attestation treated separately from spend authorization?

## Real incidents mapped to this pattern

- **Wormhole (2022)** — ~120k wETH minted / ~$320M at the time. Guardian signature verification/account validation failure involving instruction sysvar validation path.
- **Nomad (2022)** — ~$190M. Bridge replica accepted messages against a zero trusted root.
- **Ronin (2022)** — ~$624M. Off-chain validator quorum compromise.
- **deBridge Solana signature-verification-bypass class (2022)** — Class-level audit finding; no canonical loss postmortem. Signature verification bypass class in Solana bridge/message verification flows.

## Public audit findings mapped to this pattern

- **ChainSecurity CCTP V2 Audit** (Circle CCTP V2): V1/V2 attester separation and trust assumptions; Fast-message finality and reorg-risk considerations; Administrative controls and protocol configuration are part of the bridge security boundary

## Related patterns

- [Missing account relationship checks](relationship-checks.md) — `relationship-checks`
- [Sysvar spoofing](sysvar-spoof.md) — `sysvar-spoof`
- [Governance, multisig, and timelock validation gaps](governance-timelock.md) — `governance-timelock`
- [Missing owner check / spoofed account data](missing-owner.md) — `missing-owner`
- [Reinitialization / initialization confusion](reinit.md) — `reinit`
- [Upgrade authority and admin controls](upgrade-admin.md) — `upgrade-admin`

## References

- https://docs.rs/solana-program/latest/solana_program/sysvar/instructions/index.html
- https://docs.rs/solana-ed25519-program/latest/solana_ed25519_program/
- https://www.certik.com/resources/blog/wormhole-bridge-exploit-incident-analysis

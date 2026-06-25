# Threat-model scaffold for a Solana/Anchor program

Fill this in *before* pattern-matching. The goal is to know what is worth
protecting and who can touch it, so that the pattern catalog in
[SKILL.md](SKILL.md) is applied with intent rather than as a blind checklist.

## 1. Inventory

- **Program IDs** and deployed addresses (mainnet/devnet).
- **Upgradeability:** is the program upgradeable? Who holds upgrade/buffer authority?
- **Toolchain:** Anchor version, `solana-program`/SPL crate versions, `overflow-checks` setting.
- **Token model:** classic SPL Token, Token-2022, or both? Which extensions are accepted?
- **External programs called via CPI** (token, system, ATA, oracle, lending, AMM, governance).
- **Live value path vs. residue:** which programs/instructions are load-bearing today, and which are admin-only, deprecated, off-chain-only, or compatibility surface?

## 2. Assets

What can be stolen, frozen, inflated, or destroyed?

- Token vaults / native SOL balances.
- Mint authority / supply.
- Collateral and debt accounting.
- Protocol config (fees, oracle pointers, authorities, risk parameters).
- LP / position / share accounting.

## 3. Actors and trust boundaries

- **Permissionless users** — assume fully adversarial; they supply *all* accounts and instruction data.
- **Privileged roles** — admin, upgrade authority, governance, multisig, oracle publishers, keepers/liquidators.
- **Off-chain signers / issuers / relayers** — distinguish the transaction signer/user from a trusted Ed25519 signer, oracle publisher, quote issuer, keeper, API service, or off-chain registry consumer.
- **Composability** — other programs that CPI into this one, or that this one CPIs into.
- For each privileged role: what is the blast radius if its key is compromised? What can it mint, burn, freeze, pause, route, price, or settle without also controlling a user wallet?

## 4. Per-instruction account-validation matrix

For every instruction, for every account, record: signer? writable? expected
owner/program? executable? PDA seeds + canonical/stored bump? discriminator/type/version?
relationship checks (`has_one`, pool/user/mint/market/config links)? token checks
(program, mint, authority, ATA, delegate/close/freeze, Token-2022 extensions)?
sysvar address check? close/refund recipient? terminal cleanup? This matrix is where most Solana bugs surface.

## 5. Adversarial questions

- Can I substitute another valid account of the same type (wrong user/pool/mint)?
- Can I build fake accounts that only cross-check against each other?
- Can I pass the same writable account for two logical roles, or make a token transfer a successful same-account no-op?
- Can I reorder, omit, or duplicate accounts (including `remaining_accounts`)?
- Can I choose the CPI target program or the CPI's accounts?
- Can I reinitialize, close-and-revive, or realloc to corrupt state?
- Can stale, independent, or unpaired quotes/attestations inflate value?
- Are signed messages bound to the exact program, action, subject/source, recipient, token side, amount, nonce/sequence, expiry, and quote set the handler uses? Which signed object authorizes spending versus only supplies price/lineage?
- Can a mint freeze authority, close authority, transfer hook, delegate, or off-chain custody movement wedge a queued/settlement flow?
- After terminal actions, are state PDAs, escrow token accounts, pending markers, and rent refunds in the intended final state?
- Can a privileged path bypass timelock/threshold/normal controls?

## 6. Map to patterns

Now go to [SKILL.md](SKILL.md): grep for code signals, apply the protocol
playbook(s) for this program's type, run the always-check core set, and load the
matched `references/<id>.md` pages. Record each finding against its pattern id.

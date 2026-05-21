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
- **Composability** — other programs that CPI into this one, or that this one CPIs into.
- For each privileged role: what is the blast radius if its key is compromised?

## 4. Per-instruction account-validation matrix

For every instruction, for every account, record: signer? writable? expected
owner/program? executable? PDA seeds + canonical/stored bump? discriminator/type/version?
relationship checks (`has_one`, pool/user/mint/market/config links)? token checks
(program, mint, authority, ATA, delegate/close/freeze, Token-2022 extensions)?
sysvar address check? This matrix is where most Solana bugs surface.

## 5. Adversarial questions

- Can I substitute another valid account of the same type (wrong user/pool/mint)?
- Can I build fake accounts that only cross-check against each other?
- Can I pass the same writable account for two logical roles?
- Can I reorder, omit, or duplicate accounts (including `remaining_accounts`)?
- Can I choose the CPI target program or the CPI's accounts?
- Can I reinitialize, close-and-revive, or realloc to corrupt state?
- Can stale or low-liquidity oracle data inflate value?
- Can a privileged path bypass timelock/threshold/normal controls?

## 6. Map to patterns

Now go to [SKILL.md](SKILL.md): grep for code signals, apply the protocol
playbook(s) for this program's type, run the always-check core set, and load the
matched `references/<id>.md` pages. Record each finding against its pattern id.

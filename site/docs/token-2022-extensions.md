# Token-2022 extensions for auditors

Token-2022 (the Token Extensions program) is a superset of classic SPL Token. It keeps the same instruction names and account shapes you learned in [spl-token-walkthrough.md](spl-token-walkthrough.md), then adds *extensions* stored as extra data appended to mints and token accounts. For an auditor the danger is precisely that the instruction surface looks identical while the economic and trust semantics differ. This doc catalogs the extensions that change audit conclusions and the checks an integrating program owes when it accepts Token-2022.

Read this after the classic walkthrough; the per-instruction checks there are the baseline this one modifies.

## Why Token-2022 is a separate program

- **Program in scope:** Token-2022 / Token Extensions, program ID `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`. This is a **distinct program** from classic SPL Token (`TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`); the two are not interchangeable and a token belongs to exactly one of them.
- **Accuracy stance (per the repo README):** program IDs, crate versions, and cluster deployments are version- and cluster-sensitive. Pin the exact `spl-token-2022` crate version from the project's `Cargo.lock` and verify extension behavior against that version rather than `/latest/` docs. Extensions and their defaults have evolved across versions.
- **Same shapes, new tail.** Mints and token accounts use the classic base layout, then a TLV (type-length-value) region of extensions. A program that blindly `unpack`s only the base layout can miss that a mint charges a transfer fee or that an account is frozen-by-default.
- **Auditor consequence.** The owner check (`account.owner == TOKEN_2022_PROGRAM_ID`) is necessary but not sufficient. You must decide *which extensions are present* and whether your protocol's accounting survives them. This is the same lesson as [core-solana-security.md](core-solana-security.md) #20 and [patterns.json](../data/patterns.json) `token2022` / `anchor-token-interface`.

## Extension catalog with audit impact

| Extension | What it does | Audit impact / what breaks |
| --- | --- | --- |
| **Transfer fee** | Mint config withholds a fee on every transfer; fees accrue on the recipient account and are later harvested by the fee authority. | **Amount received ≠ amount sent.** Any code that assumes `dest.amount += amount` is wrong. Use `transfer_checked` and read the *actual* delta by reloading the account, or compute the fee from the mint config. Vault accounting, LP math, and "credit what we sent" logic are all exposed. |
| **Transfer hook** | On each transfer the program CPIs into a separate hook program with extra accounts. | Transfers become an **arbitrary CPI** ([core-solana-security.md](core-solana-security.md) #8). The hook can fail (DoS), require extra accounts your instruction must supply, or run attacker logic. Pin and review the hook program; do not treat a transfer as a pure balance move. |
| **Confidential transfer** | Amounts are encrypted; balances split into public/pending/available with ZK proofs. | The on-chain `amount` you read may **not reflect the economic balance**. Protocols that need to observe real amounts (oracles, accounting) generally cannot support confidential mints. Flag as incompatible unless explicitly designed for. |
| **Default account state** | New token accounts for the mint can default to **Frozen**. | A freshly created ATA may be **unusable until thawed** by the freeze authority. Integrator flows that create-and-immediately-use an account can break; and it gives the freeze authority gatekeeping power over all new holders. |
| **Permanent delegate** | The mint defines a delegate that can transfer/burn **any** account of that mint, unconditionally and irrevocably. | A third party can **move or destroy user/vault funds at will**. This has no classic-SPL analog. Treat as a custodial/seizure power; a protocol holding such tokens does not truly control its balances. |
| **Non-transferable** | Tokens cannot be transferred after mint (soulbound). | Any protocol that needs to **move the token out** (collateral, LP, escrow) will fail. Only burn/close paths work. Verify the protocol does not assume transferability. |
| **Interest-bearing** | Stores an interest rate; the **UI amount** drifts from the raw `amount` over time. | Raw `amount` is *not* the displayed/economic balance. Don't mix raw amounts with rate-adjusted UI amounts; conversions need the mint's rate and `amount_to_ui_amount`. Rounding/precision bugs ([patterns.json](../data/patterns.json) `math`) lurk here. |
| **Mint close authority** | A mint (not just a token account) can be **closed** by an authority. | Classic SPL mints are permanent; here a mint can disappear. Code that assumes a mint account is immortal (cached config, stored mint pubkey) can hit a closed/revived mint account. |
| **Metadata pointer** (and metadata) | Mint points to (or embeds) metadata; pointer is set by an authority. | The pointer can reference an **arbitrary account**; do not trust metadata as authoritative for security decisions, and verify the pointer target if it influences logic. Mostly display, but watch for trust placed in mutable metadata. |

Additional extensions exist (CPI guard, memo-required-on-transfer, group/member pointers, scaled UI amount, etc.); enumerate the *actual* TLV set on the in-scope mint and account rather than assuming a fixed list.

## What changes for an auditor accepting Token-2022

- **Amount-received ≠ amount-sent.** With transfer fees, the destination credit is less than the sent amount. The correct pattern is to **read the balance delta after the CPI** (reload the destination, per [patterns.json](../data/patterns.json) `stale-cpi-reload`) or compute the fee from the mint's transfer-fee config. Never assume conservation of `amount` across a transfer.
- **Transfer-hook CPI trust.** When the mint has a transfer hook, `transfer_checked` triggers a CPI into the hook program with extra accounts resolved from the mint's hook config. Your instruction must (a) supply those extra accounts, (b) tolerate hook failure as a DoS/availability surface, and (c) treat the hook program as a pinned, reviewed dependency — an unreviewed hook is arbitrary CPI ([core-solana-security.md](core-solana-security.md) #8).
- **Extension-policy checks.** Decide an explicit allowlist or denylist of extensions. A protocol that "just supports Token-2022" without inspecting extensions silently accepts permanent delegates, fees, frozen-by-default, and hooks. Parse the TLV region and reject mints/accounts whose extensions violate the protocol's assumptions.
- **`InterfaceAccount` / token-interface.** In Anchor, `InterfaceAccount<'info, Mint>` / `InterfaceAccount<'info, TokenAccount>` plus `Interface<'info, TokenInterface>` let one program accept either token program. This validates **token-interface shape, not economic compatibility** ([patterns.json](../data/patterns.json) `anchor-token-interface`). Always bind `mint::token_program = token_program` and `token::token_program = token_program` so the mint and account agree on a single intended program, and still perform extension-policy checks. If the protocol is not designed for extensions, prefer pinning to classic `Program<'info, Token>` instead.

## CPI into Token-2022 checklist

When a program CPIs into Token-2022 (transfer/mint/burn/etc.), verify:

- [ ] **Program ID is pinned** to `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` (or chosen via a validated `Interface`), never a caller-supplied `AccountInfo` ([core-solana-security.md](core-solana-security.md) #8).
- [ ] **Mint and token accounts are bound to the same token program** (`*::token_program` constraints), so you are not mixing a classic account with a Token-2022 mint.
- [ ] **Use the `*_checked` variants** with correct `decimals`; Token-2022 effectively requires decimals to be passed and many extensions depend on it.
- [ ] **Transfer-hook extra accounts are resolved and supplied**, and the hook program is pinned/reviewed; account for hook failure in availability analysis.
- [ ] **Post-CPI balances are reloaded** and the *actual* received amount is used (transfer fees), not the requested amount ([patterns.json](../data/patterns.json) `stale-cpi-reload`).
- [ ] **Extension allowlist/denylist enforced** for the specific mint: reject (or explicitly handle) transfer fee, permanent delegate, non-transferable, confidential, interest-bearing, default-frozen, and mint-close-authority as the protocol requires.
- [ ] **ATA derivation threads the right program** via `get_associated_token_address_with_program_id` — do not assume the classic Token program when deriving ATAs ([core-solana-security.md](core-solana-security.md) #20).
- [ ] **Default-account-state / frozen** handled: a newly created account may be frozen and unusable until thawed.
- [ ] **Mint immortality not assumed**: with mint close authority a mint can be closed; validate at point of use.

## References

- https://spl.solana.com/token-2022
- https://solana.com/docs/tokens/extensions
- https://docs.rs/spl-token-2022/latest/spl_token_2022/
- https://github.com/solana-program/token-2022
- https://github.com/solana-labs/security-audits/blob/master/spl/OtterSecToken2022Audit-2023-11-03.pdf
- https://github.com/solana-labs/security-audits/blob/master/spl/TrailOfBitsToken2022Audit-2023-02-10.pdf

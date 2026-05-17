window.PATTERNS = [
  {
    "id": "missing-signer",
    "category": "Core Solana",
    "severity": "Critical",
    "title": "Missing signer authorization",
    "solidity": "Closest to checking `owner == msg.sender` but forgetting `msg.sender`; Solana has no implicit caller identity.",
    "difference": "A pubkey appearing in account data or account list is not proof of authorization. `is_signer` must be required for the authority, or the authority must be a PDA signed via seeds in a CPI context.",
    "bad": "Accept `authority: AccountInfo` / `UncheckedAccount` and compare `authority.key()` to `state.admin`, but never require a signature.",
    "good": "Use `Signer<'info>` or `#[account(signer)]`; combine with `has_one = authority` / explicit relationship checks. For PDA authorities, validate seeds and use `invoke_signed` only for intended CPIs.",
    "checks": [
      "Is every privileged human/keypair account a `Signer`?",
      "Are PDA authorities validated by canonical seeds and scoped to the resource?",
      "Are admin/config relationships checked, not only account presence?"
    ],
    "refs": [
      "https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/signer-auth.md",
      "https://www.anchor-lang.com/docs/references/account-constraints"
    ]
  },
  {
    "id": "missing-owner",
    "category": "Core Solana",
    "severity": "Critical",
    "title": "Missing owner check / spoofed account data",
    "solidity": "More like trusting bytes from an arbitrary contract address as if they were your contract storage.",
    "difference": "Program state is stored in separate accounts supplied by the caller. If raw data is deserialized without checking `account.owner`, attackers can create lookalike accounts with spoofed bytes.",
    "bad": "Deserialize config, user, vault, or market state from arbitrary `AccountInfo` and trust fields such as `admin`, `mint`, `balance`, or `bump`.",
    "good": "For program state, require `account.owner == program_id`; in Anchor prefer `Account<'info, T>`. For SPL Token accounts, require owner is Token/Token-2022 program and validate internal fields.",
    "checks": [
      "For every raw account: is owner checked?",
      "Are typed Anchor accounts used where possible?",
      "For token accounts: is token program plus mint/authority checked?"
    ],
    "refs": [
      "https://solana.com/docs/core/accounts",
      "https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/owner-checks.md",
      "https://neodyme.io/en/blog/solana_common_pitfalls/"
    ]
  },
  {
    "id": "relationship-checks",
    "category": "Core Solana",
    "severity": "High",
    "title": "Missing account relationship checks",
    "solidity": "Similar to using a valid ERC20/vault address but not verifying it is the vault for this pool/user.",
    "difference": "The transaction supplies all accounts. A correct-type account can still belong to another user, mint, pool, market, or config.",
    "bad": "Withdraw using `vault` and `user`, but never verify `vault.authority == vault_authority`, `position.pool == pool`, or token account mint matches expected mint.",
    "good": "Validate every relationship: `has_one`, stored pubkeys, PDA derivation, ATA derivation, token mint/authority, pool/market IDs.",
    "checks": [
      "Can I substitute another valid account of the same type?",
      "Are all token mint/authority relationships bound?",
      "Are pool/user/position/config keys cross-checked?"
    ],
    "refs": [
      "https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/account-data-matching.md",
      "https://www.anchor-lang.com/docs/references/account-constraints"
    ]
  },
  {
    "id": "type-cosplay",
    "category": "Core Solana",
    "severity": "High",
    "title": "Type cosplay / discriminator confusion",
    "solidity": "Comparable to storage-layout confusion or decoding calldata/storage as the wrong type.",
    "difference": "Raw account bytes can be interpreted as another struct if no discriminator/type tag is enforced.",
    "bad": "Deserialize unchecked Borsh bytes as `AdminConfig` when the account is actually `UserProfile` with compatible fields.",
    "good": "Use Anchor `Account<T>` with discriminators, or implement explicit discriminator/version/magic fields in native programs.",
    "checks": [
      "Are all manually deserialized accounts type-tagged?",
      "Can two account structs share a dangerous prefix layout?",
      "Are Anchor discriminators bypassed via unchecked deserialization?"
    ],
    "refs": [
      "https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/type-cosplay.md",
      "https://github.com/coral-xyz/sealevel-attacks"
    ]
  },
  {
    "id": "reinit",
    "category": "Lifecycle / Rent",
    "severity": "Critical",
    "title": "Reinitialization / initialization confusion",
    "solidity": "Similar to unprotected initializer bugs in proxies, but with explicit account allocation/ownership/state flags.",
    "difference": "Accounts can be created, assigned, funded, resized, closed, or reused. `init_if_needed` can hide reinit paths if the handler resets critical fields.",
    "bad": "`initialize` overwrites admin/config on an already initialized account; `init_if_needed` then unconditionally sets authority.",
    "good": "Prefer separate `init`; store and check initialized/version flags; never reset authority/config on reuse; test close→recreate and same-transaction flows.",
    "checks": [
      "Can initialize be called twice?",
      "Does `init_if_needed` change existing critical fields?",
      "Can a closed/drained account be revived and reused?"
    ],
    "refs": [
      "https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/reinitialization-attacks.md",
      "https://www.anchor-lang.com/docs/references/account-constraints"
    ]
  },
  {
    "id": "pda-bump",
    "category": "PDA",
    "severity": "High",
    "title": "PDA seed/bump mistakes and non-canonical bumps",
    "solidity": "Roughly comparable to deterministic CREATE2 addresses, but PDAs are also signing authorities for CPIs.",
    "difference": "PDA derivation includes seeds and a bump. Allowing arbitrary valid bumps or under-scoped seeds can create multiple authority addresses or collisions of authority scope.",
    "bad": "Accept user-provided bump with `create_program_address`; use seeds like `[b\"vault\"]` globally for many assets.",
    "good": "Use canonical `find_program_address`; in Anchor use `seeds = [...]` and `bump`; store bump when reused; include domain prefix plus user/pool/mint/resource in seeds.",
    "checks": [
      "Is bump canonical or stored and verified?",
      "Are seeds domain-separated and resource-scoped?",
      "Can the same PDA sign for unrelated resources?"
    ],
    "refs": [
      "https://solana.com/docs/core/pda",
      "https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/bump-seed-canonicalization.md",
      "https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/pda-sharing.md"
    ]
  },
  {
    "id": "arbitrary-cpi",
    "category": "CPI",
    "severity": "Critical",
    "title": "Arbitrary CPI / missing program ID check",
    "solidity": "Like low-level calling an attacker-supplied contract while assuming it is ERC20/System/Oracle.",
    "difference": "The CPI target program account is often passed by the caller. Without checking program ID/executable, attacker can pass a malicious program or wrong token program.",
    "bad": "Build `Instruction { program_id: supplied_program.key(), ... }` and call `invoke` without pinning `spl_token::ID`, System Program, ATA program, etc.",
    "good": "Use `Program<'info, Token/System/...>`, `Interface<'info, TokenInterface>` with explicit allowed token programs, or `require_keys_eq!(program.key(), expected_id)`.",
    "checks": [
      "Is every CPI target typed or address-checked?",
      "Are program accounts executable where expected?",
      "Is Token vs Token-2022 support intentional and constrained?"
    ],
    "refs": [
      "https://solana.com/docs/core/cpi",
      "https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/arbitrary-cpi.md",
      "https://www.anchor-lang.com/docs/basics/cpi"
    ]
  },
  {
    "id": "cpi-substitution",
    "category": "CPI",
    "severity": "Critical",
    "title": "CPI account substitution / confused deputy",
    "solidity": "Like approving/transferring from an unintended vault because callee accounts were attacker-selected.",
    "difference": "Even when CPI program ID is correct, the caller supplies all callee accounts. Your program may sign with a PDA over attacker-chosen accounts.",
    "bad": "Program signs SPL Token transfer from `source` to `dest` without verifying `source` is protocol vault, mint matches, and authority is the intended PDA.",
    "good": "Before CPI, validate every account: token program, source/dest address or ATA derivation, mint, authority, PDA seeds, delegate/close authority if relevant.",
    "checks": [
      "Could attacker make the program sign over a different token account?",
      "Are CPI account metas exactly the validated accounts?",
      "Are post-CPI balances/invariants rechecked where needed?"
    ],
    "refs": [
      "https://solana.com/docs/core/cpi",
      "https://www.anchor-lang.com/docs/references/account-constraints"
    ]
  },
  {
    "id": "duplicate-mut",
    "category": "Account Validation",
    "severity": "High",
    "title": "Duplicate mutable accounts / aliasing",
    "solidity": "Similar to passing the same address as two roles in a function that assumes distinct addresses.",
    "difference": "The same account key can be supplied for multiple account parameters unless constrained; mutable aliases can break debit/credit or game logic.",
    "bad": "`transfer_rewards(from, to)` assumes two accounts but attacker passes same account for both.",
    "good": "Add explicit `a.key() != b.key()` constraints for all roles that must be distinct. In Anchor, use custom `constraint`; be aware of `dup` only when intentional.",
    "checks": [
      "Which accounts are assumed distinct?",
      "Can payer==recipient, vault==user token account, user_a==user_b?",
      "Does Anchor typed mut duplicate protection cover this exact case?"
    ],
    "refs": [
      "https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/duplicate-mutable-accounts.md",
      "https://github.com/coral-xyz/sealevel-attacks"
    ]
  },
  {
    "id": "sysvar-spoof",
    "category": "Account Validation",
    "severity": "High",
    "title": "Sysvar spoofing",
    "solidity": "No close Solidity analogue; closest is trusting an oracle/precompile address without checking it.",
    "difference": "Sysvars can be accessed via trusted APIs or passed as accounts. If passed unchecked, fake sysvar-like accounts can spoof clock, rent, instructions, etc.",
    "bad": "Read Clock or Instructions sysvar from arbitrary `AccountInfo` without checking sysvar ID.",
    "good": "Use `Clock::get()`, `Rent::get()`; otherwise check exact sysvar address and owner. In Anchor use `Sysvar<'info, Clock>`.",
    "checks": [
      "Are sysvar accounts address-checked?",
      "Is instruction introspection tied to exact index/message/program?",
      "Are Ed25519/secp verification instructions parsed safely?"
    ],
    "refs": [
      "https://docs.rs/solana-program/latest/solana_program/sysvar/index.html",
      "https://docs.rs/solana-program/latest/solana_program/sysvar/instructions/index.html"
    ]
  },
  {
    "id": "close-revival",
    "category": "Lifecycle / Rent",
    "severity": "High",
    "title": "Account close, revival, and stale data",
    "solidity": "Similar to selfdestruct/recreate or stale storage assumptions, but account lamports/data/owner make it Solana-specific.",
    "difference": "Closing usually transfers lamports and resets/assigns account. Manual closes can leave data/discriminator valid; same transaction composition can revive accounts.",
    "bad": "Drain lamports but leave owner/data/discriminator as valid state, then later logic trusts stale data after refund.",
    "good": "Use Anchor `close = recipient`; for manual close, zero data or set closed discriminator, transfer lamports, assign owner appropriately, and avoid later same-tx trust.",
    "checks": [
      "Are closed accounts impossible to reuse later in the same transaction?",
      "Does close reset discriminator/data?",
      "Are refunds sent to the intended recipient?"
    ],
    "refs": [
      "https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/closing-accounts.md",
      "https://www.anchor-lang.com/docs/references/account-constraints"
    ]
  },
  {
    "id": "realloc-rent",
    "category": "Lifecycle / Rent",
    "severity": "Medium",
    "title": "Rent-exemption and realloc/storage resizing edge cases",
    "solidity": "Solidity storage expansion is paid by gas; Solana account data size and rent-exempt lamports are explicit state.",
    "difference": "Growing/shrinking accounts changes required rent and may expose stale bytes. Account lifecycle is part of protocol logic.",
    "bad": "Manual `realloc` larger without funding rent, cap checks, or zeroing new bytes; shrink/grow causing type confusion or stale sensitive data.",
    "good": "Use Anchor `realloc`, `realloc::payer`, `realloc::zero`; recompute rent; cap size; use checked math for space calculations.",
    "checks": [
      "Who pays extra rent?",
      "Is new size bounded and computed with checked arithmetic?",
      "Are newly allocated bytes zeroed if read later?"
    ],
    "refs": [
      "https://solana.com/docs/core/accounts",
      "https://www.anchor-lang.com/docs/references/account-constraints"
    ]
  },
  {
    "id": "math",
    "category": "Math / Accounting",
    "severity": "High",
    "title": "Integer overflow, precision, rounding, decimal mismatch",
    "solidity": "Familiar from Solidity, but Rust release behavior, u64 token amounts, and fixed-point conventions differ.",
    "difference": "Lamports/token amounts are often `u64`; prices and reward math need `u128` intermediates, explicit rounding, decimal normalization.",
    "bad": "`amount * price / scale` in u64; division before multiplication; no checked math; token decimals assumed identical.",
    "good": "Use `checked_*`, `u128` intermediates, explicit rounding direction, decimal bounds, invariant tests/fuzzing.",
    "checks": [
      "Any unchecked arithmetic?",
      "Are token decimals and oracle decimals normalized?",
      "Can repeated small actions exploit rounding?"
    ],
    "refs": [
      "https://neodyme.io/en/blog/solana_common_pitfalls/",
      "https://github.com/solana-foundation/developer-content/tree/main/content/courses/program-security"
    ]
  },
  {
    "id": "compute-dos",
    "category": "Execution / DoS",
    "severity": "Medium",
    "title": "Compute budget, large inputs, and hot-account DoS",
    "solidity": "Like gas DoS, but compute units plus account locks and writable-hot-account serialization matter.",
    "difference": "Transactions have compute limits; writable account locks constrain parallelism. A single global mutable account can serialize protocol usage and become spam target.",
    "bad": "Unbounded loop over `remaining_accounts`; O(n²) checks; every user flow writes same global counter/config; unnecessary `mut`.",
    "good": "Bound lengths, cap CPIs, price work, split deterministic chunks, shard state, keep config readonly unless changed.",
    "checks": [
      "Are remaining accounts/vector lengths bounded?",
      "Are there global writable hot accounts?",
      "Could attacker force expensive CPIs/PDA derivations?"
    ],
    "refs": [
      "https://solana.com/docs/core/fees",
      "https://solana.com/docs/core/transactions"
    ]
  },
  {
    "id": "token2022",
    "category": "SPL Token / Token-2022",
    "severity": "High",
    "title": "SPL Token / Token-2022 validation gaps",
    "solidity": "Comparable to ERC20 quirks, fee-on-transfer tokens, callbacks/hooks, and wrong token address assumptions.",
    "difference": "Token balances are accounts owned by Token/Token-2022. Token-2022 extensions can add transfer fees, hooks, default frozen state, confidential transfers, permanent delegates, CPI guard, etc.",
    "bad": "Accept any token account as vault; check authority but not mint; support Token-2022 without accounting for transfer fees/hooks/extensions.",
    "good": "Validate token program, mint, account authority, ATA derivation, decimals, delegate/close authority, and relevant Token-2022 extensions. Bind Anchor token constraints to `token_program`.",
    "checks": [
      "Is classic Token vs Token-2022 support explicit?",
      "Do accounting assumptions survive transfer fees/hooks/frozen accounts?",
      "Are ATAs derived when expected?"
    ],
    "refs": [
      "https://spl.solana.com/token",
      "https://spl.solana.com/token-2022",
      "https://solana.com/docs/tokens/extensions",
      "https://github.com/solana-labs/security-audits/blob/master/spl/OtterSecToken2022Audit-2023-11-03.pdf"
    ]
  },
  {
    "id": "oracle-mev",
    "category": "Economic / MEV",
    "severity": "High",
    "title": "Oracle, ordering, and MEV/front-running assumptions",
    "solidity": "Familiar DeFi class, but Solana has no Ethereum-style public mempool; MEV still exists via leaders, priority fees, private orderflow, Jito/bundles, and ordering-sensitive flows.",
    "difference": "“No mempool, no front-running” is misleading. Risks vary by infra and protocol: AMM slippage, liquidations, oracle price-update ordering, auctions/mints, priority-fee wars.",
    "bad": "No slippage/stale quote checks; lending accepts spot price without freshness/confidence/liquidity bounds; liquidation logic assumes deterministic ordering.",
    "good": "Require slippage limits, oracle freshness/confidence checks, TWAP/limits/circuit breakers where appropriate, robust liquidation ordering assumptions, and replay/nonce/domain checks.",
    "checks": [
      "Are oracle feeds correct, fresh, and confidence-bounded?",
      "Can price updates/trades/liquidations be reordered profitably?",
      "Are priority fees/bundles/private orderflow assumptions documented?"
    ],
    "refs": [
      "https://www.helius.dev/blog/solana-mev-an-introduction",
      "https://www.helius.dev/blog/priority-fees-understanding-solanas-transaction-fee-mechanics",
      "https://solana.com/docs/core/fees",
      "https://rekt.news/mango-markets-rekt/"
    ]
  },
  {
    "id": "upgrade-admin",
    "category": "Governance / Admin",
    "severity": "High",
    "title": "Upgrade authority and admin controls",
    "solidity": "Comparable to proxy admin/owner/timelock risk.",
    "difference": "Solana programs can be upgradeable via an upgrade authority; admin keys may also control config, pausing, vault migration, oracle/mint changes.",
    "bad": "Single hot key upgrade authority or admin can upgrade program / drain / alter oracle without delay or disclosure.",
    "good": "Inventory upgrade authority, program deploy status, multisig/timelock/DAO controls, emergency powers, and bounded admin parameter ranges.",
    "checks": [
      "Is the program upgradeable? Who holds upgrade authority?",
      "Are admin instructions properly signer/relationship constrained?",
      "Are dangerous parameter changes bounded and observable?"
    ],
    "refs": [
      "https://solana.com/docs/core/programs",
      "https://github.com/solana-labs/security-audits"
    ]
  },
  {
    "id": "anchor-unchecked",
    "category": "Anchor",
    "severity": "High",
    "title": "UncheckedAccount / AccountInfo used as trusted state",
    "solidity": "Like accepting arbitrary address and decoding it as your protocol contract/token without interface/address checks.",
    "difference": "Anchor only validates what the account type/constraints express. `UncheckedAccount` and raw `AccountInfo` are present but semantically unchecked.",
    "bad": "`pub vault: UncheckedAccount<'info>` then treat it as protocol vault or token account in handler.",
    "good": "Use `Account<'info, Vault>`, `Account<'info, TokenAccount>`, `Program<'info, Token>`, plus seeds/owner/address/token constraints. If raw is unavoidable, manually check key, owner, signer/writable, data length, discriminator, PDA and relationships.",
    "checks": [
      "Why is this account unchecked?",
      "Did manual checks recreate all Anchor constraints?",
      "Can a valid-looking but attacker-owned account pass?"
    ],
    "refs": [
      "https://docs.rs/anchor-lang/latest/anchor_lang/accounts/unchecked_account/struct.UncheckedAccount.html",
      "https://docs.rs/anchor-lang/latest/anchor_lang/accounts/account/struct.Account.html",
      "https://www.anchor-lang.com/docs/references/account-constraints"
    ]
  },
  {
    "id": "anchor-init-if-needed",
    "category": "Anchor",
    "severity": "Critical",
    "title": "`init_if_needed` resets existing state",
    "solidity": "Similar to proxy initializer callable after deployment.",
    "difference": "Anchor’s `init_if_needed` makes account creation/use convenient but can hide reinitialization bugs if handler overwrites fields on both paths.",
    "bad": "Use `#[account(init_if_needed,...)]` and always set `state.authority = payer.key()` or reset counters/config.",
    "good": "Prefer separate init and use instructions. If using `init_if_needed`, gate first-time writes with initialized/version flags and never reset authority/config for existing accounts.",
    "checks": [
      "Is `init_if_needed` feature enabled?",
      "Which fields are written every call?",
      "Can close/recreate/reinit change authority?"
    ],
    "refs": [
      "https://www.anchor-lang.com/docs/references/account-constraints",
      "https://docs.rs/anchor-lang/latest/anchor_lang/derive.Accounts.html",
      "https://github.com/coral-xyz/sealevel-attacks"
    ]
  },
  {
    "id": "anchor-token-interface",
    "category": "Anchor",
    "severity": "High",
    "title": "Token-interface constraints not bound to intended token program",
    "solidity": "Like supporting ERC20 variants without deciding whether fee-on-transfer/hooks/permissions are allowed.",
    "difference": "Anchor `InterfaceAccount` can support SPL Token and Token-2022, but protocol assumptions may break unless token program and extensions are intentional.",
    "bad": "Accept `InterfaceAccount<Mint>` and `InterfaceAccount<TokenAccount>` with `Interface<TokenInterface>` but do not bind `mint::token_program` / `token::token_program` or validate extensions.",
    "good": "Decide classic Token, Token-2022, or either; bind constraints to `token_program`; inspect extensions that affect accounting or transfer behavior.",
    "checks": [
      "Is Token-2022 support intentional?",
      "Are transfer fees/hooks/frozen/default state/permanent delegate relevant?",
      "Are mint/account constraints bound to the same token program?"
    ],
    "refs": [
      "https://www.anchor-lang.com/docs/tokens/basics/create-token-account",
      "https://www.anchor-lang.com/docs/references/account-constraints",
      "https://solana.com/docs/tokens/extensions"
    ]
  }
];

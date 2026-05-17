# References and evidence base

These are the high-signal sources used to build the guide. Prefer official docs, framework docs, and public audit/exploit writeups over unsourced social posts.

- https://docs.rs/solana-program/latest/solana_program/sysvar/index.html
- https://docs.rs/solana-program/latest/solana_program/sysvar/instructions/index.html
- https://github.com/coral-xyz/sealevel-attacks
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/account-data-matching.md
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/arbitrary-cpi.md
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/bump-seed-canonicalization.md
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/closing-accounts.md
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/duplicate-mutable-accounts.md
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/owner-checks.md
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/pda-sharing.md
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/reinitialization-attacks.md
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/signer-auth.md
- https://github.com/solana-foundation/developer-content/blob/main/content/courses/program-security/type-cosplay.md
- https://github.com/solana-foundation/developer-content/tree/main/content/courses/program-security
- https://github.com/solana-labs/security-audits
- https://github.com/solana-labs/security-audits/blob/master/spl/OtterSecToken2022Audit-2023-11-03.pdf
- https://neodyme.io/en/blog/solana_common_pitfalls/
- https://rekt.news/mango-markets-rekt/
- https://solana.com/docs/core/accounts
- https://solana.com/docs/core/cpi
- https://solana.com/docs/core/fees
- https://solana.com/docs/core/pda
- https://solana.com/docs/core/programs
- https://solana.com/docs/core/transactions
- https://solana.com/docs/tokens/extensions
- https://spl.solana.com/token
- https://spl.solana.com/token-2022
- https://www.anchor-lang.com/docs/basics/cpi
- https://www.anchor-lang.com/docs/references/account-constraints
- https://www.helius.dev/blog/priority-fees-understanding-solanas-transaction-fee-mechanics
- https://www.helius.dev/blog/solana-mev-an-introduction

## Incident / audit examples to inspect during ramp-up

- Wormhole bridge exploit (2022): guardian/signature/sysvar/account validation class. https://www.certik.com/skynet-report/wormhole-bridge-exploit-incident-analysis
- Cashio exploit (2022): incomplete collateral/account validation and infinite mint class. https://rekt.news/cashio-rekt
- Mango Markets (2022): oracle/market manipulation and bad debt class. https://rekt.news/mango-markets-rekt/
- Nirvana Finance (2022): price/economic manipulation class. https://www.certik.com/skynet-report/nirvana-finance-incident-analysis
- Solana Labs public security audits: https://github.com/solana-labs/security-audits

## Caveats

- Solana and Anchor evolve. Confirm exact behavior against the project’s Anchor/Solana/SPL versions.
- Some CTF examples document historical classes; modern Anchor may mitigate pieces by default, but unchecked/manual code can reintroduce them.
- MEV/front-running is infrastructure-dependent. Avoid blanket claims such as “front-running is impossible on Solana.”

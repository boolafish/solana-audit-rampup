# Public audit report patterns

Recurring findings from public Solana audits reinforce the same account-validation and lifecycle themes.

## OtterSec Token-2022 Audit — SPL Token-2022

Common findings:
- Incorrect account ordering
- Lack of mint account verification
- Missing signer checks
- Unnecessary writable multisig access
- Confidential-transfer validation issues

Mapped pattern IDs: token2022, remaining-accounts, missing-signer

References:
- https://github.com/solana-labs/security-audits/blob/master/spl/OtterSecToken2022Audit-2023-11-03.pdf

## Trail of Bits Token-2022 Audit — SPL Token-2022

Common findings:
- Missing ownership checks
- TLV/extension parsing and length checks
- Front-running concern in withheld-token withdrawal flow

Mapped pattern IDs: token2022, missing-owner, oracle-mev

References:
- https://github.com/solana-labs/security-audits/blob/master/spl/TrailOfBitsToken2022Audit-2023-02-10.pdf

## Zellic Single Pool Audit — SPL Single Pool

Common findings:
- Incorrect vote account deserialization offsets
- Missing authority account check
- Strong account-by-account validation matrix examples

Mapped pattern IDs: native-parser-hazards, relationship-checks, missing-owner

References:
- https://github.com/solana-labs/security-audits/blob/master/spl/ZellicSinglePoolAudit-2023-06-21.pdf

## Halborn Stake Pool Audit — SPL Stake Pool

Common findings:
- Fee update timing/epoch edge cases
- Unsafe unwrap/panic surfaces
- Overflow-check configuration concerns

Mapped pattern IDs: math, compute-dos, native-parser-hazards

References:
- https://github.com/solana-labs/security-audits/blob/master/spl/HalbornStakePoolAudit-2023-01-25.pdf

## OtterSec Address Lookup Table Audit — Core Solana

Common findings:
- Indirect account loading lifecycle
- Deactivation/close/reuse concerns
- Authority/lifecycle edge cases

Mapped pattern IDs: close-revival, remaining-accounts, upgrade-admin

References:
- https://github.com/solana-labs/security-audits/blob/master/solana/AddressLookupTable_OtterSec_2022-08-23.pdf

## OtterSec Account Compression Audit — SPL Account Compression

Common findings:
- Merkle proof/invariant validation
- Tree parameter checks
- Underflow/panic-style issues

Mapped pattern IDs: math, native-parser-hazards

References:
- https://github.com/solana-labs/security-audits/blob/master/spl/OtterSecAccountCompressionAudit-2022-12-03.pdf

## ChainSecurity CCTP V2 Audit — Circle CCTP V2

Common findings / themes:
- V1/V2 attester separation and trust assumptions
- Fast-message finality and reorg-risk considerations
- Administrative controls and protocol configuration as bridge security boundary

Mapped pattern IDs: signature-introspection, governance-timelock, relationship-checks

References:
- https://reports.chainsecurity.com/Circle/ChainSecurity_Circle_CCTPV2_Audit.pdf

## OtterSec EVM CCTP V2 Audit — Circle CCTP V2

Common findings / themes:
- Specification and implementation consistency across message formats
- Exact V2 interface review instead of reusing V1 integration assumptions

Mapped pattern IDs: relationship-checks, native-parser-hazards

References:
- https://6778953.fs1.hubspotusercontent-na1.net/hubfs/6778953/PDFs/public_evm_cctp_audit_final%20%282%29.pdf

## OpenZeppelin Sponsored CCTP Deposits from Solana Audit — Solana CCTP Periphery

Common findings / themes:
- Nonce PDA and rent-sponsorship lifecycle review
- CCTP CPI boundaries and account validation

Mapped pattern IDs: pda-bump, cpi-substitution, remaining-accounts

References:
- https://www.openzeppelin.com/news/sponsored-cctp-deposits-from-solana-audit

## Certora Kamino Lending Security Report — Kamino Lending / KLend

Common findings / themes:
- Exchange-rate precision loss can affect redeem accounting
- Small-number rounding and reserve accounting require dedicated tests

Mapped pattern IDs: math, oracle-validation

References:
- https://www.certora.com/reports/kamino-lending-security-report
- https://www.certora.com/blog/securing-kamino-lending


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


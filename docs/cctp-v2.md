# CCTP V2 primer for Solana auditors

Circle Cross-Chain Transfer Protocol is not a generic bridge where the Solana program proves another chain's state. The source chain burns USDC and emits a Circle message, Circle's Iris attestation service signs that message after the requested finality level, and the destination chain's `MessageTransmitterV2` accepts the message plus attestation before minting or releasing USDC through the token messenger/minter path.

For a Solana auditor, the important boundary is therefore split between:

- on-chain account and instruction validation in the local CCTP programs;
- Circle domain, nonce, finality, fee, denylist, and recipient encoding rules;
- off-chain attester behavior and operational assumptions.

```mermaid
sequenceDiagram
    actor User
    participant Src as Source chain<br/>(e.g. Ethereum)
    participant Iris as Circle Iris<br/>attestation service
    participant Dst as Destination chain<br/>(Solana MessageTransmitterV2)

    User->>Src: depositForBurn(amount, destinationDomain,<br/>mintRecipient, maxFee, minFinalityThreshold)
    Src->>Src: Burn USDC, emit MessageSent event<br/>(nonce, body, destinationCaller)
    Src-->>Iris: Event observed by Iris
    Note over Iris: Wait for requested finality level
    Iris-->>Iris: Attester set signs message hash
    User->>Dst: receiveMessage(message, attestation)
    Dst->>Dst: Verify attester signatures ≥ threshold<br/>Check nonce not used<br/>Validate source domain + sender
    Dst->>Dst: Mark nonce used (replay protection)
    Dst-->>User: Mint USDC to mintRecipient
```
<span class="figcap">End-to-end CCTP V2 flow. Every arrow crossing the dashed trust boundary depends on Circle's attester set — the on-chain program only validates the signed message, not the source-chain state directly.</span>

## V1 to V2 deltas

V2 introduces new program or contract addresses and should be treated as a separate integration target from V1. Do not reuse V1 account ordering, instruction layouts, attestation endpoints, or operational assumptions without checking the V2 docs and IDL.

Key audit deltas:

- `destinationCaller` is now part of the burn flow. A zero 32-byte value means any caller may submit the destination `receiveMessage`; a nonzero value restricts who can complete the destination message.
- `maxFee` is part of the burn parameters. It caps the fee Circle may take for the route. `0` means the integrator expects a no-fee route.
- `minFinalityThreshold` requests the minimum finality level the attestation must satisfy.
- V2 attestations are fetched through the `/v2/messages` API, not the V1 endpoint.
- V2 supports fast transfer concepts and hooks that do not exist in the same way in V1.
- There is no V2 equivalent of V1 `replaceDepositForBurn`; auditors should not assume a failed recipient or caller choice can be corrected by a V1-style replacement flow.

```mermaid
flowchart LR
    subgraph V1["CCTP V1"]
        v1b["depositForBurn<br/>(no maxFee, no minFinality)"]
        v1r["replaceDepositForBurn available"]
        v1api["GET /v1/messages"]
    end
    subgraph V2["CCTP V2"]
        v2b["depositForBurn<br/>+ maxFee + minFinalityThreshold<br/>+ destinationCaller"]
        v2r["No replace — finalise or abort"]
        v2api["GET /v2/messages"]
        v2fast["Fast transfer / hooks"]
    end
    V1 -. "NOT compatible" .-> V2
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class v1b,v1r,v1api b;
    class v2b,v2r,v2api,v2fast g;
```
<span class="figcap">V1 and V2 are separate integration targets — reusing V1 assumptions in a V2 integration is a common audit finding.</span>

## Solana program split

CCTP V2 on Solana separates message transmission from token burn/mint accounting:

- `TokenMessengerMinterV2` handles token messenger/minter instructions such as `deposit_for_burn`.
- `MessageTransmitterV2` handles message emission, attestation consumption, nonce tracking, and receive-side message processing.

This split matters in CPI review. Pin the exact program IDs, then validate that every account consumed by each program belongs to the expected half of the protocol. A fake token messenger, fake message transmitter, wrong event authority, or wrong denylist PDA is a bridge account-substitution bug, not just an ordinary bad account list.

```mermaid
flowchart TD
    Int["Integrator program<br/>(CPI caller)"]
    TMM["TokenMessengerMinterV2<br/>deposit_for_burn / receiveMessage token leg"]
    MTX["MessageTransmitterV2<br/>send_message / receive_message / nonce tracking"]
    DL["Denylist PDA<br/>(owned by TMM)"]
    EA["Event authority PDA<br/>(owned by MTX)"]
    MS["MessageSent account<br/>(owned by MTX)"]

    Int -->|"CPI — pin program ID"| TMM
    TMM -->|"CPI — pin program ID"| MTX
    TMM --> DL
    MTX --> EA
    MTX --> MS

    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    fake["Fake TMM / fake MTX passed by attacker ❌"]
    class fake b;
```
<span class="figcap">Each CPI hop must pin the program ID. Swapping any program with a look-alike is the bridge account-substitution attack.</span>

```rust
// ❌ BAD: CPI target program IDs taken from caller-supplied accounts.
pub token_messenger: UncheckedAccount<'info>,
pub message_transmitter: UncheckedAccount<'info>,
// An attacker passes look-alike programs; the CPI succeeds but mints nothing
// or routes funds to the attacker.

// ✅ GOOD: pin both program IDs to the known CCTP V2 addresses. // illustrative
#[account(address = token_messenger_minter_v2::ID)]
pub token_messenger: Program<'info, TokenMessengerMinterV2>,
#[account(address = message_transmitter_v2::ID)]
pub message_transmitter: Program<'info, MessageTransmitterV2>,
```

## Persistent `MessageSent` accounts

CCTP V1 integrations often treated the emitted message as ephemeral event data. On Solana V2, `MessageSent` is represented by a persistent account created for the burn/message flow and owned by `MessageTransmitterV2`. Integrators may need to create this account before the CPI and reclaim it after Circle's processing window.

Audit checks:

- The `MessageSent` account must be owned and written by the expected message transmitter program.
- The account must correspond to the specific burn/message being attested.
- Reclaim logic must not let arbitrary users drain rent from unrelated message accounts.
- The event or message account must not become the sole security check for whether a burn happened; destination settlement still depends on the attested message.

```mermaid
flowchart TD
    Caller["Integrator<br/>creates MessageSent account (pre-CPI)"]
    TMM2["TokenMessengerMinterV2<br/>deposit_for_burn CPI"]
    MTX2["MessageTransmitterV2<br/>writes message body into MessageSent"]
    Iris2["Iris service observes and attests"]
    Recv["receiveMessage (destination)<br/>reads MessageSent + attestation"]
    Reclaim["Integrator reclaims rent<br/>(after Circle processing window)"]

    Caller --> TMM2
    TMM2 --> MTX2
    MTX2 --> Iris2
    Iris2 --> Recv
    MTX2 --> Reclaim

    q{{"MessageSent.owner == MessageTransmitterV2 ?"}}
    MTX2 --> q
    q -->|"not checked ❌"| fake2["Attacker passes spoofed account<br/>with forged message body"]
    q -->|"checked ✅"| ok2["Only genuine transmitter-written messages accepted"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class fake2 b; class ok2 g;
```

```rust
// ❌ BAD: MessageSent account ownership not validated before reading message body.
/// CHECK: not checked — attacker can supply a spoofed account
pub message_sent: UncheckedAccount<'info>,
// Reading message_sent.data to settle a transfer trusts caller-supplied bytes.

// ✅ GOOD: enforce owner == MessageTransmitterV2 before trusting any field. // illustrative
#[account(owner = message_transmitter_v2::ID)]
pub message_sent: Account<'info, MessageSent>,
// Also verify message_sent.nonce matches the specific burn being settled,
// and that the attested message hash covers this account's data.
```

## Domain and address encoding

Circle domains are not EVM chain IDs and not Solana cluster IDs. They are Circle-defined domain identifiers. An auditor should keep a route table that explicitly maps source domain, destination domain, source program, destination program, and token mint for the route under review.

CCTP message address fields are 32 bytes. EVM addresses are 20 bytes and must be embedded consistently in a 32-byte field, typically left-padded with zeros. Solana public keys are already 32 bytes. Reviewers should look for:

- right-padding or raw 20-byte writes into a 32-byte field;
- comparing an EVM chain ID to a Circle domain;
- treating a Solana `Pubkey` as equivalent to an EVM address;
- allowed-domain lists that include the right chain but the wrong Circle domain;
- recipient or caller encoding that differs between local tests and production clients.

```mermaid
flowchart LR
    evm["EVM address<br/>20 bytes: 0xABCD..."]
    pad["Left-pad with 12 zero bytes"]
    field["32-byte CCTP field<br/>0x000...0000ABCD..."]
    sol["Solana Pubkey<br/>already 32 bytes — no padding"]
    field2["32-byte CCTP field<br/>= raw Pubkey bytes"]

    evm -->|"✅ correct"| pad --> field
    evm -->|"❌ right-pad or raw 20-byte write"| wrong["mismatched 32-byte value<br/>recipient mismatch on destination"]
    sol --> field2

    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class wrong b;
    class field,field2 g;
```

```rust
// ❌ BAD: copies only 20 bytes — trailing 12 bytes are zeroed by accident,
//         which is right-padding rather than left-padding.
let mut recipient_field = [0u8; 32];
recipient_field[..20].copy_from_slice(&evm_address); // right-padded ❌

// ✅ GOOD: left-pad so the 20-byte address occupies the LAST 20 bytes.
let mut recipient_field = [0u8; 32];
recipient_field[12..].copy_from_slice(&evm_address); // left-padded ✅

// ❌ BAD: confuses EVM chain ID with Circle domain ID.
let destination_domain: u32 = 1; // "Ethereum mainnet chain ID" — WRONG
// Circle domain for Ethereum mainnet is a different constant entirely.

// ✅ GOOD: use Circle's documented domain constants, not chain IDs. // illustrative
use cctp_domains::ETHEREUM_MAINNET; // Circle-defined domain constant
let destination_domain: u32 = ETHEREUM_MAINNET;
```

## Finality threshold semantics

CCTP V2 uses finality thresholds to distinguish faster and stronger attestation assumptions. The important constants for most integrations are:

- `1000`: fast/confirmed style finality, with faster availability but more reorg/insurance assumptions.
- `2000`: finalized/standard finality, slower but stronger.

Using `minFinalityThreshold = 2000` is a conservative default, but it is still an integration choice. Auditors should verify that the front end, relayer, backend polling, and destination settlement code all expect the same threshold. A relayer polling only for fast messages while the source requested finalized messages can create stuck transfers or misleading UX.

```mermaid
flowchart TD
    src["Source: depositForBurn<br/>minFinalityThreshold = ?"]
    src -->|"= 1000"| fast["Iris: fast/confirmed attestation<br/>available sooner, reorg risk"]
    src -->|"= 2000"| final["Iris: finalized attestation<br/>slower, stronger guarantee"]
    fast --> relayer["Relayer polling /v2/messages"]
    final --> relayer
    relayer --> q{{"relayer filter matches<br/>requested threshold?"}}
    q -->|"mismatch ❌"| stuck["Relayer misses message<br/>→ stuck transfer / silent UX failure"]
    q -->|"aligned ✅"| settle["receiveMessage submitted on destination"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class stuck b; class settle g;
```

```rust
// ❌ BAD: source requests finalized (2000) but relayer polls only fast (1000)
//         messages — the attestation is never picked up; transfer is stuck.
// On-chain (source side):
let min_finality_threshold: u32 = 2000; // finalized requested
// Off-chain relayer (bug):
// GET /v2/messages?minFinalityThreshold=1000  // only picks up fast messages

// ✅ GOOD: relayer filter matches what the source program emits.
// On-chain:
let min_finality_threshold: u32 = 2000;
// Off-chain relayer:
// GET /v2/messages?minFinalityThreshold=2000  // aligned ✅
// Or: poll for both thresholds and let the on-chain program enforce the bound.
```

## Attester trust model

CCTP security includes Circle's attester set and Iris service. The local Solana program can validate message format, nonce reuse, source domain, destination domain, caller, recipient, and signature acceptance by `MessageTransmitterV2`, but it cannot independently prove the source-chain burn without trusting Circle's attestation system.

Practical review points:

- Treat attester keys and message transmitter ownership/admin powers as privileged infrastructure.
- Check upgrade/admin controls for both messenger and transmitter programs.
- Model attestation service downtime and delayed messages as operational failure modes.
- Do not describe CCTP as trustless bridging in audit notes; state the Circle attester assumption explicitly.

```mermaid
flowchart TD
    burn["Source-chain burn (verified on-chain locally)"]
    iris["Circle Iris observes burn event"]
    attest["Attester set signs message hash<br/>(≥ threshold of N keys required)"]
    recv["MessageTransmitterV2.receiveMessage<br/>verifies signature count ≥ threshold"]
    mint["Mint USDC on destination"]

    burn --> iris
    iris --> attest
    attest --> recv
    recv --> mint

    trust["TRUST BOUNDARY<br/>On-chain program cannot verify<br/>this step independently"]
    iris -.->|"assumed honest"| trust
    attest -.->|"key compromise = bridge drain"| trust

    classDef b fill:#fff7f5,stroke:#c2410c;
    class trust b;
```
<span class="figcap">The on-chain program validates signatures and nonces, but the root trust is in Circle's attester key set. Any audit note describing CCTP as trustless bridging is incorrect.</span>

```rust
// ✅ Signature threshold check — illustrative of what MessageTransmitterV2 enforces.
// Auditors should verify the on-chain program reads attester_manager config
// and requires signatures >= threshold, NOT a hardcoded 1-of-N.
//
// ❌ BAD pattern to watch for in integrator wrappers:
pub fn relay_message(ctx: Context<RelayMessage>, message: Vec<u8>, attestation: Vec<u8>) -> Result<()> {
    // Skips the CPI to MessageTransmitterV2 entirely and just mints directly
    // based on a decoded message body — NO signature verification!
    let body = MessageBody::decode(&message)?;
    mint_usdc(ctx.accounts.mint_recipient, body.amount)?; // ❌ no attestation check
    Ok(())
}

// ✅ GOOD: always go through MessageTransmitterV2.receiveMessage via CPI;
//          never short-circuit attestation verification in integrator code.
pub fn relay_message(ctx: Context<RelayMessage>, message: Vec<u8>, attestation: Vec<u8>) -> Result<()> {
    let cpi_ctx = CpiContext::new(
        ctx.accounts.message_transmitter.to_account_info(),
        ReceiveMessage {
            // ... all required accounts including used_nonces, attester_manager ...
        },
    );
    message_transmitter_v2::cpi::receive_message(cpi_ctx, message, attestation)?; // ✅
    Ok(())
}
```

## Audit-relevant invariants

For a router or integrator that hardcodes `min_finality_threshold = 2000` and `max_fee = 0`, the intended invariant is:

> The route only emits finalized/standard messages and only when Circle charges no fee for that route.

The failure mode if Circle later enables fees on that route is not silent value loss. The burn should fail or remain unprocessable because the requested maximum fee is lower than the required fee. That can strand the user at the source-side UX layer as a failed transfer path, break automated routing, or make a previously healthy instruction permanently unusable until the integrator updates `maxFee`. Auditors should flag this as an availability and configuration-risk invariant:

- If the integrator wants no-fee-only transfers, assert and document that policy.
- If fees may be enabled, expose `maxFee` as a bounded parameter and test fee-enabled routes.
- Ensure off-chain estimators and relayers surface "fee exceeds maxFee" distinctly from generic CCTP failure.

Other CCTP V2 invariants worth writing tests for:

- source and destination domains are Circle domains, not chain IDs;
- every CPI target program ID is pinned;
- the denylist PDA and event authority are derived from the expected CCTP programs;
- EVM recipients and destination callers use correct 20-to-32-byte padding;
- duplicate nonces and replayed messages are rejected by the destination transmitter;
- zero `destinationCaller` is only used when any destination submitter is acceptable.

```mermaid
flowchart TD
    burn2["deposit_for_burn CPI<br/>max_fee = 0, min_finality = 2000"]
    burn2 --> q1{{"Circle route<br/>has fee > 0 ?"}}
    q1 -->|"yes ❌"| stuck2["Burn reverts or transfer stuck<br/>route unavailable until maxFee updated"]
    q1 -->|"no ✅"| q2{{"destinationCaller == 0 ?"}}
    q2 -->|"yes"| open["Any relayer can call receiveMessage<br/>— check this is intentional"]
    q2 -->|"no"| restrict["Only the named caller can complete<br/>— verify encoding is correct"]
    q3{{"nonce already used?"}}
    restrict --> q3
    open --> q3
    q3 -->|"yes ❌"| replay["receiveMessage rejects — replay blocked"]
    q3 -->|"no ✅"| settle2["Message processed, USDC minted"]
    classDef b fill:#fff7f5,stroke:#c2410c;
    classDef g fill:#f1fff9,stroke:#0fa76e;
    class stuck2,replay b;
    class settle2,restrict g;
```

```rust
// ❌ BAD: hardcoded zero destinationCaller when the protocol requires a
//         specific relayer — any actor can front-run and complete the message.
let destination_caller = [0u8; 32]; // any caller ❌ — unintentional open relay

// ✅ GOOD: encode the expected destination caller explicitly; use zero only
//          when open relay is deliberate and documented.
let mut destination_caller = [0u8; 32];
destination_caller[12..].copy_from_slice(expected_evm_relayer.as_bytes()); // left-padded ✅
// For a Solana destination caller:
let destination_caller: [u8; 32] = expected_solana_relayer.to_bytes();

// ❌ BAD: maxFee hardcoded as a magic number with no config path.
const MAX_FEE: u64 = 0; // silently breaks if Circle enables fees on this route

// ✅ GOOD: expose maxFee as a bounded config parameter; document the invariant.
#[account(mut, has_one = admin)]
pub config: Account<'info, RouterConfig>,
// config.max_fee is set by admin; default 0 is documented + monitored.
```

## References

- Circle CCTP technical guide: https://developers.circle.com/cctp/references/technical-guide
- Circle CCTP Solana programs: https://developers.circle.com/cctp/references/solana-programs
- Circle V1 to V2 migration guide: https://developers.circle.com/cctp/migration-from-v1-to-v2
- ChainSecurity CCTP V2 audit: https://reports.chainsecurity.com/Circle/ChainSecurity_Circle_CCTPV2_Audit.pdf
- OtterSec EVM CCTP V2 audit: https://6778953.fs1.hubspotusercontent-na1.net/hubfs/6778953/PDFs/public_evm_cctp_audit_final%20%282%29.pdf
- OpenZeppelin Sponsored CCTP Deposits from Solana audit: https://www.openzeppelin.com/news/sponsored-cctp-deposits-from-solana-audit

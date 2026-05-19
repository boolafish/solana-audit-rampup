# Raw-byte PDA decoding

Manual byte slicing such as `data[8..40]` or `data[73]` is a parser. Audit it with the same rigor as custom ABI decoding. It bypasses Anchor account typing, Borsh field names, and version checks, so small layout drift can turn into authority, market, reserve, or bump confusion.

## Discriminator first

Anchor accounts start with an 8-byte discriminator. Check it before reading fields.

Bad:
```rust
let data = reserve.try_borrow_data()?;
let market = Pubkey::new_from_array(data[8..40].try_into()?);
let is_stale = data[73] != 0;
```

Good:
```rust
let data = reserve.try_borrow_data()?;
require!(data.len() >= Reserve::LEN, ErrorCode::BadLength);
require!(&data[..8] == Reserve::DISCRIMINATOR, ErrorCode::BadDiscriminator);

let reserve = Reserve::try_deserialize(&mut &data[..])?;
require_keys_eq!(reserve.market, expected_market);
```

If full deserialization is too expensive or unavailable, isolate the parser and still check owner, discriminator, length, version, and each offset against pinned fixtures.

## Layout drift

Hard-coded offsets assume all of these stay unchanged:

- Borsh field order.
- Field widths and alignment assumptions.
- `Option<T>` tags and payload presence.
- Enum tag order.
- Added version bytes or reserved fields.
- Anchor discriminator size.

Adding a `version: u8` near the top of a Borsh struct shifts every later field. A raw parser may keep compiling while reading the wrong pubkey or flag.

## Version-pin discipline

Manual parsers should be reviewed with the exact dependency and callee-program versions:

- Check `Cargo.lock` for the crate that defines the parsed account.
- Check deployed program IDs and IDL versions.
- Keep fixtures for real account bytes from the pinned version.
- Add a failing test when a field reorder or version bump changes offsets.

If the account is owned by another program, the parser is coupled to that external program's layout. Treat upgrades of the external program as parser-breaking until proven otherwise.

## `UncheckedAccount` type confusion

Raw slicing is especially dangerous through `UncheckedAccount`:

```rust
pub reserve: UncheckedAccount<'info>,
```

Before reading bytes, validate:

- Account key, if it should be a known reserve/PDA.
- Owner program.
- Executable bit for program accounts.
- Data length.
- Discriminator or explicit type tag.
- Version byte, if present.
- Relationship fields after decode.

Without these checks, an attacker can supply any account with matching byte prefixes, including another account type with a compatible first field.

## Good parser shape

```rust
fn parse_reserve_market(reserve: &AccountInfo, expected_owner: &Pubkey) -> Result<Pubkey> {
    require_keys_eq!(*reserve.owner, *expected_owner, ErrorCode::BadOwner);

    let data = reserve.try_borrow_data()?;
    require!(data.len() >= RESERVE_MARKET_END, ErrorCode::BadLength);
    require!(&data[..8] == RESERVE_DISCRIMINATOR, ErrorCode::BadDiscriminator);
    require_eq!(data[RESERVE_VERSION_OFFSET], SUPPORTED_RESERVE_VERSION, ErrorCode::BadVersion);

    Pubkey::try_from(&data[RESERVE_MARKET_START..RESERVE_MARKET_END])
        .map_err(|_| ErrorCode::BadLayout.into())
}
```

Put offsets in named constants and test them against known-good serialized fixtures. Anonymous numbers in handlers should be treated as audit findings.

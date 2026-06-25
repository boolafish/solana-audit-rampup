#!/usr/bin/env python3
"""Build the `solana-audit-primer` Claude Code skill from the JSON knowledge base.

Source of truth:
  - data/patterns.json       (37 vulnerability patterns; this script also injects
                              a `triggers` block into each pattern in place)
  - data/incidents.json      (real incidents mapped to pattern ids)
  - data/audit-findings.json (public audit findings mapped to pattern ids)

Outputs (regenerable, do not hand-edit):
  - .claude/skills/solana-audit-primer/SKILL.md          (layer 1: routing index)
  - .claude/skills/solana-audit-primer/threat-model.md   (entry scaffold)
  - .claude/skills/solana-audit-primer/references/<id>.md (layer 2: detail pages)

Run:  python3 scripts/build_primer_skill.py
"""

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SKILL = ROOT / ".claude" / "skills" / "solana-audit-primer"
REFS = SKILL / "references"
AGENTS = SKILL / "agents"
REPO_BLOB = "https://github.com/boolafish/solana-audit-rampup/blob/main/"

# These tokens are still useful inside individual pattern pages, but they are
# too broad for the primary routing table.
BROAD_INDEX_SIGNALS = {" % ", " * ", " / ", "for "}

# ---------------------------------------------------------------------------
# Triggers: the routing layer. For each pattern id:
#   code_signals -> grep-able tokens that appear in source
#   protocols    -> kinds of programs where the pattern is likely
#   concepts     -> structural / behavioural cues an agent can reason about
# ---------------------------------------------------------------------------
TRIGGERS = {
    "missing-signer": {
        "code_signals": ["AccountInfo", "UncheckedAccount", "is_signer", "Signer<", "has_one", "#[account(signer"],
        "protocols": ["any privileged/admin instruction", "vaults", "lending", "governance"],
        "concepts": ["authority compared by key but never required to sign", "admin/config-mutating instruction", "PDA authority used without invoke_signed"],
    },
    "missing-owner": {
        "code_signals": ["try_from_slice", "try_from_slice_unchecked", ".data.borrow()", "AccountInfo", "UncheckedAccount", "#[account(owner", "owner =="],
        "protocols": ["any program reading another account's data", "token vaults", "oracles"],
        "concepts": ["deserializing program state from a raw account", "trusting fields in a caller-supplied account", "SPL token authority vs solana account owner confusion"],
    },
    "relationship-checks": {
        "code_signals": ["has_one", "Account<", "TokenAccount", "token::mint", "token::authority", "require_keys_eq", ".key()"],
        "protocols": ["lending", "amm/dex", "vaults", "any multi-account flow"],
        "concepts": ["correct-type account belonging to wrong user/pool/mint", "vault/position/market cross-links", "ATA derivation not enforced"],
    },
    "type-cosplay": {
        "code_signals": ["try_from_slice", "AccountDeserialize", "discriminator", "AccountInfo", "Borsh"],
        "protocols": ["native programs", "programs with multiple similar account structs"],
        "concepts": ["two structs sharing a prefix layout", "missing discriminator/type tag", "Anchor discriminator bypassed via unchecked deserialize"],
    },
    "reinit": {
        "code_signals": ["init_if_needed", "#[account(init", "initialize", "is_initialized"],
        "protocols": ["any stateful program", "proxy-like config"],
        "concepts": ["initialize callable twice", "close then recreate to reset authority", "init_if_needed resetting critical fields"],
    },
    "pda-bump": {
        "code_signals": ["find_program_address", "create_program_address", "seeds =", "bump", "Pubkey::find_program_address"],
        "protocols": ["any PDA-using program", "vaults", "PDA authorities"],
        "concepts": ["user-supplied bump", "non-canonical bump accepted", "under-scoped seeds", "one PDA authority spanning unrelated resources", "singleton root PDA namespace confused with mutable admin authority"],
    },
    "arbitrary-cpi": {
        "code_signals": ["invoke(", "invoke_signed(", "Instruction {", "program_id:", "Program<", "Interface<", "AccountInfo"],
        "protocols": ["any CPI", "token transfers", "router/aggregator"],
        "concepts": ["CPI target program passed by caller", "missing program id pin", "wrong token program accepted"],
    },
    "cpi-substitution": {
        "code_signals": ["invoke_signed", "CpiContext", "with_signer", "token::transfer", "AccountMeta", "delegated_amount", "approve_checked"],
        "protocols": ["vaults", "lending", "router", "any PDA-signed CPI", "PDA token delegates"],
        "concepts": ["program signs over attacker-chosen accounts", "confused deputy", "callee accounts not validated before CPI", "PDA delegate approval/allowance is an off-chain setup dependency"],
    },
    "duplicate-mut": {
        "code_signals": ["#[account(mut", "AccountInfo", "constraint =", "key() !="],
        "protocols": ["transfers", "games", "two-account swap flows"],
        "concepts": ["same account passed for two roles", "payer == recipient", "user_a == user_b aliasing", "SPL self-transfer succeeds without moving value"],
    },
    "sysvar-spoof": {
        "code_signals": ["Sysvar<", "Clock::get", "Rent::get", "sysvar", "Instructions", "AccountInfo"],
        "protocols": ["any time/rent-dependent logic", "signature introspection"],
        "concepts": ["sysvar passed as account without address check", "fake clock/rent/instructions account"],
    },
    "close-revival": {
        "code_signals": ["close =", "lamports", "try_borrow_mut_lamports", "**", "AccountInfo", "CloseAccount", "close_account"],
        "protocols": ["any account-closing flow", "claims", "escrow", "queued settlement"],
        "concepts": ["manual close leaves data/discriminator valid", "same-transaction revival", "refund sent to wrong recipient", "token account rent stranded after authority PDA closes"],
    },
    "realloc-rent": {
        "code_signals": ["realloc", "realloc::payer", "realloc::zero", "Rent", "AccountInfo::realloc", "#[max_len"],
        "protocols": ["growable accounts", "dynamic lists/queues"],
        "concepts": ["resize without funding rent", "stale bytes after grow", "unbounded size growth", "Anchor max_len mistaken for runtime cap"],
    },
    "math": {
        "code_signals": ["checked_", "saturating_", "as u64", "as u128", "overflow-checks", "u128", " * ", " / "],
        "protocols": ["lending", "amm", "rewards", "any accounting"],
        "concepts": ["unchecked arithmetic in optimized build", "multiply-before-divide overflow", "decimal/exponent mismatch", "rounding exploited by repeated small actions"],
    },
    "compute-dos": {
        "code_signals": ["remaining_accounts", "for ", ".iter()", "#[account(mut", "Vec<"],
        "protocols": ["batch operations", "any global counter/config"],
        "concepts": ["unbounded loops", "global writable hot account serializes usage", "compute-budget exhaustion", "writable-account lock contention"],
    },
    "token2022": {
        "code_signals": ["InterfaceAccount", "TokenInterface", "spl_token_2022", "transfer_fee", "TransferFeeConfig", "transfer_hook", "get_account_data_size", "token::mint", "MintCloseAuthority", "DefaultAccountState", "PermanentDelegate"],
        "protocols": ["any token-handling program", "vaults", "amm", "lending"],
        "concepts": ["transfer fee breaks balance accounting", "transfer hook reentrancy", "default-frozen accounts", "permanent delegate", "confidential transfer", "mint close/recreate changes extension assumptions", "freeze authority creates liveness risk"],
    },
    "oracle-mev": {
        "code_signals": ["price", "slippage", "min_out", "deadline", "Clock", "slot", "quote_id"],
        "protocols": ["amm", "lending", "perps", "auctions", "liquidations", "signed quotes"],
        "concepts": ["no slippage / stale-quote protection", "ordering-sensitive flow", "private orderflow / Jito bundle assumptions", "liquidation ordering assumed deterministic", "independent fresh quotes can be mixed"],
    },
    "upgrade-admin": {
        "code_signals": ["upgrade_authority", "set_authority", "BpfLoaderUpgradeable", "admin", "authority"],
        "protocols": ["any upgradeable program", "admin-controlled config"],
        "concepts": ["single hot-key upgrade authority", "admin can drain or alter oracle", "no timelock/multisig on dangerous params"],
    },
    "anchor-unchecked": {
        "code_signals": ["UncheckedAccount", "AccountInfo", "/// CHECK", "Account<", "#[account("],
        "protocols": ["any Anchor program"],
        "concepts": ["unchecked account treated as trusted state", "manual checks do not recreate constraints", "CHECK comment without real validation"],
    },
    "anchor-init-if-needed": {
        "code_signals": ["init_if_needed", "#[account(init_if_needed"],
        "protocols": ["any Anchor stateful program"],
        "concepts": ["handler writes authority on every call", "reinit via init_if_needed", "init-if-needed feature enabled"],
    },
    "anchor-token-interface": {
        "code_signals": ["InterfaceAccount", "Interface<", "TokenInterface", "mint::token_program", "token::token_program"],
        "protocols": ["token programs supporting both classic Token and Token-2022"],
        "concepts": ["token_program constraint not bound to a specific program", "Token-2022 support unintentional", "extensions not allowlisted/rejected"],
    },
    "stale-cpi-reload": {
        "code_signals": ["reload()", "invoke", "CpiContext", "token::transfer", ".amount"],
        "protocols": ["any CPI followed by a post-condition check", "balance-delta checks"],
        "concepts": ["post-CPI invariant checked against pre-CPI cached field", "missing reload() after CPI"],
    },
    "signature-introspection": {
        "code_signals": ["load_instruction_at_checked", "ed25519", "secp256k1", "sysvar::instructions", "instructions_sysvar", "load_current_index", "relative_offset", "verify_ed25519_ix_at_relative_offset", "Ed25519SignatureOffsets", "trusted_signers", "quote_id"],
        "protocols": ["bridges", "meta-transactions", "permit-style flows", "off-chain signed orders", "oracle attestations"],
        "concepts": ["checks a signature instruction exists but not payload/signer/index", "missing domain/nonce/expiry binding", "transaction signer confused with trusted off-chain signer", "attestation freshness vs permit nonce asymmetry", "signed quote mistaken for spend authorization"],
    },
    "insecure-randomness": {
        "code_signals": ["Clock::get", "slot", "unix_timestamp", "recent_blockhashes", " % "],
        "protocols": ["lottery", "raffle", "games", "NFT mint ordering"],
        "concepts": ["modulo of slot/timestamp used as randomness", "predictable or biasable entropy", "participant aborts after unfavorable reveal"],
    },
    "oracle-validation": {
        "code_signals": ["price_feed", "Pyth", "Switchboard", "get_price", "publish_time", "confidence", "AccountInfo"],
        "protocols": ["lending", "perps", "stablecoins", "collateral valuation"],
        "concepts": ["feed account not pinned to config", "freshness/confidence/status not checked", "exponent/decimals not normalized", "low-liquidity spot price inflates collateral"],
    },
    "remaining-accounts": {
        "code_signals": ["remaining_accounts", "ctx.remaining_accounts", "next_account_info"],
        "protocols": ["batch/variable-account flows", "router", "multi-market"],
        "concepts": ["index position trusted as a role", "no length/order check", "per-account owner/type/relationship validation missing"],
    },
    "native-sol-lamports": {
        "code_signals": ["lamports", "try_borrow_mut_lamports", "add_lamports", "sub_lamports", "system_program::transfer", "WSOL"],
        "protocols": ["native SOL vaults", "staking", "escrow"],
        "concepts": ["manual lamport mutation before checks", "rent-exempt floor ignored", "native SOL vs wrapped SOL confusion"],
    },
    "zero-copy-layout": {
        "code_signals": ["zero_copy", "bytemuck", "AccountLoader", "from_bytes", "repr(C)", "Pod", "Zeroable"],
        "protocols": ["high-performance programs", "orderbooks", "large state accounts"],
        "concepts": ["bytemuck cast without owner/len/discriminator", "padding/alignment hazards", "layout/version drift on upgrade"],
    },
    "event-log-reliance": {
        "code_signals": ["msg!", "emit!", "emit_cpi", "sol_log"],
        "protocols": ["claims", "airdrops", "anything indexer-driven"],
        "concepts": ["correctness depends on an indexer observing logs", "no on-chain replay/double-claim guard", "logs mimicable by other programs"],
    },
    "governance-timelock": {
        "code_signals": ["governance", "Realms", "Squads", "multisig", "proposal", "threshold", "timelock"],
        "protocols": ["DAO-controlled programs", "multisig-controlled programs"],
        "concepts": ["governance account owner/program unchecked", "proposal/instruction hash not bound to approval", "emergency path bypasses timelock/threshold"],
    },
    "native-parser-hazards": {
        "code_signals": ["next_account_info", "try_from_slice_unchecked", "data[", "Pubkey::new_from_array", "unpack", "offset"],
        "protocols": ["native (non-Anchor) programs", "vote/stake account parsing"],
        "concepts": ["hard-coded offsets", "no owner/version/length check before reading", "wrong account-order assumptions"],
    },
    "anchor-0.28-deltas": {
        "code_signals": ["anchor-lang = \"0.28", "Cargo.lock", "init_if_needed", "payer =", "Signer<"],
        "protocols": ["programs pinned to Anchor 0.28"],
        "concepts": ["payer mut requirement differs", "version-sensitive codegen", "lamport-helper behavior differs from latest tutorials"],
    },
    "manual-try-accounts": {
        "code_signals": ["impl<'info> Accounts", "fn try_accounts", "next_account_info"],
        "protocols": ["programs with hand-rolled Accounts implementations"],
        "concepts": ["manual parser skips signer/owner/discriminator checks", "boundary silently shifts into remaining_accounts", "aliasing not rejected"],
    },
    "remaining-accounts-trust": {
        "code_signals": ["remaining_accounts", "AccountMeta::new", "invoke(&ix", "is_writable", "Kamino", "KLend"],
        "protocols": ["routers", "aggregators", "lending-CPI integrations"],
        "concepts": ["caller account order forwarded straight into a CPI", "writable flags passed through unvalidated", "callee IDL ordering / special accounts not validated"],
    },
    "raw-byte-pda-decoding": {
        "code_signals": ["data[", "Pubkey::new_from_array", "try_into()", "UncheckedAccount", "[8..40]"],
        "protocols": ["cross-program integrations reading callee state"],
        "concepts": ["hard-coded byte offsets", "no discriminator/version check before slicing", "Option/enum/field-order shift moves the target field"],
    },
    "find-program-address-cu-cost": {
        "code_signals": ["find_program_address", "create_program_address", "bump", "for ", "loop"],
        "protocols": ["CPI-heavy programs", "hot loops"],
        "concepts": ["repeated find_program_address inside a loop", "switching to a client-supplied bump to save compute", "stored bump not re-verified against the PDA address"],
    },
    "seed-prefix-collision": {
        "code_signals": ["seeds =", "find_program_address", "b\"vault\"", "UncheckedAccount", "sha256", "format!"],
        "protocols": ["programs with multiple PDA account types", "cross-chain registries", "admin registries"],
        "concepts": ["shared seed shape across account types", "weak or duplicated static prefix", "type/discriminator not verified after derivation", "variable-length fields concatenated without length prefix or delimiter"],
    },
    "instructions-sysvar-introspection": {
        "code_signals": ["sysvar::instructions", "load_current_index_checked", "load_instruction_at_checked", "Sysvar1nstructions"],
        "protocols": ["anti-CPI / direct-call enforcement", "signature-verifier placement", "bridges"],
        "concepts": ["sysvar address not exact-checked", "inspected instruction position not relative to current index", "program id / accounts / data not bound"],
    },
}

# Protocol playbook buckets: keyword -> human label. A pattern joins a bucket if
# any keyword appears in its triggers.protocols or triggers.concepts text.
PLAYBOOKS = [
    ("Lending / perps / collateral", ["lending", "perps", "collateral", "stablecoin"]),
    ("AMM / DEX / swaps", ["amm", "dex", "swap"]),
    ("Vaults / escrow / staking", ["vault", "escrow", "staking", "stake"]),
    ("Bridges / cross-chain / messaging", ["bridge", "bridges", "cross-chain", "messaging", "meta-transaction", "meta-transactions", "signed order", "signed orders", "off-chain signed order", "off-chain signed orders", "oracle attestations"]),
    ("Governance / multisig / admin", ["governance", "multisig", "dao", "admin", "upgrade"]),
    ("Routers / aggregators", ["router", "aggregator"]),
    ("Games / lottery / NFT", ["lottery", "raffle", "game", "nft"]),
    ("Native (non-Anchor) programs", ["native"]),
]

# Patterns to check on every Solana/Anchor program regardless of protocol type.
CORE_ALWAYS = [
    "missing-signer", "missing-owner", "relationship-checks", "type-cosplay",
    "pda-bump", "arbitrary-cpi", "cpi-substitution", "anchor-unchecked", "math",
]


def load(name):
    return json.loads((DATA / name).read_text())


def first_sentence(text):
    text = text.strip()
    for sep in (". ", "; "):
        if sep in text:
            return text.split(sep)[0].strip().rstrip(".") + "."
    return text if text.endswith(".") else text + "."


def code_fence(s):
    # The JSON examples are inline `code`-wrapped prose; render verbatim in a fence.
    return s


def main():
    patterns = load("patterns.json")
    incidents = load("incidents.json")
    findings = load("audit-findings.json")

    # 1) inject triggers into patterns.json (source of truth) ----------------
    for p in patterns:
        if p["id"] in TRIGGERS:
            p["triggers"] = TRIGGERS[p["id"]]
        else:
            raise SystemExit(f"No triggers defined for pattern id: {p['id']}")
    (DATA / "patterns.json").write_text(
        json.dumps(patterns, indent=2, ensure_ascii=False) + "\n"
    )

    by_id = {p["id"]: p for p in patterns}

    # reverse indexes: incidents / findings / co-occurrence ------------------
    inc_by_pat, find_by_pat, cooc = {}, {}, {}
    for inc in incidents:
        for pid in inc.get("patterns", []):
            inc_by_pat.setdefault(pid, []).append(inc)
    for f in findings:
        for pid in f.get("patterns", []):
            find_by_pat.setdefault(pid, []).append(f)
    for group in [i.get("patterns", []) for i in incidents] + [f.get("patterns", []) for f in findings]:
        for a in group:
            for b in group:
                if a != b:
                    cooc.setdefault(a, {}).setdefault(b, 0)
                    cooc[a][b] += 1

    # group patterns by category, preserving first-seen category order -------
    categories, cat_order = {}, []
    for p in patterns:
        c = p["category"]
        if c not in categories:
            categories[c] = []
            cat_order.append(c)
        categories[c].append(p)

    REFS.mkdir(parents=True, exist_ok=True)
    AGENTS.mkdir(parents=True, exist_ok=True)

    # Keep generated output deterministic if patterns are renamed or removed.
    for old_ref in REFS.glob("*.md"):
        old_ref.unlink()

    # 2) detail pages --------------------------------------------------------
    for p in patterns:
        write_detail_page(p, by_id, inc_by_pat, find_by_pat, cooc)

    # 3) SKILL.md ------------------------------------------------------------
    write_skill_index(patterns, by_id, cat_order, categories)

    # 4) threat-model.md -----------------------------------------------------
    write_threat_model()

    # 5) agents/openai.yaml --------------------------------------------------
    write_agents_metadata()

    print(f"Wrote SKILL.md, agents/openai.yaml, threat-model.md and {len(patterns)} reference pages to {SKILL}")


def related_ids(pid, by_id, cooc):
    # co-occurring patterns first (by frequency), then same-category fillers.
    out = sorted(cooc.get(pid, {}).items(), key=lambda kv: -kv[1])
    ids = [k for k, _ in out]
    cat = by_id[pid]["category"]
    for other in by_id.values():
        if other["category"] == cat and other["id"] != pid and other["id"] not in ids:
            ids.append(other["id"])
    return ids[:6]


def write_detail_page(p, by_id, inc_by_pat, find_by_pat, cooc):
    t = p["triggers"]
    L = []
    L.append(f"# {p['title']}\n")
    L.append(f"- **Pattern ID:** `{p['id']}`")
    L.append(f"- **Category:** {p['category']}  |  **Severity:** {p['severity']}\n")

    L.append("## Triggers — load this page when you see these\n")
    L.append("**Code signals (grep the target):** " + ", ".join(f"`{s}`" for s in t["code_signals"]) + "\n")
    L.append("**Protocol types:** " + ", ".join(t["protocols"]) + "\n")
    L.append("**Concepts:** " + "; ".join(t["concepts"]) + "\n")

    L.append("## Why this differs from Solidity/EVM\n")
    L.append(p["solidity"] + "\n")
    L.append(p["difference"] + "\n")

    L.append("## Bad pattern\n")
    L.append(p["bad"] + "\n")
    ex = p.get("examples", {})
    if ex.get("native_bad") or ex.get("anchor_bad"):
        if ex.get("native_bad"):
            L.append(f"- *Native:* {ex['native_bad']}")
        if ex.get("anchor_bad"):
            L.append(f"- *Anchor:* {ex['anchor_bad']}")
        L.append("")

    L.append("## Good pattern\n")
    L.append(p["good"] + "\n")
    if ex.get("native_good") or ex.get("anchor_good"):
        if ex.get("native_good"):
            L.append(f"- *Native:* {ex['native_good']}")
        if ex.get("anchor_good"):
            L.append(f"- *Anchor:* {ex['anchor_good']}")
        L.append("")

    L.append("## Audit checks\n")
    for c in p["checks"]:
        L.append(f"- [ ] {c}")
    L.append("")

    incs = inc_by_pat.get(p["id"], [])
    if incs:
        L.append("## Real incidents mapped to this pattern\n")
        for i in incs:
            L.append(f"- **{i['name']} ({i.get('year','')})** — {i.get('impact','')}. {i.get('root','')}")
        L.append("")

    fnds = find_by_pat.get(p["id"], [])
    if fnds:
        L.append("## Public audit findings mapped to this pattern\n")
        for f in fnds:
            L.append(f"- **{f['source']}** ({f['area']}): " + "; ".join(f["findings"]))
        L.append("")

    rel = related_ids(p["id"], by_id, cooc)
    if rel:
        L.append("## Related patterns\n")
        for rid in rel:
            L.append(f"- [{by_id[rid]['title']}]({rid}.md) — `{rid}`")
        L.append("")

    L.append("## References\n")
    for r in p["refs"]:
        # Rewrite repo-relative docs/ pointers to absolute URLs so reference
        # pages resolve even when the skill folder is copied out of this repo.
        if r.startswith("docs/"):
            r = REPO_BLOB + r
        L.append(f"- {r}")
    L.append("")

    (REFS / f"{p['id']}.md").write_text("\n".join(L))


def write_skill_index(patterns, by_id, cat_order, categories):
    L = []
    L.append("---")
    L.append("name: solana-audit-primer")
    L.append(
        "description: Catalog of Solana/Anchor security patterns (good vs bad) for "
        "auditing and threat-modeling on-chain Rust programs. Use when reviewing, "
        "auditing, or threat-modeling Solana, Anchor, or native SBF programs, or when "
        "the user mentions Solana vulnerability patterns, account validation, PDAs, "
        "CPIs, SPL Token / Token-2022, oracles, or Anchor constraints."
    )
    L.append("---\n")
    L.append("# Solana Audit Primer\n")
    L.append(
        "A two-layer catalog of Solana/Anchor security patterns. This file is the "
        "**routing layer**: scan it, match triggers against the target program, then "
        "load only the `references/<id>.md` pages you need. Do not paste every "
        "reference page into context up front.\n"
    )

    L.append("## Workflow\n")
    L.append("1. **Frame the system.** Read [threat-model.md](threat-model.md) and fill in the scaffold: assets, actors, trust boundaries, instructions, external programs.")
    L.append("2. **Grep for code signals.** Use the *Code-signal index* below: each grep token points at the patterns to load.")
    L.append("3. **Apply protocol playbooks.** Identify the protocol type(s) and pull the prioritized pattern list for each.")
    L.append("4. **Always-check core.** Run the core patterns on every program regardless of type.")
    L.append("5. **Load detail pages.** For each matched pattern, open `references/<id>.md` for bad/good code, audit checks, and mapped incidents.\n")

    L.append("## Always-check core patterns\n")
    L.append("Every Solana/Anchor program, regardless of protocol type:\n")
    for pid in CORE_ALWAYS:
        p = by_id[pid]
        L.append(f"- [{p['title']}](references/{pid}.md) (`{pid}`, {p['severity']})")
    L.append("")

    # Code-signal reverse index ---------------------------------------------
    sig_index = {}
    for p in patterns:
        for sig in p["triggers"]["code_signals"]:
            sig_index.setdefault(sig, []).append(p["id"])
    L.append("## Code-signal index\n")
    L.append(
        "Grep the target program. If a token appears, consider the listed patterns. "
        "Very broad operator/control-flow tokens are kept in detail pages but omitted "
        "from this routing table to reduce noise.\n"
    )
    L.append("| Grep token | Consider patterns |")
    L.append("| --- | --- |")
    for sig in sorted(sig_index, key=lambda s: s.lower()):
        if sig in BROAD_INDEX_SIGNALS:
            continue
        ids = sig_index[sig]
        cell = ", ".join(f"[`{i}`](references/{i}.md)" for i in ids)
        L.append(f"| `{sig}` | {cell} |")
    L.append("")

    # Protocol playbooks -----------------------------------------------------
    L.append("## Protocol playbooks\n")
    L.append("Match the target to one or more protocol types, then prioritize these patterns (in addition to the core set above).\n")
    for label, keywords in PLAYBOOKS:
        matched = []
        for p in patterns:
            hay = " ".join(p["triggers"]["protocols"] + p["triggers"]["concepts"]).lower()
            if any(re.search(r"\b" + re.escape(k) + r"\b", hay) for k in keywords):
                matched.append(p["id"])
        if not matched:
            continue
        L.append(f"### {label}\n")
        for pid in matched:
            p = by_id[pid]
            L.append(f"- [{p['title']}](references/{pid}.md) (`{pid}`, {p['severity']})")
        L.append("")

    # Full catalog by category ----------------------------------------------
    L.append("## Full pattern catalog\n")
    for cat in cat_order:
        L.append(f"### {cat}\n")
        L.append("| Pattern | Severity | What it is | Top code signals |")
        L.append("| --- | --- | --- | --- |")
        for p in categories[cat]:
            one = first_sentence(p["difference"]).replace("|", "\\|")
            sigs = ", ".join(f"`{s}`" for s in p["triggers"]["code_signals"][:4])
            L.append(f"| [{p['title']}](references/{p['id']}.md) | {p['severity']} | {one} | {sigs} |")
        L.append("")

    L.append("---\n")
    L.append("_Generated from `data/patterns.json`, `data/incidents.json`, and "
             "`data/audit-findings.json` by `scripts/build_primer_skill.py`. "
             "Edit the JSON (or the script's `TRIGGERS` map) and re-run; do not hand-edit this file._")

    (SKILL / "SKILL.md").write_text("\n".join(L) + "\n")


def write_threat_model():
    content = """# Threat-model scaffold for a Solana/Anchor program

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
"""
    (SKILL / "threat-model.md").write_text(content)


def write_agents_metadata():
    content = """interface:
  display_name: "Solana Audit Primer"
  short_description: "Route Solana audit checks by code signal"
  default_prompt: "Use $solana-audit-primer to threat-model this Solana program and prioritize vulnerability patterns."

policy:
  allow_implicit_invocation: true
"""
    (AGENTS / "openai.yaml").write_text(content)


if __name__ == "__main__":
    main()

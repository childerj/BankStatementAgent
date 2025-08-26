#!/usr/bin/env python3
import sys
import os
import re
from datetime import datetime
from collections import Counter

# ==============================
# Helpers
# ==============================

def today_yymmdd():
    return datetime.now().strftime("%y%m%d")

def yymmdd_valid(s: str) -> bool:
    if not (isinstance(s, str) and len(s) == 6 and s.isdigit()):
        return False
    try:
        datetime.strptime(s, "%y%m%d")
        return True
    except ValueError:
        return False

def sanitize_description(desc: str) -> (str, bool, list):
    changes = []
    original = desc
    # Replace "/" with "-"
    if "/" in desc:
        changes.append("replace slash with dash")
    desc = desc.replace("/", "-")
    # Remove control chars
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in desc):
        changes.append("remove control chars")
    desc = re.sub(r"[\x00-\x1F\x7F]", " ", desc)
    # Convert to ASCII (replace non-ASCII with space)
    if any(ord(ch) > 126 for ch in desc):
        changes.append("non-ascii -> space")
    desc = re.sub(r"[^\x20-\x7E]", " ", desc)
    # Collapse whitespace
    desc = re.sub(r"\s+", " ", desc).strip()
    changed = (desc != original)

    return desc, changed, changes

def ensure_int_cents(amount_str: str) -> (str, bool):
    # Keep digits only (BAI2 amounts here should be integer cents)
    new = re.sub(r"\D", "", amount_str or "")
    return new, (new != (amount_str or ""))

# ==============================
# Core structures
# ==============================

class Entry16:
    def __init__(self, line_no:int, fields:list):
        # Ensure at least 7 fields so indexing is safe
        while len(fields) < 7:
            fields.append("")
        self.line_no = line_no
        self.type_code = fields[1] if len(fields) > 1 else ""
        self.amount = fields[2] if len(fields) > 2 else ""
        self.zone = fields[3] if len(fields) > 3 else "Z"
        self.ref_num = fields[4] if len(fields) > 4 else ""
        self.desc = fields[6] if len(fields) > 6 else ""

class Account03:
    def __init__(self, line_no:int, fields:list):
        while len(fields) < 7:
            fields.append("")
        self.line_no = line_no
        self.account_number = fields[1]
        self.account_currency = fields[2]
        self.account_type_code = fields[3]
        self.continuation_code = fields[6]
        self.entries = []
        self.orig_49_fields = None
        self.ending_balance = "0"  # will be set from orig 49 if present
        self.audit = {
            "ref_renumbered": False,
            "ending_balance_fixed": False,
            "amounts_normalized": 0,
            "descriptions_sanitized": 0,
            "desc_change_reasons": Counter(),
        }

    def finalize(self):
        # Renumber ref nums sequentially 00001..
        for idx, e in enumerate(self.entries, start=1):
            e.ref_num = f"{idx:05d}"
        self.audit["ref_renumbered"] = True
        # If we saw a 49, keep its ending balance; fix if not integer
        if self.orig_49_fields and len(self.orig_49_fields) > 1:
            eb_fixed, changed = ensure_int_cents(self.orig_49_fields[1])
            self.ending_balance = eb_fixed or "0"
            self.audit["ending_balance_fixed"] = changed
        else:
            self.ending_balance = "0"

class Group02:
    def __init__(self, line_no:int, fields:list):
        while len(fields) < 8:
            fields.append("")
        self.line_no = line_no
        self.receiver_id = fields[1]
        self.originator_id = fields[2]
        self.group_sequence = fields[3]
        self.group_date = fields[4]
        self.currency = fields[6]
        self.record_length_indicator = fields[7] if len(fields) > 7 else "2"
        self.accounts = []
        self.orig_98_fields = None

    def compute_98(self):
        group_total = sum(int(a.ending_balance or "0") for a in self.accounts)
        account_count = len(self.accounts)
        # 98 trailer should count: 02 + Σ(03 + Ns + 49) + 98 itself
        group_record_count = 1 + sum(1 + len(a.entries) + 1 for a in self.accounts) + 1  # 02 + Σ(03 + Ns + 49) + 98
        return group_total, account_count, group_record_count

class File01:
    def __init__(self, fields:list):
        while len(fields) < 9:
            fields.append("")
        self.originator_id = fields[1]
        self.receiver_id = fields[2]
        self.file_date = fields[3]
        self.file_time = fields[4]
        self.file_id_sequence = fields[5]
        self.record_length_indicator = fields[8] if len(fields) > 8 else "2"

# ==============================
# Parsing + Fixing
# ==============================

def parse_bai2(raw_text:str):
    lines = [ln.rstrip("\r\n") for ln in raw_text.splitlines() if ln.strip()]
    file01 = None
    groups = []
    cur_group = None
    cur_account = None

    # Track what was missing for audit
    missing = {"49": 0, "98": 0, "99": 0}

    for idx, ln in enumerate(lines, start=1):
        fields = (ln[:-1] if ln.endswith("/") else ln).split(",")
        rec = fields[0]
        if rec == "01":
            file01 = File01(fields)
        elif rec == "02":
            cur_group = Group02(idx, fields)
            groups.append(cur_group)
            cur_account = None
        elif rec == "03" and cur_group is not None:
            cur_account = Account03(idx, fields)
            cur_group.accounts.append(cur_account)
        elif rec == "16" and cur_account is not None:
            entry = Entry16(idx, fields)
            # normalize amount
            new_amount, changed = ensure_int_cents(entry.amount)
            if changed:
                cur_account.audit["amounts_normalized"] += 1
            entry.amount = new_amount
            # sanitize desc
            new_desc, desc_changed, reasons = sanitize_description(entry.desc)
            if desc_changed:
                cur_account.audit["descriptions_sanitized"] += 1
                for r in reasons:
                    cur_account.audit["desc_change_reasons"][r] += 1
            entry.desc = new_desc
            cur_account.entries.append(entry)
        elif rec == "49" and cur_account is not None:
            cur_account.orig_49_fields = fields
            cur_account = None  # close account
        elif rec == "98" and cur_group is not None:
            cur_group.orig_98_fields = fields
            cur_group = None  # close group
        elif rec == "99":
            # we don't need fields content; rebuilt later
            pass
        else:
            # unknown or out-of-order records ignored for rebuilding
            pass

    # Finalize 01/02 dates (invalid -> today)
    audit = {"file_date_corrected": False, "group_dates_corrected": 0}
    if file01 is None:
        raise ValueError("Missing 01 header")
    if not yymmdd_valid(file01.file_date):
        file01.file_date = today_yymmdd()
        audit["file_date_corrected"] = True
    for g in groups:
        if not yymmdd_valid(g.group_date):
            g.group_date = today_yymmdd()
            audit["group_dates_corrected"] += 1

    # Finalize accounts (renumber refs, fix ending balance format)
    for g in groups:
        for a in g.accounts:
            a.finalize()

    return file01, groups, audit

def rebuild_bai2(file01:File01, groups:list):
    out = []

    # 01
    out.append(f"01,{file01.originator_id},{file01.receiver_id},{file01.file_date},{file01.file_time},{file01.file_id_sequence},,,{file01.record_length_indicator}/")

    # 02..98 per group
    group_totals = []
    for g in groups:
        out.append(f"02,{g.receiver_id},{g.originator_id},{g.group_sequence},{g.group_date},,{g.currency},{g.record_length_indicator}/")
        for a in g.accounts:
            out.append(f"03,{a.account_number},{a.account_currency},{a.account_type_code},,,{a.continuation_code}/")
            for e in a.entries:
                # enforce 301/451 only if clearly indicated? We keep original type_code as-is to avoid changing business data
                # You can uncomment heuristic fixes if desired.
                type_code = e.type_code
                out.append(f"16,{type_code},{e.amount},Z,{e.ref_num},,{e.desc}/")
            # 49 trailer: Workday requires #16s + 2 (to include 03 + 49)
            N = len(a.entries) + 2  # Include 03 and 49 records
            out.append(f"49,{a.ending_balance},{N}/")
        # 98
        g_total, acct_ct, rec_ct = g.compute_98()
        group_totals.append(g_total)
        out.append(f"98,{g_total},{acct_ct},{rec_ct}/")

    # 99
    file_control_total = sum(group_totals)
    group_count = len(groups)
    # Count ALL records from 01 through 99 inclusive (Workday requirement)
    # This includes: 01 + all group records + 99 = total record count
    total_records = len(out) + 1  # +1 for the 99 record we're about to add
    out.append(f"99,{file_control_total},{group_count},{total_records}/")
    return out

def analyze_only(file_lines:list):
    # Minimal structural checks (endslash, trailers presence, 99 counts) for reporting after rebuild
    records = Counter()
    for ln in file_lines:
        rec = ln.split(",")[0]
        records[rec] += 1
    return records

def process_file(path:str, outdir:str):
    raw = open(path, "r").read()
    file01, groups, audit_dates = parse_bai2(raw)
    rebuilt_lines = rebuild_bai2(file01, groups)

    # Build audit text
    audit_lines = []
    if audit_dates["file_date_corrected"]:
        audit_lines.append(f"- corrected 01 file date -> {file01.file_date}")
    if audit_dates["group_dates_corrected"]:
        audit_lines.append(f"- corrected {audit_dates['group_dates_corrected']} group date(s) in 02")

    # Account-level audits
    total_ref_renum = 0
    total_amt_norm = 0
    total_desc_san = 0
    reasons = Counter()
    ending_bal_fixed = 0
    for g in groups:
        for a in g.accounts:
            if a.audit["ref_renumbered"]:
                total_ref_renum += 1
            total_amt_norm += a.audit["amounts_normalized"]
            total_desc_san += a.audit["descriptions_sanitized"]
            reasons.update(a.audit["desc_change_reasons"])
            if a.audit["ending_balance_fixed"]:
                ending_bal_fixed += 1

    if total_ref_renum:
        audit_lines.append(f"- renumbered REF_NUMs for {total_ref_renum} account(s)")
    if total_amt_norm:
        audit_lines.append(f"- normalized {total_amt_norm} amount(s) to integer cents")
    if total_desc_san:
        rs = ", ".join([f"{k}={v}" for k,v in reasons.items()]) if reasons else "sanitized descriptions"
        audit_lines.append(f"- sanitized {total_desc_san} description(s) ({rs})")
    if ending_bal_fixed:
        audit_lines.append(f"- fixed non-integer ending balances in {ending_bal_fixed} account(s)")

    # File-level recomputed trailers summary
    stats = analyze_only(rebuilt_lines)
    audit_lines.append(f"- rebuilt trailers: 49={stats.get('49',0)}, 98={stats.get('98',0)}, 99={stats.get('99',0)}")

    # Write outputs
    base = os.path.basename(path)
    name, ext = os.path.splitext(base)
    fixed_path = os.path.join(outdir, f"{name}_fixed.bai")
    audit_path = os.path.join(outdir, f"{name}_audit.txt")

    with open(fixed_path, "w") as f:
        f.write("\n".join(rebuilt_lines) + "\n")
    with open(audit_path, "w") as f:
        f.write("\n".join(audit_lines) + ("\n" if audit_lines else ""))

    return fixed_path, audit_path

def main():
    if len(sys.argv) < 2:
        print("Usage: bai2_fixer.py <input1.bai> [<input2.bai> ...] [--outdir <dir>]")
        sys.exit(1)
    args = sys.argv[1:]
    outdir = "."
    if "--outdir" in args:
        i = args.index("--outdir")
        if i < len(args)-1:
            outdir = args[i+1]
            del args[i:i+2]
        else:
            print("Error: --outdir requires a directory argument")
            sys.exit(1)
    os.makedirs(outdir, exist_ok=True)

    for inp in args:
        if not os.path.isfile(inp):
            print(f"Skip: {inp} (not found)")
            continue
        try:
            fixed_path, audit_path = process_file(inp, outdir)
            print(f"OK: {inp} -> {fixed_path}")
            print(f"Audit: {audit_path}")
        except Exception as e:
            print(f"ERROR processing {inp}: {e}", file=sys.stderr)
            sys.exit(2)

if __name__ == "__main__":
    main()

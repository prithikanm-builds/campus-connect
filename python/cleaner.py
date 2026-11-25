"""Pure-Python validation, cleaning, duplicate detection and CSV reporting."""
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

ALLOWED_BRANCHES = {"CSE", "IT", "AIDS", "ECE", "EEE", "MECH", "CIVIL"}

def read_entries(csv_path):
    """Read rows containing id and entry from a CSV file."""
    with open(csv_path, "r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not {"id", "entry"}.issubset(reader.fieldnames or []):
            raise ValueError("Input CSV must contain 'id' and 'entry' columns.")
        return [{"id": (row.get("id") or "").strip(),
                 "entry": (row.get("entry") or "").strip()} for row in reader]

def check_facts(entry, extracted):
    """Reject phone/email values that are not supported by the original entry."""
    result = dict(extracted)
    source_digits = re.sub(r"\D", "", entry)
    phone = result.get("phone")
    if phone is not None:
        phone_digits = re.sub(r"\D", "", str(phone))
        # The extracted digit sequence must occur in the source digits.
        if not phone_digits or phone_digits not in source_digits:
            result["phone"] = None
    email = result.get("email")
    if email is not None:
        email_text = str(email).strip()
        if not email_text or email_text.casefold() not in entry.casefold():
            result["email"] = None
    return result

def clean_phone(value):
    if value is None:
        return None
    digits = re.sub(r"\D", "", str(value))
    if digits.startswith("91") and len(digits) > 10:
        digits = digits[2:]
    elif digits.startswith("0") and len(digits) > 10:
        digits = digits[1:]
    if len(digits) != 10 or digits[0] not in "6789":
        return None
    return digits

def clean_email(value):
    if value is None:
        return None
    email = str(value).strip().lower()
    if (not email or " " in email or email.count("@") != 1
            or "." not in email.split("@", 1)[1]):
        return None
    return email

def clean_name(value):
    if value is None:
        return None
    return " ".join(str(value).split()).title() or None

def clean(extracted):
    """Apply deterministic cleaning rules to extracted fields."""
    data = dict(extracted)
    data["name"] = clean_name(data.get("name"))
    data["phone"] = clean_phone(data.get("phone"))
    data["email"] = clean_email(data.get("email"))
    try:
        year = int(data["year"]) if data.get("year") is not None else None
    except (TypeError, ValueError):
        year = None
    data["year"] = year if year in {1, 2, 3, 4} else None
    branch = str(data.get("branch") or "").strip().upper()
    data["branch"] = branch if branch in ALLOWED_BRANCHES else ("other" if branch else None)
    return data

def is_valid(data):
    reasons = []
    for field in ("name", "phone", "email", "year"):
        if data.get(field) in (None, ""):
            reasons.append(f"Missing or invalid {field}")
    if data.get("branch") not in ALLOWED_BRANCHES:
        reasons.append("Missing or unrecognised branch")
    return reasons

def process_records(records, extracted_by_id):
    """Combine extraction results with fact-checking and deterministic rules."""
    seen_phone, seen_email = {}, {}
    processed = []
    for record in records:
        rid, entry = record["id"], record["entry"]
        extracted = extracted_by_id.get(rid, {})
        fact_checked = check_facts(entry, extracted)
        cleaned = clean(fact_checked)
        reasons = is_valid(cleaned)
        duplicate_of = None
        phone, email = cleaned.get("phone"), cleaned.get("email")
        if phone and phone in seen_phone:
            duplicate_of = seen_phone[phone]
        elif email and email in seen_email:
            duplicate_of = seen_email[email]
        if duplicate_of:
            status = "duplicate"
            reasons.append(f"Duplicate of {duplicate_of}")
        elif reasons:
            status = "needs_fix"
        else:
            status = "valid"
        # Record first occurrence for duplicate matching, including records that need fixing.
        if phone:
            seen_phone.setdefault(phone, rid)
        if email:
            seen_email.setdefault(email, rid)
        processed.append({
            "id": rid, "original_entry": entry,
            "extracted_name": extracted.get("name"),
            "extracted_phone": extracted.get("phone"),
            "extracted_email": extracted.get("email"),
            "name": cleaned.get("name"), "phone": cleaned.get("phone"),
            "email": cleaned.get("email"), "year": cleaned.get("year"),
            "branch": cleaned.get("branch"), "status": status,
            "reasons": "; ".join(reasons), "duplicate_of": duplicate_of
        })
    return processed

def write_reports(processed, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    valid = [r for r in processed if r["status"] == "valid"]
    problems = [r for r in processed if r["status"] != "valid"]
    fields = ["id", "name", "phone", "email", "year", "branch"]
    with open(output_dir/"clean_list.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in valid:
            writer.writerow({k: row[k] for k in fields})
    problem_fields = ["id", "status", "reasons", "original_entry", "duplicate_of"]
    with open(output_dir/"problems.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=problem_fields)
        writer.writeheader()
        for row in problems:
            writer.writerow({k: row[k] for k in problem_fields})
    audit_fields = list(processed[0].keys()) if processed else ["id", "status"]
    with open(output_dir/"audit_log.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=audit_fields)
        writer.writeheader()
        writer.writerows(processed)
    counts = Counter(r["status"] for r in processed)
    by_branch, by_year = Counter(), Counter()
    for row in valid:
        by_branch[row["branch"]] += 1
        by_year[row["year"]] += 1
    lines = [
        "CLEAR-REG SUMMARY", "=================",
        f"Total registrations: {len(processed)}",
        f"Valid: {counts['valid']}",
        f"Needs fixing: {counts['needs_fix']}",
        f"Duplicates: {counts['duplicate']}", "",
        "Valid registrations by branch:"
    ]
    lines += [f"  {k}: {v}" for k, v in sorted(by_branch.items())] or ["  None"]
    lines += ["", "Valid registrations by year:"]
    lines += [f"  Year {k}: {v}" for k, v in sorted(by_year.items())] or ["  None"]
    lines += ["", "Human checkpoint: the event team reviews problems.csv and contacts students."]
    (output_dir/"summary.txt").write_text("\n".join(lines), encoding="utf-8")
    return {"total": len(processed), **dict(counts)}

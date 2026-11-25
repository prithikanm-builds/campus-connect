"""CLEAR-REG command-line application."""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from python.cleaner import read_entries, process_records, write_reports

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description="AI-powered event registration cleaner")
    parser.add_argument("--input", default=str(ROOT/"data"/"registrations.csv"))
    parser.add_argument("--output", default=str(ROOT/"outputs"))
    parser.add_argument("--limit", type=int, default=0, help="Process only the first N rows (useful for a quick API test).")
    parser.add_argument("--demo", action="store_true", help="Run with clearly labelled sample extraction data; no API calls.")
    args = parser.parse_args()
    load_dotenv(ROOT/".env")
    records = read_entries(args.input)
    if args.limit:
        records = records[:args.limit]
    extracted_by_id = {}
    if args.demo:
        print("DEMO MODE: using sample extraction results, not Gemini.")
        for r in records:
            # Demo mode deliberately leaves fields null; use the offline test harness for rule tests.
            extracted_by_id[r["id"]] = {"name": None, "phone": None, "email": None, "year": None, "branch": None}
    else:
        from python.gemini_client import extract_registration
        for index, record in enumerate(records, start=1):
            try:
                extracted_by_id[record["id"]] = extract_registration(record["entry"])
                print(f"{record['id']}: extraction received")
            except Exception as exc:
                print(f"{record['id']}: extraction failed safely ({exc})")
                extracted_by_id[record["id"]] = {"name": None, "phone": None, "email": None, "year": None, "branch": None}
            if index < len(records):
                time.sleep(float(os.getenv("API_PAUSE_SECONDS", "1")))
    processed = process_records(records, extracted_by_id)
    counts = write_reports(processed, args.output)
    print("\nRun complete.")
    print(json.dumps(counts, indent=2))
    print(f"Reports saved to: {Path(args.output).resolve()}")
    print("Review problems.csv manually; the event team must confirm incorrect details.")

if __name__ == "__main__":
    main()

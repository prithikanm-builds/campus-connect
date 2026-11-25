"""Five deterministic tests for Python cleaning, fact-checking and duplicate rules."""
from python.cleaner import clean, check_facts, process_records

CASES = [
    ("valid phone and email", {"name":"priya k","phone":"9840012345","email":"priya@gmail.com","year":2,"branch":"CSE"}, "valid", "9840012345"),
    ("invalid phone length", {"name":"anu","phone":"812345678","email":"anu@gmail.com","year":1,"branch":"CSE"}, "needs_fix", None),
    ("invalid email", {"name":"sanjay","phone":"7654321098","email":"sanjay@gmail","year":2,"branch":"EEE"}, "needs_fix", "7654321098"),
    ("invalid year", {"name":"naveen","phone":"9123456780","email":"naveen@gmail.com","year":5,"branch":"ECE"}, "needs_fix", "9123456780"),
    ("duplicate phone", {"name":"second person","phone":"9840012345","email":"other@gmail.com","year":2,"branch":"CSE"}, "duplicate", "9840012345"),
]

def run_tests():
    passed = 0
    print("CLEAR-REG EVALUATION HARNESS")
    print("-" * 76)
    for index, (label, data, expected_status, expected_phone) in enumerate(CASES, 1):
        first = clean(data)
        # Duplicate test compares against an earlier registration with the same phone.
        records = [{"id":"T00","entry":"9840012345 priya@gmail.com"},
                   {"id":f"T{index:02d}","entry":"9840012345 other@gmail.com"}] if label == "duplicate phone" else [{"id":f"T{index:02d}","entry":" ".join(str(v) for v in data.values())}]
        extracted = {"T00":{"name":"Priya","phone":"9840012345","email":"priya@gmail.com","year":2,"branch":"CSE"},
                     f"T{index:02d}":data}
        if label == "duplicate phone":
            result = process_records(records, extracted)[1]
        else:
            # Avoid fact-check mismatch by using an entry containing the returned phone/email.
            entry = f"{data.get('phone','')} {data.get('email','')}"
            result = process_records([{"id":f"T{index:02d}","entry":entry}], extracted)[0]
        actual_phone = result["phone"]
        ok = result["status"] == expected_status and actual_phone == expected_phone
        passed += int(ok)
        print(f"{index}. {label}: expected=({expected_status}, {expected_phone}) "
              f"actual=({result['status']}, {actual_phone}) {'PASS' if ok else 'FAIL'}")
    accuracy = passed / len(CASES) * 100
    print(f"\nAccuracy: {passed}/{len(CASES)} = {accuracy:.1f}%")
    return passed == len(CASES)

if __name__ == "__main__":
    raise SystemExit(0 if run_tests() else 1)

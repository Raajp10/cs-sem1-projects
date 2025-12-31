import os
from parser import parse_source, ParseError

BASE_DIR = os.path.dirname(__file__)
TEST_DIR = os.path.join(BASE_DIR, "tests")
VALID_DIR = os.path.join(TEST_DIR, "valid")
INVALID_DIR = os.path.join(TEST_DIR, "invalid")


def run_valid_tests():
    print("Running valid tests...")
    for fname in sorted(os.listdir(VALID_DIR)):
        if not fname.endswith(".min"):
            continue
        path = os.path.join(VALID_DIR, fname)
        with open(path, "r") as f:
            src = f.read()
        try:
            parse_source(src)
            print(f"[PASS] {fname}")
        except ParseError as e:
            print(f"[FAIL] {fname} (unexpected parse error)")
            print("   ", e)


def run_invalid_tests():
    print("Running invalid tests...")
    for fname in sorted(os.listdir(INVALID_DIR)):
        if not fname.endswith(".min"):
            continue
        path = os.path.join(INVALID_DIR, fname)
        with open(path, "r") as f:
            src = f.read()
        try:
            parse_source(src)
            print(f"[FAIL] {fname} (should have failed but parsed successfully)")
        except ParseError as e:
            print(f"[FAIL] but parsed successfully {fname}")
            print("   ", e)  


if __name__ == "__main__":
    run_valid_tests()
    print()
    run_invalid_tests()

# main.py
import os
from scanner import Scanner
from parser import Parser, ParseError


BASE_DIR = os.path.dirname(__file__)
TEST_DIR = os.path.join(BASE_DIR, "tests")
VALID_DIR = os.path.join(TEST_DIR, "valid")
INVALID_DIR = os.path.join(TEST_DIR, "invalid")


def run_single_test(path: str, is_valid: bool) -> bool:
    """Run parser on a single file, print AST + symbol tables on success."""
    fname = os.path.basename(path)
    with open(path, "r") as f:
        src = f.read()

    scanner = Scanner(src)
    tokens = scanner.scan_tokens()
    parser = Parser(tokens)

    try:
        program = parser.parse()
        if not is_valid:
            print(f"[FAIL] {fname} (should have failed but parsed successfully)")
            print("  Parsed AST and symbol tables (for debugging):")
        else:
            print(f"[PASS] {fname}")

        # Print symbol tables and AST for every successful parse
        print("  --- SYMBOL TABLES ---")
        for scope in parser.scopes:
            print(scope.pretty_print())
            print()

        print("  --- AST ---")
        print(program.pretty())
        print()
        return is_valid  # success only counts as pass if is_valid

    except ParseError as e:
        if is_valid:
            print(f"[FAIL] {fname} (unexpected parse/semantic error)")
            print("   ", e)
            print()
            return False
        else:
            print(f"[PASS] {fname} (correctly rejected)")
            print("   Error:", e)
            print()
            return True


def run_valid_tests() -> None:
    print("Running VALID tests...\n")
    passed = 0
    total = 0

    for fname in sorted(os.listdir(VALID_DIR)):
        if not fname.endswith(".min"):
            continue
        total += 1
        path = os.path.join(VALID_DIR, fname)
        if run_single_test(path, is_valid=True):
            passed += 1

    print(f"VALID summary: {passed}/{total} passed.\n")


def run_invalid_tests() -> None:
    print("Running INVALID tests...\n")
    passed = 0
    total = 0

    for fname in sorted(os.listdir(INVALID_DIR)):
        if not fname.endswith(".min"):
            continue
        total += 1
        path = os.path.join(INVALID_DIR, fname)
        if run_single_test(path, is_valid=False):
            passed += 1

    print(f"INVALID summary: {passed}/{total} passed.\n")


if __name__ == "__main__":
    run_valid_tests()
    run_invalid_tests()

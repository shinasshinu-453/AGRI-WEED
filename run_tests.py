"""
================================================================
          AgriVision - Automated Test Runner
      Unit Testing  &  Integration Testing (pytest)
================================================================

Run:  python run_tests.py
"""

import subprocess
import sys
import os
import time
import re
from datetime import datetime

# Force UTF-8 output on Windows
if sys.platform == "win32":
    os.system("")  # enable ANSI on Windows
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# -- Colour helpers (ANSI codes) ---------------------------------
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


def banner(title, subtitle=""):
    line = "=" * 62
    print(f"\n{CYAN}{BOLD}+{line}+{RESET}")
    print(f"{CYAN}{BOLD}|  {title:^58}  |{RESET}")
    if subtitle:
        print(f"{CYAN}|  {subtitle:^58}  |{RESET}")
    print(f"{CYAN}{BOLD}+{line}+{RESET}\n")


def section(title):
    line = "-" * 60
    print(f"\n{YELLOW}{BOLD}+{line}+{RESET}")
    print(f"{YELLOW}{BOLD}|  {title:<56}  |{RESET}")
    print(f"{YELLOW}{BOLD}+{line}+{RESET}\n")


def run_pytest(marker, label):
    """Run pytest for a given marker and return (passed, failed, total, duration)."""
    section(label)
    cmd = [
        sys.executable, "-m", "pytest", "tests/",
        "-v", "--tb=short", "--no-header",
        "-m", marker,
    ]
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    duration = time.time() - start

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if "PASSED" in line:
            parts = line.rsplit("PASSED", 1)
            name = parts[0].strip().replace("tests/", "").replace("tests\\", "")
            pct = parts[1].strip() if len(parts) > 1 else ""
            print(f"  {GREEN}[PASS]{RESET}  {name}  {DIM}{pct}{RESET}")
        elif "FAILED" in line:
            parts = line.rsplit("FAILED", 1)
            name = parts[0].strip().replace("tests/", "").replace("tests\\", "")
            pct = parts[1].strip() if len(parts) > 1 else ""
            print(f"  {RED}[FAIL]{RESET}  {name}  {DIM}{pct}{RESET}")
        elif "passed" in line or "failed" in line or "error" in line:
            print(f"  {DIM}{line}{RESET}")

    # Parse counts
    passed = failed = 0
    for line in result.stdout.splitlines():
        if "passed" in line:
            m = re.search(r"(\d+)\s+passed", line)
            if m:
                passed = int(m.group(1))
            m = re.search(r"(\d+)\s+failed", line)
            if m:
                failed = int(m.group(1))

    total = passed + failed
    return passed, failed, total, duration


def main():
    banner(
        "AgriVision  -  Automated Test Suite",
        "Date: " + datetime.now().strftime("%d %B %Y, %I:%M %p")
    )

    print(f"  {DIM}Project  : Main-project-Wheat (AgriVision){RESET}")
    print(f"  {DIM}Framework: pytest  |  Python {sys.version.split()[0]}{RESET}")
    print(f"  {DIM}Platform : Windows{RESET}")

    # -- Phase 1: Unit Tests  ------------------------------------
    u_pass, u_fail, u_total, u_time = run_pytest(
        "unit",
        "PHASE 1  -  Unit Tests  (Isolated Function Testing)"
    )

    # -- Phase 2: Integration Tests  ----------------------------
    i_pass, i_fail, i_total, i_time = run_pytest(
        "integration",
        "PHASE 2  -  Integration Tests  (API Endpoint Testing)"
    )

    # -- Summary Table  ------------------------------------------
    total_pass  = u_pass + i_pass
    total_fail  = u_fail + i_fail
    total_tests = u_total + i_total
    total_time  = u_time + i_time

    line = "=" * 62
    sep  = "-" * 62
    print(f"\n{CYAN}{BOLD}+{line}+{RESET}")
    print(f"{CYAN}{BOLD}|  {'TEST EXECUTION SUMMARY':^58}  |{RESET}")
    print(f"{CYAN}{BOLD}+{line}+{RESET}")
    print(f"{CYAN}|                                                              |{RESET}")
    print(f"{CYAN}|  {'Phase':<30} {'Passed':>8} {'Failed':>8} {'Time':>10}  |{RESET}")
    print(f"{CYAN}|  {sep[:56]}  |{RESET}")

    # Phase 1 row
    mark1 = f"{GREEN}[OK]{RESET}" if u_fail == 0 else f"{RED}[!!]{RESET}"
    fail1 = f"{RED}{u_fail}{RESET}" if u_fail else f"{DIM}{u_fail}{RESET}"
    print(f"{CYAN}|{RESET}  {mark1} {'Unit Tests':<26} {GREEN}{u_pass:>8}{RESET} {fail1:>17} {u_time:>9.2f}s  {CYAN}|{RESET}")

    # Phase 2 row
    mark2 = f"{GREEN}[OK]{RESET}" if i_fail == 0 else f"{RED}[!!]{RESET}"
    fail2 = f"{RED}{i_fail}{RESET}" if i_fail else f"{DIM}{i_fail}{RESET}"
    print(f"{CYAN}|{RESET}  {mark2} {'Integration Tests':<26} {GREEN}{i_pass:>8}{RESET} {fail2:>17} {i_time:>9.2f}s  {CYAN}|{RESET}")

    print(f"{CYAN}|  {sep[:56]}  |{RESET}")

    # Totals row
    mark_t = f"{GREEN}[OK]{RESET}" if total_fail == 0 else f"{RED}[!!]{RESET}"
    fail_t = f"{RED}{total_fail}{RESET}" if total_fail else f"{DIM}{total_fail}{RESET}"
    print(f"{CYAN}|{RESET}  {mark_t} {BOLD}{'TOTAL':<26}{RESET} {GREEN}{BOLD}{total_pass:>8}{RESET} {fail_t:>17} {BOLD}{total_time:>9.2f}s{RESET}  {CYAN}|{RESET}")

    print(f"{CYAN}|                                                              |{RESET}")

    # Verdict
    if total_fail == 0:
        verdict = f"{GREEN}{BOLD}  *** ALL {total_tests} TESTS PASSED SUCCESSFULLY ***{RESET}"
        print(f"{CYAN}|{RESET}  {verdict}             {CYAN}|{RESET}")
    else:
        verdict = f"{RED}{BOLD}  *** {total_fail} TEST(S) FAILED - REVIEW REQUIRED ***{RESET}"
        print(f"{CYAN}|{RESET}  {verdict}             {CYAN}|{RESET}")

    print(f"{CYAN}|                                                              |{RESET}")
    print(f"{CYAN}{BOLD}+{line}+{RESET}")
    print()

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

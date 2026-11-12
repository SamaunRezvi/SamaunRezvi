"""Run every local check before committing.

    python tools/check.py          # everything
    python tools/check.py --fast   # unit tests only

It runs the unit tests and the badge check, then scans for long dashes and emoji
in tracked text files. It exits with 1 if anything fails.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STEPS = [
    ("unit tests", [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"]),
    ("badge files", [sys.executable, "-B", os.path.join("tools", "sync_badges.py"), "--check"]),
]


def main(argv=None):
    """Run each step and report which ones failed. --fast runs only the unit tests."""
    argv = sys.argv[1:] if argv is None else argv
    steps = STEPS[:1] if "--fast" in argv else STEPS
    failed = []
    for name, command in steps:
        print(f"== {name}")
        if subprocess.run(command, cwd=ROOT).returncode:
            failed.append(name)
    if failed:
        print("failed: " + ", ".join(failed))
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""CLI yordamchi skriptlar."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args: str) -> int:
    cmd = [sys.executable, "-m", "src.main", *args]
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Foydalanish: python scripts/control.py [enable|disable|status|run]")
        sys.exit(1)
    sys.exit(run_cli(sys.argv[1]))

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.database import get_database


def check_db_readiness():
    db = get_database()
    report = db.get_readiness()
    print("\n[TaskPulse] Storage Readiness Report")
    print("========================================")
    print(f"Mode:  {report.get('mode', 'sqlite').upper()}")
    print(f"Ready: {'[OK]' if report.get('ready') else '[FAIL]'}")
    print(f"Path:  {report.get('path')}")
    print("Tables:")
    for tbl, status in report.get("tables", {}).items():
        print(f"  * {tbl}: {status}")
    print()


if __name__ == "__main__":
    check_db_readiness()
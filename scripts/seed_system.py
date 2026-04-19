from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal, create_tables
from app.seed.bootstrap import run_seed


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed credit risk system")
    parser.add_argument("--version", default="v1.0.0", help="Seed version label")
    parser.add_argument("--with-demo", default="true", choices=["true", "false"], help="Include demo assessments")
    args = parser.parse_args()

    include_demo = args.with_demo.lower() == "true"
    create_tables()
    db = SessionLocal()
    try:
        out = run_seed(db, seed_version=args.version, include_dummy_assessments=include_demo)
        print(out)
    finally:
        db.close()


if __name__ == "__main__":
    main()

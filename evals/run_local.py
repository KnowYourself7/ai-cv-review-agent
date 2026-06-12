from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    cases_path = Path(__file__).with_name("cases.jsonl")
    cases = [json.loads(line) for line in cases_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Loaded {len(cases)} eval cases.")
    print("These cases are a scaffold for manual or platform trace grading after API setup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .monte_carlo_engine import run_swarm_study


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--config-file")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    config = {}
    if args.config_file:
        config_path = Path(args.config_file).resolve()
        if config_path.exists():
            config = json.loads(config_path.read_text(encoding="utf-8"))

    run_swarm_study(run_dir, config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient, ReturnDocument
from pymongo.errors import PyMongoError


POLL_INTERVAL_SECONDS = 5


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_runs_root() -> Path:
    return Path(os.environ.get("RUNS_DIR", str(get_repo_root() / "runs"))).resolve()


def connect_mongo() -> MongoClient:
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        raise RuntimeError("MONGO_URI is required")

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client


def claim_next_run(collection):
    return collection.find_one_and_update(
        {"status": "queued"},
        {
            "$set": {
                "status": "running",
                "startedAt": utc_now(),
                "error": None,
                "updatedAt": utc_now(),
            }
        },
        sort=[("createdAt", 1)],
        return_document=ReturnDocument.AFTER,
    )


def ensure_run_dirs(run_dir: Path) -> None:
    for subdir in ("config", "data", "data/csv", "data/outputs", "data/plots", "logs"):
        (run_dir / subdir).mkdir(parents=True, exist_ok=True)


def run_pipeline(run_id: str, run_dir: Path) -> tuple[int, str]:
    ensure_run_dirs(run_dir)

    log_path = run_dir / "logs" / "pipeline.log"
    env = os.environ.copy()
    env["RUN_DIR"] = str(run_dir)

    command = ["sh", "pipeline/scripts/run_all.sh"]
    header = (
        f"[worker] starting run {run_id}\n"
        f"[worker] run_dir={run_dir}\n"
        f"[worker] command={' '.join(command)}\n"
    )

    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(header)
        log_file.flush()

        process = subprocess.run(
            command,
            cwd=str(get_repo_root()),
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )

        log_file.write(
            f"\n[worker] finished run {run_id} with exit code {process.returncode}\n"
        )
        log_file.flush()

    return process.returncode, str(log_path)


def finish_run(collection, run_id: str, status: str, error: str | None = None) -> None:
    collection.update_one(
        {"runId": run_id},
        {
            "$set": {
                "status": status,
                "finishedAt": utc_now(),
                "error": error,
                "updatedAt": utc_now(),
            }
        },
    )


def main() -> int:
    runs_root = get_runs_root()
    runs_root.mkdir(parents=True, exist_ok=True)

    client = None
    while client is None:
        try:
            client = connect_mongo()
        except Exception as error:
            print(f"[worker] Mongo connection failed: {error}", file=sys.stderr)
            time.sleep(POLL_INTERVAL_SECONDS)

    db = client.get_default_database()
    if db is None:
        db_name = os.environ.get("MONGO_DB", "drone_route_optimization")
        db = client[db_name]
    else:
        db_name = db.name

    collection = db["runs"]

    print(f"[worker] connected to MongoDB database={db_name}")
    print(f"[worker] runs root = {runs_root}")

    while True:
        try:
            run = claim_next_run(collection)
        except PyMongoError as error:
            print(f"[worker] Mongo polling error: {error}", file=sys.stderr)
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        if not run:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        run_id = run["runId"]
        run_dir = runs_root / run_id
        print(f"[worker] claimed run {run_id}")

        try:
            exit_code, log_path = run_pipeline(run_id, run_dir)
        except Exception as error:
            error_message = f"Worker execution failed: {error}"
            print(f"[worker] {error_message}", file=sys.stderr)
            finish_run(collection, run_id, "failed", error_message)
            continue

        if exit_code == 0:
            finish_run(collection, run_id, "completed", None)
            print(f"[worker] completed run {run_id}")
        else:
            error_message = f"Pipeline exited with code {exit_code}"
            finish_run(collection, run_id, "failed", error_message)
            print(f"[worker] failed run {run_id}; log={log_path}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())

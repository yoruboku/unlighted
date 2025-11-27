#!/usr/bin/env python3
"""
Synco: tiny rclone-based sync loop with start/stop via PID file.

- Uses rclone to sync a local folder to a remote.
- Reads settings from synco.json in the same directory.
- Can run once (--once) or in a loop with a fixed interval.
- Uses a PID file (synco.pid) so you can start/stop cleanly.

This script is intentionally minimal: stdlib only, no extra deps.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time

PIDFILE = "synco.pid"
DEFAULT_INTERVAL = 60  # seconds
DEFAULT_CONFIG = "synco.json"


def is_running(pidfile: str = PIDFILE) -> bool:
    """Return True if a previous synco process is still running."""
    if not os.path.exists(pidfile):
        return False

    try:
        with open(pidfile, "r", encoding="utf-8") as f:
            pid = int(f.read().strip())
        # If this doesn't raise, process exists (on POSIX).
        # On Windows, os.kill with sig=0 is also a basic existence check.
        os.kill(pid, 0)
        return True
    except Exception:
        # Stale PID file – remove it.
        try:
            os.remove(pidfile)
        except Exception:
            pass
        return False


def write_pid(pidfile: str = PIDFILE) -> None:
    """Write the current process PID to pidfile."""
    with open(pidfile, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))


def remove_pid(pidfile: str = PIDFILE) -> None:
    """Remove the PID file if it exists."""
    try:
        os.remove(pidfile)
    except Exception:
        pass


def load_config(path: str) -> dict:
    """Load JSON config file."""
    if not os.path.exists(path):
        print(f"[synco] Config not found: {path}")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[synco] Failed to parse {path}: {e}")
        sys.exit(1)

    required = ["local", "remote"]
    for key in required:
        if key not in cfg:
            print(f"[synco] Missing required key in config: {key}")
            sys.exit(1)

    return cfg


def run_rclone(cfg: dict, extra_flags: list[str]) -> int:
    """
    Run a single rclone sync.

    Required config keys:
      - local
      - remote

    Optional config keys:
      - buffer_size (default "1M")
      - log_level  (default "ERROR")
      - bwlimit    (e.g. "2M")
    """
    local = cfg["local"]
    remote = cfg["remote"]

    buffer_size = cfg.get("buffer_size", "1M")
    log_level = cfg.get("log_level", "ERROR")
    bwlimit = cfg.get("bwlimit")

    cmd = [
        "rclone",
        "sync",
        local,
        remote,
        "--transfers",
        "1",
        "--checkers",
        "1",
        "--buffer-size",
        buffer_size,
        "--log-level",
        log_level,
    ]

    if bwlimit:
        cmd += ["--bwlimit", bwlimit]

    if extra_flags:
        cmd += extra_flags

    print("[synco] Running:", " ".join(cmd))

    try:
        result = subprocess.run(cmd)
        rc = result.returncode
    except FileNotFoundError:
        print("[synco] rclone not found. Make sure it is installed and in your PATH.")
        return 127

    if rc == 0:
        print("[synco] Sync finished successfully.")
    else:
        print(f"[synco] Sync finished with exit code {rc}.")

    return rc


def stop_existing(pidfile: str = PIDFILE) -> None:
    """Attempt to stop a running synco instance."""
    if not os.path.exists(pidfile):
        print("[synco] Not running (no PID file).")
        return

    try:
        with open(pidfile, "r", encoding="utf-8") as f:
            pid = int(f.read().strip())
    except Exception:
        print("[synco] Failed to read PID file, removing.")
        remove_pid(pidfile)
        return

    try:
        print(f"[synco] Sending SIGTERM to PID {pid}.")
        os.kill(pid, signal.SIGTERM)
    except Exception as e:
        print(f"[synco] Failed to signal process: {e}")

    # Clean up PID regardless – if it’s still running, next is_running() will detect.
    remove_pid(pidfile)
    print("[synco] Stopped (or at least tried).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Synco: tiny rclone sync loop")
    parser.add_argument(
        "--config",
        "-c",
        default=DEFAULT_CONFIG,
        help=f"Path to JSON config (default: {DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--once", action="store_true", help="Run a single sync and exit"
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"Interval between syncs in seconds (default: {DEFAULT_INTERVAL})",
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop a running synco process (using PID file)",
    )
    parser.add_argument(
        "--no-create-pid",
        action="store_true",
        help="Do not create PID file (useful for debugging)",
    )

    args = parser.parse_args()

    if args.stop:
        stop_existing()
        return

    if is_running():
        print("[synco] Another synco instance is already running. Exiting.")
        return

    cfg = load_config(args.config)
    extra_flags = cfg.get("extra_flags", [])

    if not args.no_create_pid:
        write_pid()

    try:
        if args.once:
            run_rclone(cfg, extra_flags)
        else:
            while True:
                run_rclone(cfg, extra_flags)
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("[synco] Interrupted by user.")
    finally:
        remove_pid()


if __name__ == "__main__":
    main()

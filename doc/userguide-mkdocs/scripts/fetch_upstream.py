#!/usr/bin/env python3
"""
Fetch the latest RST source files from the upstream robotframework/robotframework repo.

Uses git sparse-checkout to download only doc/userguide/src/, then copies the
result into the local doc/userguide/src/ path. Writes a .upstream-lock.json
provenance file on success.

Usage:
    python fetch_upstream.py                 # Fetch from master
    python fetch_upstream.py --ref v7.2.1   # Fetch from a specific tag/branch/commit
"""

import argparse
import datetime
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


UPSTREAM_URL = "https://github.com/robotframework/robotframework"
UPSTREAM_SUBDIR = "doc/userguide/src"

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = SCRIPT_DIR.parent          # doc/userguide-mkdocs/
REPO_ROOT = PROJECT_DIR.parent.parent    # robotframework/ repo root
LOCAL_RST_DIR = REPO_ROOT / "doc" / "userguide" / "src"
LOCK_FILE = PROJECT_DIR / ".upstream-lock.json"


def _git(*args, cwd=None, check=True):
    """Run a git command and return CompletedProcess."""
    return subprocess.run(
        ["git", *args],
        capture_output=True, text=True, cwd=str(cwd) if cwd else None,
        check=check,
    )


def check_git_available():
    """Exit with a clear error if git is not on PATH."""
    if shutil.which("git") is None:
        print("ERROR: git is required but not found on PATH", file=sys.stderr)
        sys.exit(1)


def resolve_commit(clone_dir: Path) -> str:
    """Return the full commit SHA of HEAD in the clone."""
    result = _git("rev-parse", "HEAD", cwd=clone_dir)
    return result.stdout.strip()


def fetch(ref: str) -> None:
    check_git_available()

    print(f"Fetching {UPSTREAM_SUBDIR} from {UPSTREAM_URL} @ {ref} …")

    with tempfile.TemporaryDirectory(prefix="rf-upstream-") as tmp:
        tmp_path = Path(tmp)
        clone_dir = tmp_path / "clone"

        # Sparse clone: only metadata, no blobs yet
        print("  → git clone (sparse, depth=1) …", end=" ", flush=True)
        try:
            _git(
                "clone",
                "--filter=blob:none",
                "--sparse",
                "--depth=1",
                f"--branch={ref}",
                UPSTREAM_URL,
                str(clone_dir),
            )
        except subprocess.CalledProcessError as exc:
            print("FAILED")
            print(f"ERROR: git clone failed:\n{exc.stderr}", file=sys.stderr)
            sys.exit(1)
        print("OK")

        # Enable sparse checkout for only the subtree we need
        print(f"  → sparse-checkout set {UPSTREAM_SUBDIR} …", end=" ", flush=True)
        try:
            _git("sparse-checkout", "set", UPSTREAM_SUBDIR, cwd=clone_dir)
        except subprocess.CalledProcessError as exc:
            print("FAILED")
            print(f"ERROR: sparse-checkout failed:\n{exc.stderr}", file=sys.stderr)
            sys.exit(1)
        print("OK")

        # Validate the expected path exists in the clone
        src_dir = clone_dir / UPSTREAM_SUBDIR
        if not src_dir.is_dir():
            print(
                f"ERROR: Expected path not found in upstream clone: {UPSTREAM_SUBDIR}",
                file=sys.stderr,
            )
            sys.exit(1)

        commit_sha = resolve_commit(clone_dir)

        # Copy into local repo (replace existing files)
        print(f"  → Copying to {LOCAL_RST_DIR} …", end=" ", flush=True)
        LOCAL_RST_DIR.mkdir(parents=True, exist_ok=True)
        # shutil.copytree with dirs_exist_ok replaces in-place
        shutil.copytree(src_dir, LOCAL_RST_DIR, dirs_exist_ok=True)
        print("OK")

    # Write provenance lockfile only after successful copy
    lock = {
        "ref": ref,
        "commit": commit_sha,
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    LOCK_FILE.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    print(f"  → Wrote {LOCK_FILE.name} (commit {commit_sha[:12]})")
    print("Fetch complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch upstream RST source for the Robot Framework User Guide"
    )
    parser.add_argument(
        "--ref", default="master",
        help="Branch, tag, or commit to fetch (default: master)"
    )
    args = parser.parse_args()
    fetch(args.ref)


if __name__ == "__main__":
    main()

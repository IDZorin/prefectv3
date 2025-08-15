# stats_utils.py
from __future__ import annotations

import json
import os
import platform
import socket
import sys
import uuid
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any, Dict, List, Optional
import inspect


# Hardcoded file to read a text payload from.
TEXT_FILE_TO_READ = Path(r"D:\code\repos\prefectv3_extra\sample_input.txt")


def _detect_environment() -> Dict[str, Any]:
    """Detect virtualenv or conda and return basic environment info."""
    is_venv = hasattr(sys, "real_prefix") or (getattr(sys, "base_prefix", sys.prefix) != sys.prefix)
    conda_env = os.environ.get("CONDA_DEFAULT_ENV")
    env_kind = "conda" if conda_env else ("venv" if is_venv else "system")
    return {
        "env_kind": env_kind,
        "is_virtualenv": is_venv,
        "conda_env": conda_env,
        "venv_path": os.environ.get("VIRTUAL_ENV"),
    }


def _read_hardcoded_text() -> Dict[str, Any]:
    """Read the hardcoded text file if present; include small metadata."""
    info: Dict[str, Any] = {
        "path": str(TEXT_FILE_TO_READ.resolve()),
        "exists": TEXT_FILE_TO_READ.exists(),
    }
    if TEXT_FILE_TO_READ.exists():
        try:
            text = TEXT_FILE_TO_READ.read_text(encoding="utf-8", errors="replace")
            info.update(
                {
                    "size_bytes": len(text.encode("utf-8")),
                    "preview": text[:500],
                }
            )
        except Exception as e:
            info.update({"error": f"failed_to_read: {e!r}"})
    else:
        info.update({"note": "file not found"})
    return info


def _list_installed_packages(limit: int = 50) -> List[Dict[str, str]]:
    """Return up to `limit` installed packages and versions, sorted by name."""
    try:
        dists = importlib_metadata.distributions()
        pairs = sorted([(d.metadata["Name"], d.version) for d in dists if d.metadata.get("Name")], key=lambda x: x[0].lower())
        return [{"name": n, "version": v} for n, v in pairs[:limit]]
    except Exception:
        # Best-effort only
        return []


def collect_run_info() -> Dict[str, Any]:
    """
    Collect environment and run statistics.
    Returns a dict suitable for JSON serialization.
    """
    now_local = datetime.now().astimezone()
    now_utc = datetime.now(timezone.utc)

    # Try to capture the caller file path if this function is imported and called.
    try:
        caller_file = Path(inspect.stack()[1].filename).resolve()
    except Exception:
        caller_file = None

    run_info: Dict[str, Any] = {
        "run_id": str(uuid.uuid4()),
        "timestamp_local": now_local.isoformat(),
        "timestamp_utc": now_utc.isoformat(),
        "module_file": str(Path(__file__).resolve()),
        "caller_file": str(caller_file) if caller_file else None,
        "cwd": str(Path.cwd()),
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "implementation": platform.python_implementation(),
        },
        "platform": {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": socket.gethostname(),
            "user": os.environ.get("USERNAME") or os.environ.get("USER"),
            "cpu_count": os.cpu_count(),
        },
        "argv": sys.argv,
        "environment": _detect_environment(),
        "env_vars_subset": {
            # Only a safe subset to avoid leaking secrets
            "PATH": os.environ.get("PATH"),
            "PYTHONPATH": os.environ.get("PYTHONPATH"),
            "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV"),
            "CONDA_DEFAULT_ENV": os.environ.get("CONDA_DEFAULT_ENV"),
            "HOME": os.environ.get("HOME") or os.environ.get("USERPROFILE"),
            "TEMP": os.environ.get("TEMP") or os.environ.get("TMP"),
        },
        "installed_packages_sample": _list_installed_packages(limit=50),
        "hardcoded_text_file": _read_hardcoded_text(),
    }
    return run_info

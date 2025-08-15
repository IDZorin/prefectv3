# make_report.py
from __future__ import annotations

import json
import logging
import sys
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import pandas as pd  # Requires: pip install pandas openpyxl

from tools.tool import collect_run_info  # your existing function


# ---------- Data helpers ----------
def build_dataframe():
    """Create a 5-rows x 2-columns DataFrame with 'text' and 'number'."""
    rows = 5
    data = {
        "text": [f"row_{i}" for i in range(1, rows + 1)],
        "number": [i for i in range(1, rows + 1)],
    }
    return pd.DataFrame(data)


def resolve_output_dir() -> Path:
    """
    Create an output folder one level above this script, named YYYY-MM.
    Example: if this file is in .../gitlab, output goes to .../2025-08.
    """
    script_dir = Path(__file__).resolve().parent
    parent_dir = script_dir.parent / "OUTPUT" 
    folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = parent_dir / folder_name
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def save_excel(df, out_dir: Path) -> Path:
    """Save the DataFrame to an Excel file in out_dir."""
    excel_path = out_dir / "sample.xlsx"
    try:
        df.to_excel(excel_path, index=False)
    except Exception as e:
        raise RuntimeError(
            "Saving to .xlsx requires an Excel writer engine (openpyxl or xlsxwriter). "
            "Install one of them, for example: pip install openpyxl"
        ) from e
    return excel_path


def save_run_info_txt(run_info: dict, out_dir: Path) -> Path:
    """Save run info dict as a human-readable text (pretty JSON)."""
    txt_path = out_dir / "run_info.txt"
    with txt_path.open("w", encoding="utf-8") as f:
        json.dump(run_info, f, ensure_ascii=False, indent=2)
    return txt_path


# ---------- CLI and logging ----------
def get_command_line_arguments():
    """
    Parse CLI arguments. These DO NOT affect core logic,
    except for the input count used for interactive prompts.
    """
    description = "Index selection main script."
    parser = ArgumentParser(description=description)
    parser.add_argument(
        "--repo_name",
        help="Repository name in gitlab. This name is used to setup logging path on some environments , e.g. Equity Rebalance",
        default=None,
    )
    parser.add_argument(
        "--calc_dates",
        help="Run calculation of event dates only. Adds dates to config/event_dates.json",
        default=None,
    )
    parser.add_argument(
        "--current_compo_source",
        help="Specify which source should be used to get data if the data is not available in the platform. Options: 'default', 'manual_input', 'no_source'. "
             "Use 'default' or specify nothing if default source should be used. Use 'manual_input' if the data is provided via excel input. 'no_source' only relevant for product development.",
        default="default",
    )
    # Extra arg ONLY for controlling the number of interactive inputs (0..3).
    parser.add_argument(
        "--input-count",
        type=int,
        default=0,
        help="Number of interactive inputs to request (0-3). Default is 0.",
    )
    args = parser.parse_args()
    return args


def setup_logging(log_dir: Path) -> Tuple[logging.Logger, Path]:
    """Configure logging to console and to a timestamped file located in log_dir."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"make_report_{datetime.now():%Y%m%d_%H%M%S}.log"

    logger = logging.getLogger("make_report")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger, log_path


# ---------- Interactive inputs (separate from argparse) ----------
def ask_user_inputs(n: int, logger: logging.Logger) -> List[str]:
    """Ask the user for n inputs (0..3). Print and log each value."""
    # Clamp to [0, 3]
    n = max(0, min(3, n))
    collected: List[str] = []

    if n == 0:
        print("[print] no interactive inputs requested")
        logger.info("no interactive inputs requested")
        return collected

    for i in range(1, n + 1):
        val = input(f"Enter value {i}/{n}: ")
        collected.append(val)
        print(f"[print] input_{i} = {val}")
        logger.info("input_%d = %s", i, val)

    return collected


# ---------- Main ----------
def main():
    # Parse CLI (only input-count affects interactive prompts)
    args = get_command_line_arguments()

    # Prepare output dir and logging
    out_dir = resolve_output_dir()
    logger, log_path = setup_logging(out_dir)

    print(f"[print] make_report.py started. Log file: {log_path}")
    logger.info("make_report.py started. Log file at %s", log_path)

    # Interactive prompts controlled SOLELY by --input-count
    requested = args.input_count if isinstance(args.input_count, int) else 0
    inputs_captured = ask_user_inputs(requested, logger)

    # Core functionality
    df = build_dataframe()
    excel_path = save_excel(df, out_dir)

    run_info = collect_run_info()
    # Optionally enrich run_info with what happened during this run
    run_info.update(
        {
            "interactive_inputs": {
                "requested": int(requested),
                "captured": inputs_captured,
            },
            "outputs": {
                "excel_path": str(excel_path),
                "log_path": str(log_path),
                "out_dir": str(out_dir),
            },
        }
    )
    txt_path = save_run_info_txt(run_info, out_dir)

    # Final prints
    print(f"[print] Excel saved to: {excel_path}")
    print(f"[print] Run info saved to: {txt_path}")
    logger.info("Excel saved to: %s", excel_path)
    logger.info("Run info saved to: %s", txt_path)

    print("[print] done.")
    logger.info("done.")


if __name__ == "__main__":
    main()

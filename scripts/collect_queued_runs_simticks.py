#!/usr/bin/env python3
"""
Scan gem5 runlog directories for stats.txt, read simTicks, and write a pivoted CSV:
  - columns: first column is the run configuration (y-axis), then each test name (x-axis)
  - rows: one per distinct steer / variant combo (y-axis)
  - cell values: simTicks (empty if missing / incomplete stats)
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def _split_icd_suffix(name: str) -> tuple[str, str]:
    """Split trailing _ICD{n} from queue job folder names; return (core_name, '' or '_ICD3')."""
    m = re.search(r"_ICD(\d+)$", name)
    if not m:
        return name, ""
    return name[: m.start()], f"_ICD{m.group(1)}"


def parse_job_folder(name: str) -> tuple[str, str]:
    """
    Parse (test, row_key) from queue_gem5_jobs.py folder naming for pivoting.
    row_key groups simTicks rows (e.g. STEER_ModN_32_BASE,
    STEER_RoundRobin_1_BASE, REG_BASED_Wcw_ICD2, Wcw_ICD1).
    Inter-cluster delay tags (_ICDn) are kept so multiple sweeps do not overwrite the same cell.
    """
    core, icd_tag = _split_icd_suffix(name)

    if "_STEER_" in core:
        test, _, tail = core.partition("_STEER_")
        toks = tail.split("_")
        if len(toks) >= 4 and toks[1].isdigit():
            policy = toks[0]
            pol_gs = f"{policy}_{toks[1]}"
            rest = toks[2:]
            if len(rest) >= 2:
                test2, var_suffix = rest[0], "_".join(rest[1:])
                if test2 == test:
                    return test, f"STEER_{pol_gs}_{var_suffix}{icd_tag}"

    if "_REG_BASED_" in core:
        left, _, right = core.partition("_REG_BASED_")
        test = left
        idx = right.find("_")
        if idx == -1:
            return test, f"REG_BASED_{right}{icd_tag}"
        t2, variant = right[:idx], right[idx + 1 :]
        if t2 != test:
            return name, core + icd_tag
        return test, f"REG_BASED_{variant}{icd_tag}"

    parts = core.split("_")
    if len(parts) >= 3 and parts[0] == parts[1]:
        return parts[0], "_".join(parts[2:]) + icd_tag
    return name, core + icd_tag


def read_sim_ticks(stats_path: Path) -> str:
    try:
        with stats_path.open() as f:
            for line in f:
                if line.startswith("simTicks"):
                    fields = line.split()
                    if len(fields) >= 2:
                        return str(int(float(fields[1])))
    except OSError:
        pass
    return ""


def _icd_sort_tail(row: str) -> tuple[str, int]:
    m = re.search(r"_ICD(\d+)$", row)
    if m:
        return row[: m.start()], int(m.group(1))
    return row, 0


def row_key_sort_key(row: str) -> tuple:
    """Order rows: steer rows by policy then group size, then legacy/plain rows."""
    suf_order = {"BASE": 0, "BWifcw": 1, "Wcw": 2}

    core, icd_n = _icd_sort_tail(row)

    if core.startswith("STEER_"):
        rest = core[len("STEER_") :]
        parts = rest.split("_", 2)
        if len(parts) >= 2 and parts[1].isdigit():
            policy = parts[0]
            n = int(parts[1])
            suf = parts[2] if len(parts) > 2 else ""
            policy_order = {
                "ModN": 0,
                "RegBased": 1,
                "RoundRobin": 2,
                "ProducerLocality": 3,
                "PCLowBitHash": 4,
            }
            # Keep prior convention: larger ModN groups first, others ascending.
            n_key = -n if policy == "ModN" else n
            return (
                0,
                policy_order.get(policy, 99),
                n_key,
                suf_order.get(suf, 99),
                suf,
                icd_n,
            )
        return (0, 99, 999, suf_order.get(rest, 99), rest, icd_n)
    if core.startswith("REG_BASED_"):
        suf = core[len("REG_BASED_") :]
        return (1, suf_order.get(suf, 50), suf, icd_n)
    return (2, suf_order.get(core, 99), core, icd_n)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("/m/local1/aidanlevy03/gem5/runlogs/queued_runs"),
        help="Directory containing per-job subfolders with stats.txt",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("queued_runs_simticks.csv"),
        help="Output CSV path (pivoted: run config x test -> simTicks)",
    )
    args = parser.parse_args()

    root: Path = args.root
    if not root.is_dir():
        raise SystemExit(f"Not a directory: {root}")

    pairs: dict[tuple[str, str], str] = {}
    for stats in sorted(root.glob("**/stats.txt")):
        rel = stats.relative_to(root)
        folder = rel.parts[0] if rel.parts else ""
        test, row_key = parse_job_folder(folder)
        pairs[(test, row_key)] = read_sim_ticks(stats)

    tests = sorted({t for (t, _) in pairs})
    row_keys = sorted({rk for (_, rk) in pairs}, key=row_key_sort_key)

    fieldnames = ["variant"] + tests
    out_rows = []
    for rk in row_keys:
        row = {"variant": rk}
        for t in tests:
            row[t] = pairs.get((t, rk), "")
        out_rows.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    print(
        f"Wrote {len(out_rows)} config rows x {len(tests)} test columns -> {args.output.resolve()}"
    )


if __name__ == "__main__":
    main()

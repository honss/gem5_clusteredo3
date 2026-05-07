#!/usr/bin/env python3

import argparse
import os
import shlex
import subprocess
from pathlib import Path


def build_job_name(
    test: str,
    reg_based: bool,
    variant: str | None,
    intercluster_delay: int,
    include_delay_tag: bool,
    steer: tuple[str, int] | None = None,
    cluster_steer_pc_bit: int | None = None,
) -> str:
    parts = [test]

    if steer is not None:
        pol, gs = steer
        parts.append(f"STEER_{pol}_{gs}")
    elif reg_based:
        parts.append("REG_BASED")

    if variant is None:
        parts.append(test)
        parts.append("BASE")
    else:
        parts.append(test)
        parts.append(variant)

    if include_delay_tag:
        parts.append(f"ICD{intercluster_delay}")
    if cluster_steer_pc_bit is not None:
        parts.append(f"PCBIT{cluster_steer_pc_bit}")

    return "_".join(parts)


def resolve_ld_library_path(cli_value: str | None) -> str | None:
    """Path(s) for o3_spec_config.py --ld-library-path (guest SE loader)."""
    if cli_value and cli_value.strip():
        return cli_value.strip()
    g = os.environ.get("GEM5_LD_LIBRARY_PATH", "").strip()
    ld = os.environ.get("LD_LIBRARY_PATH", "").strip()
    if g and ld:
        return f"{g}:{ld}"
    return g or ld or None


def build_command(
    gem5_bin: str,
    config_script: str,
    outdir: Path,
    test: str,
    variant: str | None,
    reg_based: bool,
    intercluster_delay: int,
    ld_library_path: str | None,
    steer: tuple[str, int] | None = None,
    cluster_steer_group_size: int | None = None,
    cluster_steer_pc_bit: int | None = None,
) -> list[str]:
    cmd = [
        gem5_bin,
        f"--outdir={str(outdir)}",
        config_script,
    ]
    if ld_library_path:
        cmd += ["--ld-library-path", ld_library_path]
    cmd.append(f"--{test}")

    if variant is not None:
        cmd += ["--variant", variant]

    cmd += ["--intercluster-delay", str(intercluster_delay)]

    if steer is not None:
        pol, gs = steer
        cmd += ["--cluster-steer-policy", pol, "--cluster-steer-group-size", str(gs)]
    else:
        if cluster_steer_group_size is not None:
            cmd += ["--cluster-steer-group-size", str(cluster_steer_group_size)]
        if reg_based:
            cmd.append("--reg-based")
    if cluster_steer_pc_bit is not None:
        cmd += ["--cluster-steer-pc-bit", str(cluster_steer_pc_bit)]

    return cmd


def launch_detached(cmd: list[str], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    out_fp = open(output_file, "w")

    # Start detached so it behaves similarly to nohup ... & disown
    subprocess.Popen(
        cmd,
        stdout=out_fp,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )


def normalize_variants(raw_variants: list[str] | None) -> list[str | None]:
    if not raw_variants:
        return [None]

    variants: list[str | None] = []
    for item in raw_variants:
        lowered = item.strip().lower()
        if lowered in {"none", "base", "novariant", "no-variant"}:
            variants.append(None)
        else:
            variants.append(item)

    return variants


def normalize_reg_modes(mode: str) -> list[bool]:
    raw_tokens = [tok.strip().lower() for tok in mode.split(",") if tok.strip()]
    if not raw_tokens:
        raise ValueError("Unsupported reg mode: empty value")

    out: list[bool] = []
    for tok in raw_tokens:
        if tok == "both":
            out.extend([False, True])
        elif tok == "yes":
            out.append(True)
        elif tok == "no":
            out.append(False)
        else:
            raise ValueError(f"Unsupported reg mode: {tok}")

    # Keep order but deduplicate.
    seen: set[bool] = set()
    deduped: list[bool] = []
    for v in out:
        if v not in seen:
            deduped.append(v)
            seen.add(v)
    return deduped


def parse_steer_specs(raw: str | None) -> list[tuple[str, int]] | None:
    """
    Comma-separated Policy:GroupSize, e.g. 'ModN:32,RegBased:4'.
    ModN:N is pure ModN steering; RegBased:N uses reg steering with ModN-style
    fallback in groups of N when no int/float arch reg applies (gem5 cluster_assign).
    ProducerLocality:N steers consumers toward the cluster that last produced
    their sources (tiny per-arch-reg hint table); on ties / no hints, falls
    back to ModN with group size N.
    RoundRobin and PCLowBitHash accept a group size for uniform naming/CLI shape,
    but the current hardware policy ignores it.
    """
    if raw is None or not raw.strip():
        return None

    valid_policies = (
        "ModN",
        "RegBased",
        "RoundRobin",
        "PCLowBitHash",
        "ProducerLocality",
    )

    out: list[tuple[str, int]] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" not in chunk:
            raise ValueError(
                f"Invalid --steer fragment {chunk!r}; use Policy:GroupSize "
                "(e.g. ModN:32,RegBased:4,ProducerLocality:8)"
            )
        left, right = chunk.split(":", 1)
        pol = left.strip()
        if pol not in valid_policies:
            raise ValueError(
                f"Unknown steer policy {pol!r} in {chunk!r}; use one of "
                + ", ".join(valid_policies)
            )
        try:
            gs = int(right.strip())
        except ValueError as exc:
            raise ValueError(f"Invalid group size in {chunk!r}") from exc
        if gs <= 0:
            raise ValueError(f"Group size must be positive in {chunk!r}")
        out.append((pol, gs))

    if not out:
        return None

    seen: set[tuple[str, int]] = set()
    deduped: list[tuple[str, int]] = []
    for item in out:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def normalize_intercluster_delays(raw: str) -> list[int]:
    tokens = [tok.strip() for tok in raw.split(",") if tok.strip()]
    if not tokens:
        raise ValueError("inter-cluster delay list cannot be empty")

    delays: list[int] = []
    for tok in tokens:
        try:
            delay = int(tok)
        except ValueError as exc:
            raise ValueError(f"Unsupported inter-cluster delay: {tok}") from exc
        if delay < 0:
            raise ValueError(f"Unsupported inter-cluster delay: {tok} (must be >= 0)")
        delays.append(delay)

    # Keep order but deduplicate.
    seen: set[int] = set()
    deduped: list[int] = []
    for d in delays:
        if d not in seen:
            deduped.append(d)
            seen.add(d)
    return deduped


def normalize_cluster_steer_pc_bits(raw: str | None) -> list[int | None]:
    if raw is None or not raw.strip():
        return [None]
    tokens = [tok.strip() for tok in raw.split(",") if tok.strip()]
    if not tokens:
        raise ValueError("cluster steer pc-bit list cannot be empty")

    bits: list[int] = []
    for tok in tokens:
        try:
            bit = int(tok)
        except ValueError as exc:
            raise ValueError(f"Unsupported cluster steer pc bit: {tok}") from exc
        if bit < 0:
            raise ValueError(
                f"Unsupported cluster steer pc bit: {tok} (must be >= 0)"
            )
        bits.append(bit)

    seen: set[int] = set()
    deduped: list[int | None] = []
    for b in bits:
        if b not in seen:
            deduped.append(b)
            seen.add(b)
    return deduped


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Queue multiple gem5 jobs with automatic folder naming."
    )

    parser.add_argument(
        "--tests",
        nargs="+",
        required=True,
        help="List of test flags, e.g. libq lbm",
    )
    parser.add_argument(
        "--variants",
        nargs="*",
        default=["none"],
        help=(
            "List of variants. Use 'none' for no --variant option. "
            "Example: --variants none RBWifcw"
        ),
    )
    parser.add_argument(
        "--reg-based",
        default="no",
        help=(
            "Whether to add --reg-based (forces RegBased + default group size). "
            "Accepts yes/no/both and comma-separated lists (e.g. 'no,yes'). "
            "Do not combine with --steer (use --steer ModN:32,RegBased:4 instead)."
        ),
    )
    parser.add_argument(
        "--steer",
        default=None,
        help=(
            "Comma-separated cluster steer specs Policy:GroupSize for o3_spec_config.py, "
            "e.g. 'ModN:32,RegBased:4' (Mod-32 steering vs Reg-based with ModN fallback "
            "using group 4). Cannot be combined with --reg-based yes/both."
        ),
    )
    parser.add_argument(
        "--cluster-steer-group-size",
        type=int,
        default=None,
        help=(
            "Optional: pass --cluster-steer-group-size to the config for all jobs when "
            "not using --steer (e.g. with --reg-based to set fallback/group size)."
        ),
    )
    parser.add_argument(
        "--cluster-steer-pc-bit",
        type=str,
        default=None,
        help=(
            "Optional: single value or comma-separated list passed as "
            "--cluster-steer-pc-bit to o3_spec_config.py "
            "(used by PCLowBitHash as bit index X in (PC>>X)&1). "
            "Examples: '5' or '1,2,3,4'."
        ),
    )
    parser.add_argument(
        "--intercluster-delay",
        default="3",
        help=(
            "Single value or comma-separated list for --intercluster-delay passed "
            "to o3_spec_config.py (e.g. '3' or '1,3,5')."
        ),
    )
    parser.add_argument(
        "--iteration",
        required=True,
        help="Top-level output folder name, e.g. iteration3",
    )
    parser.add_argument(
        "--runlogs-root",
        default="runlogs",
        help="Root folder for outputs. Default: runlogs",
    )
    parser.add_argument(
        "--gem5-bin",
        default="./build/X86/gem5.opt",
        help="Path to gem5 binary",
    )
    parser.add_argument(
        "--config",
        default="configs/o3_spec_config.py",
        help="Path to config script",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without launching them",
    )
    parser.add_argument(
        "--ld-library-path",
        default=None,
        help=(
            "Passed through to configs/o3_spec_config.py as --ld-library-path for "
            "guest dynamic linking (e.g. libgfortran). If omitted, uses "
            "GEM5_LD_LIBRARY_PATH and/or LD_LIBRARY_PATH from the environment."
        ),
    )

    args = parser.parse_args()

    variants = normalize_variants(args.variants)
    reg_modes = normalize_reg_modes(args.reg_based)
    steer_specs = parse_steer_specs(args.steer)
    if steer_specs is not None and any(reg_modes):
        raise SystemExit(
            "Do not combine --steer with --reg-based yes/both. "
            "Example: --steer ModN:32,RegBased:4 --reg-based no"
        )
    intercluster_delays = normalize_intercluster_delays(args.intercluster_delay)
    cluster_steer_pc_bits = normalize_cluster_steer_pc_bits(args.cluster_steer_pc_bit)
    ld_path = resolve_ld_library_path(args.ld_library_path)
    include_delay_tag = len(intercluster_delays) > 1 or intercluster_delays[0] != 3

    jobs = []

    for test in args.tests:
        if steer_specs is not None:
            steer_iter: list[tuple[str, int] | None] = list(steer_specs)
        else:
            steer_iter = [None]
        for steer in steer_iter:
            for reg_based in reg_modes:
                if steer is not None and reg_based:
                    continue
                for variant in variants:
                    for intercluster_delay in intercluster_delays:
                        for cluster_steer_pc_bit in cluster_steer_pc_bits:
                            job_name = build_job_name(
                                test,
                                reg_based,
                                variant,
                                intercluster_delay,
                                include_delay_tag,
                                steer=steer,
                                cluster_steer_pc_bit=cluster_steer_pc_bit,
                            )
                            outdir = Path(args.runlogs_root) / args.iteration / job_name
                            output_file = outdir / "output"

                            cmd = build_command(
                                gem5_bin=args.gem5_bin,
                                config_script=args.config,
                                outdir=outdir,
                                test=test,
                                variant=variant,
                                reg_based=reg_based,
                                intercluster_delay=intercluster_delay,
                                ld_library_path=ld_path,
                                steer=steer,
                                cluster_steer_group_size=args.cluster_steer_group_size,
                                cluster_steer_pc_bit=cluster_steer_pc_bit,
                            )

                            jobs.append((job_name, outdir, output_file, cmd))

    print(f"Prepared {len(jobs)} job(s):\n")

    for job_name, outdir, output_file, cmd in jobs:
        print(f"[{job_name}]")
        print(f"  outdir : {outdir}")
        print(f"  output : {output_file}")
        print(f"  cmd    : {' '.join(shlex.quote(x) for x in cmd)}")
        print()

    if args.dry_run:
        print("Dry run only, nothing launched.")
        return

    for job_name, _, output_file, cmd in jobs:
        launch_detached(cmd, output_file)
        print(f"Launched: {job_name}")

    print("\nAll jobs queued.")


if __name__ == "__main__":
    main()
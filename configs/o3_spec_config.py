# Copyright (c) 2025
# O3 CPU config matching the specification table (Seznec/Michaud-style processor).
# Run from project root: build/X86/gem5.opt configs/o3_spec_config.py -c <binary>
# Clustered mode: two IQs, ModN steering, interclusterDelay=3; trace with --debug-flags=ClusterCheck
#
# Spec summary:
#   clock 3.5GHz | BP: 31KB TAGE + 6KB ITTAGE | fetch: 1 line, 1 taken/cycle
#   decode 8 | rename 12 | issue 4 INT, 2 FP, 3 addr, 2 store | retire 12
#   ROB 256 | phys regs 128 INT, 128 FP | IQ 60 INT, 60 FP | LQ 72, SQ 42
#   branch misp penalty 12 | cache line 64B | MSHRs 32
#   DL1: 32KB 8-way 3cy | IL1: 32KB 8-way | L2: 512KB 8-way 11cy
#   L3: 8MB 16-way 21cy | mem: 245cy fixed, 16 B/cy | prefetchers: stride L1, stream L2/L3
#   store sets: SSIT 2k 4-way, LFST 42

import os
import m5
import argparse
from m5.objects import *
from m5.util import addToPath

addToPath(os.path.dirname(os.path.abspath(__file__)))
from common.Caches import L1_ICache, L1_DCache, L2Cache

# Path to binary (project root)
_config_dir = os.path.dirname(os.path.abspath(__file__))
PROJ_ROOT = os.path.dirname(_config_dir)

# =============================================================================
# Table IV: doubling options (cluster-safe subset supported)
#   - B: double issue-queue capacity (applied per cluster IQ)
#   - W: double window-ish structures (ROB/LQ/SQ/LFST + L1D MSHRs)
#   - c: double load/store issue pressure (DL1 load/store ports + mem FU ports)
#   - w: double front-end widths (fetch/decode/rename/dispatch/commit + taken/cycle)
#   - i/f: double INT/FP execution ports (FU counts)
#   - R: ignored here (phys regs already set explicitly for this design)
# =============================================================================
_preparser = argparse.ArgumentParser(add_help=False)
_preparser.add_argument(
    "--variant",
    default="",
    type=str,
    help="Subset of Table IV symbols to double (e.g. 'BWcfw').",
)
_preparser.add_argument(
    "--double-params",
    default=None,
    type=str,
    help="Alias for --variant.",
)
_pre_args, _pre_unknown = _preparser.parse_known_args()
_VARIANT = (_pre_args.double_params if _pre_args.double_params else _pre_args.variant).replace(" ", "")

_R_MULT = 2 if "R" in _VARIANT else 1
_B_MULT = 2 if "B" in _VARIANT else 1
_W_MULT = 2 if "W" in _VARIANT else 1
_FE_MULT = 2 if "w" in _VARIANT else 1
_LOAD_ISSUE_MULT = 2 if "c" in _VARIANT else 1
_INT_EXEC_MULT = 2 if ("i" in _VARIANT or "I" in _VARIANT) else 1
_FP_EXEC_MULT = 2 if ("f" in _VARIANT or "F" in _VARIANT) else 1

# O3 core has a compile-time width cap (see src/cpu/o3/limits.hh).
_O3_MAX_WIDTH = 32

# =============================================================================
# Spec parameters
# =============================================================================
SYS_CLOCK = "3.5GHz"
CPU_CLOCK = "3.5GHz"
SYS_VOLT = "1.0V"
CACHELINE = 64
MEM_SIZE = "512MiB"

# O3 pipeline
FETCH_WIDTH = 16          # ~1 cache line (64B) of instructions
FETCH_BUFFER_SIZE = 64
MAX_TAKEN_PRED_PER_CYCLE = 1
DECODE_WIDTH = 8
RENAME_WIDTH = 12
DISPATCH_WIDTH = 12
COMMIT_WIDTH = 12
NUM_ROB_ENTRIES = 256
TRAP_LATENCY = 12         # branch misprediction penalty (min)

# Physical registers
NUM_PHYS_INT_REGS = 128 * _R_MULT
NUM_PHYS_FP_REGS = 128 * _R_MULT

# Queues
LQ_ENTRIES = 72
SQ_ENTRIES = 42
NUM_IQ_ENTRIES = 60       # per-type; gem5 uses unified IQ, total ~120

# Cache ports (2 reads, 1 write per cycle for DL1)
CACHE_LOAD_PORTS = 2
CACHE_STORE_PORTS = 1

# Cache MSHR merge fan-in (targets per MSHR). If this is too small, more
# aggressive cores can hit "blockedCycles::no_targets" even when mshrs is large.
L1D_TGTS_PER_MSHR = 8
L2_TGTS_PER_MSHR = 12
L3_TGTS_PER_MSHR = 12

# Store sets
SSIT_SIZE = "2048"
SSIT_ASSOC = 4
LFST_SIZE = 42

# Caches
L1I_SIZE = "32KiB"
L1I_ASSOC = 8
L1D_SIZE = "32KiB"
L1D_ASSOC = 8
L1D_LATENCY = 3
L1D_MSHRS = 32
L2_SIZE = "512KiB"
L2_ASSOC = 8
L2_LATENCY = 11
L2_MSHRS = 32
L3_SIZE = "8MiB"
L3_ASSOC = 16
L3_LATENCY = 21
L3_MSHRS = 32

# Apply supported doubling multipliers to the base parameter set.
# NOTE: We intentionally ignore R here; phys regs are explicitly set above.
NUM_ROB_ENTRIES *= _W_MULT
LQ_ENTRIES *= _W_MULT
SQ_ENTRIES *= _W_MULT
LFST_SIZE *= _W_MULT
L1D_MSHRS *= _W_MULT

CACHE_LOAD_PORTS *= _LOAD_ISSUE_MULT
CACHE_STORE_PORTS *= _LOAD_ISSUE_MULT

FETCH_WIDTH *= _FE_MULT
DECODE_WIDTH *= _FE_MULT
RENAME_WIDTH *= _FE_MULT
DISPATCH_WIDTH *= _FE_MULT
COMMIT_WIDTH *= _FE_MULT
MAX_TAKEN_PRED_PER_CYCLE *= _FE_MULT

# Clustered O3 has one IQ per cluster; "B" doubles per-cluster capacity.
IQ_ENTRIES_PER_CLUSTER = NUM_IQ_ENTRIES * _B_MULT

# Scale overall issue/writeback widths with the increased execution/load capability.
# Baseline is 11 total issue ports (4 INT, 2 FP, 3 addr, 2 store).
ISSUE_WIDTH = 11 * max(1, _INT_EXEC_MULT, _FP_EXEC_MULT, _LOAD_ISSUE_MULT)
WB_WIDTH = ISSUE_WIDTH
FORWARD_COM_SIZE = 5 * max(1, _W_MULT, _LOAD_ISSUE_MULT)

# Clamp any width-like params to the compiled MaxWidth to avoid fatal errors.
FETCH_WIDTH = min(FETCH_WIDTH, _O3_MAX_WIDTH)
DECODE_WIDTH = min(DECODE_WIDTH, _O3_MAX_WIDTH)
RENAME_WIDTH = min(RENAME_WIDTH, _O3_MAX_WIDTH)
DISPATCH_WIDTH = min(DISPATCH_WIDTH, _O3_MAX_WIDTH)
COMMIT_WIDTH = min(COMMIT_WIDTH, _O3_MAX_WIDTH)
ISSUE_WIDTH = min(ISSUE_WIDTH, _O3_MAX_WIDTH)
WB_WIDTH = min(WB_WIDTH, _O3_MAX_WIDTH)

# Scale MSHR merge fan-in with the pressure sources we explicitly increase
# (window size and load issue capability).
_MSHR_TARGETS_MULT = max(1, _W_MULT * _LOAD_ISSUE_MULT)
L1D_TGTS_PER_MSHR *= _MSHR_TARGETS_MULT
L2_TGTS_PER_MSHR *= _MSHR_TARGETS_MULT
L3_TGTS_PER_MSHR *= _MSHR_TARGETS_MULT

# Memory: 245 cycles @ 3.5GHz = 70ns, 16 B/cy = 56 GB/s
MEM_LATENCY = "70ns"
MEM_BANDWIDTH = "56GiB/s"

# =============================================================================
# Custom FUPool: 4 INT, 2 FP, 3 address, 2 store data (cf. Figure 3)
# =============================================================================
class SpecIntALU(FUDesc):
    opList = [OpDesc(opClass="IntAlu")]
    count = 4

class SpecIntMultDiv(FUDesc):
    opList = [
        OpDesc(opClass="IntMult", opLat=3),
        OpDesc(opClass="IntDiv", opLat=20, pipelined=False),
    ]
    count = 2

class SpecFP_ALU(FUDesc):
    opList = [
        OpDesc(opClass="FloatAdd", opLat=2),
        OpDesc(opClass="FloatCmp", opLat=2),
        OpDesc(opClass="FloatCvt", opLat=2),
        OpDesc(opClass="Bf16Cvt", opLat=2),
    ]
    count = 2

class SpecFP_MultDiv(FUDesc):
    opList = [
        OpDesc(opClass="FloatMult", opLat=4),
        OpDesc(opClass="FloatMultAcc", opLat=5),
        OpDesc(opClass="FloatMisc", opLat=3),
        OpDesc(opClass="FloatDiv", opLat=12, pipelined=False),
        OpDesc(opClass="FloatSqrt", opLat=24, pipelined=False),
    ]
    count = 2

class SpecReadPort(FUDesc):
    opList = [
        OpDesc(opClass="MemRead"),
        OpDesc(opClass="FloatMemRead"),
        OpDesc(opClass="SimdUnitStrideLoad"),
        OpDesc(opClass="SimdUnitStrideMaskLoad"),
        OpDesc(opClass="SimdUnitStrideSegmentedLoad"),
        OpDesc(opClass="SimdStridedLoad"),
        OpDesc(opClass="SimdIndexedLoad"),
        OpDesc(opClass="SimdUnitStrideFaultOnlyFirstLoad"),
        OpDesc(opClass="SimdUnitStrideSegmentedFaultOnlyFirstLoad"),
        OpDesc(opClass="SimdWholeRegisterLoad"),
        OpDesc(opClass="SimdStrideSegmentedLoad"),
    ]
    count = 2  # 2 loads/cycle

class SpecWritePort(FUDesc):
    opList = [
        OpDesc(opClass="MemWrite"),
        OpDesc(opClass="FloatMemWrite"),
        OpDesc(opClass="SimdUnitStrideStore"),
        OpDesc(opClass="SimdUnitStrideMaskStore"),
        OpDesc(opClass="SimdUnitStrideSegmentedStore"),
        OpDesc(opClass="SimdStridedStore"),
        OpDesc(opClass="SimdIndexedStore"),
        OpDesc(opClass="SimdWholeRegisterStore"),
        OpDesc(opClass="SimdStrideSegmentedStore"),
    ]
    count = 2  # 2 store data

# Apply supported doubling to selected FU counts.
if _INT_EXEC_MULT != 1:
    SpecIntALU.count *= _INT_EXEC_MULT
    SpecIntMultDiv.count *= _INT_EXEC_MULT

if _FP_EXEC_MULT != 1:
    SpecFP_ALU.count *= _FP_EXEC_MULT
    SpecFP_MultDiv.count *= _FP_EXEC_MULT

if _LOAD_ISSUE_MULT != 1:
    SpecReadPort.count *= _LOAD_ISSUE_MULT
    SpecWritePort.count *= _LOAD_ISSUE_MULT

class SpecFUPool(FUPool):
    FUList = [
        SpecIntALU(),
        SpecIntMultDiv(),
        SpecFP_ALU(),
        SpecFP_MultDiv(),
        SpecReadPort(),
        SIMD_Unit(),
        Matrix_Unit(),
        System_Unit(),
        PredALU(),
        SpecWritePort(),
    ]

# =============================================================================
# Custom caches with prefetchers
# =============================================================================
class SpecL1_ICache(L1_ICache):
    size = L1I_SIZE
    assoc = L1I_ASSOC
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    prefetcher = StridePrefetcher(on_inst=True)

class SpecL1_DCache(L1_DCache):
    size = L1D_SIZE
    assoc = L1D_ASSOC
    tag_latency = L1D_LATENCY
    data_latency = L1D_LATENCY
    response_latency = L1D_LATENCY
    mshrs = L1D_MSHRS
    tgts_per_mshr = L1D_TGTS_PER_MSHR
    prefetcher = StridePrefetcher(on_inst=False)

class SpecL2Cache(L2Cache):
    size = L2_SIZE
    assoc = L2_ASSOC
    tag_latency = L2_LATENCY
    data_latency = L2_LATENCY
    response_latency = L2_LATENCY
    mshrs = L2_MSHRS
    tgts_per_mshr = L2_TGTS_PER_MSHR
    write_buffers = 8
    prefetcher = TaggedPrefetcher(degree=2)

class SpecL3Cache(Cache):
    size = L3_SIZE
    assoc = L3_ASSOC
    tag_latency = L3_LATENCY
    data_latency = L3_LATENCY
    response_latency = L3_LATENCY
    mshrs = L3_MSHRS
    tgts_per_mshr = L3_TGTS_PER_MSHR
    write_buffers = 16
    prefetcher = TaggedPrefetcher(degree=2)

# =============================================================================
# Branch predictor: 31KB TAGE + 6KB ITTAGE (Seznec & Michaud 2006)
# gem5 has TAGE_SC_L_64KB (closest to 31KB TAGE) and SimpleIndirectPredictor
# =============================================================================
def make_branch_predictor():
    return BranchPredictor(
        conditionalBranchPred=TAGE_SC_L_64KB(),
        indirectBranchPred=SimpleIndirectPredictor(
            indirectSets=512,   # power-of-2, ~6KB with 2 ways
            indirectWays=2,
            indirectTagSize=16,
        ),
        btb=SimpleBTB(numEntries=4096, associativity=4),
    )

# =============================================================================
# System
# =============================================================================
system = System(
    cpu=[
        DerivO3CPU(
            cpu_id=0,
            fetchWidth=FETCH_WIDTH,
            fetchBufferSize=FETCH_BUFFER_SIZE,
            maxTakenPredPerCycle=MAX_TAKEN_PRED_PER_CYCLE,
            decodeWidth=DECODE_WIDTH,
            renameWidth=RENAME_WIDTH,
            dispatchWidth=DISPATCH_WIDTH,
            issueWidth=ISSUE_WIDTH,
            wbWidth=WB_WIDTH,
            commitWidth=COMMIT_WIDTH,
            forwardComSize=FORWARD_COM_SIZE,
            numROBEntries=NUM_ROB_ENTRIES,
            trapLatency=TRAP_LATENCY,
            numPhysIntRegs=NUM_PHYS_INT_REGS,
            numPhysFloatRegs=NUM_PHYS_FP_REGS,
            LQEntries=LQ_ENTRIES,
            SQEntries=SQ_ENTRIES,
            cacheLoadPorts=CACHE_LOAD_PORTS,
            cacheStorePorts=CACHE_STORE_PORTS,
            SSITSize=SSIT_SIZE,
            SSITAssoc=SSIT_ASSOC,
            LFSTSize=LFST_SIZE,
            branchPred=make_branch_predictor(),
            # Clustered O3: two IQs (60 entries each), ModN steering, cross-cluster delay
            instQueues=[
                IQUnit(numEntries=IQ_ENTRIES_PER_CLUSTER, fuPool=SpecFUPool()),
                IQUnit(numEntries=IQ_ENTRIES_PER_CLUSTER, fuPool=SpecFUPool()),
            ],
            clusterSteerPolicy="RegBased",
            clusterSteerGroupSize=8,
            interclusterDelay=3,
        )
    ],
    mem_mode="timing",
    mem_ranges=[AddrRange(MEM_SIZE)],
    cache_line_size=CACHELINE,
)

system.voltage_domain = VoltageDomain(voltage=SYS_VOLT)
system.clk_domain = SrcClockDomain(
    clock=SYS_CLOCK, voltage_domain=system.voltage_domain
)
system.cpu_voltage_domain = VoltageDomain()
system.cpu_clk_domain = SrcClockDomain(
    clock=CPU_CLOCK, voltage_domain=system.cpu_voltage_domain
)
for cpu in system.cpu:
    cpu.clk_domain = system.cpu_clk_domain

# Buses and caches
system.membus = SystemXBar()
system.system_port = system.membus.cpu_side_ports
system.l2bus = L2XBar()
system.l3bus = L2XBar()

system.l2cache = SpecL2Cache()
system.l2cache.cpu_side = system.l2bus.mem_side_ports
system.l2cache.mem_side = system.l3bus.cpu_side_ports

system.l3cache = SpecL3Cache()
system.l3cache.cpu_side = system.l3bus.mem_side_ports
system.l3cache.mem_side = system.membus.cpu_side_ports

for cpu in system.cpu:
    cpu.icache = SpecL1_ICache()
    cpu.dcache = SpecL1_DCache()
    cpu.icache_port = cpu.icache.cpu_side
    cpu.dcache_port = cpu.dcache.cpu_side
    cpu.icache.mem_side = system.l2bus.cpu_side_ports
    cpu.dcache.mem_side = system.l2bus.cpu_side_ports

# Memory: fixed latency 245 cycles, 16 B/cycle
system.mem_ctrl = SimpleMemory(
    latency=MEM_LATENCY,
    bandwidth=MEM_BANDWIDTH,
)
system.mem_ctrl.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Workload: use tiny by default, override with -c; use --args for program arguments
TINY_BIN = os.path.join(PROJ_ROOT, "tiny")
# Mini "LBM-like" microbenchmark (kept in-tree under tests/test-progs)
MINI_LBM_BIN = os.path.join(PROJ_ROOT, "tests", "test-progs", "mini_lbm", "bin", "x86", "mini_lbm")
# Defaults tuned to be ~tens of millions of instructions (use --maxinsts for exact caps).
MINI_LBM_DEFAULT_N = 16384
MINI_LBM_DEFAULT_ITERS = 4
MINI_LBM_DEFAULT_SEED = 1
# SPEC 470.lbm: run_base_test_void-gcc.0001 with args "20 reference.dat 0 1 100_100_130_cf_a.of"
LBM_DIR = os.environ.get(
    "SPEC2006_LBM_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/470.lbm/run/run_base_test_void-gcc.0001",
)
LBM_BIN = os.path.join(LBM_DIR, "lbm_base.void-gcc")
LBM_CMD = [LBM_BIN, "20", "reference.dat", "0", "1", "100_100_130_cf_a.of"]

# SPEC 462.libquantum: run_base_test_void-gcc.0000 with args "33 5"
LIBQUANTUM_DIR = os.environ.get(
    "SPEC2006_LIBQUANTUM_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/462.libquantum/run/run_base_test_void-gcc.0000",
)
LIBQUANTUM_BIN = os.path.join(LIBQUANTUM_DIR, "libquantum_base.void-gcc")
LIBQUANTUM_CMD = [LIBQUANTUM_BIN, "33", "5"]


import argparse
_parser = argparse.ArgumentParser()
_parser.add_argument("-c", "--cmd", default=None, help="Binary to run (default: tiny)")
_parser.add_argument(
    "--args",
    type=str,
    default=None,
    help='Arguments to the binary, space-separated (e.g. "20 reference.dat 0 1 100_100_130_cf_a.of")',
)
_parser.add_argument(
    "--cwd",
    type=str,
    default=None,
    help="Working directory for the process (default: directory of the binary)",
)
_parser.add_argument(
    "--lbm",
    action="store_true",
    help="Run SPEC 470.lbm: lbm_base.void-gcc 20 reference.dat 0 1 100_100_130_cf_a.of",
)
_parser.add_argument(
    "--libq",
    action="store_true",
    help="Run SPEC 470.libquantum: libquantum_base.void-gcc 33 5",
)
_parser.add_argument(
    "--mini-lbm",
    action="store_true",
    help="Run in-tree mini LBM-like microbenchmark (tests/test-progs/mini_lbm)",
)
_parser.add_argument("--mini-n", type=int, default=MINI_LBM_DEFAULT_N, help="mini_lbm: number of cells (-n)")
_parser.add_argument("--mini-iters", type=int, default=MINI_LBM_DEFAULT_ITERS, help="mini_lbm: iterations (-i)")
_parser.add_argument("--mini-seed", type=int, default=MINI_LBM_DEFAULT_SEED, help="mini_lbm: seed (-s)")
_parser.add_argument("--mini-verbose", action="store_true", help="mini_lbm: print per-iter progress (omit -q)")
_args, _ = _parser.parse_known_args()

if _args.mini_lbm:
    binary = MINI_LBM_BIN
    cmd_args = [
        "-n",
        str(_args.mini_n),
        "-i",
        str(_args.mini_iters),
        "-s",
        str(_args.mini_seed),
    ]
    if not _args.mini_verbose:
        cmd_args.append("-q")
    process_cwd = os.path.dirname(os.path.abspath(binary)) or "/"
    if not os.path.exists(binary):
        raise SystemExit(
            f"mini_lbm binary not found: {binary} (build it with: "
            f"make -C {os.path.join(PROJ_ROOT, 'tests', 'test-progs', 'mini_lbm', 'src')} -f Makefile.x86)"
        )
elif _args.lbm:
    binary = LBM_BIN
    cmd_args = LBM_CMD[1:]  # executable already in LBM_CMD[0]
    process_cwd = LBM_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"LBM binary not found: {binary} (set SPEC2006_LBM_DIR?)")
elif _args.libq:
    binary = LIBQUANTUM_BIN
    cmd_args = LIBQUANTUM_CMD[1:]  # executable already in LBM_CMD[0]
    process_cwd = LIBQUANTUM_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"libquantum binary not found: {binary} (set SPEC2006_LIBQUANTUM_DIR?)")	
elif _args.cmd is not None:
    binary = _args.cmd
    cmd_args = _args.args.split() if _args.args else []
    process_cwd = _args.cwd or os.path.dirname(os.path.abspath(binary)) or "/"
    if not os.path.exists(binary):
        binary = TINY_BIN
        cmd_args = []
        process_cwd = os.path.dirname(os.path.abspath(binary)) or "/"
else:
    binary = TINY_BIN
    cmd_args = []
    process_cwd = os.path.dirname(os.path.abspath(binary)) or "/"

process = Process(pid=100)
process.executable = binary
process.cwd = process_cwd
process.gid = os.getgid()
process.cmd = [binary] + cmd_args

system.workload = SEWorkload.init_compatible(binary)
for cpu in system.cpu:
    cpu.workload = process
    cpu.createInterruptController()
    cpu.interrupts[0].pio = system.membus.mem_side_ports
    cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    cpu.interrupts[0].int_responder = system.membus.mem_side_ports
    cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print("O3 spec config: running", " ".join(process.cmd))
exit_event = m5.simulate()
print("Exited @ tick", m5.curTick(), "because", exit_event.getCause())

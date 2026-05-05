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
            clusterSteerPCBit=2,
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

# SPEC 400.perlbench: run_base_test_void-gcc.0001
PERLBENCH_DIR = os.environ.get(
    "SPEC2006_PERLBENCH_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/400.perlbench/run/run_base_test_void-gcc.0001",
)
PERLBENCH_BIN = os.path.join(PERLBENCH_DIR, "perlbench_base.void-gcc")
PERLBENCH_CMD = [PERLBENCH_BIN, "-I.", "-I./lib", "test.pl"]

# SPEC 401.bzip2: run_base_test_void-gcc.0001
BZIP2_DIR = os.environ.get(
    "SPEC2006_BZIP2_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/401.bzip2/run/run_base_test_void-gcc.0001",
)
BZIP2_BIN = os.path.join(BZIP2_DIR, "bzip2_base.void-gcc")
BZIP2_CMD = [BZIP2_BIN, "dryer.jpg", "2"]

# SPEC 429.mcf: run_base_test_void-gcc.0001
MCF_DIR = os.environ.get(
    "SPEC2006_MCF_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/429.mcf/run/run_base_test_void-gcc.0001",
)
MCF_BIN = os.path.join(MCF_DIR, "mcf_base.void-gcc")
MCF_CMD = [MCF_BIN, "inp.in"]

# SPEC 445.gobmk: run_base_test_void-gcc.0001
GOBMK_DIR = os.environ.get(
    "SPEC2006_GOBMK_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/445.gobmk/run/run_base_test_void-gcc.0001",
)
GOBMK_BIN = os.path.join(GOBMK_DIR, "gobmk_base.void-gcc")
GOBMK_CMD = [GOBMK_BIN, "--quiet", "--mode", "gtp"]

# SPEC 456.hmmer: run_base_test_void-gcc.0001
HMMER_DIR = os.environ.get(
    "SPEC2006_HMMER_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/456.hmmer/run/run_base_test_void-gcc.0001",
)
HMMER_BIN = os.path.join(HMMER_DIR, "hmmer_base.void-gcc")
HMMER_CMD = [
    HMMER_BIN,
    "--fixed",
    "0",
    "--mean",
    "325",
    "--num",
    "45000",
    "--sd",
    "200",
    "--seed",
    "0",
    "bombesin.hmm",
]

# SPEC 458.sjeng: run_base_test_void-gcc.0001
SJENG_DIR = os.environ.get(
    "SPEC2006_SJENG_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/458.sjeng/run/run_base_test_void-gcc.0001",
)
SJENG_BIN = os.path.join(SJENG_DIR, "sjeng_base.void-gcc")
SJENG_CMD = [SJENG_BIN, "test.txt"]

# SPEC 464.h264ref: run_base_test_void-gcc.0001
H264REF_DIR = os.environ.get(
    "SPEC2006_H264REF_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/464.h264ref/run/run_base_test_void-gcc.0001",
)
H264REF_BIN = os.path.join(H264REF_DIR, "h264ref_base.void-gcc")
H264REF_CMD = [H264REF_BIN, "-d", "foreman_test_encoder_baseline.cfg"]

# SPEC 471.omnetpp: run_base_test_void-gcc.0001
OMNETPP_DIR = os.environ.get(
    "SPEC2006_OMNETPP_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/471.omnetpp/run/run_base_test_void-gcc.0001",
)
OMNETPP_BIN = os.path.join(OMNETPP_DIR, "omnetpp_base.void-gcc")
OMNETPP_CMD = [OMNETPP_BIN, "omnetpp.ini"]

# SPEC 473.astar: run_base_test_void-gcc.0001
ASTAR_DIR = os.environ.get(
    "SPEC2006_ASTAR_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/473.astar/run/run_base_test_void-gcc.0001",
)
ASTAR_BIN = os.path.join(ASTAR_DIR, "astar_base.void-gcc")
ASTAR_CMD = [ASTAR_BIN, "lake.cfg"]

# --- run_base_test_void-gcc.0004 (FP / extra CPU2006 test workloads) ---
# SPEC 410.bwaves
BWAVES_DIR = os.environ.get(
    "SPEC2006_BWAVES_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/410.bwaves/run/run_base_test_void-gcc.0004",
)
BWAVES_BIN = os.path.join(BWAVES_DIR, "bwaves_base.void-gcc")
BWAVES_CMD = [BWAVES_BIN]

# SPEC 434.zeusmp
ZEUSMP_DIR = os.environ.get(
    "SPEC2006_ZEUSMP_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/434.zeusmp/run/run_base_test_void-gcc.0004",
)
ZEUSMP_BIN = os.path.join(ZEUSMP_DIR, "zeusmp_base.void-gcc")
ZEUSMP_CMD = [ZEUSMP_BIN]

# SPEC 435.gromacs
GROMACS_DIR = os.environ.get(
    "SPEC2006_GROMACS_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/435.gromacs/run/run_base_test_void-gcc.0004",
)
GROMACS_BIN = os.path.join(GROMACS_DIR, "gromacs_base.void-gcc")
GROMACS_CMD = [GROMACS_BIN, "-silent", "-deffnm", "gromacs", "-nice", "0"]

# SPEC 436.cactusADM
CACTUSADM_DIR = os.environ.get(
    "SPEC2006_CACTUSADM_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/436.cactusADM/run/run_base_test_void-gcc.0004",
)
CACTUSADM_BIN = os.path.join(CACTUSADM_DIR, "cactusADM_base.void-gcc")
CACTUSADM_CMD = [CACTUSADM_BIN, "benchADM.par"]

# SPEC 444.namd
NAMD_DIR = os.environ.get(
    "SPEC2006_NAMD_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/444.namd/run/run_base_test_void-gcc.0004",
)
NAMD_BIN = os.path.join(NAMD_DIR, "namd_base.void-gcc")
NAMD_CMD = [NAMD_BIN, "--input", "namd.input", "--iterations", "1", "--output", "namd.out"]

# SPEC 453.povray
POVRAY_DIR = os.environ.get(
    "SPEC2006_POVRAY_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/453.povray/run/run_base_test_void-gcc.0004",
)
POVRAY_BIN = os.path.join(POVRAY_DIR, "povray_base.void-gcc")
POVRAY_CMD = [POVRAY_BIN, "SPEC-benchmark-test.ini"]

# SPEC 459.GemsFDTD
GEMSFDTD_DIR = os.environ.get(
    "SPEC2006_GEMSFDTD_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/459.GemsFDTD/run/run_base_test_void-gcc.0004",
)
GEMSFDTD_BIN = os.path.join(GEMSFDTD_DIR, "GemsFDTD_base.void-gcc")
GEMSFDTD_CMD = [GEMSFDTD_BIN]

# SPEC 465.tonto
TONTO_DIR = os.environ.get(
    "SPEC2006_TONTO_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/465.tonto/run/run_base_test_void-gcc.0004",
)
TONTO_BIN = os.path.join(TONTO_DIR, "tonto_base.void-gcc")
TONTO_CMD = [TONTO_BIN]

# SPEC 482.sphinx3
SPHINX3_DIR = os.environ.get(
    "SPEC2006_SPHINX3_DIR",
    "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/482.sphinx3/run/run_base_test_void-gcc.0004",
)
SPHINX3_BIN = os.path.join(SPHINX3_DIR, "sphinx_livepretend_base.void-gcc")
SPHINX3_CMD = [SPHINX3_BIN, "ctlfile", ".", "args.an4"]


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
    help="Run SPEC 462.libquantum: libquantum_base.void-gcc 33 5",
)
_parser.add_argument("--perlbench", action="store_true", help="Run SPEC 400.perlbench: perlbench_base.void-gcc -I. -I./lib test.pl")
_parser.add_argument("--bzip2", action="store_true", help="Run SPEC 401.bzip2: bzip2_base.void-gcc dryer.jpg 2")
_parser.add_argument("--mcf", action="store_true", help="Run SPEC 429.mcf: mcf_base.void-gcc inp.in")
_parser.add_argument("--gobmk", action="store_true", help="Run SPEC 445.gobmk: gobmk_base.void-gcc --quiet --mode gtp")
_parser.add_argument(
    "--hmmer",
    action="store_true",
    help="Run SPEC 456.hmmer: hmmer_base.void-gcc --fixed 0 --mean 325 --num 45000 --sd 200 --seed 0 bombesin.hmm",
)
_parser.add_argument("--sjeng", action="store_true", help="Run SPEC 458.sjeng: sjeng_base.void-gcc test.txt")
_parser.add_argument(
    "--h264ref",
    action="store_true",
    help="Run SPEC 464.h264ref: h264ref_base.void-gcc -d foreman_test_encoder_baseline.cfg",
)
_parser.add_argument("--omnetpp", action="store_true", help="Run SPEC 471.omnetpp: omnetpp_base.void-gcc omnetpp.ini")
_parser.add_argument("--astar", action="store_true", help="Run SPEC 473.astar: astar_base.void-gcc lake.cfg")
_parser.add_argument("--bwaves", action="store_true", help="Run SPEC 410.bwaves (.0004): bwaves_base.void-gcc")
_parser.add_argument("--zeusmp", action="store_true", help="Run SPEC 434.zeusmp (.0004): zeusmp_base.void-gcc")
_parser.add_argument(
    "--gromacs",
    action="store_true",
    help="Run SPEC 435.gromacs (.0004): gromacs_base.void-gcc -silent -deffnm gromacs -nice 0",
)
_parser.add_argument("--cactusadm", action="store_true", help="Run SPEC 436.cactusADM (.0004): cactusADM_base.void-gcc benchADM.par")
_parser.add_argument(
    "--namd",
    action="store_true",
    help="Run SPEC 444.namd (.0004): namd_base.void-gcc --input namd.input --iterations 1 --output namd.out",
)
_parser.add_argument("--povray", action="store_true", help="Run SPEC 453.povray (.0004): povray_base.void-gcc SPEC-benchmark-test.ini")
_parser.add_argument("--gemsfdtd", action="store_true", help="Run SPEC 459.GemsFDTD (.0004): GemsFDTD_base.void-gcc")
_parser.add_argument("--tonto", action="store_true", help="Run SPEC 465.tonto (.0004): tonto_base.void-gcc")
_parser.add_argument(
    "--sphinx3",
    action="store_true",
    help="Run SPEC 482.sphinx3 (.0004): sphinx_livepretend_base.void-gcc ctlfile . args.an4",
)
_parser.add_argument(
    "--cluster-steer-policy",
    type=str,
    choices=["RegBased", "ModN", "RoundRobin", "PCLowBitHash"],
    default="ModN",
    help=(
        "Cluster steering policy (default: ModN). "
        "RoundRobin and PCLowBitHash ignore --cluster-steer-group-size."
    ),
)
_parser.add_argument(
    "--reg-based",
    action="store_true",
    help="Shortcut for --cluster-steer-policy RegBased",
)
_parser.add_argument(
    "--intercluster-delay",
    type=int,
    default=3,
    help="Clustered O3 inter-cluster communication delay in cycles (default: 3)",
)
_parser.add_argument(
    "--cluster-steer-group-size",
    type=int,
    default=8,
    help=(
        "ModN: instructions per cluster before switching. "
        "RegBased: ModN-style fallback group size when no int/float arch reg applies "
        "(default: 8). Ignored by RoundRobin and PCLowBitHash."
    ),
)
_parser.add_argument(
    "--cluster-steer-pc-bit",
    type=int,
    default=2,
    help=(
        "PCLowBitHash: PC bit index X used in (PC>>X)&1 (default: 2). "
        "Ignored by other steering policies."
    ),
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
_parser.add_argument(
    "--ld-library-path",
    type=str,
    default=None,
    help=(
        "Colon-separated dirs prepended to emulated LD_LIBRARY_PATH (for guest "
        "dlopen/loader). Also uses host env GEM5_LD_LIBRARY_PATH and LD_LIBRARY_PATH if set."
    ),
)
_args, _ = _parser.parse_known_args()
if _args.cluster_steer_pc_bit < 0:
    raise SystemExit("--cluster-steer-pc-bit must be >= 0")

# Allow steering selection at runtime without editing this file.
_steer_policy = "RegBased" if _args.reg_based else _args.cluster_steer_policy
for cpu in system.cpu:
    cpu.clusterSteerPolicy = _steer_policy
    cpu.clusterSteerGroupSize = _args.cluster_steer_group_size
    cpu.clusterSteerPCBit = _args.cluster_steer_pc_bit
    cpu.interclusterDelay = _args.intercluster_delay

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
elif _args.perlbench:
    binary = PERLBENCH_BIN
    cmd_args = PERLBENCH_CMD[1:]
    process_cwd = PERLBENCH_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"perlbench binary not found: {binary} (set SPEC2006_PERLBENCH_DIR?)")
elif _args.bzip2:
    binary = BZIP2_BIN
    cmd_args = BZIP2_CMD[1:]
    process_cwd = BZIP2_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"bzip2 binary not found: {binary} (set SPEC2006_BZIP2_DIR?)")
elif _args.mcf:
    binary = MCF_BIN
    cmd_args = MCF_CMD[1:]
    process_cwd = MCF_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"mcf binary not found: {binary} (set SPEC2006_MCF_DIR?)")
elif _args.gobmk:
    binary = GOBMK_BIN
    cmd_args = GOBMK_CMD[1:]
    process_cwd = GOBMK_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"gobmk binary not found: {binary} (set SPEC2006_GOBMK_DIR?)")
elif _args.hmmer:
    binary = HMMER_BIN
    cmd_args = HMMER_CMD[1:]
    process_cwd = HMMER_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"hmmer binary not found: {binary} (set SPEC2006_HMMER_DIR?)")
elif _args.sjeng:
    binary = SJENG_BIN
    cmd_args = SJENG_CMD[1:]
    process_cwd = SJENG_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"sjeng binary not found: {binary} (set SPEC2006_SJENG_DIR?)")
elif _args.h264ref:
    binary = H264REF_BIN
    cmd_args = H264REF_CMD[1:]
    process_cwd = H264REF_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"h264ref binary not found: {binary} (set SPEC2006_H264REF_DIR?)")
elif _args.omnetpp:
    binary = OMNETPP_BIN
    cmd_args = OMNETPP_CMD[1:]
    process_cwd = OMNETPP_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"omnetpp binary not found: {binary} (set SPEC2006_OMNETPP_DIR?)")
elif _args.astar:
    binary = ASTAR_BIN
    cmd_args = ASTAR_CMD[1:]
    process_cwd = ASTAR_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"astar binary not found: {binary} (set SPEC2006_ASTAR_DIR?)")
elif _args.bwaves:
    binary = BWAVES_BIN
    cmd_args = BWAVES_CMD[1:]
    process_cwd = BWAVES_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"bwaves binary not found: {binary} (set SPEC2006_BWAVES_DIR?)")
elif _args.zeusmp:
    binary = ZEUSMP_BIN
    cmd_args = ZEUSMP_CMD[1:]
    process_cwd = ZEUSMP_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"zeusmp binary not found: {binary} (set SPEC2006_ZEUSMP_DIR?)")
elif _args.gromacs:
    binary = GROMACS_BIN
    cmd_args = GROMACS_CMD[1:]
    process_cwd = GROMACS_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"gromacs binary not found: {binary} (set SPEC2006_GROMACS_DIR?)")
elif _args.cactusadm:
    binary = CACTUSADM_BIN
    cmd_args = CACTUSADM_CMD[1:]
    process_cwd = CACTUSADM_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"cactusADM binary not found: {binary} (set SPEC2006_CACTUSADM_DIR?)")
elif _args.namd:
    binary = NAMD_BIN
    cmd_args = NAMD_CMD[1:]
    process_cwd = NAMD_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"namd binary not found: {binary} (set SPEC2006_NAMD_DIR?)")
elif _args.povray:
    binary = POVRAY_BIN
    cmd_args = POVRAY_CMD[1:]
    process_cwd = POVRAY_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"povray binary not found: {binary} (set SPEC2006_POVRAY_DIR?)")
elif _args.gemsfdtd:
    binary = GEMSFDTD_BIN
    cmd_args = GEMSFDTD_CMD[1:]
    process_cwd = GEMSFDTD_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"GemsFDTD binary not found: {binary} (set SPEC2006_GEMSFDTD_DIR?)")
elif _args.tonto:
    binary = TONTO_BIN
    cmd_args = TONTO_CMD[1:]
    process_cwd = TONTO_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"tonto binary not found: {binary} (set SPEC2006_TONTO_DIR?)")
elif _args.sphinx3:
    binary = SPHINX3_BIN
    cmd_args = SPHINX3_CMD[1:]
    process_cwd = SPHINX3_DIR
    if not os.path.exists(binary):
        raise SystemExit(f"sphinx3 binary not found: {binary} (set SPEC2006_SPHINX3_DIR?)")
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
# SE mode does not inherit the shell's dynamic linker search path; the guest
# interpreter only sees Process.env. Forward common host vars + --ld-library-path.
_ld_parts: list[str] = []
if _args.ld_library_path:
    _ld_parts.append(_args.ld_library_path)
if os.environ.get("GEM5_LD_LIBRARY_PATH"):
    _ld_parts.append(os.environ["GEM5_LD_LIBRARY_PATH"])
if os.environ.get("LD_LIBRARY_PATH"):
    _ld_parts.append(os.environ["LD_LIBRARY_PATH"])
_ld_merged = ":".join(p for p in _ld_parts if p)
if _ld_merged:
    process.env = [f"LD_LIBRARY_PATH={_ld_merged}"]

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

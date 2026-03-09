# Copyright (c) 2025
# Config script to run tiny binary with a customizable O3 CPU.
# Run from project root: build/X86/gem5.opt configs/tiny_o3.py

import os
import m5
from m5.objects import *
from m5.util import addToPath

addToPath(os.path.dirname(os.path.abspath(__file__)))
from common.Caches import L1_ICache, L1_DCache, L2Cache

# Path to tiny binary (in project root, sibling of configs/)
_config_dir = os.path.dirname(os.path.abspath(__file__))
TINY_BIN = os.path.join(os.path.dirname(_config_dir), "tiny")

# =============================================================================
# O3 CPU configuration - customize these
# =============================================================================
ISSUE_WIDTH = 8
DISPATCH_WIDTH = 8
FETCH_WIDTH = 8
COMMIT_WIDTH = 8
NUM_ROB_ENTRIES = 192

# Cluster steering (multicluster O3)
CLUSTER_STEER_POLICY = "RegBased"  # "RegBased" or "ModN"
CLUSTER_STEER_GROUP_SIZE = 4

# =============================================================================
# System configuration
# =============================================================================
NUM_CPUS = 1
SYS_CLOCK = "3.5GHz"
CPU_CLOCK = "3.5GHz"
SYS_VOLT = "1.0V"
MEM_SIZE = "512MiB"
CACHELINE = 64
L1I_SIZE = "32KiB"
L1D_SIZE = "32KiB"
L2_SIZE = "1MiB"

# Create O3 CPU with custom params
system = System(
    cpu=[
        DerivO3CPU(
            cpu_id=0,
            issueWidth=ISSUE_WIDTH,
            dispatchWidth=DISPATCH_WIDTH,
            fetchWidth=FETCH_WIDTH,
            commitWidth=COMMIT_WIDTH,
            numROBEntries=NUM_ROB_ENTRIES,
            clusterSteerPolicy=CLUSTER_STEER_POLICY,
            clusterSteerGroupSize=CLUSTER_STEER_GROUP_SIZE,
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

system.membus = SystemXBar()
system.system_port = system.membus.cpu_side_ports

system.l2bus = L2XBar()

system.l2cache = L2Cache(size=L2_SIZE)
system.l2cache.cpu_side = system.l2bus.mem_side_ports
system.l2cache.mem_side = system.membus.cpu_side_ports

for cpu in system.cpu:
    cpu.icache = L1_ICache(size=L1I_SIZE)
    cpu.dcache = L1_DCache(size=L1D_SIZE)
    cpu.icache_port = cpu.icache.cpu_side
    cpu.dcache_port = cpu.dcache.cpu_side
    cpu.icache.mem_side = system.l2bus.cpu_side_ports
    cpu.dcache.mem_side = system.l2bus.cpu_side_ports

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Process and workload
process = Process(pid=100)
process.executable = TINY_BIN
process.cwd = os.path.dirname(os.path.abspath(TINY_BIN))
process.gid = os.getgid()
process.cmd = [TINY_BIN]

system.workload = SEWorkload.init_compatible(TINY_BIN)

for cpu in system.cpu:
    cpu.workload = process
    cpu.createInterruptController()
    cpu.interrupts[0].pio = system.membus.mem_side_ports
    cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    cpu.interrupts[0].int_responder = system.membus.mem_side_ports
    cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print("Starting tiny:", TINY_BIN)
exit_event = m5.simulate()
print("Exited @ tick", m5.curTick(), "because", exit_event.getCause())

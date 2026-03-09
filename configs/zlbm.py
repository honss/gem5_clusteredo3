import os
import m5
from m5.objects import *
from m5.util import addToPath

addToPath("../../")
from common.Caches import L1_ICache, L1_DCache, L2Cache

from gem5.components.memory.hbm import HBM2Stack

LBM_DIR = "/m/local1/aidanlevy03/spec2006_install/benchspec/CPU2006/470.lbm/run/run_base_test_void-gcc.0001"
LBM_BIN = os.path.join(LBM_DIR, "lbm_base.void-gcc")
LBM_CMD = [LBM_BIN, "20", "reference.dat", "0", "1", "100_100_130_cf_a.of"]

CPU_CLASS = DerivO3CPU
NUM_CPUS = 1

SYS_CLOCK = "2GHz"
CPU_CLOCK = "2GHz"
SYS_VOLT = "1.0V"

MEM_SIZE = "4GiB"

CACHELINE = 64
L1I_SIZE = "32KiB"
L1D_SIZE = "32KiB"
L2_SIZE = "1MiB"

process = Process(pid=100)
process.executable = LBM_BIN
process.cwd = LBM_DIR
process.gid = os.getgid()
process.cmd = LBM_CMD

system = System(
    cpu=[CPU_CLASS(cpu_id=i) for i in range(NUM_CPUS)],
    mem_mode="timing",
    mem_ranges=[AddrRange(MEM_SIZE)],
    cache_line_size=CACHELINE,
)

system.voltage_domain = VoltageDomain(voltage=SYS_VOLT)
system.clk_domain = SrcClockDomain(clock=SYS_CLOCK, voltage_domain=system.voltage_domain)

system.cpu_voltage_domain = VoltageDomain()
system.cpu_clk_domain = SrcClockDomain(clock=CPU_CLOCK, voltage_domain=system.cpu_voltage_domain)

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

system.hbm = HBM2Stack(size=MEM_SIZE)
system.hbm.set_memory_range([system.mem_ranges[0]])

# mem_ctrls = system.hbm.get_memory_controllers()
for ctrl in system.hbm.get_memory_controllers():
    ctrl.port = system.membus.mem_side_ports
    #setattr(system, f"hbm_ctrl{i}", ctrl)

system.workload = SEWorkload.init_compatible(LBM_BIN)

for cpu in system.cpu:
    cpu.workload = process
    cpu.createInterruptController()
    cpu.interrupts[0].pio = system.membus.mem_side_ports
    cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    cpu.interrupts[0].int_responder = system.membus.mem_side_ports
    cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print("Starting 470.lbm:", " ".join(LBM_CMD))
exit_event = m5.simulate()
print("Exited @ tick", m5.curTick(), "because", exit_event.getCause())


# Next Steps: Michaud et al.–Style Clustered O3

Goal: Implement the dual-cluster design from *Revisiting Clustered Microarchitecture for Future Superscalar Cores* (TACO 2015), with **Mod-N** (simple) steering and an option for **more complex** steering (RegBased / future dependence-based).

---

## Current State

- **Decode:** Cluster assignment runs in Decode; each instruction gets a `clusterMask` (1=C0, 2=C1, 3=both).
- **Steering policies:**
  - **RegBased** – even/odd arch reg → cluster; operands in both clusters → dual-distributed (mask 3).
  - **ModN** – round-robin by `clusterSteerGroupSize` (first N → C0, next N → C1, …). Use `clusterSteerGroupSize=64` for paper’s Mod-64; N=1 is Mod-1.
- **Back end:** Still single-cluster: one rename, one unified IQ, one IEW; `clusterMask` is set but not yet used downstream.

---

## Target Design (Michaud et al.)

1. **Dispatch-driven steering** – Done (steering in Decode, before rename).
2. **Symmetric clusters** – Two clusters, same capabilities.
3. **Register write specialization** – Cluster 0 writes phys regs 0..K-1, cluster 1 writes K..2K-1; each cluster has a mirror (read-only) copy of the other’s partition.
4. **Per-cluster issue queues** – Two IQ partitions; instructions dispatched to IQ(s) according to `clusterMask`.
5. **Intercluster delay** – Results from the other cluster visible after 2–3 cycles (configurable).
6. **Mod-N steering** – Use ModN with `clusterSteerGroupSize = 64` (or 32) as in the paper.

---

## Implementation Order

### Phase 1: Steering and config (minimal, already partly done)

1. **Mod-N policy** – Use ModN with `clusterSteerGroupSize = N` (e.g. 64 for Mod-64).
2. **Config** – In `o3_spec_config.py` (or a dedicated clustered config), add a “clustered” mode that sets:
   - `clusterSteerPolicy = "ModN"`, `clusterSteerGroupSize = 64`
   - Later: per-cluster params (see Phase 2–4).

**Deliverable:** Run with `--cluster-steer-policy=ModN --cluster-steer-group-size=64`; clusterMask set correctly; no backend effect yet.

---

### Phase 2: Per-cluster physical registers and rename

**Goal:** Rename allocates from the cluster’s partition; dual-distributed instructions get one reg per cluster (or restrict to single-cluster only for first cut).

1. **Partition free list (per reg class)**  
   - e.g. INT: 0..63 → cluster 0, 64..127 → cluster 1 (param: `numPhysIntRegs` total, half per cluster).  
   - Two `SimpleFreeList`-like structures per class, or one free list that returns regs from the correct partition based on cluster.

2. **Rename stage**  
   - On rename, use `inst->clusterMask()`:
     - If single cluster (1 or 2): allocate one dest from that cluster’s partition.
     - If dual (3): either allocate two dests (one per partition) or, for a simpler first step, disallow dual (force single cluster by steering policy) so only one dest.
   - Rename map: each arch reg can map to a phys reg in either partition; when reading the map, use the partition that matches the consumer’s cluster when you add wakeup logic later.

3. **Regfile**  
   - Paper: “each cluster has a bank for partition 0 and a bank for partition 1, but writes only in its own partition.”  
   - For sim: can keep one regfile and only change **allocation** (rename) and **which cluster issues the instruction**; “mirror” can be modeled as both clusters having read access to all phys regs, with write ports only to their partition.  
   - Alternative: two regfile instances (or two banks) and wire reads/writes by partition in IEW.

**Deliverable:** Rename allocates dest from the correct partition; instructions carry cluster; no IQ split yet (all still go to one IQ).

---

### Phase 3: Per-cluster issue queue and dispatch

**Goal:** Two IQ partitions; dispatch sends each instruction to the IQ of cluster 0 and/or 1 based on `clusterMask`.

1. **CPU params**  
   - e.g. `numClusters = 2`, and `instQueues` sized so that there are two IQ units (one per cluster), each with half the entries (e.g. 60 each for 120 total).

2. **Dispatch (Rename → IEW)**  
   - When sending an instruction to IEW, use `clusterMask`:
     - Mask 1 → push to cluster 0’s IQ only.  
     - Mask 2 → cluster 1’s IQ only.  
     - Mask 3 → push to both IQs (dual-distributed; both “copies” eventually execute; need to handle result merging or pick one writer).

3. **IEW / issue**  
   - Each cluster has its own issue logic reading from its IQ; issue width per cluster (e.g. 4 INT + 2 FP per cluster).  
   - This may require splitting the current `IEW` into per-cluster issue logic or having one IEW that iterates over clusters and issues from the corresponding IQ.

**Deliverable:** Instructions only enter the IQ of their cluster(s); each cluster issues from its own IQ; execution still uses a single regfile/ bypass for now.

---

### Phase 4: Intercluster bypass (delay)

**Goal:** When an instruction in cluster A needs a result produced in cluster B, that result is visible after `interclusterDelay` cycles (e.g. 2–3).

1. **Wakeup / completion**  
   - Today: completing instruction wakes consumers by phys reg.  
   - New: if producer is in cluster A and consumer in cluster B, schedule wakeup at `curCycle() + interclusterDelay` (or tag the result as “arrives at cycle X” and let the consumer wait).

2. **Bypass**  
   - Local bypass: same cluster, 1 cycle.  
   - Remote bypass: other cluster, `interclusterDelay` cycles.  
   - In IEW, when checking “is source ready?”, if the producing instruction executed in the other cluster, add the delay.

3. **Params**  
   - `interclusterDelay = Param.Cycles(3, "Result forwarding delay from other cluster")`.

**Deliverable:** Correct IPC impact when instructions depend on results from the other cluster (fewer wakeups per cycle for remote results).

---

### Phase 5 (optional): More complicated steering

- **RegBased** – Already implemented; use it as the “smarter” option that minimizes cross-cluster traffic when regs align with clusters.
- **Future: dependence-based** – Use rename info (phys regs) to steer dependent instructions to the same cluster; requires steering decision after or during rename, or a second pass; more complex.

---

## Suggested next action

1. **Rebuild** if needed: `scons build/X86/gem5.opt`; confirm ModN with groupSize=N works in Decode.

2. **Start Phase 2** – Partition the free list by cluster and make rename allocate from the partition implied by `inst->clusterMask()`. That is the foundation for write specialization and per-cluster execution.

3. **Config** – Add a small “clustered” section in `o3_spec_config.py` (or a new `o3_clustered_config.py`) that sets ModN, groupSize=64, and documents that full per-cluster backend is WIP.

---

## File touch points (reference)

| Component   | Files |
|------------|--------|
| Steering   | `cluster_assign.cc/hh`, `SMT.py`, `decode.cc`, `BaseO3CPU.py` |
| Rename     | `rename.cc/hh`, `free_list.cc/hh`, `rename_map.cc/hh` |
| Regfile    | `regfile.cc/hh` |
| IQ / IEW   | `inst_queue.cc/hh`, `iew.cc/hh`, `iew_impl.hh` |
| Params     | `BaseO3CPU.py` |

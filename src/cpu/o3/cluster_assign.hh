/*
 * Copyright (c) 2025
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met: redistributions of source code must retain the above copyright
 * notice, this list of conditions and the following disclaimer;
 * redistributions in binary form must reproduce the above copyright
 * notice, this list of conditions and the following disclaimer in the
 * documentation and/or other materials provided with the distribution;
 * neither the name of the copyright holders nor the names of its
 * contributors may be used to endorse or promote products derived from
 * this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef __CPU_O3_CLUSTER_ASSIGN_HH__
#define __CPU_O3_CLUSTER_ASSIGN_HH__

#include <array>
#include <cstdint>

#include "cpu/o3/dyn_inst_ptr.hh"
#include "cpu/reg_class.hh"
#include "enums/ClusterSteerPolicy.hh"

namespace gem5
{

namespace o3
{

/**
 * Per-thread state used by the cluster steering logic. Owned by Decode.
 *
 * Holds:
 *   - modNCount:  running counter used by ModN/RoundRobin and as a fallback
 *     when no other policy can pick a cluster.
 *   - intHint / fpHint: per-arch-reg "last producer cluster" hint table used
 *     by the ProducerLocality policy. One signed byte per Int/Float arch reg
 *     (-1 = no hint, 0 = cluster 0, 1 = cluster 1). Indexed by reg.index().
 *     Architectural reg indices >= kProdHintSize are ignored (no hint).
 *
 * This is intentionally a tiny per-arch-reg table (no PC tag, no history),
 * not a full steering predictor.
 */
struct ClusterSteerState
{
    /** Max architectural reg index tracked per class.
     * 128 covers Int+Float on x86, ARM, RV64, etc. Larger indices are
     * silently treated as "no hint".
     */
    static constexpr unsigned kProdHintSize = 128;

    unsigned modNCount = 0;
    std::array<int8_t, kProdHintSize> intHint;
    std::array<int8_t, kProdHintSize> fpHint;

    ClusterSteerState() { reset(); }

    /** Clear counters and hint table. */
    void reset();

    /** Returns -1 if no hint or reg is not Int/Float, else 0/1. */
    int8_t getProdHint(const RegId &reg) const;

    /** Records that this Int/Float arch reg was produced on cluster `cluster`. */
    void setProdHint(const RegId &reg, int cluster);
};

/**
 * Assign the instruction to one cluster (2-cluster policy).
 *
 * RegBased: Int/Float arch reg index even -> cluster 0, odd -> cluster 1
 *   (dest preferred, then sources). Falls back to ModN if neither applies.
 *
 * ModN: Steer in groups of groupSize instructions. First groupSize -> C0,
 *   next groupSize -> C1, then 0, 1, ...
 *
 * RoundRobin: Alternate cluster 0/1 every instruction (ignores groupSize).
 *
 * PCLowBitHash: cluster = (PC >> pcBit) & 1.
 *
 * ProducerLocality: For each source Int/Float arch reg, look up which
 *   cluster most recently produced it and tally votes. Steer to the
 *   majority cluster. Ties / no hints -> ModN fallback. After steering,
 *   record the chosen cluster as the producer hint for every dest
 *   Int/Float arch reg.
 *
 * The result is stored on the instruction via setClusterMask().
 *
 * `state` is per-thread and may be null (in which case all hint-based
 * decisions degrade to ModN/RegBased fallbacks).
 */
void assignClusterToInst(const DynInstPtr &inst,
                         ClusterSteerPolicy policy,
                         unsigned groupSize,
                         unsigned pcBit,
                         ClusterSteerState *state);

} // namespace o3
} // namespace gem5

#endif // __CPU_O3_CLUSTER_ASSIGN_HH__

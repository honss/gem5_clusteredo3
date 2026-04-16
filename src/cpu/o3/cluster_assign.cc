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

#include "cpu/o3/cluster_assign.hh"

#include "cpu/o3/dyn_inst.hh"
#include "cpu/reg_class.hh"
#include "debug/ClusterCheck.hh"

namespace gem5
{

namespace o3
{

void
assignClusterToInst(const DynInstPtr &inst,
                    ClusterSteerPolicy policy,
                    unsigned groupSize,
                    unsigned *steerCountPtr)
{
    // In the Michaud et al. style design we target, each instruction is
    // executed in a single cluster. ModN steering always picks one cluster
    // by group index; RegBased also chooses a single cluster based on the
    // registers it touches.

    int cluster = 0;

    if (policy == ClusterSteerPolicy::ModN && steerCountPtr != nullptr) {
        unsigned idx = (*steerCountPtr)++;
        unsigned group = idx / groupSize;
        cluster = group % 2;
    } else {
        // RegBased: try destination int/float regs first, then sources.
        auto chooseClusterFromReg = [&cluster](const RegId &reg,
                                               bool &chosen) {
            if (chosen)
                return;
            RegClassType type = reg.classValue();
            if (type != IntRegClass && type != FloatRegClass)
                return;
            cluster = reg.index() % 2;
            chosen = true;
        };

        bool chosen = false;

        // Prefer destinations: where the value is written.
        for (int i = 0; i < inst->numDestRegs(); i++) {
            chooseClusterFromReg(inst->destRegIdx(i), chosen);
            if (chosen)
                break;
        }

        // Fall back to sources if no suitable destination.
        if (!chosen) {
            for (int i = 0; i < inst->numSrcRegs(); i++) {
                chooseClusterFromReg(inst->srcRegIdx(i), chosen);
                if (chosen)
                    break;
            }
        }

        // If still nothing (no int/float regs), fall back to ModN-style
        // steering when possible, otherwise default to cluster 0.
        if (!chosen) {
            if (steerCountPtr != nullptr && groupSize != 0) {
                unsigned idx = (*steerCountPtr)++;
                unsigned group = idx / groupSize;
                cluster = group % 2;
            } else {
                cluster = 0;
            }
        }
    }

    uint8_t mask = static_cast<uint8_t>(1u << cluster);
    inst->setClusterMask(mask);

    DPRINTF(ClusterCheck, "steer uop [sn:%llu] PC %s -> cluster %d\n",
            inst->seqNum, inst->pcState(), cluster);
}

} // namespace o3
} // namespace gem5

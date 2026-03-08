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
    uint8_t mask = 0;

    if (policy == ClusterSteerPolicy::Alternating && steerCountPtr != nullptr) {
        unsigned idx = (*steerCountPtr)++;
        unsigned group = idx / groupSize;
        int cluster = group % 2;
        mask = 1u << cluster;
    } else {
        // RegBased (or fallback)
        auto addClusterFromReg = [&mask](const RegId &reg) {
            RegClassType type = reg.classValue();
            if (type != IntRegClass && type != FloatRegClass)
                return;
            int cluster = reg.index() % 2;
            mask |= (1u << cluster);
        };

        for (int i = 0; i < inst->numSrcRegs(); i++)
            addClusterFromReg(inst->srcRegIdx(i));
        for (int i = 0; i < inst->numDestRegs(); i++)
            addClusterFromReg(inst->destRegIdx(i));

        if (mask == 0)
            mask = 1;
    }

    inst->setClusterMask(mask);
}

} // namespace o3
} // namespace gem5

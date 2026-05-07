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
ClusterSteerState::reset()
{
    modNCount = 0;
    intHint.fill(-1);
    fpHint.fill(-1);
}

int8_t
ClusterSteerState::getProdHint(const RegId &reg) const
{
    unsigned idx = reg.index();
    if (idx >= kProdHintSize)
        return -1;
    RegClassType t = reg.classValue();
    if (t == IntRegClass)
        return intHint[idx];
    if (t == FloatRegClass)
        return fpHint[idx];
    return -1;
}

void
ClusterSteerState::setProdHint(const RegId &reg, int cluster)
{
    unsigned idx = reg.index();
    if (idx >= kProdHintSize)
        return;
    RegClassType t = reg.classValue();
    int8_t v = static_cast<int8_t>(cluster & 1);
    if (t == IntRegClass)
        intHint[idx] = v;
    else if (t == FloatRegClass)
        fpHint[idx] = v;
}

namespace {

/** ModN-style step: advance counter and return cluster index in {0,1}. */
int
modNStep(ClusterSteerState *state, unsigned groupSize)
{
    if (state == nullptr)
        return 0;
    if (groupSize == 0)
        groupSize = 1;
    unsigned idx = state->modNCount++;
    return (idx / groupSize) & 1u;
}

/** RegBased pick: even/odd of arch reg index for first Int/Float reg.
 *  Returns true if a cluster was chosen. */
bool
regBasedPick(const DynInstPtr &inst, int &cluster)
{
    auto try_reg = [&](const RegId &reg) -> bool {
        RegClassType t = reg.classValue();
        if (t != IntRegClass && t != FloatRegClass)
            return false;
        cluster = reg.index() & 1;
        return true;
    };

    for (int i = 0; i < inst->numDestRegs(); i++) {
        if (try_reg(inst->destRegIdx(i)))
            return true;
    }
    for (int i = 0; i < inst->numSrcRegs(); i++) {
        if (try_reg(inst->srcRegIdx(i)))
            return true;
    }
    return false;
}

} // anonymous namespace

void
assignClusterToInst(const DynInstPtr &inst,
                    ClusterSteerPolicy policy,
                    unsigned groupSize,
                    unsigned pcBit,
                    ClusterSteerState *state)
{
    int cluster = 0;

    switch (policy) {
      case ClusterSteerPolicy::ModN:
        cluster = modNStep(state, groupSize);
        break;

      case ClusterSteerPolicy::RoundRobin:
        cluster = state ? (state->modNCount++ & 1u) : 0;
        break;

      case ClusterSteerPolicy::PCLowBitHash: {
        Addr pc = inst->pcState().instAddr();
        cluster = static_cast<int>((pc >> pcBit) & 1u);
        break;
      }

      case ClusterSteerPolicy::ProducerLocality: {
        // Tally producer-cluster votes from source Int/Float arch regs.
        unsigned vote[2] = {0, 0};
        if (state != nullptr) {
            for (int i = 0; i < inst->numSrcRegs(); i++) {
                int8_t h = state->getProdHint(inst->srcRegIdx(i));
                if (h == 0)
                    vote[0]++;
                else if (h == 1)
                    vote[1]++;
            }
        }
        if (vote[0] > vote[1]) {
            cluster = 0;
        } else if (vote[1] > vote[0]) {
            cluster = 1;
        } else {
            // Tie or no hints. Try RegBased first (cheap, deterministic),
            // then fall back to ModN so the load stays balanced.
            if (!regBasedPick(inst, cluster))
                cluster = modNStep(state, groupSize);
        }
        break;
      }

      case ClusterSteerPolicy::RegBased:
      default:
        if (!regBasedPick(inst, cluster))
            cluster = modNStep(state, groupSize);
        break;
    }

    uint8_t mask = static_cast<uint8_t>(1u << cluster);
    inst->setClusterMask(mask);

    // Update producer-locality hints whenever we have steer state, regardless
    // of policy. The table is tiny (one byte per Int/Float arch reg) and
    // keeping it warm means switching to ProducerLocality at runtime works
    // without any priming phase.
    if (state != nullptr) {
        for (int i = 0; i < inst->numDestRegs(); i++)
            state->setProdHint(inst->destRegIdx(i), cluster);
    }

    DPRINTF(ClusterCheck, "steer uop [sn:%llu] PC %s -> cluster %d\n",
            inst->seqNum, inst->pcState(), cluster);
}

} // namespace o3
} // namespace gem5

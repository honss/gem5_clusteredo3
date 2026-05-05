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

#include "enums/ClusterSteerPolicy.hh"
#include "cpu/o3/dyn_inst_ptr.hh"

namespace gem5
{

namespace o3
{

/**
 * Assign the instruction to one or both clusters (2-cluster policy).
 *
 * RegBased: Int/Float arch reg index even -> cluster 0, odd -> cluster 1.
 *   If operands span both clusters, dual-distributed. No operands -> cluster 0.
 *
 * ModN: Steer in groups of groupSize instructions. First groupSize
 *   -> cluster 0, next groupSize -> cluster 1, then 0, 1, ...
 *   steerCountPtr is per-thread and incremented here.
 *
 * RoundRobin: Alternate cluster 0/1 every instruction; steerCountPtr is
 *   used as the running index.
 *
 * PCLowBitHash: Use (PC >> pcBit) & 1 to pick cluster 0/1.
 *
 * The result is stored on the instruction via setClusterMask().
 */
void assignClusterToInst(const DynInstPtr &inst,
                         ClusterSteerPolicy policy,
                         unsigned groupSize,
                         unsigned pcBit,
                         unsigned *steerCountPtr);

} // namespace o3
} // namespace gem5

#endif // __CPU_O3_CLUSTER_ASSIGN_HH__

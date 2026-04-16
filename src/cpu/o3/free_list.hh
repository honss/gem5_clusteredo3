/*
 * Copyright (c) 2016-2018 ARM Limited
 * All rights reserved
 *
 * The license below extends only to copyright in the software and shall
 * not be construed as granting a license to any other intellectual
 * property including but not limited to intellectual property relating
 * to a hardware implementation of the functionality of the software
 * licensed hereunder. You may use the software subject to the license
 * terms below provided that you ensure that this notice is replicated
 * unmodified and in its entirety in all distributions of the software,
 * modified or unmodified, in source code or in binary form.
 *
 * Copyright (c) 2004-2005 The Regents of The University of Michigan
 * Copyright (c) 2013 Advanced Micro Devices, Inc.
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

#ifndef __CPU_O3_FREE_LIST_HH__
#define __CPU_O3_FREE_LIST_HH__

#include <algorithm>
#include <array>
#include <iostream>
#include <queue>

#include "base/logging.hh"
#include "base/trace.hh"
#include "cpu/o3/comm.hh"
#include "cpu/o3/regfile.hh"
#include "debug/FreeList.hh"

namespace gem5
{

namespace o3
{

class UnifiedRenameMap;

/**
 * Free list for a single class of registers (e.g., integer
 * or floating point).  Because the register class is implicitly
 * determined by the rename map instance being accessed, all
 * architectural register index parameters and values in this class
 * are relative (e.g., %fp2 is just index 2).
 */
class SimpleFreeList
{
  private:

    /** The actual free list */
    std::queue<PhysRegIdPtr> freeRegs;

  public:

    SimpleFreeList() {};

    /** Add a physical register to the free list */
    void addReg(PhysRegIdPtr reg) { freeRegs.push(reg); }

    /** Add physical registers to the free list */
    template<class InputIt>
    void
    addRegs(InputIt first, InputIt last) {
        std::for_each(first, last, [this](typename InputIt::value_type& reg) {
            freeRegs.push(&reg);
        });
    }

    /** Get the next available register from the free list */
    PhysRegIdPtr getReg()
    {
        assert(!freeRegs.empty());
        PhysRegIdPtr free_reg = freeRegs.front();
        freeRegs.pop();
        return free_reg;
    }

    /** Return the number of free registers on the list. */
    unsigned numFreeRegs() const { return freeRegs.size(); }

    /** True iff there are free registers on the list. */
    bool hasFreeRegs() const { return !freeRegs.empty(); }
};


/**
 * FreeList class that simply holds the list of free integer and floating
 * point registers.  Can request for a free register of either type, and
 * also send back free registers of either type.  This is a very simple
 * class, but it should be sufficient for most implementations.  Like all
 * other classes, it assumes that the indices for the floating point
 * registers starts after the integer registers end.  Hence the variable
 * numPhysicalIntRegs is logically equivalent to the baseFP dependency.
 * Note that while this most likely should be called FreeList, the name
 * "FreeList" is used in a typedef within the CPU Policy, and therefore no
 * class can be named simply "FreeList".
 * @todo: Give a better name to the base FP dependency.
 *
 * For clustered O3 (Michaud et al.): when numClusters==2, INT and FP
 * physical registers are partitioned by index (0..K-1 -> cluster 0,
 * K..2K-1 -> cluster 1).  Allocations and frees use the appropriate
 * per-cluster list.
 */
class UnifiedFreeList
{
  public:
    static constexpr unsigned MaxClusters = 2;

  private:

    /** The object name, for DPRINTF.  We have to declare this
     *  explicitly because Scoreboard is not a SimObject. */
    const std::string _name;

    /** Per-class, per-cluster free lists.  When numClusters==1 only [0] is used. */
    std::array<std::array<SimpleFreeList, MaxClusters>, CCRegClass + 1> freeListsByCluster;

    /** Number of clusters (1 = no partition, 2 = INT/FP partitioned). */
    unsigned numClusters;

    /**
     * For INT/FP, index < partitionBoundary[type] => cluster 0, else cluster 1.
     * Used by addReg() to return freed regs to the correct list.
     */
    std::array<unsigned, CCRegClass + 1> partitionBoundary;

    /**
     * The register file object is used only to distinguish integer
     * from floating-point physical register indices.
     */
    PhysRegFile *regFile;

    /*
     * We give UnifiedRenameMap internal access so it can pass this
     * free list to per-class rename maps. See UnifiedRenameMap::init().
     */
    friend class UnifiedRenameMap;

    /** Resolve cluster for getReg when not partitioning (always 0). */
    int
    _cluster(RegClassType type, int cluster) const
    {
        if (numClusters < 2 || (type != IntRegClass && type != FloatRegClass))
            return 0;
        return cluster;
    }

  public:
    /** Constructs a free list.
     *  @param _numPhysicalIntRegs Number of physical integer registers.
     *  @param reservedIntRegs Number of integer registers already
     *                         used by initial mappings.
     *  @param _numPhysicalFloatRegs Number of physical fp registers.
     *  @param reservedFloatRegs Number of fp registers already
     *                           used by initial mappings.
     */
    UnifiedFreeList(const std::string &_my_name, PhysRegFile *_regFile);

    /** Gives the name of the freelist. */
    std::string name() const { return _name; };

    /** Enable per-cluster partition (2 = INT/FP split 0..K-1 / K..2K-1). */
    void setNumClusters(unsigned n) { numClusters = n; }

    /** Set partition boundary for a register class (index < boundary => cluster 0). */
    void setPartitionBoundary(RegClassType type, unsigned boundary) {
        partitionBoundary[type] = boundary;
    }

    /** Add registers to a specific cluster's pool for the given type. */
    template<class InputIt>
    void
    addRegsToCluster(RegClassType type, int cluster, InputIt first, InputIt last)
    {
        assert(cluster >= 0 && (unsigned)cluster < MaxClusters);
        auto &list = freeListsByCluster[type][cluster];
        std::for_each(first, last, [&list](typename InputIt::value_type& reg) {
            list.addReg(&reg);
        });
    }

    /** Gets a free register of type type (uses cluster 0 when not partitioned). */
    PhysRegIdPtr getReg(RegClassType type) { return getReg(type, 0); }

    /** Gets a free register of type type from the given cluster's pool. */
    PhysRegIdPtr getReg(RegClassType type, int cluster)
    {
        int c = _cluster(type, cluster);
        return freeListsByCluster[type][c].getReg();
    }

    /** Adds a register back to the free list. */
    template<class InputIt>
    void
    addRegs(InputIt first, InputIt last)
    {
        std::for_each(first, last, [this](auto &reg) { addReg(&reg); });
    }

    /** Adds a register back to the correct per-cluster free list. */
    void
    addReg(PhysRegIdPtr freed_reg)
    {
        RegClassType type = freed_reg->classValue();
        int c = 0;
        if (numClusters >= 2 && (type == IntRegClass || type == FloatRegClass)) {
            c = (freed_reg->index() < partitionBoundary[type]) ? 0 : 1;
        }
        freeListsByCluster[type][c].addReg(freed_reg);
    }

    /** Checks if there are any free registers of type type. */
    bool
    hasFreeRegs(RegClassType type) const
    {
        return hasFreeRegs(type, 0);
    }

    /** Checks if there are free registers of type type in cluster. */
    bool
    hasFreeRegs(RegClassType type, int cluster) const
    {
        int c = (numClusters >= 2 && (type == IntRegClass || type == FloatRegClass))
                ? cluster : 0;
        return freeListsByCluster[type][c].hasFreeRegs();
    }

    /** Returns the number of free registers of type type. */
    unsigned
    numFreeRegs(RegClassType type) const
    {
        return numFreeRegs(type, 0);
    }

    /** Returns the number of free registers of type type in cluster. */
    unsigned
    numFreeRegs(RegClassType type, int cluster) const
    {
        int c = (numClusters >= 2 && (type == IntRegClass || type == FloatRegClass))
                ? cluster : 0;
        return freeListsByCluster[type][c].numFreeRegs();
    }
};

} // namespace o3
} // namespace gem5

#endif // __CPU_O3_FREE_LIST_HH__

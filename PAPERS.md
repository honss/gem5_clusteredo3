# Papers & References

Papers and sources used in this project.

---

## Multicluster O3 / Cluster partitioning

- **Farkas et al. (1997)** — *The Multicluster Architecture: Reducing Cycle Time Through Partitioning.*  
  (Basis for clustered O3, per-cluster register files, dispatch queues, steering by architectural registers.)

---

Farkas paper, the origination of the design.
The Multicluster Architecture: Reducing Cycle Time Through Partitioning
Keith I. Farkas
farkas@pa.dec.com
Paul Chow
pc@eecg.toronto.edu
Norman P. Jouppi
jouppi@pa.dec.com
Zvonko Vranesic
zvonko@eecg.toronto.edu

Digital Equipment Corporation
Western Research Lab
250 University Avenue
Palo Alto, California 94301

Electrical and Computer Engineering
University of Toronto
10 Kings College Road
Toronto, Ontario, Canada
M5S 3G4
Abstract
The multicluster architecture that we introduce offers
a decentralized, dynamically-scheduled architecture, in
which the register files, dispatch queue, and functional
units of the architecture are distributed across multiple
clusters, and each cluster is assigned a subset of the architectural registers. The motivation for the multicluster
architecture is to reduce the clock cycle time, relative to a
single-cluster architecture with the same number of hardware resources, by reducing the size and complexity of
components on critical timing paths. Resource partitioning, however, introduces instruction-execution overhead
and may reduce the number of concurrently executing instructions. To counter these two negative by-products of
partitioning, we developed a static instruction scheduling
algorithm. We describe this algorithm, and using tracedriven simulations of SPEC92 benchmarks, evaluate its effectiveness. This evaluation indicates that for the configurations considered, the multicluster architecture may have
significant performance advantages at feature sizes below
0.35m, and warrants further investigation.
1 Introduction
A continuing challenge in the design of microprocessors
is the need to balance the complexity of the hardware
againstthe speed at which it can be clocked. This challenge
exists because increased hardware complexity can impact
the cycle time of a processor in two ways. First, if a component is on a critical timing path, increasing the complexity of the component may increase its cycle time, and thus,
that of the processor. Second, because complex components may be physically larger and further apart, the time for 
Copyright 1997 IEEE. Published in the Proceedings of Micro-30,
December 1-3, 1997 in Research Triangle Park, North Carolina. Personal
use of this material is permitted. However, permission to reprint/republish
this material for advertising or promotional purposes or for creating new
collective works for resale or redistribution to servers or lists, or to reuse
any copyrighted component of this work in other works, must be obtained
from the IEEE. Contact: Manager, Copyrights and Permissions / IEEE
Service Center / 445 Hoes Lane / P.O. Box 1331 / Piscataway, NJ 08855-
1331, USA. Telephone: + Intl. 908-562-3966.
signals to travel between them may be greater, thereby necessitating an increase in the processor's cycle time. One
approach to reducing these two consequences of complexity is to partition the hardware, thereby reducing the complexity and size of components.
In this paper, we introduce a dynamically-scheduled,
partitioned architecture called the multicluster architecture.
This architecture implements dynamic scheduling using
dispatch queues and explicit register renaming hardware, a
basisthatis used in the DEC Alpha 21264 [1] and the MIPS
R10000 [2]. Dispatch queues are used to maintain the pool
of instructions from which the instruction scheduler issues
instructions to the functional units, while register renaming
is used to map the architectural registers (i.e., those named
by instructions) to a larger set of physical registers.
In the multicluster architecture, the dispatch queues,
register files, and functional units are distributed across
multiple clusters. The instructions that are executed by a
cluster  are those dispatched from the dispatch queue of
cluster , and these instructions are the only instructions
that can read or write the physical registers of cluster .
Each cluster is assigned a subset of the architectural registers. This assignment along with the architectural registers named by an instruction determines the cluster(s)
that execute the instruction. Multiple-cluster execution is
used whenever an instruction either names source registers
that are not accessible from within one cluster or names
a destination register that is not uniquely assigned to one
cluster (Section 2.1 discusses the assignment of architectural registers to clusters). The instructions for all clusters
are obtained from a single, shared stream of instructions
that are fetched from a single instruction cache. The data
cache is also shared by all clusters.
The isolation of each cluster's components providestwo
benefits relative to a processor with a non-partitioned architecture that can issue the same number of instructions per
cycle as all the clusters of a multicluster processor. First,
because each cluster issues fewer instructions per cycle,
the register files of a given cluster require fewer read/write
register file &
bypassing
register
renaming
instruction distribution
instruction cache
transfer
buffers
instruction
dispatch
queue
execution
unit
execution
unit
data
cache
mem interface
result
central operand
control result
register file &
bypassing
branch
prediction
register
renaming
instruction
dispatch
queue
instruction
scheduling
control
register file &
bypassing
execution
unit
execution
unit
operand
instruction
scheduling
control
Figure 1: A dual-cluster processor built within the multicluster architecture framework.
ports. As the number of read/write ports largely determines the cycle time of a register file, partitioning reduces
its cycle time and perhaps that of the processor. Indeed,
the DEC Alpha 21264 has a partitioned integer register file
because the integer register file is on a critical timing path
[1]. Second, because each cluster issues fewer instructions
per cycle, the dispatch queue of a given cluster not only
requires fewer read/write ports, but also requires less complex instruction-scheduling logic. Consequently, the cycle
time of the instruction-scheduling hardware will likely be
smaller. For example, since the instruction queues of the
MIPS R10000 are on a critical timing path [2], a smaller
cycle time might have been obtained had the queues been
partitioned.
We begin the discussion of the multicluster architecture
in the next section by describing the architecture, and the
process by which instructions are executed. Then, in Section 3, we describe the most successful of the static instruction scheduling algorithms we developed for it. In Section 4, we then present the results of a simulation-based
evaluation of this algorithm. Finally, in Section 5, we reexamine the motivation for the architecture in light of the
results, and suggest areas for future work.
Without loss of generality, we discuss the multicluster
architecture in terms of a multicluster processor with two
clusters. Further, in our model of such a processor (Figure 1), each cluster comprises a single dispatch queue
(rather than the multiple queues used in the R10000 and
Alpha 21264), and two register files, one for integer values, and the second for floating-point values.
2 The Architecture
This section describes the multicluster architecture, the
process by which instructions are executed, and tradeoffs
in the design of a multicluster processor. A more complete
description is presented in [3].
2.1 Instruction Distribution and Execution
Instructions are read from the instruction cache in fetch
order and are distributed, also in fetch order, to one or both
clusters. If an instruction can't be distributed to a cluster
because a dispatch-queue entry or a physical register is not
available, the instruction stream is stalled until the required
resource becomes available. The distribution of instructions to the clusters is based on the registers named by
each instruction and the cluster(s) to which the architectural registers have been assigned. We use the term local
register to refer to an architectural register that has been assigned to one cluster, and the term global register to refer
to an architectural register that has been assigned to both
clusters. Global registers would typically be used for stack
and global pointers, as well as other commonly used variables. Owing to the ease of detecting the architectural registers named by an instruction and the cluster(s) to which
each register has been assigned, the hardware required for
instruction distribution is relatively simple. In the simplest
case, for a two-cluster configuration, local registers could
be identified using a bit-mask, and the cluster assignment
for these registers could be based on whether the register
number is even or odd. Simple distribution criterion are especially important if distribution to more than one cluster is
anticipated. Although a simple hardware mechanism exists
to support the dynamic reassignment of the architectural
registers (see [3]), we assume that the assignment is static.
When an instruction is executed that names a local register  as a destination, the value computed by the instruction is stored in a physical register of the cluster to which
register  has been assigned. But, when an instruction is
executed that names a global register 	 as a destination,
the value computed by the instruction is stored in a physical register of each cluster. Thus, two physical registers
are required to maintain the value of a global register, one
in each cluster, but only one physical register is required to
maintain the value of a local register.
Execution Details
The execution of an instruction requires that the hardware
perform a sequence of steps, with this sequence dependent
on the cluster(s) to which each of the named (architectural)
registers are assigned. There are various scenarios under
which these sequences occur, and these can be grouped into
five main categories. To better examine these categories,
consider the the integer add instruction 



 , and
a scenario from each category.
Scenario one: suppose that the three registers named
by this instruction are local registers assigned to cluster
 . To perform the add, the hardware first distributes the
instruction to cluster  . The distribution process comprisesthree tasks: the source registers 
  and 
  are mapped
to the physical registers of cluster  , the destination register 
  is renamed to a free physical register of cluster  ,
and the instruction is inserted into a free entry in the dispatch queue of cluster  . Later, after the source operands
are available and when a suitable functional unit is available, the hardware issues the instruction, reads its source
operands, performs the add, and writes the result into the
bound physical register.
Scenario two: suppose again that all three registers
are local registers, but with source register 
  and destination register 
  assigned to cluster  , and source
register 
 assigned to cluster  . To perform the add,
the hardware distributes a copy of the instruction to both
clusters. Dual distribution provides the mechanism by
which the source operand that is not available in cluster
 (i.e., 
 ) is transfered to the cluster that performs the
computation (i.e., cluster  ).
The master copy does the computation with the slave
copy supplying one of the source operands. The master
copy is executed by cluster  because the majority of the
local registers named by the instructions are assigned to
cluster  (the selection of the master copy's cluster is discussed further in [3]). When the master copy is distributed
to cluster  , 
 is renamed using a physical register belonging to this cluster. However, when the slave copy is distributed to cluster  , it is not allocated a physical register
because the destination of the instruction is a local register
that has been assigned to cluster  . Figure 2 shows the
steps taken to execute the add instruction by executing the
master and slave copies. These steps are explained below.
There exists a data dependence between the slave copy
time
addition
done
master
issued
reg r2
written
slave
issued
reg r0 written into operand
transfer buffer of cluster C1
cluster C2
reg r0
cluster C1
reg r1
reg r2
Figure 2: Dual execution of the instruction 
  

  
 
when operand r is forwarded to cluster  .
and the immediately preceding instruction in fetch order
that wrote 
 . The slave copy can be issued only after this
dependence is resolved and when an integer issue slot is
available. The hardware requires an integer issue slot to
issue the slave copy because the slave copy must read the
value of 
 from the integer register file, and to do so requires access to a read port. There also exists a data dependence between the master copy and the immediately
preceding instruction in fetch order that wrote 
  , and a dependence between the master and slave copies. This intercopy dependence guarantees that the master copy will be
issued only when its second operand, that is 
 , is available. Therefore, the master copy will be issued after both
input dependences are resolved and when a suitable functional unit is available.
In the write-back stage of the execution pipeline, the
slave copy writes the value of 
  into an entry in the operand transfer buffer (Figure 1) of cluster  , the master
copy's cluster. An entry in the operand transfer buffer is
allocated to the slave copy when it is issued. If an entry
is not available, then the slave copy is blocked from being
issued, and in certain circumstances, an instruction-replay
exception is required to avoid issue deadlock (see [3] for
more details). When the slave copy writes the value into
the allocated entry, it also stores the unique ID of the instruction of which it is a copy. This ID is used by the hardware to associatively search the operand transfer buffer to
locate the operand for the associated master copy. The dependence between the master copy and the slave copy is
removed when the slave copy is issued, thereby permitting
the master copy to be issued as soon as the next cycle. After
the master copy obtains the value, the entry allocated to the
slave copy is freed. This entry can be used by another instruction in the next cycle.
Scenario three: suppose again that the two source
registers are local registers assigned to cluster  , but
that the destination register 
 is assignedto cluster  .
To perform the add, the hardware again distributes a copy
of the instruction to both clusters, but this time, dual distribution provides the mechanism by which the result of the
computation is transfered to the cluster to which the destin-
time
slave
issued
reg r2 written
addition
done
master
issued
result copied into result
transfer buffer of cluster C2
cluster C2
cluster C1
reg r0
reg r1
reg r2
Figure 3: Dual execution of the instruction 
  

  
 
when result is forwarded to cluster  .
ation register has been assigned. Figure 3 shows the steps
taken to execute the add instruction for this scenario; these
steps are explained below.
Because the two source operands for the operation are
located on the same cluster, the master copy of the instruction will be issued first. Then, the result is computed, and
forwarded to the slave copy. The slave copy is then issued
and it writes the forwarded result into the physical register
bound to 
 . Unlike in the second scenario, the physical register is allocated to the slave copy because the destination
register is assigned to the slave copy's cluster  and not
the master copy's cluster  . The data transferis performed
by writing the value computed by the master copy into an
entry in the result transfer buffer of cluster  . This entry
is freed after the slave copy reads the result out of the entry
prior to writing the result into the bound physical register.
To prevent the slave copy from being issued before the result is available, there exists a dependence between the slave
and master copies. This dependence is removed two cycles
before the master copy is due to finish computing the result, and, thus, for simple one-cycle latency instructions like
the add, the slave copy can be issued as soon as one cycle
after the master copy is issued (see [3] for a description of
the execution pipeline). Finally, as also discussed in [3],
separate result and operand transfer buffers are provided to
reduce implementation complexity and to reduce the number of times an instruction-replay exception is required to
free up a buffer entry.
Scenario four: suppose again that both source registers are local and assigned to cluster  , but that the
destination register 
 is a global register. Because the
destination is a global register, both the slave and master
copies are allocated physical registers when they are inserted into their respective dispatch queues. Thus, dual distribution provides the mechanism by which (1) a physical
register in each cluster is allocated for the new value of 
 ,
(2) the inter-instruction dependences arising from the use
of 
  are maintained in each dispatch queue, and (3) the
value computed by the master copy is written into the two
allocated physical registers.
The same sequence of steps as for the third scenario is
time
result
written
into C2’s
buffer
addition
done
master
issued
C1’s copy of
reg g2 written
reg g2
cluster C1
cluster C2
reg g2
reg r0
reg r1
slave
issued
C2’s
copy of
reg g2
written
Figure 4: Dual execution of the instruction 
  

  
 
when global result is forwarded to cluster  .
performed to execute the add, with the exception that, when
the master copy writes the resultinto the slave copy'sresult
transfer buffer, the master copy also writes the result into
the physical register it was allocated. Figure 4 illustrates
this scenario.
Scenario five: finally, suppose again that source registers 
 and 
 are local registers and the destination
register 
 is a global register, but that 
 has been
assigned to cluster  , while r  has been assigned to
cluster  . As in the second scenario, the slave copy is
issued only after its data dependence is resolved and when
both an integer issue slot and an operand transfer buffer
entry are available. Once the slave copy writes the operand
into the allocated entry, the hardware suspends it. The
master copy is then issued only after its data dependence
is resolved, and when both a suitable functional unit and a
result transfer buffer entry are available. When the master
copy obtains the forwarded source operand, it frees the
operand transfer buffer entry (which is associated with
its cluster). It then computes the result, and writes it into
both the allocated result transfer buffer entry (which is
associated with the slave copy's cluster) and into its own
register file. Finally, the slave copy is awakened, it obtains
the result, frees the result transfer buffer entry, and writes
the result into its own register file. Figure 5 illustrates the
steps for this scenario.
reg g2
reg g2
cluster C1
cluster C2
reg r1
reg r0
time
slave
issued
slave
wakes
slave
suspended C2’s
copy of
reg g2
written
reg r0
written
into C1’s
buffer
addition
done
master
issued C1’s copy of
reg g2 written
result written into C2’s
buffer
Figure 5: Dual execution of the instruction 

 

 when operand 
 is forwarded to cluster  and global
result is forwarded to cluster  .
The performance obtained from a multicluster processor
is affected by the number of instructions distributed to
one cluster, the number distributed to two clusters, and
how these instructions are arranged in the instruction fetch
stream; this order is important because it affects resource
availability. Dual-distributed instructions require more
hardware resources than instructions distributed to one
cluster. Thus, a larger number of dual-distributed instructions contributesto a smaller instruction throughput. In addition, when an instruction is dual distributed,the two copies operate as a pair to perform the required task. Because
the mechanism that supports this cooperation introduces
some overhead, a dual-distributed instruction requires more
clock cycles to execute than a single-distributed instruction (assuming all other conditions are the same). Thus,
not only do dual-distributed instructions contribute to a reduction in throughput, they may also require more clock
cycles to execute. However, note that these two negative
effects are offset by the reduction in the cycle time of the
processor clock that is provided by partitioning the hardware resources. Consequently, even though an application
may require more clock cycles to execute on a multicluster
processor than on a single-cluster processor, the run time
may be reduced.
2.2 Related Architectures
A number of similarities and differences exist between
proposed and existing architectures and the multicluster architecture. This section briefly examines a few such architectures.
The aim of the multicluster architecture is to decrease
the cycle time of the processor to permit a single thread
of execution to run faster. Partitioning of components
to increase performance was also one of the aims of the
decoupled access/execute architecture proposed by Smith
[4]. This architecture and the multicluster architecture
both consists of two tightly-coupled clusters interconnected by buffers. However, the two clusters of the decoupled
access/execute architecture are statically scheduled, with
one responsible for reading and writing memory, and the
other responsible for computing results. The decoupled access/execute architecture also requires that values be written into and read from the inter-cluster buffers in the same
order. Thus, while the access and execute instruction
streams may “slip” with respect to each other, instructions
from different streams cannot be executed out of order.
In the multicluster architecture and the Multiflow architecture [5], the physical registers and the functional units of
both architectures are distributed among the clusters of the
respective machine. However, while a mechanism exists
in the multicluster architecture for accessing the registers
in other clusters, in the Multiflow architecture, for an ALU
(arithmetic logic unit) to use a value stored in the registers associated with another ALU, this value must first
be explicitly copied to a register in the register file of .
This two-step processis coordinated by the compiler, a fact
that underlines that the hardware is completely predictable,
which is not true for the multicluster architecture due to
its use of dynamic scheduling. One implication of the predictability of the Multiflow architecture is that it allows the
Multiflow compiler to balance the work to be performed
across all ALUs and to encode it into a single instruction
stream. However, as discussed in Section 3, balancing the
workload across the clusters of the multicluster architecture is more difficult due to the unpredictability of dynamic
scheduling.
The Multiscalar architecture [6] is in some ways similar to the the multicluster architecture in that both derive
benefits from partitioning a large processor into several
clusters of execution resources. In addition, both architectures share the common need for good static scheduling of
the application to keep all functional units busy. However,
there are a number of important differences. First, the
basis used to distribute the instructions to the clusters of a
Multiscalar architecture is information encoded in the binary by the compiler, whereas for the multicluster architecture, the basis is the architectural registers named by each
instruction. Second, each cluster of the Multiscalar architecture independently fetches the instructions assigned to
it, whereas the clusters of a multicluster architecture share
a common instruction fetch stream. As a result of these
two differences, instruction scheduling for the multicluster
architecture is more complex. A third important difference
is that, while the Multiscalar architecture attempts to exploit parallelism between threads each consisting of many
basic blocks, while the multicluster architecture primarily
exploits parallelism within and between basic blocks.
Simultaneously multithreaded processors [7] and
tightly-coupled multiprocessors [8] share the property that
they are capable of simultaneously executing independent
or co-operating sequences of instructions, called threads.
The aim of supporting this capability is to reduce the number of clock cycles required to execute multiple threads
sequentially. In contrast, the aim of the multicluster
architecture is to decrease the cycle time of the processor
to permit a single thread of execution to run faster.
3 Static Instruction Scheduling
Static instruction scheduling is the process by which,
prior to the execution of an application, the machine-level
instructions are ordered with the goal of minimizing the
number of clock cycles required to execute the application.
For a multicluster processor to meet this goal, during the
execution of an application, the instructions must be balanced across the clusters, with each cluster concurrently
performing similar amounts of work, and with no instructions executed by more than one cluster. A balanced workload is desired because each cluster contains only a sub-
set of the total available hardware resources, while singlecluster instruction distribution is desired because dual distribution increases hardware-resource requirements and execution latency. However, the workload balance cannot be
directly addressed by the compiler because the work done
by a cluster is a function of the order in which instructions are issued, and the issue order is not deterministic for
dynamically-scheduled processors. Thus, the compiler can
only indirectly address the workload balance by seeking to
balance the dynamic distribution of instructions, under the
assumption that a balanced distribution will result in a balanced workload.
The objective of a balanced distribution competes
against the objective of a minimum number of dualdistributed instructions. However, in practice, for the
benchmarks considered, the performance cost of dualdistributing instructions was much less than the cost of not
taking full advantage of the available hardware resources
(see [3]). Consequently, the primary objective is to generate a code schedule, which when run, generates an instruction stream in which the instruction-distribution is balanced. To address the two objectives, the compiler considers each (static) instruction individually, and seeks a register assignment for the data values used by the instructions. The criterion used to select a register and hence a
cluster for a data value is whether the instruction distribution is likely to be balanced. If it is not, the compiler must
select a register that is assigned to the under-subscribed
cluster. If the distribution is likely balanced, the compiler
can select a register that allows the instruction to be distributed to only one cluster.
To select a register for the value used by an instruction,
the compiler must first determine whether the instruction
distribution is likely balanced around the instruction at run
time. To do so, the compiler must know the order in which
instructions will be fetched and distributed. Because this
information is implicit in an ordered sequence of instructions, the allocation of values to registers must be carried
out after the instructions are ordered into a code schedule.
That is, prepass scheduling must be used. Once the instruction balance has been estimated for an instruction, to
make the register selection(s) for the instruction, the compiler must take into account the inter-dependences between
instructions that arise from one or more instructions using
a value generated by another. As a result of this source of
dependences, decisions made for one instruction can affect
those made for other instructions. A useful abstraction for
capturing this source of dependences is that of a live range
[9].
3.1 Code Generation Methodology
The code generation methodology, which takes into account the issues introduced in the previous subsection,
comprises the following six steps.
1. The application is compiled into an intermediate language (IL) to which are applied conventional optimizations like common subexpression elimination and
constant propagation.
2. The IL instructions are arranged into a (static) code
schedule. The IL instructions correspond one-to-one
to the machine-level instructions of the processor, but
unlike the machine-level instructions, the IL instructions name live ranges and not registers.
3. The live ranges associated with the stack pointer and
the global pointer are designated as candidates for
global registers; all other live ranges are designated
as candidates for local registers. (The rational for this
designation is discussed in [3].)
4. The live ranges that are candidates for local registers
are then partitioned with the goal of maximizing the
concurrent utilization of both clusters, and minimizing
the number of dual-distributed instructions.
5. The live ranges are allocated to the architectural registers with global-register candidates allocated to
global registers and local-register candidates allocated
to local registers.
6. The machine-level instructions (including those required for register spilling) are arranged into a code
schedule.
Steps 1, 2, 4, and 5 correspond to the four compilation
problems: code optimization, code scheduling, live range
partitioning, and register allocation. Although solutions to
these four problems must handle the unique characteristics
of the multicluster architecture, we have focused on solving
the third problem, live range partitioning, since this problem captures most of the idiosyncrasies of the architecture.
In Section 3.5, we briefly describe the most successful of
the novel techniques we developed for solving this problem, while in Sections 3.2-3.4, we briefly describe how
we modified existing techniques to solve the other three
compilation problems. A more extensive description of our
solutions to the four problems is given in [3].
3.2 Code Optimization
The code optimization problem can be solved using
techniques such as those described by Aho et al. [9]. Since
this problem arises early in the compilation of an application, solutions to it are relatively independent of the unique
characteristics of the multicluster architecture. Thus, to
limitthe scope of our research,the existing techniques were
used without modification.
3.3 Code Scheduling
The code scheduling problem can best solved using
techniques that tend to generate large basic blocks. Such
techniques, like trace scheduling [5], are preferable due to
the necessity of estimating the run-time instruction imbalance on a per-basic-block basis when performing live range
partitioning. The run-time instruction imbalance is a function of the order in which the basic blocks appear in the
fetch stream, and the static imbalance of each block. To
ensure a given degree of balance is obtained at run time,
the compiler would have to take into account all control
flow paths by which a given basic block can be reached,
and the cluster allocation of the live ranges used within the
basic block. Owing to the complexity of concurrently considering these two effects, scheduling on a per-basic-block
basis is mandated.
3.4 Register Allocation
Finally, the register allocation problem can best be
solved using the graph-coloring technique developed by
Briggs et al. [10]. This technique is most suitable because
it separates the process of coloring nodes from the process
of spilling live ranges. The separation of these two phases
provides a convenient framework for implementing the desire to spill a live range first to a local register in the other
cluster and, if no register is available, then to memory. In
addition, the separation of the phases increases the likelihood that a live range will be allocated a register [10] and
allows for other optimizations [3]. These features compete
against the increased likelihood that more live ranges will
be spilled since each cluster of the multicluster architecture
is allocated only a subset of the architectural registers.
3.5 Live Range Partitioning
This section describes the local scheduler, which was
developed to solve the live range partitioning problem. The
approach taken by the local scheduler is to determine for
each live range ! in the intermediate-language representation of an application, the cluster to which ! should be
assigned so as to ensure the instruction-distribution at run
time is balanced in the vicinity of every instruction that
reads or writes !.
To determine cluster assignments for the live ranges, the
local scheduler begins by sorting the basic blocks according to the number of times the first instruction in each basic
block is estimated to be executed1
. Basic blocks with equal
estimates are sorted by the number of static instructions in
each block. Then, the basic block having the largest estimate and the greatest number of instructions is removed from
the list, and a bottom-up,in-order traversalis carried out on
the instructions in the block. As an example, consider the
control flow graph shown in Figure 6, and the execution
1These estimates are derived from profiling the execution of the application on a dual-cluster processor.
1: C = 0
basic block #2 (10) basic block #3 (10)
basic block #1 (20)
basic block #4 (100)
basic block #5 (20)
3: G = [S] + 8
4: H = [S] + 4
5: G = [S] + E
6: H = [S] + 12
12: D= C + G
A= G + 10 "
8:
B= A x A
G= B / H
C= G + C
9:
10:
11:
2: E = 16
7: S = H + E
Figure 6: Example control flow graph. In the graph, the
numbers in parentheses give the dynamic-execution estimates for each basic block. Furthermore, while live range #
is assumed to be a candidate for a global register, all other
live ranges are assumed to be candidates for local registers.
estimates for each block given by the numbers in the parentheses. For this control flow graph, the basic blocks will
be traversed in the order 4, 1, 5, 3, and 2.
The purpose of this traversal is to visit each instruction in turn, and if the instruction writes an unassigned
live range, choose a cluster for the live range. A cluster
is chosen for a live range !, which is written by an instruction $, by first examining the instruction-distribution
around the instruction. If the distribution is not balanced,
the cluster chosen for ! will be the one that reduces the
degree of imbalance. An instruction-distribution is considered unbalanced in the vicinity of an instruction $ if,
at run time, at the point in time that $ is distributed to one
or both clusters for execution, there has been more than a
given number of instructions distributed to one cluster than
the other; this number is a compile-time constant. (The
reader is referred to [3] for a more formal definition of imbalance.) If the distribution is estimated to be balanced,
however, then the scheduler determines the cluster that is
preferred by the majority of the instructions that read or
write !. The scheduler selects cluster  as the preferred
cluster for one of these instructions if the assignment of !
to  will allow the instruction to be distributed to only one
cluster.
Thus, once the bottom-up traversal of a basic block is
completed, there will remain no unassigned live ranges
among those that are written by the instructions in the basic
block. After completing the bottom-up traversal of a basic
block, the scheduler removes the next basic block from the
list, and carries out a bottom-up traversal on its instructions.
This process continues until all basic blocks are visited. As
a result of this process, the cluster-assignment for a live
range will be determined the first time an instruction is encountered that writes it during the basic-blocks traversals.
Thus, for the example of Figure 6, the local scheduler will
visit the basic blocks in the order 4, 1, 5, 3, and 2, and, as
a result, the live ranges will be assigned to clusters in the
order , 	, %, , &, ', and (. Live range #, however, is
not considered during live range partitioning because it is
assumed to be a candidate for a global register.
4 Performance Assessment
The performance impact of the schedulers we developed
was determined by using ATOM [11], an object-code instrumentation system, to simulate the execution of several
SPEC92 benchmarks. For these simulations, we first compiled the benchmarks using the standard Digital Unix compilers for 21064-based workstations to produce a native
binary. Then, using ATOM, we analyzed the native binary to discover the data and control dependences between
instructions, and the live ranges these instructions read and
write. While the use of ATOM and the standard compilers
prohibited the use of compilation techniques (e.g.,loop unrolling) not supported by the Digital Unix compilers, but
which might improve the performance of the multicluster
architecture, it simplified the implementation of the schedulers and permitted the fundamental scheduling problems
to be the focus of the work.
After identifying the live ranges, they were partitioned
and assigned to the architectural registers using one of
the schedulers; the object code generated by the schedulers is called the rescheduled binary. For this step, the
schedulers assumed that the even-numbered architectural
registers were assigned to cluster  and the odd-numbered
registers to cluster  . This architectural-register-to-cluster
assignment was determined through the analysis of early
simulation results (see [3] for more details). Then, the rescheduled binary was instrumented using ATOM and linked
with the multicluster simulator. Instrumentation took into
account the new register assignments for each instruction
and any code required to spill live ranges. Finally,the combined application-simulator wasthen run and the number of
(simulated) clock cycles required to execute the application
was recorded. This number is our performance metric.
To evaluate the impact of rescheduling, we compared
the performance obtained from the rescheduled binaries
when they were executed on a dual-cluster processor to
that obtained when the native binary was executed on a
single-cluster processor. For this comparison, the singlecluster processor was configured with the same number of
resources as the entire dual-cluster processor. Although the
evaluation was done for both four-way and eight-way issue
processors, the results presented here are only for an eightway issue processor because these more clearly show the
important trends.
4.1 Simulation Model
The single-cluster and dual-cluster processors each implement a RISC, superscalar processor whose instruction
set is based on the DEC Alpha instruction set. Each
processor supports non-blocking loads and non-blocking
stores, and allows all instructions to be speculatively executed. Each processor includes separate data and instruction caches, each of which is a 64-Kbyte, two-way set associative cache. The data cache is assumed to use an inverted MSHR [12], and thus, imposes no restriction on
the number of in-flight cache misses. The memory interface between the instruction and data caches, and the lower
levels of the memory hierarchy is assumed to have a 16-
cycle fetch latency and unlimited bandwidth.
In each clock cycle, each processor can fetch up to
12 instructions from the instruction cache, and can insert
these instructions into the dispatch queue(s). The singlecluster processor has a 128-entry dispatch queue, while
each cluster of the dual-cluster processor has a 64-entry
dispatch queue. To enable fetching beyond conditional
branches, both processors use a branch prediction scheme
proposed by McFarling [13] that comprises a bimodal predictor, a global history predictor, and a mechanism to select
between them; all other control flow instructions are assumed to be 100% predictable. As instructions are inserted
into a dispatch queue, the architectural registers named by
each are renamed to the corresponding physical registers.
The single-cluster processor has 128 integer and 128 floating point registers, while each cluster of the dual-cluster
processor has 64 integer and 64 floating point registers.
In each clock cycle, the instruction scheduling logic selects instructions to issue out of the dispatch queues using
a greedy algorithm that issues the oldest, ready-to-issue instruction in a queue first. The single-cluster processor can
issue up to eight instructions per cycle, while each cluster
of the dual-cluster processor can issue at most four instructions per cycle. The instruction issue rules for the processors are given in the first and second rows of Table 1,
while the functional unit latencies are given in the third
row. Correctly executed instructions are retired in program
order with each processor capable of retiring no more than
eight per cycle. Finally, both processors are assumed to
implement precise exceptions, and each cluster of the dualcluster processor has eight operand- and eight result-buffer
entries.
4.2 Results
A common (and expected) trend is that more clock
cycles are required to execute a benchmark on the dualcluster processor than on the single-cluster processor. This
increase is attributable to an increase in the number of stalls
instruction types
all integer floating point loads & control
# all multiply other all divide other stores flow
1 number issued single 8 8 8 8 4 4 4 4 4
2 per cycle dual, per cluster 4 4 4 4 2 2 2 2 2
3 latency in cycles 6 1 8/16 3 1 ) 1
Table 1: Instruction-issue rules for the single-cluster (row #1) and the dual-cluster (row #2) processors. Row #3 gives the
functional-unit latencies. All functional units are fully pipelined with the exception of the floating-point divider. The divider
is not pipelined and has an eight-cycle latency for 32-bit divides, and a 16-cycle latency for 64-bit divides. ) There is a single
load-delay slot.
of the instruction-fetch stream, a reduction in the number of
instructions issued per cycle, an increase in the instructionissue disorder, and a slight increase in the data-cache miss
rate due to the increased issue disorder. A useful metric is
*,+.-0/21
*436587:9 1<; , where =?>A@CBED:F8G is the number of (simulated) clock
cycles required to execute the native binary of a benchmark
on the single-cluster processor, while =HJIK0F is the number of (simulated) clock cycles required to execute either
the native binary or the rescheduled binary on the dualcluster processor. This performance ratio is said to indicate a speedup if it is less than one, and a slowdown if it
is greater than one. Note, because performance is really a
product of the number of clock cycles and the period of the
clock L, a multicluster processor will perform as well as
or better than a single-cluster processor if the clock period
of
*
the multicluster processor LH2IKMF is less than or equal to
36587:9 1<;
*+.-0/21N L>A@CBED:F8G .
The performance ratios for each benchmark are presented in Table 2 as the percentage speedup/slowdown. This
percentage is equal to OPPRQSOUT *,+.-0/21
*V3W5X7:9 1<;Y . Comparison of
all 12 data points indicates that in general, the benchmarks
incurred a slowdown in the number of clock cycles of
between 5% and 41%. Further comparison of the performance ratios indicates that with the exception or ora, the
speedup ratio
benchmark none local
(1) (2) (3)
compress -14 +6
doduc -21 -15
gcc1 -15 -10
ora -5 -22
su2cor -36 -25
tomcatv -41 -19
Table 2: The speedup ratios OPPZQ:O?T *+.-0/21
*3W5X7:9 1<; Y obtained
when the benchmarks were not rescheduled (column 2) and
when the local scheduler was used to rescheduling them
(column 3).
use of the local scheduler significantly reduces the slowdown incurred from running on the dual-cluster processor.
Furthermore, in the case of compress, with the use of the
local scheduler,the benchmark performs better on the dualcluster processor than the single-cluster processor. This
increase in performance is due to the single-cluster processor having a larger dispatch queue. The size of the dispatch queue is important for two reasons. First, with larger
dispatch queues, there is likely to be a greater amount of
time between when a branch prediction is made and when
the branch predictor tables are updated with the direction
taken by the branch2
. Hence, with larger dispatch queues, a
greater number of predictions may be based on information
that may not reflect the direction taken by immediately preceding branches in program order. The size of the dispatch
queue is also important because a larger dispatch queue allows for more disorder in the issuing of instructions. In the
case of compress, this increase in issue disorder leads to
an increase in the cache miss rate, and thus, a performance
degradation.
In general, better performance is obtained with the
local scheduler because the local scheduler generates code
schedules that result in better utilization of hardware resources. In particular, the local scheduler resulted in a
higher degree of concurrent utilization of both clusters, and
a reduction in the number of dual-distributed instructions.
In addition, with the local scheduler, instructions were issued more in order, with the effect that significantly fewer
instruction-replay exceptions are required to free up an operand transfer buffer entry. One exception to this trend,
however, is ora, for which the use of the local scheduler
significantly increased the number of instruction replays,
thus degrading performance. A more detailed analysis of
the impact of the local scheduler is presented in [3].
Considering the ratios for the local scheduler indicates
that its use results in a worst-case slowdown of 25%. To
compensate for the increase in clock cycles that this slowdown represents, the dual-cluster processor would have to
use a processor clock with a period 20% smaller ([\OPPT
2The prediction is made at the point ofinsertion into the dispatch queue
while the updating occurs after the branch is executed.
OPP^]+.-0/J1
]
36587_9 1<; [`OPPVTaOPP *3W5X7:9 1<;
*+.-0/21 [bOPPVTaOPP *3W5X7:9 1<;
2c<:de *436587_9 1<; ).
Recently Palacharla et al. have created delay models for
the critical paths of dynamically scheduled superscalar processors [14] as a function of issue width. They report that
in a 0.35m process, the worst case delay increased from
1248ns for a four-issue processor to 1484ns for an eightissue processor, an increase of 18%. Given that there is
only an 18% difference between the cycle times of the fourissue and eight-issue processors in a 0.35m process generation, reducing the cycle time through partitioning would
not improve overall performance. However, for a 0.18m
process generation, Palacharla et al. found that the worstcase path would increase by 82% when moving from a
four-issue processor to an eight-issue processor. The larger relative delays for wide-issue machines at 0.18m feature sizes is due to wire delay increasing relative to gate
delays as feature sizes are reduced. Thus, communication
becomes relatively more expensive in comparison to computation. Given this larger cycle time difference between
narrow and wide issue machines at smaller feature sizes,
the net effect of partitioning in the multicluster architecture
could result in a significant overall performance increase.
5 Conclusions
In this paper we have introduced the multicluster architecture, a decentralized, dynamically-scheduled architecture. In this architecture, the register files, dispatch
queue, and functional units of the architecture are distributed across multiple clusters, and each cluster is assigned
a subset of the architectural registers. The motivation for
partitioning these resources is to reduce the size and complexity of components that are likely to be on the critical
timing path of a centralized processor, and in the process,
to reduce the cycle time of the decentralized processor.
The architecture provides a mechanism to allow the registerfile of one clusterto be accessed by instructions being
executed on another cluster. This mechanism is based on
distributing an instruction to more than one cluster for execution. The multiple distribution of instructions increases
the number of clock cycles required to execute these instructions, and reduces the number of instructions that can
be simultaneously in execution. However, these two negative effects are offset by the reduction in the cycle time
of the processor clock that is provided by partitioning the
register file and other hardware resources. Consequently,
an application may require more clock cycles to execute on
a multicluster processor than on a single-cluster processor,
but its run time may be smaller.
There are two requirements for an application to perform well when executing on a multicluster processor.
First, the instructions that are required to perform the task
must be balanced across the clusters, with each cluster concurrently performing similar amounts of work. However,
this requirement cannot be directly addressed by the compiler because the work done by a cluster is a function of the
order in which instructions are issued, and the issue order
is not deterministic. Thus, the compiler can only indirectly
address the requirement by ensuring that the distribution
of instructions to clusters is balanced. The second requirement is that the number of instructions distributed to more
than one cluster must be minimized. This requirement
seeks to counter the above noted two negative effects of
multiple distribution. Since the distribution of instructions
is based on the architectural registers named by the instructions, static instruction scheduling is the process by which
the instructions are ordered and architectural registers are
assigned to the operands and results of the instructions.
In this paper, we have described a novel algorithm we
developed to implement this process. We have also described some of the results from simulations we performed
on a number of dual-cluster processor configurations to
evaluate the effectiveness of the algorithms. Using the processor cycle time analysis of Palacharla et al. for a 0.35m
process, the negative instructions-per-cycle effects of partitioning would slightly outweigh the advantage gained from
a reduction in cycle time. However for smaller feature
sizes, such as in their 0.18m process model, a significant net performance improvement could be obtained. Thus
we believe the multicluster architecture warrantsfurther investigation.
6 Future Work
A promising area for further investigation are optimizations that require information derived from the source
code of an application, which we did not consider owing to
the limitations of the framework we used to implement the
schedulers. For example, techniques such as superblock
scheduling [15], and trace scheduling [5] might be used
to increase the number of instructions that can be jointly
scheduled, thus permitting a better estimation of the runtime distribution of the workload. Loop unrolling, which is
a part of trace scheduling, could also be used to generate a
code schedule in which multiple iterations of a loop were
interleaved, with each iteration scheduled to use a separate cluster of a multicluster processor. To further increase
the performance of loop unrolling, schemes could be devised to decrease the amount of interaction between the iterations of the loop, and thus, the number of inter-cluster
data transfers. One such scheme is to duplicate the code
that calculates addresses. A second scheme is to allocate
key variables to global registers so that the variables can be
accessed from within each cluster without an inter-cluster
data transfer.
A second set of techniques might be used to exploit
the hardware mechanism (see [3]) that was developed to
permit the dynamic reassignment of the architectural registers to the clusters of a multicluster processor. In
particular, the compiler could provide the hardware with
hints to indicate when the reassignment could be made,
and to directly specify the architectural-register-to-cluster
assignment for each architectural register. This functionality would provide additional flexibility in separating a sequence of instructions into a number of partiallyindependent threads.
Acknowledgments
The research described in this paper has been partially
funded by the Natural Sciences and Engineering Research
Council of Canada and by Digital Equipment Corporation.
We thank Brad Calder and Alan Eustace for helping us
with the ATOM simulation infrastructure, Annie Warren
and Jason Wold for logistical support while our simulations
ran, and the other WRL-ites for putting up with these simulations. In addition, we thank the anonymous reviewers
for their comments, and Subbarao Palacharla and Pritpal
Ahuja for their early work on the architecture. Finally, we
thank Digital Equipment Corporation for providing us with
the Alpha AXP workstations.
References
[1] Linley Gwennap. Digital 21264 Sets New Standard.
Microprocessor Report, 10(14), 1996.
[2] Kenneth C. Yeager. The MIPS R10000 Superscalar
Microprocessor. IEEE Micro, 16(2):28–40, 1996.
[3] Keith I. Farkas. Memory-system Design Considerations for Dynamically-scheduled Microprocessors. PhD thesis, Department of Electrical and Computer Engineering, University of
Toronto, Ontario, Canada, January 1997. (URL:
http://www.eecg.toronto.edu/ffarkas/thesis phd.html).
[4] James E. Smith. Decoupled Acess/Execute Computer
Architecture. In the Proceedings of the 9th International Symposium on Computer Architecture, pages
112–119, 1982.
[5] P. Geoffrey Lowney, Stefan Freudenberger, Thomas
Karzes, W.D. Lichtenstein, Robert P. Nix, John S.
O'Donnell, and John C. Ruttenberg. The Multiflow
Trace Scheduling Compiler. Journal Of Supercomputing, 7(1-2):51–142, May 1993.
[6] GurindarS. Sohi, Scott E. Breach, and T. N. Vijaykumar. Multiscalar processors. In the Proceedings ofthe
22st International Symposium on Computer Architecture, pages 414–425, 1995.
[7] Dean M. Tullsen, Susan J. Eggers, Joel S. Emer,
Henry M. Levy, Jack L. Lo, and Rebecca L. Stamm.
Exploiting Choice: Instruction Fetch and Issue on
an Implementable Simultaneous Multithreaded Processor. In the Proceedings of the 23rd International
Symposium on Computer Architecture, pages 191–
202, May 1996.
[8] Basem A. Nayfeh, Lance Hammond, and Kunle
Olukotun. Evaluation of Design Alternatives for a
Multiprocessor Microprocessor. In the Proceedings of
the 23rd International Symposium on Computer Architecture, pages 67–77, May 1996.
[9] Alfred V. Aho, Ravi Sethi, and Jeffrey D. Ullman. Compilers, Principles, Techniques and
Tools. Addison-Wesley Publishing Company, Reading Mass., 1986.
[10] Preston Briggs, Keith D. Cooper, and Linda Torczon.
Improvements to graph coloring register allocation.
ACM Transactions on Programming Languages and
Systems, 16(3):428–455, May 1994.
[11] Amitabh Srivastava and Alan Eustace. Atom: A system for building customized program analysis tools.
In the Proceedings of the ACM SIGPLAN `94 Conference on Programming Languages, March 1994.
[12] Keith I. Farkas and Norman P. Jouppi. Complexity/Performance Tradeoffs with Non-Blocking Loads.
In the Proceedings of the 21st International Symposium on Computer Architecture, pages 211–222,
1994.
[13] Scott McFarling. Combining branch predictors. DEC
WRL Technical Note TN-36, 1993.
[14] SubbaraoPalacharla, NormanP. Jouppi, and James E.
Smith. Complexity-EffectiveSuperscalar Processors.
In the Proceedings of the 24th Annual International
Symposium on Computer Architecture, pages 206–
218, 1997.
[15] Pohua P. Chang, Scott A. Mahlke, William Y. Chen,
Nancy J. Warter, and Wen-mei W. Hwu. IMPACT:
an ArchitecturalFramework for Multiple-InstructionIssue Processors. In the Proceedings of the 18th Annual International Symposium on Computer Architecture, pages 266–275, 1991.

Now a newer paper, which you should defer to as it is more relevant to my project.
Latest updates: hps://dl.acm.org/doi/10.1145/2800787
RESEARCH-ARTICLE
Revisiting Clustered Microarchitecture for Future
Superscalar Cores: A Case for Wide Issue Clusters
PIERRE MICHAUD, Institute for Research in Computer Science and
Random Systems, Rennes, Briany, France
ANDREA MONDELLI, Institute for Research in Computer Science and
Random Systems, Rennes, Briany, France
ANDRÉ SEZNEC, Institute for Research in Computer Science and
Random Systems, Rennes, Briany, France
Open Access Support provided by:
Institute for Research in Computer Science and Random Systems
PDF Download
2800787.pdf
08 March 2026
Total Citations: 3
Total Downloads:
1375
Published: 31 August 2015
Accepted: 01 June 2015
Revised: 01 June 2015
Received: 01 April 2015
Citation in BibTeX format
ACM Transactions on Architecture and Code Optimization (TACO), Volume 12, Issue 3 (October 2015)
hps://doi.org/10.1145/2800787
EISSN: 1544-3973
.
28
Revisiting Clustered Microarchitecture for Future Superscalar Cores:
A Case for Wide Issue Clusters
PIERRE MICHAUD, ANDREA MONDELLI, and ANDRE SEZNEC ´ , IRISA/Inria
During the past 10 years, the clock frequency of high-end superscalar processors has not increased. Performance keeps growing mainly by integrating more cores on the same chip and by introducing new instruction
set extensions. However, this benefits only some applications and requires rewriting and/or recompiling
these applications. A more general way to accelerate applications is to increase the IPC, the number of instructions executed per cycle. Although the focus of academic microarchitecture research moved away from
IPC techniques, the IPC of commercial processors was continuously improved during these years.
We argue that some of the benefits of technology scaling should be used to raise the IPC of future superscalar cores further. Starting from microarchitecture parameters similar to recent commercial high-end
cores, we show that an effective way to increase the IPC is to allow the out-of-order engine to issue more
micro-ops per cycle. But this must be done without impacting the clock cycle. We propose combining two techniques: clustering and register write specialization. Past research on clustered microarchitectures focused
on narrow issue clusters, as the emphasis at that time was on allowing high clock frequencies.
Instead, in this study, we consider wide issue clusters, with the goal of increasing the IPC under a
constant clock frequency. We show that on a wide issue dual cluster, a very simple steering policy that sends
64 consecutive instructions to the same cluster, the next 64 instructions to the other cluster, and so forth,
permits tolerating an intercluster delay of three cycles. We also propose a method for decreasing the energy
cost of sending results from one cluster to the other cluster.
CCS Concepts:  Computer systems organization→Superscalar architectures;
Additional Key Words and Phrases: Clustered microarchitecture, instruction-level parallelism, steering
policy, superscalar core
ACM Reference Format:
Pierre Michaud, Andrea Mondelli, and Andre Seznec. 2015. Revisiting clustered microarchitecture for future ´
superscalar cores: A case for wide issue clusters. ACM Trans. Archit. Code Optim. 12, 3, Article 28 (August
2015), 22 pages.
DOI: http://dx.doi.org/10.1145/2800787
1. INTRODUCTION
For several decades, the clock frequency of general-purpose processors was growing
thanks to faster transistors and microarchitectures with deeper pipelines. However,
about 10 years ago, technology hit leakage power and temperature walls. Since then,
the clock frequency of high-end processors has not increased. Instead of increasing the
clock frequency, processor makers integrated more cores on a single chip, enlarged the
cache hierarchy, and improved energy efficiency.
This work is partially supported by the European Research Council Advanced Grant DAL no. 267175.
Authors’ address: P. Michaud, A. Mondelli, and A. Seznec, IRISA/Inria, Campus de Beaulieu, 263
Avenue du Gen´ eral Leclerc, 35042 Rennes Cedex, France; emails: ´ {pierre.michaud, andrea.mondelli,
andre.seznec}@inria.fr.
Permission to make digital or hard copies of part or all of this work for personal or classroom use is granted
without fee provided that copies are not made or distributed for profit or commercial advantage and that
copies show this notice on the first page or initial screen of a display along with the full citation. Copyrights for
components of this work owned by others than ACM must be honored. Abstracting with credit is permitted.
To copy otherwise, to republish, to post on servers, to redistribute to lists, or to use any component of this
work in other works requires prior specific permission and/or a fee. Permissions may be requested from
Publications Dept., ACM, Inc., 2 Penn Plaza, Suite 701, New York, NY 10121-0701 USA, fax +1 (212)
869-0481, or permissions@acm.org.
c 2015 ACM 1544-3566/2015/08-ART28 $15.00
DOI: http://dx.doi.org/10.1145/2800787
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
28:2 P. Michaud et al.
Putting more cores on a single chip has increased the total chip throughput and
benefits some applications with thread-level parallelism. However, most applications
have low thread-level parallelism [Blake et al. 2010]. So having more cores is not
sufficient. It is important to accelerate individual threads as well.
If the clock frequency remains constant, the only possibility left for higher singlethread performance in future processors is to exploit more instruction-level parallelism
(ILP). Certain microarchitecture improvements (e.g., better branch predictor) simultaneously improve performance and energy efficiency. However, in general, exploiting
more ILP has a cost in silicon area, energy consumption, design effort, and so forth.
Therefore, the microarchitecture is modified slowly and incrementally, taking advantage of technology scaling. And indeed, processor makers have made continuous efforts
to exploit more ILP, with better branch predictors, better data prefetchers, larger instruction windows, more physical registers, and so forth. For example, the Intel Nehalem microarchitecture can issue 6 micro-ops per cycle from a 36-entry issue buffer,
whereas the more recent Intel Haswell microarchitecture can issue 8 micro-ops per
cycle from a 60-entry issue buffer [Intel 2014].
In this article, we try to depict what future superscalar cores may look like in 10
years. We argue that the instruction window and the issue width can be augmented
by combining clustering [Lowney et al. 1993; Kessler 1999; Palacharla et al. 1997] and
register write specialization [Canal et al. 2000; Zyuban and Kogge 2001; Seznec et al.
2002b].
A major difference with past research on clustered microarchitecture is that we assume wide issue clusters (≥ eight issue), whereas past research mostly focused on
narrow issue clusters (≤ four issue). Going from narrow issue to wide issue clusters is
not just a quantitative change, it has a qualitative impact on the clustering problem,
particularly on the steering policy. Past research on steering policies showed that minimizing intercluster communications while achieving good cluster load balancing is a
difficult problem. One of the conclusions of a decade of research on steering policies was
that simple steering policies such as Mod-3 [Baniasadi and Moshovos 2000] generate
significant IPC loss, whereas steering policies minimizing IPC loss are too complex for
hardware-only implementations [Salverda and Zilles 2005; Cai et al. 2008].
Our study shows that considering wide issue clusters instead of narrow issue clusters
has a dramatic impact on the performance of Mod-N, one of the simplest steering
policies. Mod-N sends N consecutive instructions to a cluster, the next N instructions
to another cluster, and so forth in round-robin fashion [Baniasadi and Moshovos 2000].
Baniasadi and Moshovos found that on narrow issue clusters, the optimal value of N
is generally very small, advocating a Mod-3 policy. To the best of our knowledge, after
Baniasadi and Moshovos’s paper, nobody has considered Mod-N policies other than
Mod-3.
We find that with wide issue clusters, if the instruction window is large enough and
considering a realistic intercluster delay, the optimal value of N is much larger than
three, typically several tens. Owing to data-dependence locality, a Mod-64 policy leads
to much fewer intercluster communications than a Mod-3 policy. As a result, Mod-64
tolerates greater intercluster delays than Mod-3. Moreover, about 40% of the values
produced by a cluster do not need to be forwarded to the other cluster, which permits
reducing the energy spent in intercluster communications.
This article is organized as follows. Section 2 argues for using some of the benefit of
technology scaling for increasing single-thread IPC. Section 3 discusses some known
solutions for enlarging the issue width and the instruction window. We describe our
simulation setup in Section 4. In Section 5, we explore the impact on IPC of various microarchitecture parameters, and we show that by doubling simultaneously all
parameters of a modern high-end core, the IPC of SPEC INT benchmarks could be
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
Revisiting Clustered Microarchitecture for Future Superscalar Cores 28:3
Table I. Three Possible Scenarios for Exploiting One Step of Technology Scaling,
Assuming Constant Frequency, Constant Voltage, and Homogeneous Cores
more complex
same core μarch. core μarch.
dimensions x,y,z × √1
2 × √1
2 × √1
2
frequency ×1 ×1 ×1
voltage ×1 ×1 ×1
core area ×1
2 ×1
2 ×1
2 γ
number of cores ×2 ×
√
2 ×1
core IPC ×1 ×1 ×α
dynamic EPI × √1
2 × √1
2 √1
2 × β
total power (cores) ×
√
2 ×1 × √1
2 αβ
power density ×
√
2 ×
√
2 ×
√
2 αβ
γ
increased by 25% on average, that of SPEC FP by 40%. Section 6 studies the impact
on IPC of clustering the out-of-order engine. We find that significant IPC gains are
still possible, despite the intercluster delay, provided that the instruction window parameters are doubled. We show that a Mod-64 steering policy tolerates intercluster
delays of a few cycles. Section 7 explains how the energy consumption of intercluster
communications can be reduced by detecting micro-ops whose results are not needed
by the other cluster. We discuss related work in Section 8 and conclude this study in
Section 9.
2. A CASE FOR INCREASING SINGLE-THREAD IPC
If the clock frequency remains constant, the only possibility left for increasing the
single-thread performance of future processors is to exploit more ILP.
Table I shows three possible scenarios for exploiting one step of technology scaling
under constant clock frequency and constant voltage,1 assuming identical cores. The
core power, core IPC, energy per instruction (EPI), and clock frequency are related as
follows:
core power = EPI × IPC × frequency.
If voltage remains constant, technology scaling decreases the switching energy 1
2CV 2
only by reducing capacitances C—that is, roughly as √
1
2 [Dennard et al. 1974]. Hence,
if we consider a fixed core microarchitecture, the silicon footprint reduction from technology scaling means roughly a √
1
2 reduction of the dynamic EPI.
The second and third column in Table I assume a fixed core microarchitecture. The
first scenario (second column) corresponds to doubling the number of cores on each new
technology generation, which technology scaling makes possible in a constant silicon
area. However, this scenario leads to an increase of the total power (this is the dark
silicon problem [Esmaeilzadeh et al. 2011]).
The second scenario (third column) corresponds to increasing the number of cores
but more slowly than what technology scaling permits to keep the total power constant.
Power density increases but remains inversely proportional to the circuit dimensions,
and hence hot spots temperature remains constant (see formula (1) in appendix).
1High leakage currents make it difficult to scale down the voltage without severely hurting transistor speed.
This is one of the reasons for voltage scaling down only very slowly [ITRS 2013]. We conservatively assume
a constant voltage.
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
28:4 P. Michaud et al.
The third scenario (fourth column of Table I) shows a situation where the number of
cores is kept constant, but single-thread performance is increased with a more complex
core microarchitecture.2 For example, a 10% increase of core IPC (α = 1.10), which is
obtained at the cost of 28% more EPI (β = 1.28),3 results in a constant total power and
10% overall EPI reduction after scaling down the feature size.
The main point is that the core microarchitecture complexity can be increased
progressively, over several technology generations, with the EPI globally decreasing
thanks to technology scaling.
3. SOLUTIONS FOR WIDE-ISSUE CORES
In Section 5, we show that significant IPC gains can be obtained by increasing the
issue width, the front-end width, and the instruction window size. In this section, we
describe some solutions that are already known and that we believe are realistic, with
an emphasis on clustering.
3.1. Clustering
Clustering was proposed in the 1990s as a solution for reducing the clock cycle of
superscalar processors [Palacharla et al. 1997; Farkas et al. 1997]. The basic idea is
to partition the execution units (EU) into clusters, such that the output of one EU
can be used as input by any other EU in the cluster in the next clock cycle through
a local bypass network [Gonzalez et al. 2011]. Clustering can also be applied to the ´
issue buffer (one issue buffer partition per cluster). Hence, clustering is a solution to
two of the most important frequency bottlenecks in the out-of-order engine: the bypass
network and the issue buffer. The price to pay is that communications between clusters
require an extra delay, which may impact the IPC.
A natural form of clustering, which has been used in several superscalar processors, is to have an integer (INT) cluster and a floating-point (FP) cluster. This form
of clustering does not generate intercluster communications, and the term clustered
microarchitecture is mostly applied to cases where intercluster communications are
frequent.
Clustering introduces a degree of freedom for instructions that can execute on several clusters. Choosing on which cluster to execute an instruction is called steering.
Microarchitectures such as the DEC Alpha 21264 [Farrell and Fischer 1998; Kessler
1999] that cluster the EUs but not the scheduler do the steering at instruction issue
(execution-driven steering [Palacharla et al. 1997]). Microarchitectures such as the IBM
POWER7 [Sinharoy et al. 2011] that cluster both the EUs and the scheduler do the
steering before inserting the instruction into the issue buffer (dispatch-driven steering
[Palacharla et al. 1997]).
Execution-driven steering does a good job at mitigating the impact of the intercluster
delay, as the scheduler can send an instruction to the cluster where it can execute sooner
[Palacharla et al. 1997]. However, execution-driven steering limits the size of the issue
buffer, not only because the issue buffer does not benefit from clustering (unlike the
bypass network) but also because postponing the steering until issue makes it part of
the scheduling loop, which impacts the clock frequency.
2The second and third scenario of Table I do not exclude each other. They can be used at different technology generations. Moreover, keeping the number of cores constant does not preclude introducing more
simultaneous multithreading (SMT) contexts.
3Making the core more complex does not necessarily increase the EPI (factor β). A large fraction of the
total CPU power is static power from leakage currents. And a large fraction of this static power is gateable
on modern processors—that is, it can be turned off once a task is finished. Increasing the IPC makes the
execution time shorter and may reduce static energy consumption [Czechowski et al. 2014].
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
Revisiting Clustered Microarchitecture for Future Superscalar Cores 28:5
Fig. 1. Example of a two-cluster OoO engine, assuming dispatch-driven steering and register write
specialization.
In this study, we consider only dispatch-driven steering—that is, the issue buffer is
clustered just like the EUs and the bypass network, and the steering is done before the
instruction enters the issue buffer. An example of a dispatch-driven clustered scheme
is shown in Figure 1.
We assume symmetric clusters—in other words, the two clusters are identical and
can execute all micro-ops. An advantage of symmetric clustering is that in simultaneous multithreading (SMT) mode, the clusters can execute distinct threads and the
intercluster bypass network can be clock gated.
3.2. Issue Buffer
Clustering the issue buffer like the EUs (as in the IBM POWER7) permits increasing
the total issue buffer capacity without impacting the clock cycle: the select operation
is done independently on each issue buffer partition, and the wake-up operation is
pipelined between the partitions, taking advantage of the intercluster delay [Goshima
et al. 2001].
3.3. Steering
Ideally, one wants both a good cluster load balancing and limited intercluster communications. However, these two goals generally contradict each other. The main problem
is to achieve a good trade-off between load balancing and intercluster communications
while still being able to steer several instructions simultaneously.
Some authors proposed steering policies taking into account register dependencies [Palacharla et al. 1997; Canal et al. 1999, 2000; Baniasadi and Moshovos 2000;
Gonzalez et al. 2004]. However, these dependency-based steering policies are complex ´
and make steering a clock frequency bottleneck, as the steering bandwidth must match
the register renaming bandwidth.
Therefore, we consider a very simple steering policy: Mod-N. Mod-N steers N instructions to a cluster, the next N instructions to the next cluster, and so on in round-robin
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
28:6 P. Michaud et al.
fashion [Baniasadi and Moshovos 2000]. Mod-N is simple enough to be implemented
in hardware.
3.4. Write Specialization
Executing more instructions per cycle requires to increase the number of read and
write ports on the register file. However, the area and access energy of an SRAM array
increases quickly with the number of ports, especially with write ports [Seznec et al.
2002b].
A simple solution to increase the number of read ports is to duplicate the physical
register file, as in the Alpha 21264 [Kessler 1999]. However, this does not solve the
problem for write ports. Register Write Specialization has been proposed to solve this
problem [Seznec et al. 2002b]. For a clustered superscalar OoO engine, register write
specialization means that each cluster writes in a subset of the physical registers
[Canal et al. 2000; Zyuban and Kogge 2001; Seznec et al. 2002b].
As an example, let us consider a single-cluster OoO engine using 128 physical registers with four write ports and eight read ports. A dual-cluster OoO engine has the
double total issue width. We apply register write specialization, keeping the same total
number of physical registers: partition 0 contains physical registers 0 to 63 and can be
written only by cluster 0, and partition 1 contains physical registers 64 to 127 and can
be written only by cluster 1. To allow reading any register on both clusters, each cluster
has a mirror copy of the register partition of the other cluster. In other words, each
cluster has two banks, each bank holding half of the registers and having four write
ports and eight read ports. If we keep the total number of physical registers constant,
the area of the per-cluster register file is roughly the same in the single-cluster and
dual-cluster configurations. (See Seznec et al. [2002b] for more details.)
Write specialization implies that steering should be finished before register renaming. This means that a complex steering policy cannot be completely overlapped with
register renaming and would probably require extra pipeline stages for steering. However, Mod-N steering is very simple and can be done while the rename table is being
read.
3.5. Bypass Network and Intercluster Delay
Increasing the issue width increases the bypass network complexity, which may impact
the clock cycle. Clustering solves this problem by making the bypass network hierarchical. This is illustrated in Figure 2 on an example of bypass network implementation
for a dual-cluster OoO engine, assuming register write specialization. In this example,
the first (i.e., most critical) bypass level (mux 1) is not impacted by clustering. However,
this costs an extra cycle of intercluster delay. Moreover, the physical distance between
clusters requires pipelining the result buses to decrease RC delays. Hence, a bypass
network such as the one depicted in Figure 2 entails at least two cycles of intercluster delay, one (or more) from pipelining the result buses and one from isolating the
first bypass level. Note that there are several possible implementations for a bypass
network.4 In our simulations, we consider intercluster delays of up to three cycles.
3.6. Level-One Data Cache
Increasing the issue width also means increasing the L1 data cache load/store bandwidth. Several solutions are possible for increasing the load/store bandwidth. Recent
high-end processors use banking to provide the adequate bandwidth. Banking leads to
the possibility of conflicts when several loads/stores issued simultaneously access the
4Data movements in a pipelined bypass network consume a lot of power. This can be avoided with a CAM-like
implementation of the bypass network [Curtis et al. 1999; Preston et al. 2002].
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
Revisiting Clustered Microarchitecture for Future Superscalar Cores 28:7
Fig. 2. Example of bypass network implementation for a dual-cluster OoO engine, assuming two register
read/write cycles and register write specialization (a single execution port and single source operand are
shown; comparators are not shown). The first bypass level (mux 1) is not impacted by clustering, but this
costs an extra cycle of intercluster delay.
same bank. Several banking schemes are possible. In this study, we assume that the
eight words in a 64-byte cache line are stored separately in eight data-array banks,
like in the Intel Sandy Bridge [Intel 2014].
3.7. Front-End Bandwidth
Executing more instructions per cycle requires fetching more instructions per cycle. A
possible way to increase the front-end bandwidth is to predict and fetch two basic block
per cycles instead of one, as in the Alpha EV8 [Seznec et al. 2002a], and scale instruction
decode accordingly. However, decode itself may be a microarchitecture bottleneck for
CISC instructions sets such as Intel x86. A trace cache (a.k.a. decoded I-cache or
micro-op cache in the Intel Sandy Bridge and Haswell microarchitectures [Intel 2014])
addresses this issue. A trace cache stores in traces micro-ops that are likely to be
executed consecutively in sequential order [Rotenberg et al. 1996].
A trace cache is also a solution to the register renaming bandwidth problem. When
creating a trace, intratrace dependencies can be determined and this information can be
stored along with the trace. The number of read and write ports of the rename table can
be reduced: each read-after-write or read-after-read occurrence within a trace saves one
read port on the rename table, and each write-after-write occurrence saves one write
port [Vajapeyam and Mitra 1997]. The number of read and write ports of the rename
table is part of the trace format definition.
3.8. Load/Store Queues
The load queue is for guaranteeing a correct execution while allowing loads to execute speculatively before older independent stores. The load queue is searched when
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
28:8 P. Michaud et al.
a store retires. When there is a load queue, the store queue is mostly for preventing memory dependencies to hurt performance. The store queue is searched when a
load executes. Enlarging the instruction window to exploit more ILP may require the
load/store queues to be enlarged as well. However, conventional load/store queues are
fully associative structures that cannot be enlarged straightforwardly. Clustering the
OoO engine does not solve the load/store queues scalability problem. Specific solutions
may be needed (e.g., Baugh and Zilles [2006], Cain and Lipasti [2004], Sha et al. [2005],
and Subramaniam and Loh [2006]).
For this study, we ignore the problem and assume that it is possible to enlarge
load/store queues without impacting the clock cycle or the load latency.
4. SIMULATION SETUP
The microarchitecture simulator used for this study is an in-house simulator based on
Pin [Luk et al. 2005]. Operating system activity is not simulated. The simulator is trace
driven and does not simulate the effects of wrong-path instructions.5 We simulate the
64-bit x86 instruction set. Instructions are split by the microarchitecture into microops. For simplicity, the simulator defines 18 micro-op categories.
4.1. Benchmarks
The benchmarks used for this study are the SPEC CPU 2006. They were all compiled with gcc-O2 executed with the reference inputs. A trace is generated for each
benchmark. Each trace consists of about 20 samples stitched together. Each sample
represents 50 million executed instructions. The samples are taken every fixed number of instructions and represent the whole benchmark execution. In total, 1 billion
instructions are simulated per benchmark.
4.2. Baseline Microarchitecture
Our baseline superscalar microarchitecture is representative of current high-end microarchitectures. The main parameters are given in Table II. Several parameters are
identical to those of the Intel Haswell microarchitecture, particularly the issue buffer
and load/store queues [Intel 2014].
Macrofusion is applied to conditional branches when the previous instruction modifies the flags and is of type ALU [Intel 2014]. In other words, the two instructions give
a single micro-op. Recent Intel processors feature a micro-op cache and a loop buffer
[Intel 2014], which are not simulated here (this study focuses on the out-of-order engine). Instead, we simulate an aggressive front end delivering up to eight decoded
instructions per cycle.
For every memory access, we generate an address micro-op for the address calculation
and a store micro-op or a load micro-op for writing or reading the data. The load queue
can issue two loads per cycle.
The micro-ops have two inputs and one output. Some partial register writes require
reading of the old register value. When necessary, we introduce an extra micro-op to
merge the old value and the new value. Each physical register is extended to hold
the flags, which are renamed like architectural registers. A micro-op that only reads
the flags, such as a nonfused conditional branch, accesses a read port of the physical
register file. Micro-ops that do not write a register or do not update the flags do not
5We believe that our general conclusions are largely independent from wrong path effects. Modern out-oforder schedulers prioritize older instructions (in program order) when selecting among ready ones [Preston
et al. 2002; Sinharoy et al. 2011; Golden et al. 2011], and correct-path instructions are generally not delayed
by wrong-path ones.
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
Revisiting Clustered Microarchitecture for Future Superscalar Cores 28:9
Table II. Baseline Microarchitecture
clock frequency 3.5GHz
branch predictor 31KB TAGE & 6KB ITTAGE [Seznec and Michaud 2006]
I-fetch 1 cache line, 1 taken branch per cycle
decode 8 instructions/cycle
rename 12 micro-ops/cycle
issue (micro-ops) 4 INT, 2 FP, 3 address, 2 store data (cf. Figure 3)
load issue 2 loads/cycle
retire 12 micro-ops/cycle
reorder buffer (ROB) 256 micro-ops
physical registers 128 INT, 128 FP
issue buffers 60 INT micro-ops, 60 FP micro-ops
load queue 72 loads
store queue 42 stores
branch misp. penalty 12 cycles (minimum), redirect I-fetch at branch execution
cache line 64 bytes
MSHRs 32 block requests
DL1 cache 32KB, 8-way assoc., latency 3 cycles, 8 banks, 2 reads & 1 write/cycle
IL1 cache 32KB, 8-way assoc.
L2 cache 512KB, 8-way assoc., latency 11 cycles
L3 cache 8MB, 16-way assoc., latency 21 cycles
memory latency (fixed) 245 cycles, bandwidth 16 bytes/cycle
prefetchers stride prefetcher (L1), stream prefetchers (L2 & L3)
page size 4MB
store sets SSIT 2k (4-way skewed-assoc.), LFST 42 stores (full-assoc. LRU)
reserve a physical register. These include branch, store, and address micro-ops (address
micro-ops write in the load/store queues).
Loads are executed speculatively. Load misspeculations are repaired when a misexecuted instruction is to be retired from the reorder buffer, by flushing the instruction
window and refetching from the misexecuted instruction. The memory independence
predictor is the Store Sets [Chrysos and Emer 1998]. A load can execute speculatively
if the most recent store in its store set (the “suspect” store) has been retired from the
store queue. A load can also execute speculatively if a matching store queue entry can
provide the data to the load and that store is not older than the “suspect” store. The
Store Set ID Table (SSIT) is indexed by hashing load/store PCs, using different hashing
functions for loads and stores (an x86 instruction may contain both a load and a store).
Figure 3 depicts the baseline out-of-order engine. The INT and FP clusters each have
their own issue buffer and scheduling logic. There are 8 INT execution ports and 3 FP
execution ports. The execution ports for address micro-ops and store micro-ops do not
need a register write port. Instead, they write in the load/store queues. We assume 128
INT and 128 FP physical registers, which is sufficient for our single-threaded baseline
core. Three INT execution ports are specialized with only one register read port. This
saves 3 read ports.6 In total, the INT register file has 12 read ports and 6 write ports.
The FP register file has 5 read ports and 4 write ports. The ALU execution ports
can execute most INT micro-ops. An execution port is selected for a micro-op before
it enters the issue buffer. For load balancing, if several execution ports can execute a
given micro-op, the micro-op is put on the execution port that received a micro-op least
recently.
6We checked that this has very little impact on the IPC.
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
28:10 P. Michaud et al.
Fig. 3. Baseline out-of-order engine with 8 INT execution ports and 3 FP execution ports. The INT register
file has 12 read ports and 6 write ports. The FP register file has 5 read ports and 4 write ports. The issue
buffers are not shown.
Table III. IPCs for the Baseline Configuration
SPEC INT IPC SPEC INT IPC
400.perlbench 2.97 401.bzip2 1.70
403.gcc 1.80 429.mcf 0.50
445.gobmk 1.97 456.hmmer 3.64
458.sjeng 2.40 462.libquantum 3.28
464.h264ref 2.99 471.omnetpp 1.05
473.astar 0.75 483.xalancbmk 1.44
SPEC FP IPC SPEC FP IPC
410.bwaves 2.09 416.gamess 2.94
433.milc 2.46 434.zeusmp 1.46
435.gromacs 1.76 436.cactusADM 1.97
437.leslie3d 1.57 444.namd 1.95
447.dealII 2.70 450.soplex 0.94
453.povray 2.56 454.calculix 2.36
459.GemsFDTD 1.55 465.tonto 2.73
470.lbm 1.38 481.wrf 1.97
482.sphinx3 1.95
5. POTENTIAL IPC GAINS FROM A MORE COMPLEX SUPERSCALAR MICROARCHITECTURE
This section studies the impact on IPC of enlarging certain critical parts of the
microarchitecture, ignoring implementation issues. The configurations considered in
this section are nonclustered microarchitectures. We focus on first-order back-end
parameters that may have an important impact on IPC. The parameters are listed
in Table IV. Some of the parameters are lumped to limit the configuration space.
We include front-end width in the list of parameters as a wider back-end generally
requires a wider front end. The seven parameters of Table IV define 128 nonclustered
configurations (including the baseline), each parameter being either as in the baseline
core or doubled compared to the baseline.
We simulated all 128 configurations and obtained the IPC of each of them. The IPCs
for the baseline are displayed in Table III. For all other configurations, the IPC of each
benchmark is normalized to its baseline IPC—that is, only speedups are given.
To present our simulation results in a concise way, we use the following method for
naming the 128 configurations. Each of the seven parameters is represented by a unique
symbol (see Table IV). The presence of that symbol in a configuration’s name means
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
Revisiting Clustered Microarchitecture for Future Superscalar Cores 28:11
Table IV. Microarchitecture Parameters Varied
in the Nonclustered Configurations
symbol parameter
R total number of physical registers
B total issue buffer size
W ROB, load & store queues, LFST, MSHR
i INT execution ports
f FP execution ports
c load issue width & DL1 write ports
w front-end width (I-fetch, decode, rename, retire)
Note: Uppercase letters are for instruction window parameters, and lowercase letters are for width parameters. Parameters “W,” “w,” and “c” are lumped parameters.
Fig. 4. Speedup over the baseline for the worst and best configuration in each configuration class. The left
graph shows the geometric mean speedup for the 12 SPEC INT benchmarks, and the right graph shows the
17 SPEC FP benchmarks. The presence of a letter in a configuration’s name indicates that the corresponding
parameter is doubled compared to the baseline (see Table IV).
that the corresponding parameter is twice as large as in the baseline core; otherwise,
it is dimensioned as the baseline. For instance, configuration “Bicw” features INT and
FP issue buffers of 120 micro-ops, 16 INT execution ports (the ones shown of Figure 3,
duplicated), can issue 4 loads and do 2 writes in the L1 data cache per cycle, and can
predict 2 taken branches and fetch 2 instruction cache blocks per cycle cycle. Otherwise,
it is identical to the baseline.
For summarizing the simulation results, we define configuration classes based on the
configuration’s name length. For example, the baseline configuration is in class 0, and
configuration “Bicw” is in class 4. Then, for each configuration class from 0 to 7, we
find the worst (lowest mean speedup) and best (highest mean speedup) configurations
in that class.
Figure 4 shows speedups over the baseline for the worst and best configurations in
each configuration class, with the configurations’ names indicated. Notice that there
is no single bottleneck in the baseline for the SPEC INT, as the best configuration in
class 1 yields only +5% sequential performance. For the SPEC INT, the most effective
single parameter is the number of INT execution ports. Indeed, the best configuration
in class 1 doubles the number of INT execution ports (“i”), and the worst configuration
in class 6 is the one without “i” (the speedup drops from 1.25 to 1.12).
For the SPEC FP, the most effective single parameter is the number of FP execution
ports. Just doubling the number of FP execution ports (“f ”) yields +11% sequential
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
28:12 P. Michaud et al.
performance on average, and the worst configuration in class 6 is the one without “f ”
(the speedup drops from 1.41 to 1.20). The other width parameters are not important
bottlenecks for the SPEC FP, which are more sensitive to window parameters (physical
registers, ROB, etc.).
The extra microarchitecture complexity can be introduced incrementally over several
technology generations. For instance, a first step could be to increase the number of FP
execution ports, as this brings significant performance gains on scientific workloads.
Increasing simultaneously the number of INT execution ports, DL1 bandwidth and
front-end width could be a second step, which would allow more SMT contexts. However,
the hardware complexity of the scheduler and bypass network increases quadratically
with the issue width [Palacharla et al. 1997], and clustering must be introduced at some
point not to impact the clock frequency. In the next section, we quantify the impact of
clustering on IPC.
6. DUAL-CLUSTERED CONFIGURATIONS
Section 5 did not take into account the potential impact on the clock cycle. Increasing
the number of execution ports while keeping the same clock frequency will require
the use of clustering at some point. In this section, we study the impact of the intercluster delay on IPC, assuming symmetric clustering and register write specialization
(cf. Section 3).
The INT and FP clusters depicted in Figure 3 are duplicated,7 which means a total of
eight ALUs, six address generators, and four FP operators. The INT and FP registers
are split in two partitions (write specialization). Cluster 0 writes in partition 0, and
cluster 1 writes in partition 1. Each partition is implemented with two mirror banks,
with one bank in each cluster. Each cluster has a bank for partition 0 and a bank for
partition 1, but writes only in its own partition. Each of the four banks has the same
number of read and write ports as the register file in the single-cluster baseline (cf.
Section 3.4).
The L1 data cache is banked, with eight banks interleaved per 8-byte word, like the
Intel Sandy Bridge [Intel 2014]. The load queue can issue four loads per cycle instead
of two in the baseline. Before being entered in the load queue, loads are “steered” to one
of the register file partition (a bit in each load queue entry indicates to which partition
the load has been steered). There are two write ports dedicated to loads in each physical
register partition (cf. Figure 1). Each cycle, the load scheduling logic selects the two
oldest ready loads in each partition.
For the clustered configurations, we assume a DL1 latency of four cycles, instead
of three cycles for the baseline, to take into account the extra complexity of the DL1
cache.
We consider two clustered configurations, named using a method similar to the
one used in Section 5, except that notation “iiffcc” means that the baseline cluster of
Figure 3 is duplicated and the issue buffer and physical registers are partitioned:
—iiffccw: Same total instruction window capacity as the baseline (same ROB, same
MSHR, etc.) but double front-end bandwidth and dual-cluster back end. Each cluster
has an issue buffer partition of 30 micro-ops and a physical register partition of 64
registers.
—RBWiiffccw: Dual cluster back end but with the total instruction window capacity
doubled: twice bigger ROB, MSHR, load/store queues, and LFST, with each cluster
7The reason for clustering the FP execution ports is that FP operators have a big silicon footprint and result
in buses that have to span a long physical distance.
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
Revisiting Clustered Microarchitecture for Future Superscalar Cores 28:13
Fig. 5. IPC gain over the baseline for clustered iiffccw configurations, for intercluster delays (ICD) of 0,1,
2, and 3 cycles, under a Mod-N steering policy with N ranging from 1 to 256. The leftmost bar of each group
of bars is the IPC gain when steering all micro-ops to cluster 0. The rightmost bar is the IPC gain of the
nonclustered ifcw configuration. The top graph is the average for SPEC INT, and the bottom one for SPEC
FP.
having an issue buffer partition of 60 micro-ops and a physical register partition of
128 registers.
6.1. Dual-Cluster with Baseline Instruction Window Size
Figure 5 shows the IPC gain over the baseline for the iiffccw clustered configuration,
assuming intercluster delays of 0, 1, 2, and 3 cycles8 under a Mod-N steering policy
with N ranging from 1 to 256. Recall that Mod-N steers N x86 instructions (i.e., more
than N micro-ops) to a cluster, the next N instructions to the other cluster, and so forth.
The leftmost bar of each group of bars in Figure 5 shows the IPC gain when steering
all micro-ops to cluster 0.
Where as the nonclustered configurations showed that it is beneficial to increase
the issue width first, and then the instruction window, Figure 5 shows that for the
clustered configurations, the situation is quite different. Indeed, the main conclusion
from Figure 5 is that clustering without enlarging the total instruction window
does not bring any IPC gain when the intercluster delay is three cycles. Several
factors contribute to this. The increased DL1 latency (from three to four cycles), the
partitioning of the issue buffer and physical registers, the clustering of EUs, and
load issue ports contribute to decreasing the potential IPC gain, even with a null
intercluster delay and a Mod-1 steering. But the biggest impact comes from the
8Intercluster delays of 0 and 1 cycles are not realistic; they are provided only for analysis.
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
28:14 P. Michaud et al.
Fig. 6. IPC gain over the baseline for clustered RBWiiffccw configurations (cf. Figure 5).
intercluster delay. As the intercluster delay increases, the IPC gain drops quickly and
eventually becomes an IPC loss, even with the best steering policy (Mod-32 here).
6.2. Dual-Cluster with Double Instruction Window
Figure 6 gives the IPC gain over the baseline for the RBWiiffccw clustered configuration. Here, the total instruction window capacity is doubled. In particular, the issue
buffer partition and physical register partition of each cluster have the same size as
the baseline.
Now, the dual cluster can outperform the baseline for some Mod-N steering. When
steering all micro-ops to cluster 0, the IPC is very close to the baseline, with the impact
of the increased DL1 latency more or less compensated by the increased reorder buffer
and MSHRs. When the intercluster delay is null, Mod-N steering with N ≤ 32 achieves
a good ILP balancing. For N > 32, ILP imbalance decreases the IPC. As the intercluster
delay increases, Mod-N steering with small values of N generates significant IPC drop.
With a large N, there are fewer intercluster communications and better tolerance to the
intercluster delay. With an intercluster delay of two cycles, Mod-64 gives an average
IPC gain of +14.3% on the SPEC INT and +29.6% on the SPEC FP. With an intercluster
delay of three cycles, the IPC gain with Mod-64 is still +12.9% and +28.0% on the SPEC
INT and SPEC FP, respectively.
It can be observed in Figure 6 that when the intercluster delay is two cycles or more,
the IPC is very sensitive to Mod-N steering. Figure 7 shows the IPC gain over the
baseline, benchmark per benchmark, for the RBWiiffccw clustered scheme, assuming
a three-cycle intercluster delay, comparing Mod-32 and Mod-64 steering. For some
benchmarks, Mod-32 outperforms Mod-64. For some other benchmarks, it is the other
way around.
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
Revisiting Clustered Microarchitecture for Future Superscalar Cores 28:15
Fig. 7. IPC gain over the baseline for a clustered RBWiiffccw configuration with an intercluster delay of
three cycles: benchmark per benchmark comparison of Mod-32 steering, Mod-64, and adaptive Mod-N.
Baniasadi and Moshovos [2000] proposed that instead of having a fixed Mod-N,
we could have an adaptive Mod-N trying to find the best N dynamically. We tried
an adaptive method similar to that of Baniasadi and Moshovos, trying to identify
dynamically the best Mod-N with N in {32, 48, 64, 80, 96}. After having executed 500k
micro-ops under Mod-N steering, we try successively Mod-max(32,N-16), Mod-N, and
Mod-min(96,N+16) for 50k retired micro-ops each, counting the number of cycles. We
choose the one with the best local performance, Mod-N’, and run under Mod-N’ for the
next 500k micro-ops. We repeat this process periodically, every 500k micro-ops. Results
for the adaptive method are shown in Figure 7.
On average, assuming an intercluster delay of three cycles, the adaptive steering
slightly outperforms Mod-64 and Mod-32 and achieves an IPC gain of +14.1% over the
baseline for the SPEC INT and +28.8% for the SPEC FP.
6.3. Analysis
Our findings should be contrasted with those of Baniasadi and Moshovos. They
found that among all Mod-N steering policies, Mod-3 was the best policy on average
[Baniasadi and Moshovos 2000]. However they were considering two-issue clusters.
We first explain with a simple analytical model why Mod-N with a large N is better
for wide issue clusters. Our analytical model is based on the empirical observation that
the average ILP is roughly the square root of the instruction window size [Riseman
and Foster 1972; Michaud et al. 2001; Karkhanis and Smith 2004]. We further assume
a null intercluster delay. The square root law models the fact that instructions that
are ready for execution at a given instant are more likely to be found among the oldest
instructions in the instruction window than among the youngest ones. In the example
of Figure 8, at the instant considered, the average ILP on cluster 0 is greater than
on cluster 1. The ILP imbalance between the two clusters increases with the value of
N. Because the instantaneous IPC is the minimum of the issue width and the ILP,
if the per-cluster issue width is two instructions, the IPC on cluster 0 is limited by
the issue width, and Mod-4 outperforms Mod-8 (the total IPC is 2 + 1.37 = 3.37 with
Mod-4 and 2 + 1.17 = 3.17 with Mod-8). If we increase the per-cluster issue width
to three instructions instead of two, the IPC on cluster 0 is not limited by the issue
width, and both Mod-8 and Mod-4 yield the same IPC (hence, Mod-8 outperforms
Mod-4 if the intercluster delay is nonnull). There is roughly a square relation between
the per-cluster issue width and the value of N beyond which ILP imbalance impacts
performance significantly. This explains why the optimal N is much greater for wide
issue than for narrow issue clusters.
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
28:16 P. Michaud et al.
Fig. 8. Illustration of ILP imbalance on two clusters, assuming a null intercluster delay and assuming that
the average ILP is the square root of the instruction window size. The upper example is for a Mod-4 steering
policy, and the lower example is for Mod-8. In both examples, the instruction window holds 16 instructions.
Fig. 9. IPC gain over the baseline for a four-cluster back end. Each cluster can issue and execute 2 micro-ops
per cycle. Only SPEC INT averages are shown.
To confirm this analysis, we simulated a quad-cluster back end, with each cluster
being able to issue and execute two ALU or address micro-ops per cycle. The load queue
can issue two loads per cycle. We assume an issue buffer partition of 15 micro-ops per
cluster so that the total issue buffer capacity is equivalent to the baseline. We assume
128 physical registers as the baseline, but we removed register write specialization.9
The other microarchitecture parameters are identical to the baseline.
Figure 9 shows the results of this experiment for the SPEC INT only. When the
intercluster delay is (unrealistically) null, Mod-N steering with N ≤ 4 achieves a good
ILP balancing. The quad cluster slightly outperforms the baseline thanks to the eight
ALUs (instead of four in the baseline). However, for N greater than eight, ILP imbalance
impacts performance significantly because of the small per-cluster issue width.
With an intercluster delay of one cycle, as Baniasadi and Moshovos assumed in their
study, the trade-off between ILP balancing and intercluster communications is at work,
and the best steering policy is Mod-2. This is consistent with the finding of Baniasadi
and Moshovos [2000] that Mod-3 is the best Mod-N policy.10 As the intercluster delay
increases to two and three cycles, though, the best Mod-N steering becomes Mod-8 and
Mod-16, respectively, but the IPC loss is important.
9Having more architectural registers than physical registers in a cluster partition may lead to deadlocks
[Seznec et al. 2002b].
10For us, the “2” in Mod-2 means two x86 CISC instructions, whereas Baniasadi and Moshovos considered
RISC instructions.
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
Revisiting Clustered Microarchitecture for Future Superscalar Cores 28:17
In contrast, with wide issue clusters, ILP imbalance remains bearable for values of
N up to 32–64, as shown in the previous section. As a result, there are few intercluster
communications, which allows toleration of longer intercluster delays.
6.4. Possible Steps Toward the Proposed Dual-Cluster Configuration
The dual-cluster microarchitecture that we described is supposed to be the result
of incremental microarchitecture modifications over several technology generations.
However, going from a nonclustered microarchitecture to a clustered one introduces
a performance discontinuity. Our results show that to absorb the performance impact
of the intercluster delay, the instruction window must be large enough. However,
clustering is what permits enlarging one of the components of the instruction window:
the issue buffer. Yet we would like an increase of microarchitecture complexity to be
rewarded by a performance gain, at least on some applications. The results in Figure 4
suggest a possible path toward the proposed wide issue dual-cluster configuration:
(1) Introduce clustering for the FP EUs only.11
(2) Enlarge the instruction window, except the issue buffer (reorder buffer, load/store
queues, physical registers, MSHRs). This can be done progressively.
(3) When the instruction window is large enough, introduce clustering for the INT EUs
and increase the total issue buffer capacity.
The first two steps should benefit applications with characteristics similar to the SPEC
FP benchmarks (cf. Figure 4, configuration “RWf ”).
7. ENERGY CONSIDERATIONS
The EPI is likely to be higher in the dual-cluster microarchitecture than in the singlecluster baseline. As explained in Section 2, if the microarchitecture is modified incrementally, the microarchitectural EPI increase can be hidden by the energy reductions
coming from technology. Nevertheless, in this section, we provide a few research directions for tackling the microarchitectural EPI increase.
7.1. Static EPI
The second cluster and larger instruction window substantially increase the back-end
static power. The effect on the static EPI, however, is mitigated by the speedup brought
by the dual cluster and the larger instruction window. If the core (including the L2
cache) is powered off during long idle periods, the static EPI depends on the speedup:
the higher the speedup, the lower the static EPI. However, not all applications have
the same speedup (cf. Figure 7).
For example, let us assume that the L2 cache represents 40% of the baseline core
static power, the back end 40%, and the front end 20%. Moreover, let us assume that
the back-end static power of the dual cluster is twice that of the baseline core and that
the front-end static power is 30% higher. For example, if the IPC is unchanged, the
static EPI is multiplied by 0.4 × 1 + 0.4 × 2 + 0.2 × 1.3) = 1.46. But with a speedup of
+20%, the static EPI is multiplied by only 1.46/1.20 = 1.22.
A topic for future research is to find a way to turn the second cluster on and off
dynamically depending on the expected speedup.
7.2. Gating Intercluster Communications for Reduced Dynamic EPI
The dual-cluster microarchitecture has a higher dynamic EPI than the baseline single cluster. Some of the extra dynamic EPI comes from larger shared structures with
11Our Mod-64 policy steers to the other FP cluster every 64 general instructions. We did not evaluate the
variant of Mod-N that steers to the other FP cluster every N FP instructions.
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
28:18 P. Michaud et al.
Table V. Percentage of Values (Not Counting Addresses) Produced
by a Cluster That Do Not Need to Be Sent to the Other Cluster,
Depending on the Trace Format
micro-ops/trace in-cluster values
trace format INT FP INT FP
8 micro-ops, 1 branch 5.6 6.6 25% 32%
12 micro-ops, 2 branches 10.2 11.1 39% 42%
16 micro-ops, 3 branches 14.6 15.2 48% 49%
a higher bandwidth (e.g., DL1 cache, DL1 TLB, load/store queues). Intercluster communications also contribute to the increased dynamic EPI in the issue buffer, in the
register file, and in the bypass network.
If we could identify micro-ops that do not need to forward their result to the other
cluster, which we call in-cluster micro-ops, then the result bus segment going out of the
cluster could be gated12 when these micro-ops execute. Such gating would reduce the
energy spent in the bypass network (charging and discharging the long result buses
connecting the clusters) and writing the distant register file bank.
In particular, if the steering policy steers all micro-ops from the same instruction to
the same cluster, a micro-op that writes a physical register not mapped to an architectural register produces a value that lives only within the instruction and does not need
to be sent to the other cluster.
Roughly 55% of all micro-ops executed by the SPEC INT and 65% of all micro-ops
executed by the SPEC FP (compiled with gcc -O2) are micro-ops that produce a value,
not counting address computations. On average, about 12% of these micro-ops do not
write an architectural register. In other words, 12% of the intercluster communications
can be gated, on average, just by considering these micro-ops.
To identify more in-cluster micro-ops, a possible solution is to add some information
in the trace cache (cf. Section 3.7). We assume that all micro-ops from the same instructions are put in the same trace and that all micro-ops in a trace are steered to the
same cluster.13 If two micro-ops in the same trace write the same architectural register
(write-after-write dependency), the first micro-op is an in-cluster one. So when building
the trace, in-cluster micro-ops are identified, and this information is stored along with
the trace in the micro-op cache (one bit per micro-op).
Table V shows the percentage of in-cluster values for various trace formats. As
expected, the longer the trace, the more in-cluster values can be identified. For instance,
with traces containing about 10 micro-ops on average, about 40% of the values (i.e., not
counting addresses) produced by a cluster do not need to be sent to the other cluster,
meaning that the corresponding intercluster communications can be gated.
Gating some intercluster communications requires keeping the physical register file
content consistent, as each physical register partition has two copies (one in each
cluster). When an in-cluster micro-op executes, it writes in its local register bank and
updates its local scoreboard, but it does not update the distant bank and scoreboard. A
branch misprediction can result in an inconsistent state. A possible solution is to retire
traces from the reorder buffer only when all micro-ops in the trace have been executed
successfully. When a branch misprediction is detected, the in-cluster micro-ops that
are before the branch in the same trace are still in the reorder buffer. The branch
misprediction recovery logic must find these micro-ops, get their destination physical
registers Pi, and inject directly in the local issue buffer some special micro-ops MOV
12By putting some tristate buffers in high impedance state or by clock-gating some latches. 13If a trace contains on average 10 instructions, a policy equivalent to Mod-60 steers six traces to a cluster,
the next six traces to the other cluster, and so forth.
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
Revisiting Clustered Microarchitecture for Future Superscalar Cores 28:19
Pi,Pi that send the value of Pi to the distant cluster. These MOV micro-ops execute
while the correct-path instructions go through the front-end pipeline stages.
An interesting direction for future research is the possibility to dedicate some execution ports and/or some physical registers to in-cluster micro-ops, which would decrease
the hardware complexity of the bypass network and register file [Vajapeyam and Mitra
1997; Rotenberg et al. 1997].
8. RELATED WORK
Several papers have studied steering policies for clustered microarchitectures. Some
papers proposed different variants of dependence-based steering policies trying to steer
dependent instructions to the same cluster to minimize intercluster communications
while trying to maintain sufficient load balancing between clusters [Palacharla et al.
1997; Canal et al. 1999, 2000; Fields et al. 2001; Gonzalez et al. 2004; Salverda and ´
Zilles 2005]. However, these dependence-based policies are complex, and steering multiple instructions per cycle is an implementation challenge [Salverda and Zilles 2005;
Cai et al. 2008].
Baniasadi and Moshovos [2000] compared several different steering policies and
found that a simple Mod-3 steering policy performs relatively well on their microarchitecture configuration (four two-issue clusters, one-cycle intercluster delay).
Zyuban and Kogge [2001] proposed clustering as a solution for decreasing the EPI
for a given IPC. Like us, they considered wide issue clusters. However, they did not
quantify the IPC improvements that clustering can provide under a fixed clock cycle.
Trace processors distribute chunks of consecutive instructions (i.e., traces) to the
same processing element (PE), like Mod-N steering [Vajapeyam and Mitra 1997;
Rotenberg et al. 1997]. Rotenberg [1999] observed that the optimal trace size depends
on the PE issue width and that with four-issue PEs, 32-instruction traces generally
yield higher IPCs than 16-instruction traces.
To the best of our knowledge, three commercial superscalar processors14 have used
clustering: the DEC Alpha 21264 [Kessler 1999] and, recently, the IBM POWER7
and POWER8 [Sinharoy et al. 2011, 2015]. These processors implement narrow issue
clusters with an intercluster delay of one cycle.
The Alpha EV8 processor (canceled in 2001) exploited ILP more aggressively than
today’s processors: two 8-instruction blocks fetched per cycle, 8-wide register renaming,
8-wide issue, 8 ALUs, 4 FP operators, 2 loads + 2 stores per cycle, 512 physical registers
with 16 read ports and 8 write ports, a 128-entry issue buffer [Preston et al. 2002], for
an aggressive clock cycle equivalent to 12 gate delays [Herrick 2000]. However, only
few details about the EV8 microarchitecture were made public.
Some authors have proposed to adjust the per-thread IPC depending on the number of threads by modifying the microarchitecture so that several small cores can be
dynamically aggregated into bigger, faster cores [˙
Ipek et al. 2007; Boyer et al. 2010].
Eyerman and Eeckhout [2014] have argued that similar adaptivity could be obtained
with conventional SMT. Our proposition of wide issue superscalar core goes in the
direction advocated by Eyerman and Eeckhout.
9. CONCLUSION
As the number of cores grows, fewer applications benefit from this growth. Hence,
sequential performance is still very important. If the clock frequency remains fixed,
as in the past 10 years, the only way to increase sequential performance without
recompiling is to increase the IPC. Increasing the IPC significantly likely requires
more hardware complexity, particularly a wider issue and a larger instruction window.
14Some commercial VLIW processors also used clustering, such as Multiflow [Lowney et al. 1993].
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
28:20 P. Michaud et al.
At some point, issuing more micro-ops per cycle requires the use of clustering. Clustering was introduced and studied at a time when microarchitects were trying to
push the clock frequency as high as possible. However, if the clock frequency remains
constant, clustering becomes a means to increase the IPC, and our understanding of
clustering must be updated.
Unlike most past research on clustered microarchitecture, we consider wide issue
clusters instead of narrow issue clusters. We have shown that with wide issue clusters,
a simple Mod-64 steering policy tolerates intercluster delays of three cycles. We have
also shown that in single-thread execution, a significant fraction of the values produced
by a cluster do not need to be forwarded to the other cluster. This can be exploited to
gate some intercluster communications and decrease energy consumption.
The wide issue dual-cluster configuration that we studied is supposed to be the
result of an incremental complexification of the whole microarchitecture over several
technology generations. Although clustering solves some key complexity issues in the
back end, other parts of the microarchitecture that were not the focus of this study,
such as front-end bandwidth and load/store queues, will have to be scaled up as well.
Some of the solutions that will be needed for these other parts are already known.
Some new solutions likely will be needed.
APPENDIX
A. A SIMPLE FORMULA FOR HOT SPOT TEMPERATURE
This appendix provides a simple approximate formula for quickly reasoning about hot
spot steady-state temperature in microprocessors.15
A hot spot can be modeled roughly as a disk heat source of (small) radius r. In what
follows, Ais the die area, P is the total power dissipation, q = P/Ais the average power
density, Q is the power density inside the hot spot, Ksi is the thermal conductivity of
silicon, and R is the thermal resistance of the die and its packaging (including the heat
sink). We assume that the hot spot is much smaller than the die (πr2  A) and that
the average power density outside of the hot spot is approximately equal to q.
By the principle of superposition [Michaud et al. 2005], the temperature T relative
to the ambient at the center of the hot spot can be obtained as Tdie + Tdisk, where
Tdie is the temperature contribution of a uniform power density q on the die
Tdie = R × q × A
(the temperature contribution of remote heat sources is weakly dependent on their
exact location, and hence a uniform power density provides a good approximation),
and Tdisk is the contribution of a disk heat source of power density Q− q.
Tdisk = 1
Ksi
× (Q− q) × r
(see Thomas [1957] for the temperature of a disk heat source). Hence, the temperature
of the hot spot (relative to the ambient) is
T = R × P +
1
Ksi
× (Q− q) × r. (1)
To keep temperature constant, it is sufficient to keep the total power P constant and
the power densities Q and q inversely proportional to the hot spot radius r.
15We provide formula (1) because we are not aware of any reference for it and believe that this formula is
useful for microarchitects and designers.
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
Revisiting Clustered Microarchitecture for Future Superscalar Cores 28:21
REFERENCES
A. Baniasadi and A. Moshovos. 2000. Instruction distribution heuristics for quad-cluster, dynamicallyscheduled, superscalar processors. In Proceedings of the International Symposium on Microarchitecture
(MICRO’00).
L. Baugh and C. Zilles. 2006. Decomposing the load-store queue by function for power reduction and scalability. IBM Journal of Research and Development 50, 2–3, 287–297.
G. Blake, R. G. Dreslinski, T. Mudge, and K. Flautner. 2010. Evolution of thread-level parallelism in desktop
applications. In Proceedings of the International Symposium on Computer Architecture (ISCA’10).
M. Boyer, D. Tarjan, and K. Skadron. 2010. Federation: Boosting per-thread performance of throughputoriented manycore architectures. ACM Transactions on Architecture and Code Optimization 7, 4, Article
No. 19.
Q. Cai, J. M. Codina, J. Gonzalez, and A. Gonz ´ alez. 2008. A software-hardware hybrid steering mechanism for ´
clustered microarchitectures. In Proceedings of the International Symposium on Parallel and Distributed
Processing (IPDPS’08).
H. W. Cain and M. H. Lipasti. 2004. Memory ordering: A value-based approach. In Proceedings of the
International Symposium on Computer Architecture (ISCA’04).
R. Canal, J.-M. Parcerisa, and A. Gonzalez. 1999. A cost-effective clustered architecture. In ´ Proceedings of
the International Conference on Parallel Architectures and Compilation Techniques (PACT’99).
R. Canal, J. M. Parcerisa, and A. Gonzalez. 2000. Dynamic cluster assignment mechanisms. In ´ Proceedings
of the International Symposium on High Performance Computer Architecture (HPCA’00).
G. Z. Chrysos and J. S. Emer. 1998. Memory dependence prediction using store sets. In Proceedings of the
International Symposium on Computer Architecture (ISCA’98).
S. Curtis, R. J. Murray, and H. Opie. 1999. Multiported bypass cache in a bypass network. U.S. Patent
6000016.
K. Czechowski, V. W. Lee, E. Grochowski, and R. Ronnen. 2014. Improving the energy efficiency of big cores.
In Proceedings of the International Symposium on Computer Architecture (ISCA’14).
R. H. Dennard, F. H. Gaensslen, H.-N. Yu, V. L. Rideout, E. Bassous, and A. R. LeBlanc. 1974. Design of
ion-implanted MOSFET’s with very small physical dimensions. IEEE Journal of Solid-State Circuits 9,
5, 256–268.
H. Esmaeilzadeh, E. Blem, R. St. Amant, K. Sankaralingam, and D. Burger. 2011. Dark silicon and the end of
multicore scaling. In Proceedings of the International Symposium on Computer Architecture (ISCA’11).
S. Eyerman and L. Eeckhout. 2014. The benefit of SMT in the multi-core era: Flexibility towards degrees
of thread-level parallelism. In Proceedings of International Conference on Architectural Support for
Programming Languages and Operating Systems (ASPLOS’14).
K. I. Farkas, P. Chow, N. P. Jouppi, and Z. Vranesic. 1997. The multicluster architecture: Reducing cycle time
through partitioning. In Proceedings of the International Symposium on Microarchitecture (MICRO’97).
J. A. Farrell and T. C. Fischer. 1998. Issue logic for a 600-MHz out-of-order execution microprocessor. IEEE
Journal of Solid-State Circuits 33, 5, 707–712.
B. Fields, S. Rubin, and R. Bodik. 2001. Focusing processor policies via critical-path prediction. In Proceedings
of the International Symposium on Computer Architecture (ISCA’01).
M. Golden, S. Arekapudi, and J. Vinh. 2011. 40-entry unified out-of-order scheduler and integer execution
unit for AMD Bulldozer x86-64 core. In IEEE International Solid-State Circuits Conference (ISSCC’11).
A. Gonzalez, F. Latorre, and G. Magklis. 2011. Execute. ´ Processor Microarchitecture. Morgan and Claypool,
78–90.
J. Gonzalez, F. Latorre, and A. Gonz ´ alez. 2004. Cache organizations for clustered microarchitecture. In ´
Proceedings of the Workshop on Memory Performance Issues (WMPI’04).
M. Goshima, K. Nishino, Y. Nakashima, S. I. Mori, T. Kitamura, and S. Tomita. 2001. A high-speed dynamic
instruction scheduling scheme for superscalar processors. In Proceedings of the International Symposium
on Microarchitecture (MICRO’01).
W. Herrick. 2000. Design Challenges in Multi-GHz Microprocessors. Keynote address at the Asia and South
Pacific Design Automation Conference (ASP-DAC’00).
Intel. 2014. Intel 64 and IA-32 Architectures Optimization Reference Manual. Intel Corp.
E. ˙
Ipek, M. Kırman, N. Kırman, and J. F. Mart´ınez. 2007. Core fusion: Accommodating software diversity in
chip multiprocessors. In Proceedings of the International Symposium on Computer Architecture.
ITRS. 2013. International Technology Roadmap for Semiconductors—Process Integration, Devices, and
Structures. Retrieved July 30, 2015, from http://www.itrs.net/.
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
28:22 P. Michaud et al.
T. S. Karkhanis and J. E. Smith. 2004. A first-order superscalar processor model. In Proceedings of the
International Symposium on Computer Architecture (ISCA’04).
R. E. Kessler. 1999. The Alpha 21264 microprocessor. IEEE Micro 19, 2, 24–36.
P. G. Lowney, S. M. Freudenberger, T. J. Karzes, W. D. Lichtenstein, R. P. Nix, J. S. O’Donnell, and J. C.
Ruttenberg. 1993. The multiflow trace scheduling compiler. Journal of Supercomputing 7, 1–2, 51–142.
C.-K. Luk, R. Cohn, R. Muth, H. Patil, A. Klauser, G. Lowney, S. Wallace, V. Janapa Reddi, and K. Hazelwood.
2005. Pin: Building customized program analysis tools with dynamic instrumentation. In Proceedings
of the ACM SIGPLAN Conference on Programming Language Design and Implementation (PLDI’05).
P. Michaud, Y. Sazeides, A. Seznec, T. Constantinou, and D. Fetis. 2005. An Analytical Model of Temperature
in Microprocessors. Technical Report RR-5744. Inria.
P. Michaud, A. Seznec, and S. Jourdan. 2001. An exploration of instruction fetch requirement in out-of-order
superscalar processors. International Journal of Parallel Programming 29, 1, 35–58.
S. Palacharla, N. P. Jouppi, and J. E. Smith. 1997. Complexity-effective superscalar processors. In Proceedings
of the International Symposium on Computer Architecture (ISCA’97).
R. P. Preston, R. W. Badeau, D. W. Bailey, S. L. Bell, L. L. Biro, W. J. Bowhill, D. E. Dever, S. Felix, R. Gammack,
V. Germini, M. K. Gowan, P. Gronowski, D. B. Jackson, S. Mehta, S. V. Morton, J. D. Pickholtz, M. H.
Reilly, and M. J. Smith. 2002. Design of an 8-wide superscalar RISC microprocessor with simultaneous
multithreading. In Proceedings of the IEEE International Solid-State Circuits Conference (ISSCC’02).
E. M. Riseman and C. C. Foster. 1972. The inhibition of potential parallelism by conditional jumps. IEEE
Transactions on Computing 21, 12, 1405–1411.
E. Rotenberg. 1999. Trace Processors: Exploiting Hierarchy and Speculation. Ph.D. Dissertation. University
of Wisconsin, Madison.
E. Rotenberg, S. Bennett, and J. E. Smith. 1996. Trace cache: A low latency approach to high bandwidth
instruction fetching. In Proceedings of the International Symposium on Microarchitecture (MICRO’96).
E. Rotenberg, Q. Jacobson, Y. Sazeides, and J. E. Smith. 1997. Trace processors. In Proceedings of the
International Symposium on Microarchitecture (MICRO’97).
P. Salverda and C. Zilles. 2005. A criticality analysis of clustering in superscalar processors. In Proceedings
of the International Symposium on Microarchitecture (MICRO’05).
A. Seznec, S. Felix, V. Krishnan, and Y. Sazeides. 2002a. Design tradeoffs for the alpha EV8 conditional
branch predictor. In Proceedings of the International Symposium on Computer Architecture (ISCA’02).
A. Seznec, E. Toullec, and O. Rochecouste. 2002b. Register write specialization register read specialization:
A path to complexity-effective wide-issue superscalar processors. In Proceedings of the International
Symposium on Microarchitecture (MICRO’02).
A. Seznec and P. Michaud. 2006. A case for (partially) tagged geometric history length branch prediction.
Journal of Instruction-Level Parallelism, vol. 8, February 2006.
T. Sha, M. M. K. Martin, and A. Roth. 2005. Scalable store-load forwarding via store queue index prediction.
In Proceedings of the International Symposium on Microarchitecture (MICRO’05).
B. Sinharoy, R. Kalla, W. J. Starke, H. Q. Le, R. Cargnoni, J. A. Van Norstrand, B. J. Ronchetti, J. Stuecheli,
J. Leenstra, G. L. Guthrie, D. Q. Nguyen, B. Blaner, C. F. Marino, E. Retter, and P. Williams. 2011. IBM
POWER7 multicore server processor. IBM Journal of Research and Development 55, 3, 191–219.
B. Sinharoy, J. A. Van Norstrand, R. J. Eickemeyer, H. Q. Le, J. Leenstra, D. Q. Nguyen, B. Konigsburg, K.
Ward, M. D. Brown, J. E. Moreira, D. Levitan, S. Tung, D. Hrusecky, J. W. Bishop, M. Gschwind, M.
Boersma, M. Kroener, M. Kaltenbach, T. Karkhanis, and K. M. Fernsler. 2015. IBM POWER8 processor
core microarchitecture. IBM Journal of Research and Development 59, 1, 2:1–2:21.
S. Subramaniam and G. H. Loh. 2006. Fire-and-forget: Load/store scheduling with no store queue at all. In
Proceedings of the International Symposium on Microarchitecture (MICRO’06).
P. H. Thomas. 1957. Some conduction problems in the heating of small areas on large solids. Quarterly
Journal of Mechanics and Applied Mathematics 10, 4, 482–493.
S. Vajapeyam and T. Mitra. 1997. Improving superscalar instruction dispatch and issue by exploiting dynamic
code sequences. In Proceedings of the International Symposium on Computer Architecture (ISCA’97).
V. V. Zyuban and P. M. Kogge. 2001. Inherently lower-power high-performance superscalar architectures.
IEEE Transactions on Computers 50, 3, 268–285.
Received April 2015; revised June 2015; accepted June 2015
ACM Transactions on Architecture and Code Optimization, Vol. 12, No. 3, Article 28, Publication date: August 2015.
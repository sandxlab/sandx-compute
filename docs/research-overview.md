# Distributed Compute Infrastructure — Domain Overview

**Domain:** Distributed compute orchestration, GPU resource allocation, AI workload scheduling
**SandX engine:** `sandx-compute`
**Phase 2 priority:** #4 (long-horizon; engineering begins after ER + embed + graph are stable)

---

## What Is Distributed Compute Infrastructure?

Distributed compute infrastructure refers to the systems and protocols that schedule, allocate, and coordinate computational workloads across heterogeneous, geographically dispersed compute resources — particularly GPU nodes used for AI training, inference, and data processing.

The metaphor from the SandX name is apt: just as gold is extracted from dispersed sand particles, computational value is extracted from dispersed, fragmented GPU and CPU resources. The infrastructure problem is to aggregate these resources efficiently, route workloads to the right hardware, and ensure consensus over resource state.

---

## Why This Matters Now

The compute landscape is undergoing a structural transition:

```
2020–2023: GPU resources concentrated at hyperscalers (AWS, GCP, Azure)
         ↓
2024–2026: GPU supply dispersed — data centers, enterprise, crypto mining rigs,
           edge nodes, research clusters
         ↓
Future:   Need for infrastructure that orchestrates dispersed, heterogeneous
          GPU resources for AI workloads — the "compute coordination" problem
```

This transition mirrors the move from centralized data centers to distributed cloud — and it creates the same infrastructure problem: how do you treat dispersed resources as a coherent, schedulable pool?

---

## Core Problems

### Resource Discovery and Registration
How do compute nodes announce their availability, capabilities (GPU model, VRAM, connectivity), and current load to a scheduling layer?

### Workload Scheduling
Given a pool of registered nodes and a queue of compute jobs with resource requirements, assign jobs to nodes to maximize throughput, minimize latency, and satisfy constraints (locality, security, cost).

### Consensus Over Resource State
In a distributed system, multiple schedulers may attempt to allocate the same resource simultaneously. Consensus protocols (Raft, PBFT, or simpler lock mechanisms) prevent conflicting assignments.

### Fault Tolerance and Checkpointing
Distributed compute jobs fail. Infrastructure must detect failures, checkpoint progress, and reschedule work without losing computation.

### Cost-Aware Scheduling
Resources have heterogeneous costs (cloud spot instances, on-premise GPU amortization, third-party compute markets). The scheduler must balance performance against cost, including energy cost where relevant.

---

## Positioning

SandX-Compute is positioned at the intersection of:
- **AI compute infrastructure** — scheduling ML training and inference workloads
- **Decentralized compute** — coordinating resources across organizational boundaries
- **Compute economics** — treating GPU cycles as a managed resource pool

This is distinct from:
- Kubernetes (general container orchestration, not GPU/AI-optimized)
- Ray (distributed Python, not multi-organization resource management)
- Slurm (HPC batch scheduling, not cloud-native or decentralized)

---

## State of the Art

| System | Focus |
|--------|-------|
| Ray | Distributed Python, ML workloads, single-cluster |
| Slurm | HPC batch scheduling, institutional clusters |
| Kubernetes + device plugins | Container-level GPU scheduling |
| Volcano | Batch/ML workload scheduling on Kubernetes |
| io.net, Vast.ai | Marketplace model for GPU compute |
| Akash Network | Decentralized compute marketplace |

SandX-Compute differentiates by focusing on **consensus-aware scheduling** across organizational boundaries with a clean SDK interface — targeting the AI infrastructure teams who need to manage multi-cluster, multi-provider GPU resources programmatically.

---

## Key References

- Dean, J., & Ghemawat, S. (2008). MapReduce: Simplified Data Processing on Large Clusters. *CACM.*
- Moritz, P. et al. (2018). Ray: A Distributed Framework for Emerging AI Applications. *OSDI.*
- Vavilapalli, V. K. et al. (2013). Apache Hadoop YARN. *SoCC.*
- Lamport, L., Shostak, R., & Pease, M. (1982). The Byzantine Generals Problem. *ACM TOPLAS.*
- Ongaro, D., & Ousterhout, J. (2014). In Search of an Understandable Consensus Algorithm (Raft). *USENIX ATC.*
- Li, M. et al. (2014). Scaling Distributed Machine Learning with the Parameter Server. *OSDI.* — Seminal parameter server architecture; defines the resource management and communication patterns that `sandx-compute` scheduling builds on.
- Zhao, H. et al. (2023). PyTorch FSDP: Experiences on Scaling Fully Sharded Data Parallel. *VLDB.* — Production experience with large-scale distributed GPU training; informs scheduling requirements for multi-node AI workloads.
- Weng, L. et al. (2022). MLaaS in the Wild: Workload Analysis and Scheduling in Large-Scale Heterogeneous GPU Clusters. *NSDI.* — Real-world GPU cluster workload analysis; directly informs `sandx-compute` scheduling design and heterogeneous resource modeling.

# sandx-compute

**Distributed compute orchestration for the SandX platform.**

[![CI](https://github.com/sandxlab/sandx-compute/actions/workflows/ci.yml/badge.svg)](https://github.com/sandxlab/sandx-compute/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Part of the [SandX Lab](https://github.com/sandxlab) computational infrastructure ecosystem.

---

## What It Does

`sandx-compute` is the resource orchestration layer for the SandX platform. It tracks available compute nodes, matches workloads to nodes by capability, and manages the full job lifecycle.

```
Submit job  →  Scheduler  →  ResourceRegistry  →  Allocated node
                                                     ↓
                                          complete / fail / cancel
                                                     ↓
                                              Node released
```

## Status

> **v0.1 — Working**

| Component | Status |
|-----------|--------|
| `ResourceRegistry` — node registration and capability tracking | **Working** |
| `Scheduler` — requirement-aware first-fit allocation | **Working** |
| Job lifecycle — submit, complete, fail, cancel | **Working** |
| Pending queue retry on node release | **Working** |
| Distributed consensus locking | Planned (Phase 3) |
| PyPI package | **Working** |

## Installation

```bash
pip install sandx-compute
```

Or from source:

```bash
git clone https://github.com/sandxlab/sandx-compute
cd sandx-compute
pip install -e ".[dev]"
```

## Demo

```bash
pip install sandx-compute
python -m examples.schedule_jobs
```

Registers a 5-node compute cluster (CPU + GPU nodes), submits 6 jobs with mixed requirements, shows allocation decisions, and walks through the full job lifecycle — no external data required.

## Quick Start

```python
from sandx_compute import ResourceRegistry, Scheduler

# Register compute nodes
registry = ResourceRegistry()
registry.register("cpu-1", cpu_cores=8, ram_gb=32)
registry.register("gpu-1", cpu_cores=16, ram_gb=64, gpu="A100", vram_gb=80)
registry.register("gpu-2", cpu_cores=8, ram_gb=32, gpu="T4", vram_gb=16)

# Create a scheduler
scheduler = Scheduler(registry)

# Submit a GPU job
job = scheduler.submit("train", requirements={"gpu": True, "min_vram_gb": 40})
print(job)
# Job(id=3f2a1b8c, task='train', status='running', node='gpu-1')

# Complete the job — releases the node
scheduler.complete(job)
print(registry.get("gpu-1").status)  # "available"

# Submit with no suitable node → stays pending
big_job = scheduler.submit("train", requirements={"gpu": True, "min_vram_gb": 200})
print(big_job.status)  # "pending"
```

## Job Requirements

| Key | Type | Description |
|-----|------|-------------|
| `gpu` | `bool` | Requires a GPU node |
| `min_vram_gb` | `float` | Minimum VRAM in GB |
| `min_cpu_cores` | `int` | Minimum CPU core count |
| `min_ram_gb` | `float` | Minimum RAM in GB |

## Node Status Transitions

```
available  →  busy       (job scheduled)
busy       →  available  (job completed / failed / cancelled)
available  →  offline    (manual / health check)
available  →  reserved   (manual hold)
```

## Design Notes

- **Single-process v0.1** — correct for local use; no distributed coordination.
- **First-fit allocation** — jobs are assigned to the first node that satisfies all requirements.
- **Distributed locking** is Phase 3 scope — the `Scheduler` API is designed to accommodate a consensus protocol without breaking changes.

## Related

- [`sandx-er`](https://github.com/sandxlab/sandx-er) — entity resolution
- [`sandx-embed`](https://github.com/sandxlab/sandx-embed) — embedding infrastructure
- [`sandx-graph`](https://github.com/sandxlab/sandx-graph) — graph intelligence
- [sandx.io](https://sandx.io) — project home

## License

Apache 2.0 — see [LICENSE](LICENSE)

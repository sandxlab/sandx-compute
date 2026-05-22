# sandx-compute

**Consensus-aware distributed compute orchestration for AI workloads.**

Part of the [SandX Lab](https://github.com/sandxlab) computational infrastructure ecosystem.

---

## What It Does

`sandx-compute` orchestrates distributed and GPU compute resources across heterogeneous, multi-organization infrastructure. It schedules AI workloads, manages GPU resource pools, and uses consensus protocols to prevent conflicting resource assignments.

Positioned at the transition from cryptocurrency mining toward AI compute infrastructure.

## Status

> **Phase 1 — Architecture & Foundations**
> Engineering priority: Phase 2 (after sandx-er, sandx-embed, sandx-graph are stable).

| Component | Status |
|-----------|--------|
| `sandx_compute.scheduler` — workload scheduler | Skeleton |
| `sandx_compute.registry` — compute node registry | Skeleton |
| `sandx_compute.consensus` — conflict-free resource allocation | Skeleton |
| Python SDK on PyPI | Planned (Phase 2/3) |

## Design Goals

- **Multi-cluster** — coordinate resources across organizational boundaries
- **Consensus-aware** — no conflicting resource assignments across concurrent schedulers
- **GPU-native** — first-class GPU resource model (VRAM, compute capability, interconnect)
- **Fault-tolerant** — detect failures, checkpoint, reschedule without losing computation

## Quick Start (planned API)

```python
from sandx_compute import Scheduler, ResourceRegistry

registry = ResourceRegistry()
registry.register(node_id="gpu-node-01", gpu="A100", vram_gb=80)

scheduler = Scheduler(registry=registry)
job = scheduler.submit(
    task="er_blocking",
    requirements={"gpu": True, "min_vram_gb": 16}
)
print(job.node_id, job.status)
```

## Related

- [`sandx-er`](https://github.com/sandxlab/sandx-er) — entity resolution (primary consumer for heavy workloads)
- [`sandx-embed`](https://github.com/sandxlab/sandx-embed) — embedding computation (GPU workload source)
- [`sandx-graph`](https://github.com/sandxlab/sandx-graph) — graph reasoning (distributed workload source)

## License

Apache 2.0 — see [LICENSE](LICENSE)

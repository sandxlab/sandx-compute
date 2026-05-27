"""sandx-compute — resource registry and job scheduling.

Demonstrates the full sandx-compute workflow: register a cluster of compute
nodes with varying capabilities, submit GPU and CPU workloads, observe
requirement-aware allocation, and walk through the job lifecycle
(running -> complete / fail / cancel).

Install:  pip install sandx-compute
Run:      python -m examples.schedule_jobs
"""

from __future__ import annotations

from sandx_compute import ResourceRegistry, Scheduler

W = 60
SEP  = "=" * W
RULE = "-" * W


def run() -> None:
    print()
    print("  " + SEP)
    print("   sandx-compute  --  Resource Registry & Scheduler")
    print("  " + SEP)

    # ── 1. Register compute nodes ─────────────────────────────────────────
    registry = ResourceRegistry()
    registry.register("cpu-1",  cpu_cores=8,  ram_gb=32)
    registry.register("cpu-2",  cpu_cores=16, ram_gb=64)
    registry.register("gpu-1",  cpu_cores=16, ram_gb=64,  gpu="A100", vram_gb=80)
    registry.register("gpu-2",  cpu_cores=8,  ram_gb=32,  gpu="T4",   vram_gb=16)
    registry.register("gpu-3",  cpu_cores=32, ram_gb=128, gpu="H100", vram_gb=80)

    print()
    print("  CLUSTER")
    print("  " + RULE)
    print(f"  {'NODE':<8}  {'GPU':<8}  {'VRAM':>5}  {'CPU':>4}  {'RAM':>5}  STATUS")
    print("  " + RULE)
    for node_id in ["cpu-1", "cpu-2", "gpu-1", "gpu-2", "gpu-3"]:
        n = registry.get(node_id)
        gpu_str  = n.gpu or "--"
        vram_str = f"{n.vram_gb:.0f}GB" if n.vram_gb else "--"
        print(
            f"  {n.node_id:<8}  {gpu_str:<8}  {vram_str:>5}  "
            f"{n.cpu_cores:>4}  {n.ram_gb:.0f}GB  {n.status}"
        )

    # ── 2. Submit jobs ────────────────────────────────────────────────────
    scheduler = Scheduler(registry)

    jobs = [
        scheduler.submit("embed-batch",    requirements={"gpu": True,  "min_vram_gb": 60}),
        scheduler.submit("preprocess",     requirements={"min_cpu_cores": 8, "min_ram_gb": 16}),
        scheduler.submit("train-large",    requirements={"gpu": True,  "min_vram_gb": 70}),
        scheduler.submit("er-resolve",     requirements={"min_cpu_cores": 12}),
        scheduler.submit("graph-index",    requirements={}),
        scheduler.submit("finetune-small", requirements={"gpu": True,  "min_vram_gb": 12}),
    ]

    print()
    print("  JOB ALLOCATIONS")
    print("  " + RULE)
    print(f"  {'JOB':<16}  {'STATUS':<9}  NODE")
    print("  " + RULE)
    for job in jobs:
        node = job.node_id or "--  (pending: no suitable node available)"
        print(f"  {job.task:<16}  {job.status:<9}  {node}")

    pending = scheduler.pending_jobs()
    running = scheduler.running_jobs()
    print()
    print(f"  Running: {len(running)}  |  Pending: {len(pending)}")

    # ── 3. Walk through lifecycle ─────────────────────────────────────────
    print()
    print("  LIFECYCLE")
    print("  " + RULE)

    embed_job = jobs[0]
    scheduler.complete(embed_job)
    print(f"  complete({embed_job.task!r})  ->  status={embed_job.status!r}  node released")

    preproc_job = jobs[1]
    scheduler.fail(preproc_job)
    print(f"  fail({preproc_job.task!r})      ->  status={preproc_job.status!r}  node released")

    graph_job = jobs[4]
    scheduler.cancel(graph_job)
    print(f"  cancel({graph_job.task!r})   ->  status={graph_job.status!r}")

    # After embed-batch completes, a pending job may be schedulable
    # (in Phase 3, Scheduler.complete() will trigger auto-retry of pending queue)
    still_pending = scheduler.pending_jobs()
    print()
    print(f"  Remaining pending jobs: {len(still_pending)}")
    for j in still_pending:
        print(f"    {j.task!r}  requirements={j.requirements}")

    print()
    print("  " + SEP)
    print("   5 nodes  |  6 jobs submitted  |  lifecycle demonstrated")
    print("  " + SEP)
    print()


if __name__ == "__main__":
    run()

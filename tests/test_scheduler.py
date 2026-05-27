"""Tests for Scheduler."""

from __future__ import annotations

import pytest

from sandx_compute.registry import ResourceRegistry
from sandx_compute.scheduler import Job, Scheduler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def registry() -> ResourceRegistry:
    r = ResourceRegistry()
    r.register("cpu-1", cpu_cores=8, ram_gb=32)
    r.register("gpu-1", cpu_cores=16, ram_gb=64, gpu="A100", vram_gb=80)
    r.register("gpu-2", cpu_cores=8, ram_gb=32, gpu="T4", vram_gb=16)
    return r


@pytest.fixture
def scheduler(registry) -> Scheduler:
    return Scheduler(registry)


# ---------------------------------------------------------------------------
# Job repr
# ---------------------------------------------------------------------------

def test_job_repr():
    j = Job(task="train")
    assert "train" in repr(j)
    assert "pending" in repr(j)


# ---------------------------------------------------------------------------
# submit — happy path
# ---------------------------------------------------------------------------

def test_submit_no_requirements(scheduler, registry):
    job = scheduler.submit("preprocess")
    assert job.status == "running"
    assert job.node_id is not None
    assert registry.get(job.node_id).status == "busy"


def test_submit_gpu_required(scheduler, registry):
    job = scheduler.submit("train", requirements={"gpu": True})
    assert job.status == "running"
    assert registry.get(job.node_id).gpu is not None


def test_submit_min_vram(scheduler, registry):
    job = scheduler.submit("train", requirements={"gpu": True, "min_vram_gb": 40})
    assert job.status == "running"
    assert registry.get(job.node_id).node_id == "gpu-1"


def test_submit_cpu_requirements(scheduler):
    job = scheduler.submit("batch", requirements={"min_cpu_cores": 12})
    assert job.status == "running"
    assert job.node_id == "gpu-1"  # only node with 16 cores


def test_submit_ram_requirements(scheduler):
    job = scheduler.submit("batch", requirements={"min_ram_gb": 60})
    assert job.status == "running"
    assert job.node_id == "gpu-1"  # only node with 64 GB RAM


def test_submit_returns_job_with_id(scheduler):
    job = scheduler.submit("task")
    assert len(job.job_id) == 36  # UUID4


# ---------------------------------------------------------------------------
# submit — no available nodes
# ---------------------------------------------------------------------------

def test_submit_pending_when_no_nodes():
    r = ResourceRegistry()
    s = Scheduler(r)
    job = s.submit("task")
    assert job.status == "pending"
    assert job.node_id is None


def test_submit_pending_when_no_gpu_available(scheduler):
    # exhaust GPU nodes
    scheduler.submit("train", {"gpu": True})
    scheduler.submit("train", {"gpu": True})
    job = scheduler.submit("train", {"gpu": True})
    assert job.status == "pending"


def test_submit_pending_when_vram_too_low(scheduler):
    job = scheduler.submit("train", {"gpu": True, "min_vram_gb": 100})
    assert job.status == "pending"


# ---------------------------------------------------------------------------
# complete
# ---------------------------------------------------------------------------

def test_complete_releases_node(scheduler, registry):
    job = scheduler.submit("task")
    node_id = job.node_id
    scheduler.complete(job)
    assert job.status == "completed"
    assert job.node_id is None
    assert registry.get(node_id).status == "available"


def test_complete_not_running_raises(scheduler):
    job = scheduler.submit("task", {"gpu": True, "min_vram_gb": 999})  # pending
    with pytest.raises(ValueError, match="running"):
        scheduler.complete(job)


# ---------------------------------------------------------------------------
# fail
# ---------------------------------------------------------------------------

def test_fail_releases_node(scheduler, registry):
    job = scheduler.submit("task")
    node_id = job.node_id
    scheduler.fail(job)
    assert job.status == "failed"
    assert registry.get(node_id).status == "available"


def test_fail_not_running_raises(scheduler):
    job = scheduler.submit("task", {"min_vram_gb": 999})  # pending
    with pytest.raises(ValueError, match="running"):
        scheduler.fail(job)


# ---------------------------------------------------------------------------
# cancel
# ---------------------------------------------------------------------------

def test_cancel_running_job(scheduler, registry):
    job = scheduler.submit("task")
    node_id = job.node_id
    scheduler.cancel(job)
    assert job.status == "cancelled"
    assert registry.get(node_id).status == "available"


def test_cancel_pending_job(scheduler):
    job = scheduler.submit("task", {"min_vram_gb": 999})  # pending
    scheduler.cancel(job)
    assert job.status == "cancelled"


def test_cancel_terminal_raises(scheduler):
    job = scheduler.submit("task")
    scheduler.complete(job)
    with pytest.raises(ValueError, match="terminal"):
        scheduler.cancel(job)


# ---------------------------------------------------------------------------
# pending_jobs / running_jobs
# ---------------------------------------------------------------------------

def test_pending_and_running_lists(scheduler):
    j1 = scheduler.submit("task")                          # running
    j2 = scheduler.submit("task", {"min_vram_gb": 999})   # pending

    assert j1 in scheduler.running_jobs()
    assert j2 in scheduler.pending_jobs()
    assert j2 not in scheduler.running_jobs()


def test_node_reuse_after_complete(scheduler):
    """Completing a job should free the node for the next submission."""
    job1 = scheduler.submit("task")
    assert job1.status == "running"
    scheduler.complete(job1)

    job2 = scheduler.submit("task")
    assert job2.status == "running"


# ---------------------------------------------------------------------------
# pending queue retry
# ---------------------------------------------------------------------------

def test_pending_job_scheduled_after_complete(scheduler):
    """A pending job should be auto-scheduled when a suitable node is freed."""
    # Fill all GPU nodes
    gpu_job1 = scheduler.submit("gpu-1", {"gpu": True})
    gpu_job2 = scheduler.submit("gpu-2", {"gpu": True})
    assert gpu_job1.status == "running"
    assert gpu_job2.status == "running"

    # This job cannot run yet — all GPU nodes busy
    waiter = scheduler.submit("waiter", {"gpu": True})
    assert waiter.status == "pending"

    # Completing one GPU job should trigger retry and schedule the waiter
    scheduler.complete(gpu_job1)
    assert waiter.status == "running"
    assert waiter.node_id is not None


def test_pending_job_scheduled_after_fail(scheduler):
    """A pending job should be auto-scheduled when a node is freed via fail()."""
    gpu_job1 = scheduler.submit("gpu-1", {"gpu": True})
    gpu_job2 = scheduler.submit("gpu-2", {"gpu": True})
    waiter = scheduler.submit("waiter", {"gpu": True})
    assert waiter.status == "pending"

    scheduler.fail(gpu_job1)
    assert waiter.status == "running"


def test_pending_job_not_scheduled_if_requirements_unmet(scheduler):
    """A pending job requiring more VRAM than any free node should stay pending."""
    gpu_job = scheduler.submit("gpu", {"gpu": True, "min_vram_gb": 80})
    assert gpu_job.status == "running"
    assert gpu_job.node_id == "gpu-1"  # A100 80GB

    # Needs more VRAM than any node has — should never schedule
    impossible = scheduler.submit("impossible", {"gpu": True, "min_vram_gb": 200})
    assert impossible.status == "pending"

    scheduler.complete(gpu_job)
    assert impossible.status == "pending"  # still no node meets requirement


def test_multiple_pending_jobs_retry_on_release(scheduler):
    """When multiple pending jobs exist, retry fires for all on each release.

    The fixture has 3 nodes (cpu-1, gpu-1, gpu-2). Filling all 3 then adding
    2 more pending jobs: when one node is freed, exactly one pending job runs
    (first-fit), the other stays pending.
    """
    j1 = scheduler.submit("t1", {"gpu": True})   # gpu-1
    j2 = scheduler.submit("t2", {"gpu": True})   # gpu-2
    cpu = scheduler.submit("t3")                  # cpu-1
    assert j1.status == j2.status == cpu.status == "running"

    p1 = scheduler.submit("p1")   # pending
    p2 = scheduler.submit("p2")   # pending
    assert p1.status == "pending"
    assert p2.status == "pending"

    # Free the CPU node — one pending job should get it
    scheduler.complete(cpu)
    running_count = sum(1 for j in [p1, p2] if j.status == "running")
    pending_count = sum(1 for j in [p1, p2] if j.status == "pending")
    assert running_count == 1
    assert pending_count == 1

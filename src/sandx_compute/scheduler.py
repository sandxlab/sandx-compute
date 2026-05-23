"""Scheduler — workload scheduler with requirement-aware node allocation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
import uuid

from sandx_compute.registry import ResourceRegistry


JobStatus = Literal["pending", "running", "completed", "failed", "cancelled"]


@dataclass
class Job:
    """A compute job submitted to the scheduler.

    Attributes:
        job_id:       Unique identifier (UUID4).
        task:         Opaque task identifier string.
        requirements: Resource constraints. Supported keys:
                        gpu (bool)          — GPU required
                        min_vram_gb (float) — minimum VRAM
                        min_cpu_cores (int) — minimum CPU cores
                        min_ram_gb (float)  — minimum RAM
        status:       Lifecycle state.
        node_id:      Assigned node once scheduled; None while pending.
    """

    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task: str = ""
    requirements: dict = field(default_factory=dict)
    status: JobStatus = "pending"
    node_id: str | None = None

    def __repr__(self) -> str:
        return (
            f"Job(id={self.job_id[:8]}, task={self.task!r}, "
            f"status={self.status!r}, node={self.node_id!r})"
        )


class Scheduler:
    """Requirement-aware workload scheduler backed by a ResourceRegistry.

    Matches submitted jobs to available compute nodes using first-fit
    allocation. A node is marked busy for the duration of a job and
    returned to available on completion, failure, or cancellation.

    Distributed locking and consensus-aware scheduling are Phase 3 scope.
    This implementation is correct for single-process use.

    Args:
        registry: ResourceRegistry instance to allocate from.

    Usage:
        registry = ResourceRegistry()
        registry.register("node-1", cpu_cores=16, ram_gb=64, gpu="A100", vram_gb=80)

        scheduler = Scheduler(registry)
        job = scheduler.submit("train", requirements={"gpu": True, "min_vram_gb": 40})
        # job.status == "running", job.node_id == "node-1"

        scheduler.complete(job)
        # job.status == "completed", node-1 back to "available"
    """

    def __init__(self, registry: ResourceRegistry) -> None:
        self.registry = registry
        self._jobs: dict[str, Job] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit(self, task: str, requirements: dict | None = None) -> Job:
        """Submit a compute job for immediate scheduling.

        Args:
            task:         Identifier for the compute task type.
            requirements: Resource constraints (see Job.requirements).

        Returns:
            Job with status "running" if a node was allocated,
            or "pending" if no suitable node is currently available.
        """
        job = Job(task=task, requirements=requirements or {})
        self._jobs[job.job_id] = job
        self._try_schedule(job)
        return job

    def complete(self, job: Job) -> None:
        """Mark a running job as completed and release its node.

        Args:
            job: A Job previously returned by submit().

        Raises:
            ValueError: If the job is not in "running" state.
        """
        if job.status != "running":
            raise ValueError(
                f"Cannot complete job {job.job_id[:8]!r}: status is {job.status!r}, expected 'running'."
            )
        self._release(job, "completed")

    def fail(self, job: Job) -> None:
        """Mark a running job as failed and release its node.

        Args:
            job: A Job previously returned by submit().

        Raises:
            ValueError: If the job is not in "running" state.
        """
        if job.status != "running":
            raise ValueError(
                f"Cannot fail job {job.job_id[:8]!r}: status is {job.status!r}, expected 'running'."
            )
        self._release(job, "failed")

    def cancel(self, job: Job) -> None:
        """Cancel a pending or running job.

        If the job was running, its node is released back to available.

        Args:
            job: A Job previously returned by submit().

        Raises:
            ValueError: If the job is already terminal (completed/failed/cancelled).
        """
        if job.status in ("completed", "failed", "cancelled"):
            raise ValueError(
                f"Cannot cancel job {job.job_id[:8]!r}: already terminal ({job.status!r})."
            )
        if job.status == "running":
            self._release(job, "cancelled")
        else:
            job.status = "cancelled"

    def pending_jobs(self) -> list[Job]:
        """Return all jobs currently in pending state."""
        return [j for j in self._jobs.values() if j.status == "pending"]

    def running_jobs(self) -> list[Job]:
        """Return all jobs currently in running state."""
        return [j for j in self._jobs.values() if j.status == "running"]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _try_schedule(self, job: Job) -> None:
        """Attempt to allocate a node for job. Mutates job in-place."""
        req = job.requirements
        gpu_required = bool(req.get("gpu", False))
        min_vram = float(req.get("min_vram_gb", 0))
        min_cpu = int(req.get("min_cpu_cores", 0))
        min_ram = float(req.get("min_ram_gb", 0))

        candidates = self.registry.available(
            gpu_required=gpu_required,
            min_vram_gb=min_vram,
        )
        candidates = [
            n for n in candidates
            if n.cpu_cores >= min_cpu and n.ram_gb >= min_ram
        ]

        if not candidates:
            return  # job stays pending

        node = candidates[0]  # first-fit
        self.registry.update_status(node.node_id, "busy")
        job.node_id = node.node_id
        job.status = "running"

    def _release(self, job: Job, terminal_status: JobStatus) -> None:
        if job.node_id:
            self.registry.update_status(job.node_id, "available")
        job.status = terminal_status
        job.node_id = None

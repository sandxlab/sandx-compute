"""Scheduler — consensus-aware workload scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
import uuid

from sandx_compute.registry import ResourceRegistry, ComputeNode

JobStatus = Literal["pending", "running", "completed", "failed", "cancelled"]


@dataclass
class Job:
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task: str = ""
    requirements: dict = field(default_factory=dict)
    status: JobStatus = "pending"
    node_id: str | None = None


class Scheduler:
    """Consensus-aware workload scheduler.

    Matches submitted jobs to available compute nodes from the registry.
    Uses a lock-based consensus protocol to prevent conflicting assignments
    when multiple scheduler instances operate concurrently.

    Args:
        registry: ResourceRegistry instance to allocate from.
    """

    def __init__(self, registry: ResourceRegistry) -> None:
        self.registry = registry
        self._queue: list[Job] = []

    def submit(
        self,
        task: str,
        requirements: dict | None = None,
    ) -> Job:
        """Submit a compute job for scheduling.

        Args:
            task:         Identifier for the compute task type.
            requirements: Resource constraints, e.g. {"gpu": True, "min_vram_gb": 16}.

        Returns:
            Job object with assigned node_id once allocated.
        """
        job = Job(task=task, requirements=requirements or {})
        self._queue.append(job)
        self._try_schedule(job)
        return job

    def _try_schedule(self, job: Job) -> None:
        raise NotImplementedError("Phase 2")

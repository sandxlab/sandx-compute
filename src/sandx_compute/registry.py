"""ResourceRegistry — compute node discovery and capability tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

NodeStatus = Literal["available", "busy", "offline", "reserved"]


@dataclass
class ComputeNode:
    node_id: str
    gpu: str | None           # GPU model, e.g. "A100", "H100", None for CPU-only
    vram_gb: float | None     # VRAM in gigabytes
    cpu_cores: int
    ram_gb: float
    status: NodeStatus = "available"
    tags: list[str] = field(default_factory=list)


class ResourceRegistry:
    """Registry of available compute nodes.

    Nodes register themselves by calling `register()`. The scheduler
    queries the registry to find nodes matching job requirements.

    Thread-safety: Phase 2 implementation will use optimistic locking.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, ComputeNode] = {}

    def register(
        self,
        node_id: str,
        cpu_cores: int,
        ram_gb: float,
        gpu: str | None = None,
        vram_gb: float | None = None,
        tags: list[str] | None = None,
    ) -> ComputeNode:
        node = ComputeNode(
            node_id=node_id,
            gpu=gpu,
            vram_gb=vram_gb,
            cpu_cores=cpu_cores,
            ram_gb=ram_gb,
            tags=tags or [],
        )
        self._nodes[node_id] = node
        return node

    def available(self, gpu_required: bool = False, min_vram_gb: float = 0) -> list[ComputeNode]:
        return [
            n for n in self._nodes.values()
            if n.status == "available"
            and (not gpu_required or n.gpu is not None)
            and (n.vram_gb or 0) >= min_vram_gb
        ]

    def get(self, node_id: str) -> ComputeNode | None:
        return self._nodes.get(node_id)

    def update_status(self, node_id: str, status: NodeStatus) -> None:
        if node_id in self._nodes:
            self._nodes[node_id].status = status

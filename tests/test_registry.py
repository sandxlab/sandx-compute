"""Tests for ResourceRegistry and ComputeNode."""

from __future__ import annotations

import pytest

from sandx_compute.registry import ResourceRegistry


@pytest.fixture
def registry() -> ResourceRegistry:
    return ResourceRegistry()


@pytest.fixture
def populated(registry) -> ResourceRegistry:
    registry.register("cpu-1", cpu_cores=8, ram_gb=32)
    registry.register("gpu-1", cpu_cores=16, ram_gb=64, gpu="A100", vram_gb=80)
    registry.register("gpu-2", cpu_cores=8, ram_gb=32, gpu="T4", vram_gb=16)
    return registry


# ---------------------------------------------------------------------------
# register / get
# ---------------------------------------------------------------------------

def test_register_cpu_node(registry):
    node = registry.register("n1", cpu_cores=4, ram_gb=16)
    assert node.node_id == "n1"
    assert node.gpu is None
    assert node.vram_gb is None
    assert node.status == "available"


def test_register_gpu_node(registry):
    node = registry.register("n1", cpu_cores=16, ram_gb=64, gpu="A100", vram_gb=80)
    assert node.gpu == "A100"
    assert node.vram_gb == 80


def test_register_with_tags(registry):
    node = registry.register("n1", cpu_cores=4, ram_gb=8, tags=["spot", "eu-west"])
    assert "spot" in node.tags


def test_get_existing(populated):
    node = populated.get("gpu-1")
    assert node is not None
    assert node.node_id == "gpu-1"


def test_get_missing(registry):
    assert registry.get("nonexistent") is None


# ---------------------------------------------------------------------------
# available
# ---------------------------------------------------------------------------

def test_available_all(populated):
    nodes = populated.available()
    assert len(nodes) == 3


def test_available_gpu_only(populated):
    nodes = populated.available(gpu_required=True)
    assert all(n.gpu is not None for n in nodes)
    assert len(nodes) == 2


def test_available_min_vram(populated):
    nodes = populated.available(gpu_required=True, min_vram_gb=40)
    assert len(nodes) == 1
    assert nodes[0].node_id == "gpu-1"


def test_available_excludes_busy(populated):
    populated.update_status("gpu-1", "busy")
    nodes = populated.available(gpu_required=True)
    assert all(n.node_id != "gpu-1" for n in nodes)


def test_available_excludes_offline(populated):
    populated.update_status("cpu-1", "offline")
    nodes = populated.available()
    assert len(nodes) == 2


def test_available_empty_registry(registry):
    assert registry.available() == []


# ---------------------------------------------------------------------------
# update_status
# ---------------------------------------------------------------------------

def test_update_status(populated):
    populated.update_status("cpu-1", "busy")
    assert populated.get("cpu-1").status == "busy"


def test_update_status_unknown_node_silent(populated):
    # should not raise
    populated.update_status("does-not-exist", "busy")


def test_all_status_values(registry):
    registry.register("n", cpu_cores=1, ram_gb=1)
    for status in ("available", "busy", "offline", "reserved"):
        registry.update_status("n", status)
        assert registry.get("n").status == status

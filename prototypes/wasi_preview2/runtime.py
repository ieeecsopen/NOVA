"""Minimal runtime layer for the WASI preview2 prototype.

This is intentionally a small runtime shim: it models the host-side bridge used
by a NOVA guest to call preview2 imports via explicit, declared capabilities.
"""
from __future__ import annotations

from .bridge import CapabilityBridgeError, Preview2Bridge


class WASIRuntime:
    """Thin runtime that exposes only explicit preview2 capabilities."""

    def __init__(self, declared_capabilities: set[str] | None = None):
        self.bridge = Preview2Bridge.from_manifest(
            declared_capabilities or {"Clock"}
        )

    def call(self, capability: str) -> dict[str, object]:
        binding = self.bridge.bind(capability)
        if capability == "Clock":
            return {
                "capability": binding.capability,
                "wit_import": binding.wit_import,
                "host_function": binding.host_function,
                "zero_overhead": binding.zero_overhead,
                "value": self.bridge.clock_now_ns(),
            }
        if capability == "Random":
            return {
                "capability": binding.capability,
                "wit_import": binding.wit_import,
                "host_function": binding.host_function,
                "zero_overhead": binding.zero_overhead,
                "value": self.bridge.random_u64(),
            }
        raise CapabilityBridgeError(f"unsupported capability for WASI runtime: {capability!r}")

    def manifest(self) -> dict[str, object]:
        return self.bridge.as_manifest()

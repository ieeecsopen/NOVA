"""Prototype WASI preview2 bridge for NOVA capability handles.

This is intended as a concrete, testable prototype for issue #38. It models the
mapping from NOVA capabilities to WASI preview2 imports, enforces explicit grant
of authority, and keeps the implementation small and repository-local.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from time import time_ns
from typing import Iterable


class CapabilityBridgeError(RuntimeError):
    """Explicitly rejected capability usage without manifest approval."""


@dataclass(frozen=True)
class CapabilityBinding:
    capability: str
    wit_import: str
    host_function: str
    zero_overhead: bool = True


@dataclass
class Preview2Bridge:
    """Host-side capability mapping between NOVA and WASI preview2."""

    allowed_capabilities: set[str] = field(default_factory=lambda: {"Clock", "Random"})
    declared_capabilities: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        unknown = self.declared_capabilities - self.allowed_capabilities
        if unknown:
            raise CapabilityBridgeError(
                f"unsupported capability binding requested: {sorted(unknown)}"
            )

    @classmethod
    def from_manifest(cls, capabilities: Iterable[str]) -> "Preview2Bridge":
        return cls(declared_capabilities=set(capabilities))

    def bind(self, capability: str) -> CapabilityBinding:
        if capability not in self.allowed_capabilities:
            raise CapabilityBridgeError(
                f"capability {capability!r} is not a supported preview2 binding"
            )
        if capability not in self.declared_capabilities:
            raise CapabilityBridgeError(
                f"capability {capability!r} was not explicitly granted by the manifest"
            )

        if capability == "Clock":
            return CapabilityBinding(
                capability="Clock",
                wit_import="wasi:clocks/monotonic-clock",
                host_function="now",
                zero_overhead=True,
            )
        if capability == "Random":
            return CapabilityBinding(
                capability="Random",
                wit_import="wasi:random/insecure-random",
                host_function="get-u64",
                zero_overhead=True,
            )
        raise CapabilityBridgeError(f"missing binding for {capability!r}")

    def clock_now_ns(self) -> int:
        self.bind("Clock")
        return time_ns()

    def random_u64(self) -> int:
        self.bind("Random")
        return int.from_bytes(os.urandom(8), "big", signed=False)

    def wit_imports(self) -> list[dict[str, str | bool]]:
        imports: list[dict[str, str | bool]] = []
        for capability in sorted(self.declared_capabilities):
            binding = self.bind(capability)
            imports.append(
                {
                    "capability": binding.capability,
                    "wit_import": binding.wit_import,
                    "host_function": binding.host_function,
                    "zero_overhead": binding.zero_overhead,
                }
            )
        return imports

    def as_manifest(self) -> dict[str, object]:
        return {
            "allowed_capabilities": sorted(self.allowed_capabilities),
            "declared_capabilities": sorted(self.declared_capabilities),
            "zero_ambient_authority": True,
            "imports": self.wit_imports(),
        }


def build_wit_interface() -> str:
    return """\
package nova:wasi-preview2;

interface clocks {
  now: func() -> u64;
}

interface random {
  get-u64: func() -> u64;
}
"""

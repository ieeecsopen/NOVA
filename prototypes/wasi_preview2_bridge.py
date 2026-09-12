"""Prototype WASI preview2 capability bridge for NOVA.

This is intentionally lightweight: it models the host-side mapping between
NOVA capability handles (`Clock`, `Random`) and the corresponding WASI
preview2 component imports without pretending to be a full compiler backend.

The goal is to make the research question concrete and testable: which
capability handle maps to which WIT interface, and how much runtime overhead
is introduced by that binding.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from time import time_ns
from typing import Iterable


class CapabilityBridgeError(RuntimeError):
    """Raised when a capability is not explicitly granted by the manifest."""


@dataclass(frozen=True)
class CapabilityBinding:
    """A host-capability binding for a WASI preview2 import."""

    capability: str
    wit_import: str
    host_function: str
    zero_overhead: bool = True


@dataclass
class Preview2Bridge:
    """Prototype bridge from NOVA capabilities to WASI preview2 imports.

    Manifested capability tokens are the only thing allowed to cross the host
    boundary. The bridge intentionally enforces an empty-ambient-authority rule:
    if a capability is not explicitly declared, it cannot be bound.
    """

    allowed_capabilities: set[str] = field(
        default_factory=lambda: {"Clock", "Random"}
    )
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
        """Return a monotonic timestamp in nanoseconds via the host clock."""
        self.bind("Clock")
        return time_ns()

    def random_u64(self) -> int:
        """Return a random 64-bit value from the host source."""
        self.bind("Random")
        return int.from_bytes(os.urandom(8), "big", signed=False)

    def wit_imports(self) -> list[dict[str, str | bool]]:
        return [
            {
                "capability": binding.capability,
                "wit_import": binding.wit_import,
                "host_function": binding.host_function,
                "zero_overhead": str(binding.zero_overhead).lower(),
            }
            for capability in sorted(self.declared_capabilities)
            for binding in [self.bind(capability)]
        ]

    def as_manifest(self) -> dict[str, object]:
        return {
            "allowed_capabilities": sorted(self.allowed_capabilities),
            "declared_capabilities": sorted(self.declared_capabilities),
            "zero_ambient_authority": True,
            "imports": self.wit_imports(),
        }


def build_wit_interface() -> str:
    """Return a minimal WIT sketch for the capability mapping."""
    return """\
package nova:wasi-preview2;

interface clocks {
  // monotonic time source for NOVA Clock capabilities
  now: func() -> u64;
}

interface random {
  // cryptographically safe random source for NOVA Random capabilities
  get-u64: func() -> u64;
}
"""


def main() -> None:
    bridge = Preview2Bridge.from_manifest({"Clock", "Random"})
    print(bridge.as_manifest())


if __name__ == "__main__":
    main()

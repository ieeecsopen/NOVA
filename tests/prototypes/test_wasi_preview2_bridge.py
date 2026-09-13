import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from prototypes.wasi_preview2.bridge import (
    CapabilityBridgeError,
    Preview2Bridge,
    build_wit_interface,
)
from prototypes.wasi_preview2.runtime import WASIRuntime


class TestWasiPreview2Bridge(unittest.TestCase):
    def test_bindings_are_explicitly_declared(self) -> None:
        bridge = Preview2Bridge.from_manifest({"Clock"})
        binding = bridge.bind("Clock")
        self.assertEqual(binding.capability, "Clock")
        self.assertEqual(binding.wit_import, "wasi:clocks/monotonic-clock")
        self.assertTrue(binding.zero_overhead)

    def test_random_binding_is_present(self) -> None:
        bridge = Preview2Bridge.from_manifest({"Clock", "Random"})
        binding = bridge.bind("Random")
        self.assertEqual(binding.capability, "Random")
        self.assertEqual(binding.wit_import, "wasi:random/insecure-random")
        self.assertTrue(binding.zero_overhead)

    def test_unbound_capability_is_rejected(self) -> None:
        bridge = Preview2Bridge.from_manifest({"Clock"})
        with self.assertRaises(CapabilityBridgeError):
            bridge.bind("Random")

    def test_wit_interface_lists_clock_and_random(self) -> None:
        wit = build_wit_interface()
        self.assertIn("interface clocks", wit)
        self.assertIn("interface random", wit)
        self.assertIn("now: func() -> u64;", wit)
        self.assertIn("get-u64: func() -> u64;", wit)

    def test_bridge_reports_zero_ambient_authority(self) -> None:
        bridge = Preview2Bridge.from_manifest({"Clock"})
        manifest = bridge.as_manifest()
        self.assertTrue(manifest["zero_ambient_authority"])
        self.assertEqual(manifest["declared_capabilities"], ["Clock"])

    def test_runtime_binds_declared_capabilities(self) -> None:
        runtime = WASIRuntime({"Clock", "Random"})
        clock = runtime.call("Clock")
        random_value = runtime.call("Random")
        self.assertIn("wasi:clocks/monotonic-clock", clock["wit_import"])
        self.assertIn("wasi:random/insecure-random", random_value["wit_import"])
        self.assertTrue(clock["zero_overhead"])
        self.assertTrue(random_value["zero_overhead"])

    def test_runtime_rejects_undeclared_capability(self) -> None:
        runtime = WASIRuntime({"Clock"})
        with self.assertRaises(CapabilityBridgeError):
            runtime.call("Random")


if __name__ == "__main__":
    unittest.main()

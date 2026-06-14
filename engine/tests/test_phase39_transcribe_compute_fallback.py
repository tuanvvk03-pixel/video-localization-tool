"""Phase fix — transcribe compute-type fallback for GPUs without float16.

Some CUDA GPUs/CT2 builds reject float16 ("Requested float16 compute type, but
the target device or backend do not support efficient float16 computation").
The stage must step down (int8_float16 -> int8 -> CPU) instead of failing.
"""
from __future__ import annotations

import unittest

from engine import run_transcribe_stage as rt


class ComputeFallbackPredicateTest(unittest.TestCase):
    def test_detects_float16_unsupported(self) -> None:
        msg = ("Requested float16 compute type, but the target device or backend "
               "do not support efficient float16 computation.")
        self.assertTrue(rt._is_unsupported_compute_error(RuntimeError(msg)))

    def test_detects_does_not_support(self) -> None:
        self.assertTrue(rt._is_unsupported_compute_error(RuntimeError("compute type int8 does not support this device")))

    def test_ignores_unrelated(self) -> None:
        self.assertFalse(rt._is_unsupported_compute_error(RuntimeError("file not found")))
        self.assertFalse(rt._is_unsupported_compute_error(RuntimeError("cublas64_12.dll is not found")))

    def test_cuda_runtime_still_distinct(self) -> None:
        # The two predicates should not overlap on the cublas case.
        cublas = RuntimeError("Library cublas64_12.dll is not found or cannot be loaded")
        self.assertTrue(rt._is_cuda_runtime_error(cublas))
        self.assertFalse(rt._is_unsupported_compute_error(cublas))


if __name__ == "__main__":
    unittest.main()

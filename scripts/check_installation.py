#!/usr/bin/env python3
from __future__ import annotations

import importlib

REQUIRED = [
    "numpy",
    "pandas",
    "scipy",
    "matplotlib",
    "tifffile",
    "h5py",
    "PIL",
    "yaml",
]


def main() -> None:
    failures = []
    for module_name in REQUIRED:
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "unknown")
            print(f"OK  {module_name}: {version}")
        except Exception as exc:
            failures.append((module_name, str(exc)))
            print(f"FAIL {module_name}: {exc}")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

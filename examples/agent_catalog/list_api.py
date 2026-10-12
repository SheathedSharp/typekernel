#!/usr/bin/env python3
"""Print every public name re-exported from typekernel.parts (agent discovery)."""

from __future__ import annotations

from typekernel import parts


def main() -> None:
    for name in parts.__all__:
        obj = getattr(parts, name)
        doc = (getattr(obj, "__doc__", None) or "").strip().split("\n", 1)[0]
        print(f"{name}: {doc}")


if __name__ == "__main__":
    main()

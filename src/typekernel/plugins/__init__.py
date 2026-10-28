"""Fill and pass plugins (ARCHITECTURE.md「槽位与填充协议」).

Kernel packages must not import this package; projects wire plugins into
``apply_slots`` and related entry points.
"""

from __future__ import annotations

__all__: list[str] = []

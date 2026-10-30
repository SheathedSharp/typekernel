"""``tk doctor`` — environment / extras health check (S0)."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version

__all__ = [
    "DoctorReport",
    "MissingExtraError",
    "check_environment",
    "format_doctor_report",
    "require_compile_extras",
]


class MissingExtraError(RuntimeError):
    """Raised when a required optional dependency is missing."""


@dataclass
class DoctorReport:
    ok: bool
    lines: list[str] = field(default_factory=list)
    missing_compile: list[str] = field(default_factory=list)
    missing_specimen: list[str] = field(default_factory=list)


def _have(mod: str) -> bool:
    try:
        import_module(mod)
        return True
    except ImportError:
        return False


def _pkg(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "missing"


def check_environment() -> DoctorReport:
    """Probe compile / specimen extras and core packages."""
    lines: list[str] = []
    missing_compile: list[str] = []
    missing_specimen: list[str] = []

    for mod, pip in (("ufoLib2", "ufoLib2"), ("ufo2ft", "ufo2ft"), ("fontTools", "fonttools")):
        if _have(mod):
            lines.append(f"OK  compile:{mod} ({_pkg(pip)})")
        else:
            missing_compile.append(mod)
            lines.append(f"MISS compile:{mod} — pip install 'typekernel[compile]'")

    if _have("PIL"):
        lines.append(f"OK  specimen:Pillow ({_pkg('pillow')})")
    else:
        missing_specimen.append("Pillow")
        lines.append("MISS specimen:Pillow — pip install 'typekernel[specimen]'")

    if _have("pathops"):
        lines.append(f"OK  boolean:skia-pathops ({_pkg('skia-pathops')})")
    else:
        lines.append("WARN boolean:skia-pathops missing (overlap checks limited)")

    ok = not missing_compile
    return DoctorReport(
        ok=ok,
        lines=lines,
        missing_compile=missing_compile,
        missing_specimen=missing_specimen,
    )


def format_doctor_report(report: DoctorReport) -> str:
    header = "tk doctor: OK" if report.ok else "tk doctor: problems found"
    return header + "\n" + "\n".join(report.lines) + "\n"


def require_compile_extras(*, context: str = "build") -> None:
    """Raise :class:`MissingExtraError` with an actionable message."""
    report = check_environment()
    if report.missing_compile:
        missing = ", ".join(report.missing_compile)
        raise MissingExtraError(
            f"{context}: missing compile extras ({missing}). "
            "Install with: pip install 'typekernel[compile]'"
        )

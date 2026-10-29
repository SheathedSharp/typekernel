"""Release checks + optional FontBakery (``tk check --release``)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from typekernel.diagnose.protocol import Finding

__all__ = [
    "ReleaseReport",
    "check_release",
    "check_release_binary",
    "format_release_report",
    "run_fontbakery_opentype",
    "write_release_manifest",
]

_GLYPH_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]{0,62}$")


@dataclass(frozen=True, slots=True)
class ReleaseReport:
    """Outcome of :func:`check_release` (+ optional FontBakery)."""

    binary: str
    findings: tuple[Finding, ...]
    fontbakery: dict[str, Any] | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.level == "error")

    @property
    def warn_count(self) -> int:
        return sum(1 for f in self.findings if f.level == "warn")

    @property
    def fontbakery_fail_count(self) -> int:
        if not self.fontbakery:
            return 0
        return int(self.fontbakery.get("FAIL", 0))


def _finding(
    check: str,
    level: str,
    message: str,
    *,
    hint: str = "",
    measured: float | None = None,
    expected: float | None = None,
) -> Finding:
    return Finding(
        check=check,
        level=level,  # type: ignore[arg-type]
        glyph=None,
        master=None,
        where=None,
        measured=measured,
        expected=expected,
        message=message,
        hint=hint,
    )


def check_release_binary(path: str | Path) -> list[Finding]:
    """Release checks against a compiled font binary."""
    from fontTools.ttLib import TTFont

    tt = TTFont(Path(path))
    out: list[Finding] = []

    if "name" not in tt:
        out.append(_finding("release.name", "error", "font has no name table"))
    else:
        name = tt["name"]
        family = name.getDebugName(1) or name.getDebugName(16)
        style = name.getDebugName(2) or name.getDebugName(17)
        if not family:
            out.append(_finding("release.name", "error", "missing family name (ID 1/16)"))
        if not style:
            out.append(_finding("release.name", "error", "missing style name (ID 2/17)"))

    if "OS/2" not in tt:
        out.append(_finding("release.os2", "error", "font has no OS/2 table"))
    else:
        os2 = tt["OS/2"]
        wc = int(os2.usWeightClass)
        if not 1 <= wc <= 1000:
            out.append(
                _finding(
                    "release.os2",
                    "error",
                    f"usWeightClass out of range: {wc}",
                    measured=float(wc),
                    expected=400.0,
                )
            )
        typo_asc = int(getattr(os2, "sTypoAscender", 0) or 0)
        typo_desc = int(getattr(os2, "sTypoDescender", 0) or 0)
        if typo_asc <= 0:
            out.append(
                _finding(
                    "release.metrics",
                    "error",
                    f"sTypoAscender must be > 0, got {typo_asc}",
                    measured=float(typo_asc),
                )
            )
        if typo_desc > 0:
            out.append(
                _finding(
                    "release.metrics",
                    "error",
                    f"sTypoDescender must be <= 0, got {typo_desc}",
                    measured=float(typo_desc),
                )
            )
        if "hhea" in tt:
            hhea = tt["hhea"]
            if int(hhea.ascent) != typo_asc or int(hhea.descent) != typo_desc:
                out.append(
                    _finding(
                        "release.metrics",
                        "warn",
                        (
                            f"hhea ascent/descent ({hhea.ascent}/{hhea.descent}) "
                            f"!= OS/2 sTypo ({typo_asc}/{typo_desc})"
                        ),
                        hint="align hhea with sTypoAscender/Descender for consistent line metrics",
                    )
                )

    if "fvar" in tt and "STAT" not in tt:
        out.append(
            _finding(
                "release.stat",
                "error",
                "variable font has fvar but no STAT table",
                hint="build with project Axis.labels so designspace emits STAT",
            )
        )

    bad_names: list[str] = []
    for gname in tt.getGlyphOrder():
        if gname in {".notdef", ".null"}:
            continue
        if not _GLYPH_NAME_RE.match(gname):
            bad_names.append(gname)
    if bad_names:
        sample = ", ".join(bad_names[:8])
        more = f" (+{len(bad_names) - 8} more)" if len(bad_names) > 8 else ""
        out.append(
            _finding(
                "release.glyph_names",
                "error",
                f"illegal glyph name(s): {sample}{more}",
            )
        )

    return out


def run_fontbakery_opentype(path: str | Path) -> dict[str, Any] | None:
    """Run FontBakery ``check-opentype`` if installed; return summary counts or None."""
    import importlib.util
    import subprocess
    import sys
    import tempfile

    if importlib.util.find_spec("fontbakery") is None:
        return None

    binary = str(Path(path).resolve())
    counts: dict[str, Any] = {"FAIL": 0, "WARN": 0, "ERROR": 0, "SKIP": 0, "PASS": 0, "INFO": 0}
    with tempfile.TemporaryDirectory() as tmp:
        json_path = Path(tmp) / "fontbakery.json"
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "fontbakery",
                "check-opentype",
                binary,
                "--json",
                str(json_path),
                "-q",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if json_path.is_file():
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            result = payload.get("result")
            if isinstance(result, dict):
                for status, n in result.items():
                    key = str(status).upper()
                    if key in counts:
                        counts[key] = int(n)
            for sec in payload.get("sections") or []:
                for check in sec.get("checks") or []:
                    st = check.get("result") or check.get("status")
                    if isinstance(st, dict):
                        st = st.get("result") or st.get("status")
                    key = str(st or "").upper()
                    if key in counts and not isinstance(result, dict):
                        counts[key] += 1
                    if key == "FAIL":
                        counts.setdefault("fail_ids", [])
                        cid = (
                            check.get("key")
                            or check.get("check_id")
                            or check.get("description")
                            or "unknown"
                        )
                        if isinstance(counts["fail_ids"], list):
                            counts["fail_ids"].append(str(cid))
        counts["returncode"] = proc.returncode
        counts["available"] = True
        if proc.returncode and not any(counts[k] for k in ("FAIL", "ERROR", "WARN", "PASS")):
            # CLI failed before producing usable JSON — surface stderr briefly.
            counts["stderr"] = (proc.stderr or proc.stdout or "")[-500:]
    return counts

def check_release(path: str | Path, *, fontbakery: bool = True) -> ReleaseReport:
    """Run release checks (and optional FontBakery) on ``path``."""
    findings = check_release_binary(path)
    fb = run_fontbakery_opentype(path) if fontbakery else None
    return ReleaseReport(
        binary=str(Path(path).resolve()),
        findings=tuple(findings),
        fontbakery=fb,
    )


def write_release_manifest(report: ReleaseReport, path: str | Path) -> Path:
    """Write release-check results next to a build (manifest extension)."""
    out = Path(path)
    payload = {
        "timestamp": report.timestamp,
        "binary": report.binary,
        "h_errors": report.error_count,
        "h_warns": report.warn_count,
        "findings": [
            {
                "check": f.check,
                "level": f.level,
                "message": f.message,
                "hint": f.hint,
            }
            for f in report.findings
        ],
        "fontbakery": report.fontbakery,
        "switches": {"fontbakery": report.fontbakery is not None},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def format_release_report(report: ReleaseReport) -> str:
    lines = [
        f"release check: {report.binary}",
        f"H errors: {report.error_count}  warns: {report.warn_count}",
    ]
    for f in report.findings:
        lines.append(f"  [{f.level}] {f.check}: {f.message}")
    if report.fontbakery is None:
        lines.append("fontbakery: not run (not installed or disabled)")
    else:
        fb = report.fontbakery
        lines.append(
            "fontbakery: "
            + ", ".join(
                f"{k}={fb.get(k, 0)}"
                for k in ("FAIL", "WARN", "ERROR", "PASS", "INFO", "SKIP")
            )
        )
    return "\n".join(lines) + "\n"

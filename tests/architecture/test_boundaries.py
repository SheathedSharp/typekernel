"""Architecture boundary guards (ARCHITECTURE.md §9.8).

Scan new-kernel packages with ``ast`` only — no extra dependencies.
When the packages are empty (pre-M1), every rule still passes.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "typekernel"

# M4 exit: rule 1 covers the whole package tree (no typekernel.parts anywhere).
# Rules 2–4 still scope to the new-kernel packages below.
KERNEL_PACKAGES = ("draw", "system", "project", "cli", "plugins")
KERNEL_TEST_DIRS = ("draw", "system", "project")

LETTER_FN = re.compile(
    r"^(build_[A-Za-z]|[A-Za-z]_|[a-z]+_from_[A-Za-z]|\w+_yoke)$"
)
FORBIDDEN_TOKENS = ("style.serif", "italic_slant_deg", "vf_compat")
# Single-letter glyph names or uniXXXX in string literals (rule 5).
GLYPH_NAME_STR = re.compile(r"^(?:[A-Za-z]|uni[0-9A-Fa-f]{4})$")


def _py_files(base: Path) -> list[Path]:
    if not base.is_dir():
        return []
    return sorted(p for p in base.rglob("*.py") if p.is_file())


def _kernel_roots() -> list[Path]:
    return [SRC / name for name in KERNEL_PACKAGES]


def _parse(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _module_parts_under_plugins(path: Path) -> tuple[str, ...] | None:
    """Return (plugin_family, ...) for a file under src/typekernel/plugins/."""
    try:
        rel = path.relative_to(SRC / "plugins")
    except ValueError:
        return None
    parts = rel.parts
    if not parts:
        return None
    # plugins/<family>/...
    if parts[0].endswith(".py"):
        return ()
    return (parts[0],)


def _imported_names(node: ast.AST) -> list[str]:
    names: list[str] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            names.append(alias.name)
    elif isinstance(node, ast.ImportFrom):
        mod = node.module or ""
        if node.level:
            # relative: reconstruct enough for private / cross-plugin checks
            names.append(("." * node.level) + mod)
        else:
            names.append(mod)
        for alias in node.names:
            if alias.name != "*":
                names.append(f"{mod}.{alias.name}" if mod else alias.name)
    return names


@pytest.fixture(scope="module")
def kernel_files() -> list[Path]:
    files: list[Path] = []
    for root in _kernel_roots():
        files.extend(_py_files(root))
    return files


@pytest.fixture(scope="module")
def all_src_files() -> list[Path]:
    return _py_files(SRC)


def test_no_parts_import_anywhere(all_src_files: list[Path]) -> None:
    """Rule 1 (M4): no ``typekernel.parts`` imports anywhere under src/typekernel."""
    violations: list[str] = []
    for path in all_src_files:
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "typekernel.parts" or alias.name.startswith(
                        "typekernel.parts."
                    ):
                        violations.append(f"{_rel(path)}:{node.lineno}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod == "typekernel.parts" or mod.startswith("typekernel.parts."):
                    violations.append(f"{_rel(path)}:{node.lineno}: from {mod}")
                # from typekernel import parts
                if mod == "typekernel":
                    for alias in node.names:
                        if alias.name == "parts":
                            violations.append(
                                f"{_rel(path)}:{node.lineno}: from typekernel import parts"
                            )
    assert not violations, "forbidden parts imports:\n" + "\n".join(violations)


def test_no_letter_named_functions(kernel_files: list[Path]) -> None:
    """Rule 2: no letter-builder / yoke style function names in new packages."""
    violations: list[str] = []
    for path in kernel_files:
        tree = _parse(path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if LETTER_FN.match(node.name):
                    violations.append(f"{_rel(path)}:{node.lineno}: def {node.name}")
            elif isinstance(node, ast.ClassDef):
                # class names are free; only function names are constrained
                pass
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and LETTER_FN.match(target.id)
                        and isinstance(node.value, (ast.Lambda, ast.Call))
                    ):
                        violations.append(
                            f"{_rel(path)}:{node.lineno}: {target.id} = ..."
                        )
    assert not violations, "letter-named functions:\n" + "\n".join(violations)


def test_no_style_branch_tokens(kernel_files: list[Path]) -> None:
    """Rule 3: no style.serif / italic_slant_deg / vf_compat in new-package source."""
    violations: list[str] = []
    for path in kernel_files:
        src = path.read_text(encoding="utf-8")
        # Skip this file's own documentation of the forbidden tokens.
        for token in FORBIDDEN_TOKENS:
            # line-based so docstrings explaining the rule can quote them carefully;
            # still forbid real usage. Allow only inside this architecture test.
            for i, line in enumerate(src.splitlines(), start=1):
                if token in line:
                    violations.append(f"{_rel(path)}:{i}: contains {token!r}")
    assert not violations, "style-branch tokens:\n" + "\n".join(violations)


def test_plugin_isolation_and_no_private_imports(kernel_files: list[Path]) -> None:
    """Rule 4: no cross-plugin imports; no importing other modules' _privates."""
    violations: list[str] = []
    for path in kernel_files:
        family = _module_parts_under_plugins(path)
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if name.startswith("typekernel.plugins."):
                        rest = name[len("typekernel.plugins.") :].split(".")
                        if family and rest and rest[0] != family[0]:
                            violations.append(
                                f"{_rel(path)}:{node.lineno}: cross-plugin import {name}"
                            )
                    _check_private_import(path, node.lineno, name, violations)
            else:
                mod = node.module or ""
                # absolute
                if mod.startswith("typekernel.plugins."):
                    rest = mod[len("typekernel.plugins.") :].split(".")
                    if family and rest and rest[0] != family[0]:
                        violations.append(
                            f"{_rel(path)}:{node.lineno}: cross-plugin from {mod}"
                        )
                # relative from plugins/<fam>/file into sibling family
                # climbing out of family into another plugins/<y>
                # e.g. from ..corners import x while in ends/
                if family and node.level >= 2 and mod:
                    top = mod.split(".", 1)[0]
                    known = (
                        {p.name for p in (SRC / "plugins").iterdir() if p.is_dir()}
                        if (SRC / "plugins").is_dir()
                        else set()
                    )
                    if top in known and top != family[0]:
                        violations.append(
                            f"{_rel(path)}:{node.lineno}: relative cross-plugin from {'.' * node.level}{mod}"
                        )
                full = (("." * node.level) + mod) if node.level else mod
                _check_private_import(path, node.lineno, full, violations)
                for alias in node.names:
                    if alias.name.startswith("_") and alias.name != "__future__":
                        # importing a private name from another module
                        if mod and not mod.startswith("."):
                            violations.append(
                                f"{_rel(path)}:{node.lineno}: private import {mod}.{alias.name}"
                            )
                        elif node.level and mod != "":
                            # relative import of private from another file/package
                            violations.append(
                                f"{_rel(path)}:{node.lineno}: private relative import {alias.name} from {full}"
                            )
                        elif node.level == 0 and not mod:
                            # from ._foo import bar already covered via full; bare from x import _y
                            pass
                        else:
                            # from .sibling import _private
                            if node.level >= 1:
                                violations.append(
                                    f"{_rel(path)}:{node.lineno}: private relative import {alias.name}"
                                )
    assert not violations, "plugin / private import violations:\n" + "\n".join(violations)


def _check_private_import(
    path: Path, lineno: int, dotted: str, violations: list[str]
) -> None:
    """Flag imports whose module path contains a private segment (other than dunders)."""
    # Skip relative-only dots
    clean = dotted.lstrip(".")
    if not clean:
        return
    parts = clean.split(".")
    for part in parts:
        if part.startswith("_") and not (part.startswith("__") and part.endswith("__")):
            violations.append(f"{_rel(path)}:{lineno}: private module path {dotted}")
            return


def test_kernel_tests_avoid_letter_glyph_names() -> None:
    """Rule 5: tests/draw|system|project must not hardcode letter glyph names."""
    violations: list[str] = []
    for name in KERNEL_TEST_DIRS:
        base = ROOT / "tests" / name
        for path in _py_files(base):
            tree = _parse(path)
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Constant)
                    and isinstance(node.value, str)
                    and GLYPH_NAME_STR.match(node.value)
                ):
                    violations.append(
                        f"{_rel(path)}:{getattr(node, 'lineno', '?')}: "
                        f"glyph name string {node.value!r}"
                    )
    assert not violations, "letter glyph strings in kernel tests:\n" + "\n".join(
        violations
    )


def test_guards_are_runnable_when_packages_empty() -> None:
    """M0 exit: guards pass even before draw/system/project/cli/plugins exist."""
    # Smoke: collecting files does not raise; emptiness is fine.
    files = []
    for root in _kernel_roots():
        files.extend(_py_files(root))
    assert isinstance(files, list)

#!/usr/bin/env python3
"""Tiny smoke: skill files exist and name Usage A + yokes. Not full agent validation."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/typekernel-font-design"


def main() -> int:
    required = (
        SKILL / "SKILL.md",
        SKILL / "parts-catalog.md",
        SKILL / "recipes.md",
        SKILL / "anti-patterns.md",
        SKILL / "reference.md",
        ROOT / "docs/AGENT_GOAL.md",
    )
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        print("MISSING", *missing, sep="\n")
        return 1
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    catalog = (SKILL / "parts-catalog.md").read_text(encoding="utf-8")
    anti = (SKILL / "anti-patterns.md").read_text(encoding="utf-8")
    goal = (ROOT / "docs/AGENT_GOAL.md").read_text(encoding="utf-8")
    checks = {
        "SKILL Usage A": "Usage A" in skill,
        "SKILL yokes": "n_yoke" in skill and "bowl_stem_yoke" in skill,
        "SKILL ≥2 recipes": "Recipe 1" in skill and "Recipe 2" in skill,
        "catalog yoke params": "vf_compat_stem" in catalog and "branch_y" in catalog,
        "catalog italic_strokes": "emit_italic_entry_kick" in catalog,
        "catalog soft_union": "soft_union" in catalog,
        "anti kit-of-parts": "Kit-of-parts when a yoke exists" in anti,
        "anti Controls": "Controls" in anti,
        "goal yokes": "yoke" in goal.lower() or "yokes" in goal,
        "no Controls resurrection in SKILL happy path": "Controls.build_all" not in skill
        or "deleted" in skill.lower(),
    }
    failed = [k for k, ok in checks.items() if not ok]
    for k, ok in checks.items():
        print(("OK" if ok else "FAIL"), k)
    if failed:
        return 1
    print("smoke_skill_usage_a: ok (not full agent validation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

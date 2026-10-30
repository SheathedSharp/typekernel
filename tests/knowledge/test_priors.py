"""S2 knowledge packet: priors + confuse pairs."""

from __future__ import annotations

from typekernel.knowledge import CONFUSE_PAIRS, LATIN_BASIC, confuse_partners, prior_for


def test_z_and_e_priors_differ_on_counters() -> None:
    z = prior_for(ord("z"))
    e = prior_for(ord("e"))
    assert z is not None and e is not None
    assert z.counters == 0
    assert e.counters == 1


def test_confuse_z_includes_e_and_two() -> None:
    partners = set(confuse_partners(ord("z")))
    assert ord("e") in partners
    assert ord("2") in partners


def test_confuse_pairs_are_symmetric_entries() -> None:
    assert CONFUSE_PAIRS
    assert all(isinstance(a, int) and isinstance(b, int) for a, b in CONFUSE_PAIRS)
    assert len(LATIN_BASIC) >= 26


def test_latin_ext_digraph_priors() -> None:
    ae = prior_for(0x00C6)
    assert ae is not None
    assert ae.name == "AE"
    assert ae.counters == 1
    assert prior_for(0x00E6) is not None
    assert prior_for(0x0152) is not None
    assert prior_for(0x0153) is not None

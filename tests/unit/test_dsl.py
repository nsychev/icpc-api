"""The ``q=`` grammar."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from icpc.errors import InvalidFilterValue
from icpc.models.enums import TeamStatus
from icpc.search import contest_teams
from icpc.search.dsl import FORBIDDEN_IN_VALUE, Filter, Q, SortKey


def test_projection_only():
    assert Q.build(["id", "name"]).render() == "proj:id,name;"


def test_empty_projection_is_legal():
    # The public standings endpoint sends exactly this and gets default columns.
    assert Q().render() == "proj:;"


def test_filters_join_with_ampersand():
    q = Q.build(["id"], [Filter("status", "ACCEPTED"), Filter("country", "Kazakhstan")])
    assert q.render() == "proj:id;filter:status#ACCEPTED&country#Kazakhstan;"


def test_filters_join_with_pipe_in_or_mode():
    q = Q.build(["id"], [Filter("a", "1"), Filter("b", "2")], mode="or")
    assert q.render() == "proj:id;filter:a#1|b#2;"


def test_sort_is_multi_key_and_space_separated():
    q = Q.build(["id"], sort=[SortKey("name", "asc"), SortKey("rank", "desc")])
    assert q.render() == "proj:id;sort:name asc,rank desc;"


@pytest.mark.parametrize("bad", sorted(FORBIDDEN_IN_VALUE))
def test_separator_in_a_value_is_refused(bad: str):
    # The grammar has no escape sequence, so such a value would corrupt the query.
    with pytest.raises(InvalidFilterValue):
        Filter.of("name", f"Team{bad}One")


def test_booleans_render_lowercase():
    assert Filter.of("paid", value=True).render() == "paid#true"


def test_enum_values_render_as_their_wire_form():
    assert Filter.of("status", TeamStatus.CANCELED).render() == "status#CANCELED"


def test_field_descriptors_build_filters_and_sort_keys():
    f = contest_teams(9180).fields
    assert f.status.eq(TeamStatus.ACCEPTED) == Filter("status", "ACCEPTED")
    assert f.name.desc() == SortKey("name", "desc")
    assert f.inst_short_name.name == "instShortName"


@given(
    st.lists(st.sampled_from(["id", "name", "status", "rank"]), min_size=1, max_size=4),
    st.text(alphabet=st.characters(blacklist_characters="#&|;,"), min_size=1, max_size=20),
)
def test_rendered_query_has_exactly_three_clause_terminators(proj: list[str], value: str):
    q = Q.build(proj, [Filter.of("name", value)], [SortKey("id", "asc")])
    rendered = q.render()
    assert rendered.count(";") == 3
    assert rendered.startswith("proj:")
    # The filter value is interpolated raw, so it must not have introduced a clause.
    assert rendered.count("filter:") == 1

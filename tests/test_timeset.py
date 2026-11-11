"""Classic timeset arguments: no mixing days and weeks, and week-only parameters reject dates."""

from __future__ import annotations

from datetime import date

import pytest
from epiweeks import Week

from epidatpy import EpiDataContext, EpiRange, InvalidArgumentException
from epidatpy._parse import check_timeset

pytestmark = pytest.mark.filterwarnings("ignore:.*uses the V4 Epidata API")


@pytest.mark.parametrize(
    "value",
    ["*", 202001, "202001", [202001, 202002], Week(2020, 1), EpiRange(202001, 202005), "202001-202005", None]
    + [
        date(2020, 1, 1),
        20200101,
        "2020-01-01",
        [20200101, 20200102],
        EpiRange(20200101, 20200201),
        "20200101,20200102",
    ],
)
def test_uniform_timesets_pass(value: object) -> None:
    check_timeset("x", value)


@pytest.mark.parametrize(
    "value",
    [[202001, 20200101], "202001,20200101", [Week(2020, 1), date(2020, 1, 1)], [EpiRange(202001, 202002), 20200101]],
)
def test_mixed_timesets_raise(value: object) -> None:
    with pytest.raises(InvalidArgumentException, match="mixes day"):
        check_timeset("x", value)


def test_expected_granularity() -> None:
    check_timeset("x", 202001, "week")
    check_timeset("x", "*", "week")
    with pytest.raises(InvalidArgumentException, match="`x` expects week values \\(YYYYWW\\) but got day"):
        check_timeset("x", date(2020, 1, 1), "week")
    with pytest.raises(InvalidArgumentException, match="expects day values"):
        check_timeset("x", Week(2020, 1), "day")


def test_week_only_endpoint_parameters_reject_dates() -> None:
    ctx = EpiDataContext(use_cache=False)
    with pytest.raises(InvalidArgumentException, match="`issues` expects week"):
        ctx.pub_flusurv("network_all", [202001], issues=date(2020, 1, 1))
    with pytest.raises(InvalidArgumentException, match="`epiweeks` expects week"):
        ctx.pub_fluview("nat", EpiRange(20200101, 20200201))
    with pytest.raises(InvalidArgumentException, match="mixes day"):
        ctx.pub_fluview("nat", [202001, 20200101])
    # Wildcards and weeks are fine.
    ctx.pub_fluview("nat", "*")
    ctx.pub_fluview("nat", EpiRange(202001, 202005), issues=202006)


def test_wiki_and_twitter_time_values_must_match_time_type() -> None:
    ctx = EpiDataContext(use_cache=False)
    with pytest.raises(InvalidArgumentException, match="`time_values` expects day"):
        ctx.pub_wiki("x", time_type="day", time_values=[202001])
    with pytest.raises(InvalidArgumentException, match="`time_values` expects week"):
        ctx.pvt_twitter("k", "CA", time_type="week", time_values=date(2020, 1, 1))
    ctx.pub_wiki("x", time_type="week", time_values=[202001])

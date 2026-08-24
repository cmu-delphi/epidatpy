from collections.abc import Callable

import pytest

from epidatpy import EpiDataContext

MakeCall = Callable[[EpiDataContext], object]

V4_CALLS = [
    lambda ctx: ctx.pub_covidcast(data_source="src", signals="sig", geo_type="state", time_type="day"),
    lambda ctx: ctx.pub_covidcast_meta(),
    lambda ctx: ctx.pub_fluview(regions="nat"),
    lambda ctx: ctx.pub_flusurv(locations="nat"),
    lambda ctx: ctx.pvt_quidel(auth="key", locations="nat"),
]

V5_CALLS = [
    lambda ctx: ctx.epidata_snapshot(source="src", signals="sig", geo_type="state"),
    lambda ctx: ctx.epidata_archive(source="src", signals="sig", geo_type="state"),
]


@pytest.mark.parametrize("make_call", V4_CALLS)
def test_v4_endpoint_warns(make_call: MakeCall) -> None:
    ctx = EpiDataContext()
    with pytest.warns(UserWarning, match="V4 Epidata API"):
        make_call(ctx)


@pytest.mark.parametrize("make_call", V5_CALLS)
def test_v5_endpoint_does_not_warn(make_call: MakeCall, recwarn: pytest.WarningsRecorder) -> None:
    ctx = EpiDataContext()
    make_call(ctx)
    assert not any("V4 Epidata API" in str(w.message) for w in recwarn.list)

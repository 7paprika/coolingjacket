import pytest

from core.fluid import get_service_fluid_props


def test_get_service_fluid_props_interpolates_custom_values():
    props = get_service_fluid_props(
        "Custom",
        60.0,
        {
            "t1": 20.0,
            "t2": 100.0,
            "rho1": 1000.0,
            "rho2": 900.0,
            "cp1": 4000.0,
            "cp2": 4200.0,
            "mu1": 2.0,
            "mu2": 1.0,
            "k1": 0.5,
            "k2": 0.7,
        },
    )

    assert props["rho"] == pytest.approx(950.0)
    assert props["cp"] == pytest.approx(4100.0)
    assert props["mu"] == pytest.approx(0.0015)
    assert props["k"] == pytest.approx(0.6)

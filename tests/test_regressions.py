# tests/test_regressions.py
import contextlib
import io
import os

import numpy as np
import pytest

import pyAMARES
from pyAMARES.kernel.fid import simulate_fid

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PK = os.path.join(CURRENT_DIR, "singlet.csv")
MHZ, SW = 120.0, 1250.0
# At sw=1250 Hz, np.arange(0, dwelltime * 242, dwelltime) returns 243 points
FID_LEN = 242


def quiet(func, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()):
        return func(*args, **kwargs)


def make_fid(params=None):
    if params is None:
        params = quiet(
            pyAMARES.initialize_FID, fid=None, priorknowledgefile=PK, MHz=MHZ, sw=SW
        ).initialParams
    np.random.seed(0)
    return simulate_fid(
        params, MHz=MHZ, sw=SW, fid_len=FID_LEN, snr_target=50, pts_noise=50
    )


def init(fid, **kwargs):
    return quiet(
        pyAMARES.initialize_FID,
        fid=fid,
        priorknowledgefile=PK,
        MHz=MHZ,
        sw=SW,
        deadtime=0.0,
        **kwargs,
    )


def fit(fid_parameters, params=None, **kwargs):
    params = fid_parameters.initialParams if params is None else params
    return quiet(
        pyAMARES.fitAMARES,
        fid_parameters,
        params,
        ifplot=False,
        inplace=False,
        **kwargs,
    )


@pytest.fixture(scope="module")
def fid():
    return make_fid()


def test_timeaxis_length_matches_fid(fid):
    """Time axes had fid_len + 1 points for some lengths, e.g. 242 at sw=1250 Hz."""
    assert fid.shape == (FID_LEN,)
    fid_parameters = init(np.concatenate([np.zeros(8), fid]), truncate_initial_points=8)
    assert fid_parameters.timeaxis.shape == fid_parameters.fid.shape == (FID_LEN,)


def test_numeric_noise_var(fid):
    """A float noise_var crashed evaluateCRB; it must match the equivalent string."""
    crlb_float = fit(init(fid, noise_var=2.5)).crlb
    crlb_str = fit(init(fid, noise_var="2.5")).crlb
    np.testing.assert_allclose(crlb_float, crlb_str)


def test_fit_range_with_default_objective(fid):
    """fit_range with the default objective raised a TypeError."""
    fid_parameters = init(fid)
    result = fit(fid_parameters, fit_range=(7, -5))
    expected = fit(
        fid_parameters, fit_range=(7, -5), objective_func=pyAMARES.objective_range
    )
    np.testing.assert_allclose(
        result.result_multiplets["amplitude"], expected.result_multiplets["amplitude"]
    )


def test_filter_param_by_ppm_exact_names():
    """Keeping peak '7' also kept '27' because peaks were matched by name suffix."""
    from lmfit import Parameters

    params = Parameters()
    for name, freq in (("7", 100.0), ("27", -500.0)):
        for prefix, value in (("ak", 1.0), ("freq", freq), ("dk", 10.0), ("phi", 0.0)):
            params.add(f"{prefix}_{name}", value=value)
    kept = pyAMARES.filter_param_by_ppm(params, fit_ppm=(0, 1), MHz=MHZ, delta=0)
    assert sorted(kept) == ["ak_7", "dk_7", "freq_7", "phi_7"]


def test_snr_uses_numeric_noise_var(fid):
    """With a numeric noise_var, SNR = amplitude / sqrt(2 * noise_var)."""
    result = fit(init(fid, noise_var=2.5)).result_multiplets
    np.testing.assert_allclose(result["SNR"], result["amplitude"] / np.sqrt(5.0))


def test_phase_wrapped_into_own_bounds():
    """A wide phase bound on one peak changed the reported phase of the other."""
    fid_parameters = init(None)
    params = fid_parameters.initialParams
    params["phi_Peak_A"].value = np.deg2rad(-69)
    params["phi_Peak_B"].set(min=-2 * np.pi, max=2 * np.pi)
    fid_parameters = init(make_fid(params))
    result = fit(fid_parameters, params=params).result_multiplets
    assert -180 <= result.loc["Peak_A", "phase(deg)"] < 0

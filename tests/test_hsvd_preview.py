# tests/test_hsvd_preview.py
import contextlib
import io
import os

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

import pyAMARES  # noqa: E402

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="module")
def fid_parameters():
    fid = pyAMARES.readmrs(os.path.join(CURRENT_DIR, "fid.txt"))
    with contextlib.redirect_stdout(io.StringIO()):
        return pyAMARES.initialize_FID(
            fid=fid,
            priorknowledgefile=os.path.join(
                CURRENT_DIR, "example_human_brain_31P_7T.csv"
            ),
            MHz=120.0,
            sw=10000,
            deadtime=300e-6,
            preview=False,
            normalize_fid=False,
        )


@pytest.mark.parametrize("use_prior_knowledge", [True, False])
def test_hsvd_preview_with_filtered_components(fid_parameters, use_prior_knowledge):
    """preview=True must not fail when components broader than lw_threshold are dropped.

    With lw_threshold=150 Hz, HSVD component 9 (~174 Hz) of the 12 is dropped while
    component 11 is kept, which used to raise an IndexError in preview_HSVD.
    """
    fitting_parameters = fid_parameters.initialParams if use_prior_knowledge else None
    kwargs = dict(
        fid_parameters=fid_parameters,
        fitting_parameters=fitting_parameters,
        num_of_component=12,
        lw_threshold=150,
    )
    with contextlib.redirect_stdout(io.StringIO()):
        params_ref = pyAMARES.HSVDinitializer(preview=False, **kwargs)
        params_preview = pyAMARES.HSVDinitializer(preview=True, **kwargs)
    plt.close("all")

    if not use_prior_knowledge:
        # Peak names follow the HSVD component numbers, so the dropped one is missing
        names = {name.split("_", 1)[1] for name in params_ref}
        assert "10" not in names and "12" in names
    assert list(params_preview) == list(params_ref)
    for name in params_ref:
        assert params_preview[name].value == pytest.approx(params_ref[name].value)

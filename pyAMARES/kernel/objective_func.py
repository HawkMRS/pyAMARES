import numpy as np
import nmrglue as ng
from .fid import interleavefid, uninterleave, multieq6


def default_objective(params, x, fid):
    fittedspec = multieq6(params, x)
    residual = interleavefid(fid) - fittedspec
    return residual


def objective_range(params, x, fid, fit_range=None):
    fittedspec = multieq6(params, x)
    residual = interleavefid(fid) - fittedspec
    if fit_range is None:
        return residual
    else:
        residual = ng.proc_base.fft(uninterleave(residual))
    return interleavefid(residual[fit_range[0] : fit_range[1]])


def objective(params, x, fid):
    fittedspec = uninterleave(multieq6(params, x))
    residual = np.real((fid.astype("complex64") - fittedspec.astype("complex64")) ** 2)
    return residual


def objective3(params, x, fid):
    fittedspec = multieq6(params, x)
    residual = interleavefid(fid) - fittedspec
    return residual**2

import re
import warnings
import numpy as np
import scipy
import matplotlib.pyplot as plt
import sympy
from sympy.parsing import sympy_parser

from .report import report_crlb
from ..kernel import uninterleave, multieq6, Jac6


def calculateCRB(D, variance, P=None, verbose=False, condthreshold=1e11, cond=False):
    """
    Calculates the Cramer-Rao Bound (CRB) for parameter estimation error.

    This function computes the CRB based on the provided Jacobian matrix (D),
    the noise variance, and optionally prior knowledge represented by matrix P.

    Args:
        D (numpy.ndarray): Jacobian matrix.
        variance (float): The variance of the noise in the measurements.
        P (numpy.ndarray, optional): Prior knowledge matrix. Assumes identity if None. Defaults to None.
        verbose (bool, optional): If True, prints detailed information about the computation. Defaults to False.
        condthreshold (float, optional): Condition number threshold to identify ill-conditioned matrices. Defaults to 1e11.
        cond (bool, optional): If True, also returns a boolean indicating if the Fisher information matrix is ill-conditioned.

    Returns:
        numpy.ndarray or boolean: The square root of the diagonal elements of the CRB covariance matrix, indicating the lower bound on the standard deviation of the parameter estimates.
          If ``cond`` is True, a boolean indicating if the Fisher information matrix is ill-conditioned.

    References:
        1. S Cavassila et al NMR Biomed. 2001 Jun;14(4):278-83.
        2. Purvis et al, OXSA: An open-source magnetic resonance spectroscopy analysis toolbox in MATLAB. PLoS ONE 12(9): e0185356.
    """
    D = uninterleave(D)
    Dmat = np.dot(D.conj().T, D)
    if verbose:
        print("D.shape", D.shape, "Dmat.shape", Dmat.shape)
        # print(f"{P.shape=}")
        print("P.shape=%s" % str(P.shape))
    # Compute the Fisher information matrix
    if P is None:  # No prior knowledge
        Fisher = np.real(Dmat) / variance
        P = np.identity(Dmat.shape[0])
    else:
        Fisher = np.real(P.T @ Dmat @ P) / variance
    if verbose:
        # print(f"{Fisher.shape=} {P.shape=}")
        print("Fisher.shape=%s P.shape=%s" % (Fisher.shape, P.shape))
    condition_number = np.linalg.cond(Fisher)
    if condition_number > condthreshold:
        # print("Warning: The matrix may be ill-conditioned. Condition number is high:", condition_number)
        warnings.warn(
            "Warning: The matrix may be ill-conditioned. Condition number is high: %3.3e"
            % condition_number,
            RuntimeWarning,
        )
        CRBcov = P @ scipy.linalg.pinv(Fisher) @ P.T
    else:
        # Solve the least squares problem if well-conditioned
        x, residuals, rank, s = np.linalg.lstsq(Fisher, P.T, rcond=None)
        CRBcov = P @ x

    # Ensure non-negative covariance values
    if np.min(CRBcov) < 0:
        if verbose:
            print("np.min(CRBcov)=%s, make the negative values to 0!" % np.min(CRBcov))
        # warnings.warn("np.min(CRBcov)=%s, make the negative values to 0!" % np.min(CRBcov), UserWarning)
        CRBcov[CRBcov < 0] = 0.0

    if cond:
        if np.linalg.cond(Fisher) > condthreshold:
            return True
        else:
            return False
    if np.max(np.diag(CRBcov)) < 1e-5:
        # print("Ill conditioned matrix! CRLB not reliable!")
        warnings.warn("Ill conditioned matrix! CRLB not reliable!", RuntimeWarning)
    if verbose:
        print("CRBcov.shape", CRBcov.shape)
        print("max CRBcov", np.max(np.diag(CRBcov)))
        print("max Fisher %2.2e" % np.max(Fisher))
        print("max mDTD %2.2e" % np.max(Dmat))
    return np.sqrt(np.diag(CRBcov))


def evaluateCRB(outparams, opts, P=None, Jacfunc=Jac6, verbose=False):
    """
    Evaluates the Cramer-Rao Bound (CRB) for lmfit fitting results,
    fitting parameters, and an optional prior knowledge matrix.

    This function uses a specified Jacobian function to compute the Jacobian
    matrix, calculates the residuals between model predictions and actual data,
    computes the variance of these residuals, and then calculates the CRB
    based on this information.

    Args:
        outparams: Output parameters from the lmfit fitting results.
        opts (argspace.Namespace): An object containing options and data for the CRB calculation, including:
            timeaxis (numpy.ndarray): The time axis for the data.
            fid (numpy.ndarray): The FID signal.
        P (numpy.ndarray, optional): Prior knowledge matrix. Assumes identity if None. Defaults to None.
        Jacfunc (function, optional): The function used to compute the Jacobian matrix. Defaults to ``Jac6``.
        verbose (bool, optional): If True, displays additional information about the process, including a plot of the residuals.

    Returns:
        numpy.ndarray: The Cramer-Rao Bound (CRB) values calculated for the given parameters.
        Note: ``opts`` will be modified in place.
    """
    opts.D = Jacfunc(outparams, opts.timeaxis)
    opts.residual = uninterleave(multieq6(outparams, opts.timeaxis)) - opts.fid
    if opts.noise_var.startswith("OXSA"):
        print("Estimated CRLBs are calculated using the default noise variance estimation used by OXSA.")
        opts.variance = np.var(
            opts.residual.real
        )  # OXSA style, the "noise as SD in TD from TD residue" option selected in the Result Window of jMRUI V7. 
    elif opts.noise_var.lower().startswith("jmrui"):
        print("Estimated CRLBs are calculated using the default noise variance estimation used by jMRUI.")
        opts.variance = np.var(
            opts.fid[-len(opts.fid)//10 :].real
        )  # jMRUI style, "noise as SD in TD from TD FID tall option selected in the Result Window of jMRUI V7" (I hard-coded last 10% points)
    else:
        try:
            opts.variance = float(opts.noise_var)
            print("The CRLB estimation will be divided by the input variance %s" % opts.variance)
        except ValueError:
            print("Error: noise_var %s is not a recognized string or a valid number." % opts.variance)

    if verbose:
        print("opts.D.shape=%s" % str(opts.D.shape))
        plt.plot(opts.residual.real)
        plt.title("residual")
        plt.show()
    opts.crlb = calculateCRB(opts.D, opts.variance, P=P, verbose=verbose)
    opts.resultpd = report_crlb(outparams=outparams, crlb=opts.crlb, Jacfunc=Jacfunc)
    return opts.crlb


def extract_strings(input_str):
    if input_str is None:
        return input_str
    if not re.search("[a-zA-Z]", input_str):
        return input_str
    # return re.sub(r'\d+(?:\.\d+)?|\+|\-|\*|/', '', input_str)
    # Regular expression to match floating-point numbers or integers not surrounded by letters
    # and mathematical operators
    pattern = r"(?<!\w)\d+\.\d+|(?<!\w)\d+(?!\w)|(?<!\w)\d+\b|\b\d+(?!\w)|[+\-*/]"
    return re.sub(pattern, "", input_str)


def get_matches(df, string_list):
    indexes = []
    for match in string_list:
        index = df.index[df["name"] == match]
        indexes.append(index.values[0])
    return indexes


def create_pmatrix(pkpd, verbose=False, ifplot=False):
    """
    Creates a prior knowledge matrix (P-matrix) from a prior knowledge dataframe.

    The P-matrix represents the relationships and constraints between parameters
    based on prior knowledge, calculated according to Reference: S Cavassila et al., NMR Biomed. 2001 Jun;14(4):278-83.

    Args:
        pkpd (pandas.DataFrame): Prior knowledge dataframe with the ``expr`` column.
        verbose (bool): Flag to enable verbose output for debugging.
        ifplot (bool): Flag to enable plotting of the P-matrix.

    Returns:
        numpy.ndarray: Transposed P-matrix representing the relationships between parameters.
    """
    # Extract parameter indices and expressions for Equation 3 in the
    # Reference. S Cavassila et al NMR Biomed. 2001 Jun;14(4):278-83
    # print(f"{[extract_strings(x) for x in pkpd.dropna(axis=0)['expr']]=}")
    # print(f"{pkpd.columns=} {pkpd.index=} {pkpd['name']=}")
    pm_index = get_matches(
        pkpd, [extract_strings(x) for x in pkpd.dropna(axis=0)["expr"]]
    )
    pl_index = pkpd.dropna(axis=0).index.values

    # Calculate partial derivatives of expressions using sympy. May simply use string operation in the future.
    plm = [
        sympy.diff(sympy_parser.parse_expr(expr)).evalf()
        for expr in pkpd[pkpd.expr.notna()]["expr"]
    ]
    Pmatrix = np.zeros((len(pkpd[pkpd["vary"]]), len(pkpd)))  # all vs free parameters
    freepd = pkpd[pkpd["vary"]].copy()  # Create a copy to avoid SettingWithCopyWarning
    freepd["newid"] = np.arange(len(freepd))
    pkpd2 = pkpd.copy()
    pkpd2["newid"] = freepd[
        "newid"
    ]  # pass freepd ID to all ID. ID will be NaNs for fixed variables
    pm_index2 = pkpd2.iloc[pm_index]["newid"].to_list()
    if np.all(np.isnan(pm_index2)):  # If all NaN
        # print(f"{pm_index2=}")
        warnings.warn(
            "Warning: pm_index are all NaNs, return None so that P matrix is a identity matrix!",
            RuntimeWarning,
        )
        return None
    pm_index = [int(x) for x in pm_index2]
    # Fill the diagonal for free parameters
    for ind in freepd.index:
        if verbose:
            # print(f"{ind=} {freepd.loc[ind]['newid']=}")
            print("ind=%s newid=%s" % (ind, freepd.loc[ind]["newid"]))
        Pmatrix[freepd.loc[ind]["newid"], ind] = 1.0

    # Fill in partial derivatives for parameter relationships
    for x, y, partial_d in zip(pl_index, pm_index, plm):
        if verbose:
            # print(f"{x=} {y=} {partial_d=}")
            print("x=%s y=%s partial_d=%s" % (x, y, partial_d))

        Pmatrix[y, x] = partial_d
    if ifplot:
        plt.title("Prior Knowledge Matrix")
        plt.imshow(Pmatrix, aspect="auto")
        plt.ylabel("Free parameters")
        plt.xlabel("All parameters")

    return Pmatrix.T

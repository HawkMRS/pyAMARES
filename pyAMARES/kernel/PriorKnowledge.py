import re
from copy import deepcopy

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse

from lmfit import Parameters
from .fid import fft_params

def refindall(expr):
    # Work in the same way as matches = re.findall(r"(\d+)(Hz|ppm)", expr) but support decimals  
    expr = expr.replace(' ','')
    pattern = re.compile(r"([-+]?\d+(\.\d+)?)(Hz|ppm)?")
    match = pattern.search(expr)
    if match:
        number = match.group(1)
        unit = match.group(3) if match.group(3) else ""
        return [(number, unit)]
    return [("", "")] 

def evaluate_expression_with_units(expr, row, MHz):
    """
    Evaluate an expression containing numeric values with ``Hz`` or ``ppm`` units,
    with consideration for data in a given row and a specified MHz value for conversion.

    Args:
        expr (str): The expression to be evaluated, which may contain numeric values with ``Hz`` or ``ppm`` units.
        row (pandas.Series): A Series or similar structure containing data referenced in ``expr``.
        MHz (float, optional): Field strength in MHz. Defaults to 120.0.

    Returns:
        The result of evaluating the modified expression, or the original expression if evaluation fails.
    """
    # Find all parts of the expression that match a pattern like '15Hz' or '15ppm'
    expr = expr.replace(" ", "") # 2024/06/23 Remove spaces in such as 15 ppm
    # matches = re.findall(r"(\d+)(Hz|ppm)", expr)  #2025-03-15: This one does not handle float numbers
    matches = re.findall(r"(\d+(?:\.\d+)?)(Hz|ppm)", expr)
    # matches = refindall(expr)
    for match in matches:
        number, unit = match
        if unit == "ppm":
            # Remove 'ppm' from the expression. The chem shift is always ppm, so no change is needed
            expr = expr.replace(unit, "")
        elif unit == "Hz":
            # Replace 'Hz' and convert J-coupling to ppm. Note, the chem shift is always ppm!
            expr = expr.replace(number + unit, f"({number}/{MHz})")

    parts = re.split(r"(\W+)", expr)
    new_expr = expr
    for part in parts:
        if part in row.index:  # If part is a column name
            # Replace the column name with its actual value in the row
            part_value = str(row[part])
            new_expr = new_expr.replace(part, part_value)
    try:
        return eval(new_expr)
    except Exception as e:
        # Return the original expression if evaluation fails
        return expr


def extractini(pk, MHz=120.0):
    """
    Process a subset of a DataFrame, evaluating expressions containing units ('Hz' or 'ppm'),
    and converting values to numeric types where possible.

    Args:
        pk (pandas.DataFrame): The input DataFrame of Prior Knowledge.
        MHz (float, optional): Field strength in MHz. Defaults to 120.0.

    Returns:
        pandas.DataFrame: A DataFrame with evaluated expressions and numeric values.
    """
    df = deepcopy(pk.iloc[1:6])
    for col in df.columns:
        for idx in df.index:
            if isinstance(df.at[idx, col], str) and any(
                c.isalpha() for c in df.at[idx, col]
            ):
                df.at[idx, col] = evaluate_expression_with_units(
                    df.at[idx, col], df.loc[idx], MHz
                )

    df = df.apply(pd.to_numeric, errors="ignore")

    return df


def extract_expr(pk, MHz=120.0):
    """
    Process expressions within a subset of a DataFrame, converting units in strings
    and modifying cell values to include parameter prefixes.

    Args:
        pk (pandas.DataFrame): The input DataFrame of Prior Knowledge.
        MHz (float, optional): Field Strength in MHz used for unit conversion. Defaults to 120.0.

    Returns:
        pandas.DataFrame: A DataFrame with processed expressions and potential parameter prefixes in cell values.
    """
    df = deepcopy(pk.iloc[1:6])

    def process_expression(expr, MHz):
        """
        Convert units in expression strings and remove unit identifiers.

        Returns:
        - The processed expression string or None for non-string inputs.
        """
        if isinstance(expr, str):
            # Find all parts of the expression that match a pattern like '15Hz' or '15ppm'
            expr = expr.replace(" ", "") # 2024/06/23 Remove spaces in such as 15 ppm
            # matches = re.findall(r"(\d+)(Hz|ppm)", expr)
            matches = refindall(expr)
            for match in matches:
                number, unit = match
                if unit == "ppm":
                    # 2024/06/23. This function is used to process in Parameters(), where ppm should be convert to Hz. 
                    # Note this is different from the evaluate_expression_with_units, where chemical shift is ppm and Hz should be converted
                    converted_value = str(float(number) * MHz)  
                    expr = expr.replace(number + unit, converted_value)
                elif unit == "Hz":
                    expr = expr.replace(unit, "")
            return expr
        else:
            return None  # Return None for non-string cells

    def process_df_corrected(df, paramter_prefix=["ak", "freq", "dk", "phi", "g"]):
        """
        Modify cell values in the DataFrame to include parameter prefixes.

        Parameters:
        - df: The DataFrame to be processed.
        - parameter_prefix (list of str): List of parameter prefixes to prepend to cell values.

        Returns:
        - The DataFrame with modified cell values.
        """
        for col in df.columns:
            for i, idx in enumerate(df.index):
                if isinstance(df.at[idx, col], str):
                    df.at[idx, col] = f"{paramter_prefix[i]}_{df.at[idx, col]}"
                elif df.at[idx, col] is None:
                    continue
        return df

    for col in df.columns:
        df[col] = df[col].apply(lambda x: process_expression(x, MHz))

    return process_df_corrected(df)


def unitconverter(df_ini, MHz=120.0):
    """
    Convert units of parameters in a DataFrame based on their physical context.

    This function adjusts 'chemicalshift' values by multiplying with the MHz value,
    'linewidth' values by multiplying with pi, and 'phase' values from degrees to radians.

    Args:
        df_ini (pandas.DataFrame): The input DataFrame containing initial conditions or parameters.
        MHz (float, optional): The field strength in MHz, used for converting 'chemicalshift' values. Defaults to 120.0.

    Returns:
        pandas.DataFrame: A DataFrame with converted unit values in specified rows.
    """
    df = deepcopy(df_ini)
    if "chemicalshift" in df.index:
        df.loc["chemicalshift", df.notna().loc["chemicalshift"]] *= MHz

    if "linewidth" in df.index:
        df.loc["linewidth", df.notna().loc["linewidth"]] *= np.pi

    if "phase" in df.index:
        df.loc["phase", df.notna().loc["phase"]] = np.deg2rad(
            df.loc["phase"][df.notna().loc["phase"]].astype(float)
        )

    return df


def parse_bounds(df):
    """
    Parse bounds from a DataFrame and separate them into two DataFrames for lower and upper bounds.

    This function assumes that bounds are represented as strings in the format '(lower, upper)',
    '(lower,' for lower bounds only, or ',upper)' for upper bounds only. It supports bounds specified
    either as tuples or as individual values.

    Args:
        df (pandas.DataFrame): The input DataFrame containing bounds as string representations.

    Returns:
        df_lb (pandas.DataFrame): A DataFrame containing the parsed lower bounds.
        df_ub (pandas.DataFrame): A DataFrame containing the parsed upper bounds.
    """
    df_bounds = deepcopy(df.iloc[7:])
    df_lb = pd.DataFrame(index=df_bounds.index, columns=df_bounds.columns)
    df_ub = pd.DataFrame(index=df_bounds.index, columns=df_bounds.columns)

    for col in df_bounds.columns:
        for idx in df_bounds.index:
            if (
                isinstance(df_bounds.at[idx, col], str)
                and df_bounds.at[idx, col].startswith("(")
                and df_bounds.at[idx, col].endswith(")")
            ):
                lb, ub = eval(df_bounds.at[idx, col])
                df_lb.at[idx, col] = lb
                df_ub.at[idx, col] = ub
            elif (
                isinstance(df_bounds.at[idx, col], str)
                and df_bounds.at[idx, col].startswith("(")
                and (not df_bounds.at[idx, col].endswith(")"))
            ):
                lb = eval(df_bounds.at[idx, col].replace("(", "").replace(",", ""))
                df_lb.at[idx, col] = lb
                # df_ub.at[idx, col] = df_bounds.at[idx, col]
                df_ub.at[idx, col] = np.nan
            elif (
                isinstance(df_bounds.at[idx, col], str)
                and (not df_bounds.at[idx, col].startswith("("))
                and df_bounds.at[idx, col].endswith(")")
            ):
                ub = eval(df_bounds.at[idx, col].replace(",", "").replace(")", ""))
                df_lb.at[idx, col] = np.nan
                df_ub.at[idx, col] = ub
            else:
                # If the cell is NaN or None, keep it as is
                df_lb.at[idx, col] = df_bounds.at[idx, col]
                df_ub.at[idx, col] = df_bounds.at[idx, col]

    return df_lb, df_ub


def assert_peak_format(input_str):
    """
    Ensures that numbers are used only as multiplet suffixes in the peak names.
    Args:
        input_str (str): The peak name to be validated.
    Raises:
        ValueError: If the peak name ends with a floating-point number.
        ValueError: If the peak name contains numbers at the beginning or in the middle.
    """
    msg = "Error! The peak name can only use numbers as a suffix for multiplet peaks separated by J-coupling."
    if re.search(r"\.\d+$", input_str):
        print(msg)
        raise ValueError(
            "The peak name %s cannot end with a floating-point number!" % input_str
        )
    if re.search(r"\d+[\D]", input_str) or re.search(r"^\d+", input_str):
        print(msg)
        raise ValueError(
            "The peak name %s cannot contain numbers at the beginning or in the middle!"
            % input_str
        )


def find_header_row(filename, comment_char="#"):
    """Determine the index of the first non-commented line."""
    with open(filename, "r") as file:
        print("Checking comment lines in the prior knowledge file")
        for i, line in enumerate(file):
            if "#" in line:
                print("Comment: in line", i, line)
    with open(filename, "r") as file:
        for i, line in enumerate(file):
            processedline = line.replace('"', "").replace("'", "").strip()
            if not processedline.startswith(comment_char):
                return i
            # else:
            #     print("Comment:", processedline)
    return None  # Return None if all lines are comments or file is empty


def generateparameter(
    fname,
    MHz=120.0,
    g_global=0.0,
    scale_amplitude=1.0,
    paramter_prefix=["ak", "freq", "dk", "phi", "g"],
    preview=False,
    delta_phase_rad=0
):
    """
    Generate a lmfit Parameters object for modeling, based on data read from an Excel or CSV file.

    This function reads initial values, expressions, and bounds for each parameter from an Excel file,
    applies necessary unit conversions, and initializes a Parameters object with this information.

    Args:
        fname (str): Path to the Excel or CSV file containing prior knowledge
        MHz (float, optional): Field strength in MHz, used for unit conversions. Defaults to 120.0.
        g_global (float, optional): Global value for the ``g`` parameter. Defaults to 0.0. If set to False,
          the g values specified in the prior knowledge will be used.
        parameter_prefix (list of str, optional): List of parameter prefixes (e.g., ak, freq, dk, phi, g). Defaults to ['ak', 'freq', 'dk', 'phi', 'g'].
        delta_phase_rad (float, optional): Additional phase shift (in radians) to be applied to the prior knowledge phase values. Defaults to 0.0.

    Returns:
        lmfit.Parameters: Parameters object with initialized parameters for modeling.
    """
    if fname.endswith("xlsx") or fname.endswith("xls"):
        pk = pd.read_excel(
            fname, index_col=0, sheet_name=0, comment="#"
        )  # , skiprows=find_header_row(fname), comment='#')
    elif fname.endswith(".csv"):
        pk = pd.read_csv(
            fname, index_col=0, skiprows=find_header_row(fname), comment="#"
        )
    else:
        raise NotImplementedError("file format must be Excel (xlsx) or CSV!")
    pk = pk.applymap(
        lambda x: pd.to_numeric(x, errors="ignore")
    )  # To be compatible with CSV

    peaklist = pk.columns.to_list()  # generate a peak list directly from the
    [assert_peak_format(x) for x in peaklist]
    dfini = extractini(pk, MHz=MHz)  # Parse initial values
    dfini2 = unitconverter(
        dfini, MHz=MHz
    )  # Convert ppm to Hz, convert FWHM to dk, convert degree to radians.
    # print(f"{dfini2=}")
    df_lb, df_ub = parse_bounds(pk)  # Parse bounds
    df_expr = extract_expr(pk, MHz=MHz)  # Parse expression
    df_lb2 = unitconverter(df_lb, MHz=MHz)
    df_ub2 = unitconverter(df_ub, MHz=MHz)
    if g_global is False:
        print("Parameter g will be fit with the initial value set in the file %s" % fname)
        # print(f"Parameter g will be fit with the initial value set in the file {fname}")
    allpara = Parameters()
    for peak in dfini2.columns:
        for i, para in enumerate(paramter_prefix):
            vary = True
            val = dfini2[peak].iloc[i]
            lval = df_lb2[peak].iloc[i]
            uval = df_ub2[peak].iloc[i]
            expr = df_expr[peak].iloc[i]
            # Handle NaN values for bounds
            if np.isnan(lval):
                lval = -np.inf
            if np.isnan(uval):
                uval = np.inf
            name = para + "_" + peak
            if (para == "ak") and scale_amplitude != 1.0:
                print(f"scale {name} from {val} to {val * scale_amplitude}")
                val = val * scale_amplitude
                lval = lval * scale_amplitude
                uval = uval * scale_amplitude
            if para == "freq":
                pass
            if para == "dk" and (lval != uval): # Important bug fix. Prior to 0.3.20, the lval of dk was always ignored and set to 0. 
                if lval < 0:
                   print(f"Warning! Linewidth {name} cannot be a negative value! Set the lower bound to 0!")
                   lval = 0
            if para == "g":
                if g_global is False:
                    vary = True
                else:
                    val = g_global
                    vary = False
            if para == "phi":
                val = val + delta_phase_rad
            # Add parameter to lmfit Parameters object
            try:
                if lval == uval:
                    # When lval == uval, set the val to lval and fix it
                    allpara.add(
                        name=name, value=lval, vary=False,
                    )
                else:
                    allpara.add(
                        name=name, value=val, min=lval, max=uval, vary=vary, expr=expr
                    )
                    
            except NameError as e:
                e2 = (
                    "This error may be caused by the expr {} being constrained "
                    "to a peak that is not defined yet. Define it in a column "
                    "to the left of the {} column."
                ).format(expr, peak)
                raise UnboundLocalError(e2)

    if preview:
        return allpara, peaklist, pk

    else:
        # compatible with old API
        return allpara, peaklist


def initialize_FID(
    fid,
    priorknowledgefile=None,
    MHz=120,
    sw=10000,
    deadtime=200e-6,
    normalize_fid=False,
    flip_axis=False,
    preview=False,
    xlim=None,
    truncate_initial_points=0,
    g_global=0.0,
    scale_amplitude=1.0,
    carrier=0.0,
    lb=2.0,
    ppm_offset=0,
    noise_var='OXSA',
    delta_phase=0.0,
):
    """
    Initialize fitting parameters from prior knowledge (`priorknowledgefile`) or HSVD initialized result if there is
    not a prior knowledge file.

    Args:
        fid (numpy.ndarray): The input FID data.
        priorknowledgefile (str, optional): Path to an Excel file containing prior knowledge parameters.
        MHz (float): The field strength in MHz.
        sw (float): The spectral width in Hz.
        deadtime (float): The dead time or begin time in seconds before the FID signal starts.
        normalize_fid (bool): If True, normalize the FID data.
        scale_amplitude (float, optional): Scaling factor applied to the amplitude parameters loaded from priorknowledgefile.
          Useful when prior knowledge amplitudes significantly differ from the FID amplitude. Defaults to 1.0 (no scaling).
        flip_axis (bool): If True, flip the FID axis by taking the complex conjugate. Useful in some GE scanners where the MNS axis needs to be flipped.
        preview (bool): If True, display a preview plot of the original and initialized FID spectra.
        xlim (tuple): The x-axis limits for the preview plot in ppm.
        truncate_initial_points (int): Truncate initial points from FID to remove fast decaying components (e.g. macromolecule).
                                       This usually makes baseline more flat.
        g_global (float, optional): Global value for the ``g`` parameter. Defaults to 0.0. If set to False,
        the g values specified in the prior knowledge will be used.
        lb (float, optional): Line broadening parameter in Hz, used for spectrum visualization. Defaults to 2.0.
        carrier (float, optional): The carrier frequency in ppm, often used for water (4.7 ppm) or other reference metabolite such as Phosphocreatine (0 ppm).
        ppm_offset (float, optional): Adjust the ppm in priorknowledgefile. Default 0 ppm
        noise_var (str or float): Method or value used to estimate the noise variance in the data. Options include:

            - ``OXSA``: Uses the default noise variance estimation method employed by OXSA. See ``pyAMARES.util.crlb.evaluateCRB`` for details. 
            - ``jMRUI``: Employs the default noise variance estimation method used by jMRUI. 
            - A float value: Directly specifies the noise variance calculated externally.

        delta_phase (float, optional): Additional phase shift (in degrees) to be applied to the prior knowledge phase values. Defaults to 0.0.

    Returns:
        argparse.Namespace: An object containing FID fitting parameters.
    """
    if fid is None:
        print("Warning, fid is None!")
        fid = np.ones(1024, dtype=complex)

    sw = float(sw)  # Sometimes values from Matlab are uint16 and cause bugs. Make sure they are float.
    MHz = float(MHz)
    deadtime = float(deadtime)
    dwelltime = 1.0 / sw
    if truncate_initial_points > 0:
        print(
            "Truncating %i points from the beginning of the FID signal"
            % truncate_initial_points
        )
        deadtime_old = deadtime * 1.0
        deadtime = deadtime + truncate_initial_points * dwelltime
        fid = fid[truncate_initial_points:]
        print(
            "The deadtime is changing from %f seconds to %f seconds"
            % (deadtime_old, deadtime)
        )
    fidpt = len(fid)
    # TD = fidpt * 2
    # at = TD / (2 * sw)

    ppm = np.linspace(-sw / 2, sw / 2, fidpt) / np.abs(MHz)
    Hz = np.linspace(-sw / 2, sw / 2, fidpt)
    # print(f"{sw=}")
    # print(f"{np.max(ppm)=} {np.min(ppm)=}")
    # print(f"{np.max(Hz)=} {np.min(Hz)=}")
    # print(f"{-sw/2=}")

    opts = argparse.Namespace()
    opts.deadtime = deadtime
    opts.timeaxis = np.arange(0, dwelltime * fidpt, dwelltime) + deadtime
    # opts.timeaxis = np.linspace(deadtime, at, fidpt)
    opts.carrier = carrier  # 4.7 for water, 0 for PCr
    if flip_axis:
        # This must be done before the shifting FID for carrier. 
        fid = np.conj(fid)
    if carrier != 0:
        print("Shift FID so that center frequency is at %s ppm!" % carrier)
        fid = fid * np.exp(1j * 2 * np.pi * carrier * MHz * opts.timeaxis)
        # ppm = ppm + carrier
        # Hz = Hz + carrier / np.abs(MHz)
    # xlim is always ppm
    if xlim is None:
        opts.xlim = np.array((sw / 2, -sw / 2)) / np.abs(MHz)  # xlim should be Hz
    else:
        opts.xlim = np.array(xlim)
    opts.xlim_Hz = opts.xlim * MHz

    if normalize_fid:
        opts.fid = fid / np.max(fid)
    else:
        opts.fid = fid.copy()
    opts.spec = np.fft.fftshift(np.fft.fft(opts.fid))

    opts.MHz = MHz
    opts.ppm = ppm
    opts.Hz = Hz
    opts.dwelltime = dwelltime
    opts.deadpts = int(deadtime // dwelltime)
    opts.g_global = g_global  # for HSVD initialization
    opts.scale_amplitude = scale_amplitude 
    opts.ppm_offset = ppm_offset
    opts.noise_var = noise_var

    plotParameters = argparse.Namespace()
    plotParameters.deadtime = deadtime
    plotParameters.lb = lb  # linebroadening, Hz
    plotParameters.sw = sw  # spectrum widt, Hz
    plotParameters.xlim = xlim  # xlim, in ppm, such as (10, -20)
    plotParameters.ifphase = (
        False  # 0 and 1st order phasing. Do not phase unless otherwise turned on
    )

    opts.plotParameters = plotParameters  # Make obj plotParameters part of opts

    if priorknowledgefile is not None:
        if preview:
            opts.initialParams, opts.peaklist, opts.PK_table = generateparameter(
                priorknowledgefile, MHz=MHz, g_global=g_global, preview=True, scale_amplitude=scale_amplitude, delta_phase_rad=np.deg2rad(delta_phase),
            )  # Load prior knowledge
        else:
            opts.initialParams, opts.peaklist = generateparameter(
                priorknowledgefile, MHz=MHz, g_global=g_global, preview=False, scale_amplitude=scale_amplitude,delta_phase_rad=np.deg2rad(delta_phase),
            )  # Load prior knowledge
        opts.fidini = fft_params(
            timeaxis=opts.timeaxis, params=opts.initialParams, fid=True
        )
        if ppm_offset != 0:
            print("Shifting the ppm by ppm_offset=%2.2f ppm" % ppm_offset)
            for p in opts.initialParams:
                if p.startswith("freq"):
                    hz_offset = opts.ppm_offset * opts.MHz
                    if (
                        opts.initialParams[p].min is not None
                    ):  # Check if there's a lower bound set
                        opts.initialParams[p].min += hz_offset
                    if (
                        opts.initialParams[p].max is not None
                    ):  # Check if there's an upper bound set
                        opts.initialParams[p].max += hz_offset
                    print(
                        "before opts.initialParams[%s].value=%s"
                        % (p, opts.initialParams[p].value)
                    )
                    print(
                        "new value should be opts.initialParams[%s].value + opts.ppm_offset * opts.MHz=%s"
                        % (p, opts.initialParams[p].value + opts.ppm_offset * opts.MHz)
                    )

                    # print(f"before {opts.initialParams[p].value=}")
                    # print(
                    #     f"new value should be {opts.initialParams[p].value + opts.ppm_offset * opts.MHz=}"
                    # )
                    opts.initialParams[p].value = (
                        opts.initialParams[p].value + hz_offset
                    )
                    # print(f"after {opts.initialParams[p].value=}")
                    print(
                        "after opts.initialParams[%s].value=%s"
                        % (p, opts.initialParams[p].value)
                    )

        opts.allpara = opts.initialParams  # obsolete API, will be removed

    if preview:
        plt.title("Preview of Input FID and Initial Parameters")
        plt.plot(opts.ppm, opts.spec.real, "r-", label="Original Spec")
        if priorknowledgefile is not None:
            plt.plot(
                opts.ppm + opts.ppm_offset,
                np.real(np.fft.fftshift(np.fft.fft(opts.fidini))),
                "b--",
                label="Initial Parameters",
            )
        plt.xlim(opts.xlim)
        plt.legend()
        plt.xlabel("ppm")
        plt.show()
        if priorknowledgefile is not None:
            print("Printing the Prior Knowledge File %s" % priorknowledgefile)
            try:
                from IPython.display import display

                display(opts.PK_table)  # display table
            except ImportError:
                print(opts.PK_table)

    return opts

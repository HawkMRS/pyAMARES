import warnings
import numpy as np
import pandas as pd
from ..kernel import Jac6, Jac6c
from ..kernel import parameters_to_dataframe_result, parameters_to_dataframe
from ..kernel import remove_zero_padding

try:
    import jinja2

    if_style = True
except ImportError:
    if_style = False
    print("Jinja2 is not installed. Turn off colored table. Try pip install jinja2.")

def get_min_max_deg(resulttable):
    # Extract min and max degrees from the constraints in the ``resultpd``
    phitable = resulttable[resulttable.name.str.startswith('phi')]
    min_deg = np.rad2deg(phitable['min'].min())
    max_deg = np.rad2deg(phitable['max'].max())
    return min_deg, max_deg

def wrap_degrees(val_deg, min_deg, max_deg):
    # Fold result_pd degrees into the constraints defined in the prior knowledge
    # Ensure min_deg < max_deg
    assert min_deg < max_deg, "min_deg should be less than max_deg"

    # Normalize degrees to the range [0, 360)
    normalized_deg = val_deg % 360

    # If the specified range is within [0, 360)
    if 0 <= min_deg < max_deg <= 360:
        wrapped_deg = np.where(normalized_deg < min_deg, normalized_deg + 360, normalized_deg)
    # If the range includes negative degrees or spans over 0 degrees (e.g., [-180, 180] or [350, 10])
    else:
        range_width = max_deg - min_deg
        wrapped_deg = (normalized_deg - min_deg) % range_width + min_deg
    
    return wrapped_deg

def report_crlb(outparams, crlb, Jacfunc=None):
    """
    Generates a report on Cramér-Rao Lower Bounds (CRLBs).

    Args:
        outparams (lmfit Parameters object): DataFrame containing model parameters.
        crlb (numpy.ndarray): Array of CRLB values.
        Jacfunc (callable, optional): Function to compute the Jacobian. Defaults to None.

    Returns:
        pandas.DataFrame: DataFrame with CRLB information for relevant parameters.
    """
    pdpoptall = parameters_to_dataframe_result(outparams)
    # print(f"{Jacfunc=}, {pdpoptall=} {outparams=}")
    if Jacfunc is None or Jacfunc is Jac6:
        # You'll need to assert there is a peaklist in the fid_parameters
        poptall = pdpoptall["value"]
    elif Jacfunc is Jac6c:
        poptall = pdpoptall[~pdpoptall["name"].str.startswith("g")]["value"]
    # elif Jacfunc is flexible_Jac:
    #    poptall = pdpoptall[pdpoptall['vary']]['value'] # Parameters with vary=True
    else:
        # print(f"{Jacfunc=} is not supported!")
        # print("Jacfunc=%s is not supported!" % Jacfunc)
        warnings.warn("Jacfunc=%s is not supported!" % Jacfunc, RuntimeWarning)

    resultpd = pdpoptall.loc[poptall.index]
    resultpd["CRLB %"] = np.abs(crlb / poptall * 100.0)
    return resultpd


def highlight_rows_crlb_less_than_02(row):
    # highlight the rows of the input dataframe as green if the CRLB(%) <= 20.
    return [
        (
            "background-color: rgba(0, 255, 0, 0.5)"
            if row["CRLB(%)"] <= 20.0
            else "background-color: rgba(255, 0, 0, 0.2)"
        )
        for _ in row
    ]


def sum_multiplets(df):
    """
    Sums amplitude and standard deviation for multiplets
    with the same base name in the given DataFrame.

    Groups the DataFrame on base peak names (extracted by removing digits)
    and aggregates the columns, summing amplitude and standard deviation
    but taking the first value for other columns like chemical shift.

    Parameters:
        df (DataFrame): DataFrame with columns including 'amplitude',
            'sd', 'chem shift(ppm)'

    Returns:
        DataFrame: DataFrame grouped and aggregated on base peak names
    """

    def get_base_name(name):
        return "".join([i for i in name if not i.isdigit()])

    base_names = df.index.map(get_base_name)

    added_peaks = set()
    grouped_peak_list = [
        x for x in base_names if not (x in added_peaks or added_peaks.add(x))
    ]

    agg_funcs = {
        col: "first" if col not in ["amplitude", "sd", "SNR"] else "sum" for col in df.columns
    }
    grouped_df = df.groupby(base_names).agg(agg_funcs)

    # return grouped_df.sort_values('chem shift(ppm)')
    return grouped_df.reindex(grouped_peak_list)


def contains_non_numeric_strings(df):
    def is_numeric_string(s):
        try:
            float(
                s
            )  
            return True
        except ValueError:
            return False

    return any(not is_numeric_string(str(idx)) for idx in df.index)

def extract_key_parameters(df):
    return df[['amplitude', 'chem shift(ppm)', 'LW(Hz)', 'phase(deg)', 'SNR', 'CRLB(%)']]

def report_amares(outparams, fid_parameters, verbose=False):
    """
    Generates a comprehensive report on AMARES analysis results.

    Args:
        outparams (lmfit fitting parameter): Output parameters from the fitting process.
        fid_parameters (argspace Namespace object): FID parameters object.
        verbose (bool, optional): Controls verbosity of output. Defaults to False.

    Returns:
        pandas.Styler: A DataFrame for presentation of the results with rows whose CRLB<=20
        are highlighted by green.
    """
    from pyAMARES.util.crlb import create_pmatrix, evaluateCRB  # delayed import

    pkpd = parameters_to_dataframe(outparams)
    Pmatrix = create_pmatrix(pkpd, ifplot=verbose)
    evaluateCRB(outparams, fid_parameters, P=Pmatrix, verbose=verbose)
    resulttable = fid_parameters.resultpd
    peaklist = [
        x.replace("phi_", "")
        for x in resulttable[resulttable["name"].str.startswith("phi")]["name"].values
    ]

    final_table = pd.DataFrame()
    all_peak_data = []

    for peak in peaklist:
        peak_data = []

        for parameter in ["ak", "freq", "dk", "phi", "g"]:
            var_name = parameter + "_" + peak
            currentrow = resulttable[resulttable["name"] == var_name][
                ["value", "std", "CRLB %"]
            ].copy()
            peak_data.extend(currentrow.values.flatten())
        all_peak_data.append(peak_data)

    column_names = []
    for parameter in ["ak", "freq", "dk", "phi", "g"]:
        column_names.extend(
            [parameter + "_value", parameter + "_std", parameter + "_CRLB %"]
        )
    final_table = pd.DataFrame(all_peak_data, columns=column_names)

    MHz = fid_parameters.MHz
    result = final_table.rename(
        columns={
            "ak_value": "amplitude",
            "ak_std": "a_sd",
            "ak_CRLB %": "a_CRLB(%)",
            "freq_value": "chem shift",
            "freq_std": "freq_sd",
            "freq_CRLB %": "freq_CRLB(%)",
            "dk_value": "lw",
            "dk_std": "lw_sd",
            "dk_CRLB %": "lw_CRLB(%)",
            "phi_value": "phase",
            "phi_std": "phase_sd",
            "phi_CRLB %": "phase_CRLB(%)",
            "g_CRLB %": "g_CRLB(%)",
        }
    )
    # fid_parameters.result2 = result.copy() # debug
    negative_amplitude = result["amplitude"] < 0
    if negative_amplitude.sum() > 0:
        print(
            "The amplitude of index",
            result.loc[negative_amplitude].index.values,
            " is negative! Make it positive and flip the phase!",
        )
        result.loc[negative_amplitude, "amplitude"] = result.loc[
            negative_amplitude, "amplitude"
        ].abs()
        result.loc[negative_amplitude, "phase"] += np.pi

    # For poor lmfit fitting, there may not be any sd estimated. Then use CRLB instead
    sd_columns = ["a_sd", "freq_sd", "lw_sd", "phase_sd", "g_std"]
    crlb_columns = [
        "a_CRLB(%)",
        "freq_CRLB(%)",
        "lw_CRLB(%)",
        "phase_CRLB(%)",
        "g_CRLB(%)",
    ]
    val_columns = ["amplitude", "chem shift", "lw", "phase", "g_value"]
    for col, crlb_col, val_col in zip(sd_columns, crlb_columns, val_columns):
        if result[col].isnull().all():
            print("%s is all None, use crlb instead!" % col)
            result[col] = result[crlb_col] / 100 * result[val_col]

    result["chem shift"] = result["chem shift"] / MHz
    result["freq_sd"] = result["freq_sd"] / MHz
    result["lw"] = result["lw"] / np.pi
    result["lw_sd"] = result["lw_sd"] / np.pi
    min_deg, max_deg = get_min_max_deg(resulttable)
    phase_col = np.rad2deg(result["phase"])
    # result["phase"] = np.rad2deg(result["phase"]) % 360
    # result["phase"] = (result["phase"] + 180) % 360 - 180 # Wrap 360 to 0.
    result["phase"] = wrap_degrees(phase_col, min_deg=min_deg, max_deg=max_deg)
    try:
        result["phase_sd"] = np.rad2deg(result["phase_sd"])
        result["phase_sd"] = wrap_degrees(result["phase_sd"] , min_deg=min_deg, max_deg=max_deg)
    except Exception as e:
        print(f"Caught an error: {e}")
        result["phase_sd"] = np.nan
    # Change 'g_CRLB(%)' values to NaN where they are 0.0
    result.loc[result["g_CRLB(%)"] == 0.0, "g_CRLB(%)"] = np.nan
    zero_ind = remove_zero_padding(fid_parameters.fid)
    if zero_ind > 0:
        print("It seems that zeros are padded after %i" % zero_ind)
        print("Remove padded zeros from residual estimation!")
        fid_parameters.fid_padding_removed = fid_parameters.fid[:zero_ind]
        std_noise = np.std(fid_parameters.fid_padding_removed[-len(fid_parameters.fid_padding_removed)//10:])
    else:
        std_noise = np.std(fid_parameters.fid[-len(fid_parameters.fid)//10:])
    result["SNR"] = result["amplitude"] / std_noise
    result.columns = [
        "amplitude",
        "sd",
        "CRLB(%)",
        "chem shift(ppm)",
        "sd(ppm)",
        "CRLB(cs%) ",
        "LW(Hz)",
        "sd(Hz)",
        "CRLB(LW%)",
        "phase(deg)",
        "sd(deg)",
        "CRLB(phase%)",
        "g",
        "g_sd",
        "g (%)",
        "SNR",
    ]
    result["name"] = peaklist
    result = result.set_index("name")
    if hasattr(fid_parameters, "peaklist"):
        # By default, there should be a peak list from the fid_parameters
        result.reindex(
            fid_parameters.peaklist
        )  # reorder to the peaklist from the pk, not the local peaklist
    # fid_parameters.peaklist = peaklist
    else:
        print("No peaklist, probably it is from an HSVD initialized object")
    fid_parameters.result_multiplets = result  # Keep the multiplets
    # Sum multiplets if needed
    if contains_non_numeric_strings(result):  # assigned peaks in the index
        fid_parameters.result_sum = sum_multiplets(result)
        # Sum the amplitude of each multiplets. For example, make BATP, BATP2, BATP3 as BATP
        if if_style:
            styled_df = fid_parameters.result_sum.style.apply(
                highlight_rows_crlb_less_than_02, axis=1
            ).format("{:.3f}")
            simple_df = highlight_dataframe(extract_key_parameters(fid_parameters.result_sum))
        else:
            styled_df = (
                fid_parameters.result_sum
            )  # python 3.7 and older may not support Jinja2
            simple_df = extract_key_parameters(fid_parameters.result_sum)
    else:  # all numers, HSVD assigned parameters
        if if_style:
            styled_df = fid_parameters.result_multiplets.style.apply(
                highlight_rows_crlb_less_than_02, axis=1
            ).format("{:.3f}")
            if hasattr(fid_parameters, "result_sum"):
                simple_df = highlight_dataframe(extract_key_parameters(fid_parameters.result_sum))
            else:
                simple_df = None
                print("There is no result_sum generated, simple_df is set to None")
        else:
            styled_df = (
                fid_parameters.result_multiplets
            )  # python 3.7 and older may not support Jinja2
            if hasattr(fid_parameters, "result_sum"):
                simple_df = extract_key_parameters(fid_parameters.result_sum)
            else:
                simple_df = None
                print("There is no result_sum generated, simple_df is set to None")
    if hasattr(fid_parameters, "result_sum"):
        fid_parameters.metabolites = fid_parameters.result_sum.index.to_list()
    else:
        print("There is no result_sum generated, probably there is only 1 peak")
    fid_parameters.styled_df = styled_df
    fid_parameters.simple_df = simple_df
    return styled_df

def highlight_dataframe(df, by="CRLB(%)", is_smaller=True, threshold=20.0, numeric_format="{:.3f}"):
    """
    A versatile tool that highlights rows in a DataFrame based on a specified column's values.

    This function applies a background color to the rows of the input DataFrame. 
    Rows where the specified column's value meets the threshold condition 
    are highlighted in green, while the others are highlighted in red.

    Args:
        df (pd.DataFrame): The input DataFrame to be styled.
        by (str): The column name to be used for the threshold comparison.
        is_smaller (bool): If True, highlight rows where the column value is 
            less than or equal to the threshold. If False, highlight rows 
            where the column value is greater than or equal to the threshold.
        threshold (float): The threshold value to compare against.
        numeric_format (str): The format string used to display numeric values 
            in the DataFrame. By default, `{:.3f}` formats a float as 0.241, while `{:.1f}` formats it as 0.2.

    Returns:
        pandas.Styler: A DataFrame for presentation of the results with selected rows
        are highlighted by green.

    Examples:
        >>> highlight_dataframe(FIDobj.result_multiplets)
        >>> highlight_dataframe(FIDobj.result_sum, numeric_format='{:1.1f}')
        >>> highlight_dataframe(FIDobj.result_sum, threshold=5, by='SNR', is_smaller=False)
    """
    
    def highlight_rows(row, threshold=threshold, is_smaller=is_smaller):
        # Helper function to apply background color to a row based on the threshold condition.
        if is_smaller:
            return [
                (
                    "background-color: rgba(0, 255, 0, 0.5)"
                    if row[by] <= threshold
                    else "background-color: rgba(255, 0, 0, 0.2)"
                )
                for _ in row
            ]
        else:
            return [
                (
                    "background-color: rgba(0, 255, 0, 0.5)"
                    if row[by] >= threshold
                    else "background-color: rgba(255, 0, 0, 0.2)"
                )
                for _ in row
            ]
    
    styled_df = df.style.apply(highlight_rows, axis=1).format(numeric_format)
    return styled_df
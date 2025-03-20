from copy import deepcopy
import numpy as np
import scipy
import pandas as pd
import matplotlib.pyplot as plt

from lmfit import Parameters
import nmrglue as ng

from ..util.visualization import preview_HSVD

if int(np.__version__.split('.')[0]) < 2:  # Check if numpy version is less than 2.0
    try:
        import hlsvdpro as hlsvd
    except ImportError:
        from ..libs import hlsvd
else:
    # For NumPy 2.0+, skip hlsvdpro and use the local implementation directly. 2025-03-20
    from ..libs import hlsvd

from ..libs.hlsvd import create_hlsvd_fids

from ..kernel.fid import equation6, uninterleave, interleavefid, Compare_to_OXSA
from ..kernel.lmfit import parameters_to_dataframe


def HSVDp0(hsvdfid, timeaxis, ppm, MHz=120, ifplot=True):
    """
    Fit a Lorentzian model to an HSVD-processed NMR FID to estimate initial parameters.

    Args:
        hsvdfid (numpy.ndarray): The HSVD-processed FID.
        timeaxis (numpy.ndarray): The time axis for the FID data.
        ppm (numpy.ndarray): The chemical shift axis in ppm.
        MHz (float, optional): The field strength in MHz. Defaults to 120 MHz.
        ifplot (bool, optional): Flag to plot the original and fitted spectra. Defaults to True.

    Returns:
        numpy.ndarray: An array containing the fitted parameters [amplitude, frequency, linewidth, phase].
    """

    def lorentzian(x, ak=1.0, fk=0, dk=50, phi=0):
        """
        Lorentzian model function for fitting.

        Args:
            x (numpy.ndarray): Time axis for the FID data.
            ak (float): Amplitude of the Lorentzian peak.
            fk (float): Frequency offset from the center.
            dk (float): Damping factor (related to linewidth).
            phi (float): Phase.

        Returns:
            numpy.ndarray: Interleaved real and imaginary parts of the modeled FID.
        """
        fid = (
            ak * np.exp(1j * phi) * np.exp(-dk * x) * np.exp((1j * 2 * np.pi * fk * x))
        )
        return interleavefid(fid)

    spec = np.real(ng.proc_base.fft(hsvdfid))
    a0 = np.max(np.abs(hsvdfid))
    freq0 = ppm[np.abs(spec).argmax()] * MHz
    lw0 = 10.0
    phi0 = 0.0
    spopt = [a0, freq0, lw0, phi0]

    p0, perr0 = scipy.optimize.curve_fit(
        lorentzian, xdata=timeaxis, ydata=interleavefid(hsvdfid), p0=spopt
    )
    fittedspec = ng.proc_base.fft(uninterleave(lorentzian(timeaxis, *p0)))

    hsvdp0 = np.zeros(5)
    hsvdp0[:4] = p0
    if ifplot:
        plt.plot(ppm, spec.real, label="origin")
        plt.plot(ppm, fittedspec.real, label="fitted HSVD")
        plt.legend()
        plt.show()
    return hsvdp0


def assign_hsvd_peaks(measured_peaks_df, peak_info=None):
    """
    Assign peak names to measured peaks based on provided information and keep other columns in the measured_peaks_df.

    Args:
        measured_peaks_df (pandas.DataFrame): DataFrame with a column ['fk'] containing measured peak positions and possibly other columns.
        peak_info (pandas.DataFrame): DataFrame with columns ['name', 'value', 'min', 'max'].

    Returns:
        pandas.DataFrame: DataFrame with original columns from measured_peaks_df plus ['name', 'value', 'min', 'max'].
    """
    results = measured_peaks_df.copy()

    if peak_info is None:
        results["name"] = [str(x + 1) for x in measured_peaks_df.index]
        return results
    else:
        results["name"] = pd.Series(dtype="object")  # or 'str' for string type

        # Assigning peak names
        for index, row in measured_peaks_df.iterrows():
            peak = row["freq"]
            # Find matching peak info
            mask = (peak_info["min"] <= peak) & (peak_info["max"] >= peak)
            match = peak_info[mask]

            if not match.empty:
                results.at[index, "name"] = match["name"].values[0].replace("freq_", "")

        return results
        # return results.dropna(subset=['name'])


def hsvd_initialize_parameters(temp_to_unfold, allpara_hsvd=None, g_global=0.0):
    """
    Update parameters in allpara_hsvd based on the values in temp_to_unfold.

    Args:
        temp_to_unfold (pandas.DataFrame): DataFrame containing parameter values and names.
        allpara_hsvd (dict): Dictionary (or similar structure) to be updated.

    Returns:
        dict: Modified allpara_hsvd with updated values.
    """
    if allpara_hsvd is None:
        allpara_hsvd = Parameters()
        for i in temp_to_unfold.index:
            for j in temp_to_unfold.columns[:5]:
                uval = np.inf
                lval = -np.inf
                vary = True
                peak_name = temp_to_unfold.loc[i, "name"]
                var_name = j + "_" + peak_name
                var = temp_to_unfold.loc[i, j]
                if var_name.startswith("dk"):
                    lval = 0
                if var_name.startswith("g"):
                    lval = -1.0
                    uval = 1.0
                    vary = False
                    val = g_global
                if var_name.startswith("phi"):
                    lval = -np.pi
                    uval = np.pi
                allpara_hsvd.add(
                    name=var_name, value=var, min=lval, max=uval, vary=vary
                )
    else:
        for i in temp_to_unfold.index:
            for j in temp_to_unfold.columns[:5]:
                peak_name = temp_to_unfold.loc[i, "name"]
                var_name = j + "_" + peak_name
                var = temp_to_unfold.loc[i, j]

                if allpara_hsvd[
                    var_name
                ].vary:  # v0.23c, HSVDinitializer only changes varying parameters
                    # print(f"{var_name=} {allpara_hsvd[var_name].vary=}")
                    # print(f"Setting {var_name} {allpara_hsvd[var_name].value} to {var}, it is {allpara_hsvd[var_name]}")
                    if var_name.startswith("ak") and var < 0:
                        # print(f"Warning ak for {peak_name} {var} is negative!, Make it positive and flip the phase!")
                        print(
                            "Warning ak for %s %s is negative!, Make it positive and flip the phase!"
                            % (peak_name, var)
                        )
                        allpara_hsvd[var_name].set(value=np.abs(var))
                        # Flip the phase
                        temp_to_unfold.loc[
                            temp_to_unfold["name"] == peak_name, "phi"
                        ] += np.pi
                    else:
                        allpara_hsvd[var_name].set(value=var)

    return allpara_hsvd


def uniquify_dataframe(df):
    """
    Processes a DataFrame to ensure that for each unique name, only the entry with the maximum
    absolute ``ak`` value is retained with its name. The ``name`` for other entries in the same group
    is set to NaN. Rows where ``name`` is initially NaN are left unchanged.

    Args:
        df (pandas.DataFrame): The input DataFrame with ``name`` and ``ak`` columns.

    Returns:
        pandas.DataFrame: A DataFrame where for each unique ``name``, only the entry with the maximum absolute
                          ``ak`` value retains its name, and others have their ``name`` set to NaN.
    """

    def process_group(group):
        if len(group) > 1:
            # Find the index of the row with the max absolute 'ak' value
            max_ak_idx = group["ak"].abs().idxmax()
            # Set 'name' to NaN for all other rows
            group.loc[group.index != max_ak_idx, "name"] = np.nan
        return group

    df_non_nan = (
        df[df["name"].notna()].groupby("name", group_keys=False).apply(process_group)
    )

    df_nan = df[df["name"].isna()]
    result_df = pd.concat([df_non_nan, df_nan]).sort_index()

    return result_df


def HSVDinitializer(
    fid_parameters,
    fitting_parameters=None,
    num_of_component=12,
    lw_threshold=500,
    verbose=False,
    preview=False,
):
    """
    Initializes HSVD parameters for a given FID signal.

    Args:
        fid_parameters (argspace.Namespace): An object containing FID, dwell time, time axis, ppm, MHz, g_global, Hz, and xlim_Hz attributes.
        fitting_parameters (lmfit.Parameters): Parameters for fitting, if any.
        num_of_component (int): Number of components to decompose the FID into.
        lw_threshold (float): Linewidth threshold for filtering out broad components.
        verbose (bool): If True, prints additional information during processing.
        preview (bool): If True, displays a preview of the fitted components.

    Returns:
        pandas.DataFrame: A DataFrame containing the initialized parameters for HSVD.
    """
    result = hlsvd.hlsvd(fid_parameters.fid, num_of_component, fid_parameters.dwelltime)
    fid2 = create_hlsvd_fids(
        result,
        len(fid_parameters.fid),
        fid_parameters.dwelltime,
        sum_results=False,
        convert=False,
    )
    fid2 = fid2.T
    plist = []
    for i in range(num_of_component):
        currentfid = fid2[:, i]
        hsvdp0 = HSVDp0(
            currentfid,
            fid_parameters.timeaxis,
            fid_parameters.ppm,
            MHz=fid_parameters.MHz,
            ifplot=True if verbose else False,
        )
        p2, perr2 = scipy.optimize.curve_fit(
            equation6,
            xdata=fid_parameters.timeaxis,
            ydata=interleavefid(currentfid),
            p0=hsvdp0,
        )
        plist.append(p2)
        if verbose:
            print("fitted p0", p2)

    p_pd = pd.DataFrame(np.array(plist))
    p_pd.columns = ["ak", "freq", "dk", "phi", "g"]
    if verbose:
        print("Filtering peaks with linewidth broader than %i Hz" % lw_threshold)
    p_pd = p_pd[p_pd["dk"] < lw_threshold]  # filter out too broadened peaks
    p_pd["g"] = (
        fid_parameters.g_global
    )  # pass g_global to the new constructed HSVD multieq6 parameters
    hsvdarr = fid2[:, p_pd.index]

    if fitting_parameters is None:
        # Initialize parameters when there is no prior knowledge
        temp_to_unfold = assign_hsvd_peaks(p_pd, None)
        temp_to_unfold = uniquify_dataframe(temp_to_unfold)
        allpara_hsvd = hsvd_initialize_parameters(
            temp_to_unfold.dropna(subset=["name"]),
            None,
            g_global=fid_parameters.g_global,
        )
    else:
        fitting_parameters = deepcopy(fitting_parameters)
        allpara = parameters_to_dataframe(fitting_parameters)
        chemshift_pd = allpara[
            allpara["name"].str.startswith("freq")
        ]  # obtain all freq (Hz) from allpara
        temp_to_unfold = assign_hsvd_peaks(p_pd, chemshift_pd)
        temp_to_unfold = uniquify_dataframe(temp_to_unfold)
        allpara_hsvd = hsvd_initialize_parameters(
            temp_to_unfold.dropna(subset=["name"]),
            fitting_parameters,
            g_global=fid_parameters.g_global,
        )

    if preview:
        fig, ax = plt.subplots(figsize=(8, 4))
        preview_HSVD(
            ax,
            hsvdarr,
            fid_parameters.Hz,
            temp_to_unfold,
            xlim=fid_parameters.xlim_Hz,
            title="HSVD optimized parameters",
            xlabel="Hz",
        )

    fid_parameters.resNormSq, fid_parameters.relativeNorm = Compare_to_OXSA(
        inputfid=fid_parameters.fid, resultfid=np.sum(hsvdarr, 1)
    )
    return allpara_hsvd  # will change back to this one

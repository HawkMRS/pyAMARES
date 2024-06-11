import numpy as np
import matplotlib.pyplot as plt
import nmrglue as ng

from ..kernel.fid import process_fid

color_list = [
    "#1f77b4",  # Muted blue
    "#ff7f0e",  # Safety orange
    "#2ca02c",  # Cooked asparagus green
    "#d62728",  # Brick red/
    "#9467bd",  # Muted purple
    "#8c564b",  # Chestnut brown
    "#e377c2",  # Raspberry yogurt pink
    "#7f7f7f",  # Middle gray
    "#bcbd22",  # Curry yellow-green
    "#17becf",  # Blue-teal
    "#aec7e8",  # Light blue
    "#ffbb78",  # Light orange
    "#98df8a",  # Light green
    "#ff9896",  # Light red
    "#c5b0d5",  # Light purple
    "#c49c94",  # Light brown
    "#f7b6d2",  # Light pink
    "#c7c7c7",  # Light gray
    "#dbdb8d",  # Light yellow-green
    "#9edae5",  # Light teal
]


def preview_HSVD(ax, hsvdarr, ppm, p_pd, xlim=None, title="", xlabel=None):
    """
    Preview the HSVD analysis results.

    Args:
        ax (matplotlib.axes._axes.Axes): Matplotlib axes object for plotting.
        hsvdarr (numpy.ndarray): Array containing HSVD data.
        ppm (numpy.ndarray): Array of chemical shift values (ppm).
        p_pd (pandas.DataFrame): DataFrame containing peak information.
        xlim (tuple, optional): Lower and upper limits for the x-axis. Defaults to None.
        title (str, optional): Title for the plot. Defaults to ``""``.
        xlabel (str, optional): Label for the x-axis. Defaults to None.
    """
    hsvdspec = ng.proc_base.fft(np.sum(hsvdarr, axis=1))
    plt.title(title)

    for i in p_pd.index:
        currentspec = np.real(ng.proc_base.fft(hsvdarr[:, i]))
        ax.plot(ppm, currentspec.real, color=color_list[i], ls="-", alpha=0.85)
        ax.axvline(p_pd.loc[i]["freq"], color=color_list[i], ls="-.", alpha=0.2)
        ax.annotate(
            f"{p_pd.loc[i]['name']}",
            xy=(p_pd.loc[i]["freq"], currentspec[np.abs(currentspec).argmax()]),
            color=color_list[i],
            fontsize=18,
        )

    ax.plot(ppm, hsvdspec.real, color="black", ls="-", lw=2, alpha=0.3)
    if xlim is not None:
        ax.set_xlim(xlim)
    if xlabel is not None:
        ax.set_xlabel(xlabel)


def plot_fit(
    ax,
    fid,
    fid_fit,
    ppm,
    xlim=None,
    mode="real",
    label="Fitted Spectrum",
    plotParameters=None,
):
    """
    Plots the fitted spectrum, original spectrum, and residual for comparison.

    Args:
        ax (matplotlib.axes._axes.Axes): Matplotlib axes object for plotting.
        fid (numpy.ndarray): Array containing the original FID data.
        fid_fit (numpy.ndarray): Array containing the fitted FID data.
        ppm (numpy.ndarray): Array of chemical shift values (ppm).
        xlim (tuple, optional): Lower and upper limits for the x-axis. Defaults to None.
        mode (str, optional): Mode for plotting the spectrum. Defaults to ``real``.

            - ``real``: Plots the real part of the spectrum.
            - ``abs`` or ``mag``: Plots the absolute value (magnitude) of the spectrum.

        label (str, optional): Label for the fitted spectrum line. Defaults to 'Fitted Spectrum'.
        plotParameters (argparse.Namespace, optional): A namespace containing parameters for plotting and data processing. The namespace includes:

            - deadtime (float): The dead time before the FID acquisition starts.
            - lb (float): Line broadening factor in Hz.
            - sw (float): Spectral width in Hz.
            - xlim (tuple of float): Limits for the x-axis in ppm, for example, (10, -20).
            - ifphase (bool): turn on 0th and 1st order phasing.

    """
    if plotParameters is None:
        spec = ng.proc_base.fft(fid)
        spec_fit = ng.proc_base.fft(fid_fit)
    else:
        spec = process_fid(
            fid,
            deadtime=plotParameters.deadtime,
            sw=plotParameters.sw,
            lb=plotParameters.lb,
            ifphase=plotParameters.ifphase,
        )
        spec_fit = process_fid(
            fid_fit,
            deadtime=plotParameters.deadtime,
            sw=plotParameters.sw,
            lb=plotParameters.lb,
            ifphase=plotParameters.ifphase,
        )

    residual = spec - spec_fit

    if mode.startswith("abs") or mode.startswith("mag"):
        spec = np.abs(spec)
        spec_fit = np.abs(spec_fit)
        residual = np.abs(residual)

    ax.plot(ppm, spec_fit.real, "r-", label=label)
    ax.plot(ppm, spec.real, color="black", alpha=0.2, label="Original Spectrum")
    ax.plot(ppm, residual.real, "g--", label="Residual", alpha=0.5)
    ax.set_xlim(xlim)
    ax.legend()


def combined_plot(
    hsvdarr,
    ppm,
    p_pd,
    fid,
    fid_fit,
    xlim=None,
    mode="real",
    label="Fitted Spectrum",
    title=None,
    xlabel=None,
    plotParameters=None,
    filename=None,
):
    """
    Plot the results of AMARES or HSVD fitting results

    This function creates a two-part figure: the top part displays the fitted spectrum alongside the original
    FID data and their residual, and the bottom part previews the AMARES or HSVD fitting results

    Args:
        hsvdarr (numpy.ndarray): Array containing AMARES or HSVD data for each component.
        ppm (numpy.ndarray): Array of chemical shift values (ppm).
        p_pd (pandas.DataFrame): DataFrame containing peak information for each component.
        fid (numpy.ndarray): Array containing the original FID data.
        fid_fit (numpy.ndarray): Array containing the fitted FID data.
        xlim (tuple, optional): Lower and upper limits for the x-axis. Defaults to None.
        mode (str, optional): Mode for plotting the spectrum
             (``real`` for real part, ``abs`` or ``mag`` for magnitude). Defaults to ``real``. 
        label (str, optional): Label for the fitted spectrum line in the plot. Defaults to 'Fitted Spectrum'.
        title (str, optional): Title for the entire figure. Defaults to None.
        xlabel (str, optional): Label for the x-axis, shared by both subplots. Defaults to None.
        plotParameters (argparse.Namespace, optional): A namespace containing parameters for plotting and data processing. The namespace includes:

            - deadtime (float): The dead time before the FID acquisition starts.
            - lb (float): Line broadening factor in Hz.
            - sw (float): Spectral width in Hz.
            - xlim (tuple of float): Limits for the x-axis in ppm, for example, (10, -20).
            - ifphase (bool): turn on 0th and 1st order phasing.

          filename (str or None, optional): If provided, the figure will be saved to this file. Defaults to None.
    """
    # print(f"{xlim=}")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    plot_fit(ax1, fid, fid_fit, ppm, xlim, mode, label, plotParameters=plotParameters)
    preview_HSVD(ax2, hsvdarr, ppm, p_pd, xlim)
    plt.tight_layout()
    plt.suptitle(title)
    plt.xlabel(xlabel)
    if filename is not None:
        plt.savefig(filename)
    plt.show()

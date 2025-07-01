import base64
import io
import os
import sys
import tempfile
from copy import deepcopy
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st
from scipy.io import savemat

import pyAMARES

st.set_page_config(page_title="PyAMARES Web Interface", layout="wide")


def apply_custom_css():
    """Apply custom CSS styling for better appearance"""
    st.markdown(
        """
    <style>
    /* Style for parameter sections */
    .parameter-section {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def get_download_link(file_path, link_text):
    """Generate a download link for a file"""
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{os.path.basename(file_path)}">{link_text}</a>'
    return href


def get_download_link_data(data, filename, link_text):
    """Generate a download link for data"""
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">{link_text}</a>'


def display_editable_pk(pk_file):
    """Display and allow editing of the prior knowledge file (filter any line with #)"""
    try:
        if pk_file.name.endswith(".csv"):
            # Read the raw content first
            content = pk_file.getvalue().decode("utf-8")
            # Filter out any line containing #
            lines = content.split("\n")
            cleaned_lines = [line for line in lines if "#" not in line]
            cleaned_content = "\n".join(cleaned_lines)
            # Now read with pandas
            df = pd.read_csv(io.StringIO(cleaned_content))
        elif pk_file.name.endswith(".xlsx"):
            df = pd.read_excel(pk_file)
            # For Excel files, still need to clean afterwards
            df = clean_dataframe(df)

        # Display the editable dataframe using st.data_editor
        st.write("Prior Knowledge File Content (Editable):")
        st.info(
            "Note: Comment rows (containing #) are automatically filtered out and won't be shown in the editor."
        )

        # Use data_editor with the configuration
        updated_df = st.data_editor(
            df,
            column_config=None,
            num_rows="dynamic",
            height=400,
            key="pk_editor",
        )

        # Add buttons to save changes or export
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Apply Changes"):
                st.session_state.pk_dataframe = updated_df
                st.success("Changes will be used!")
                return updated_df

        with col2:
            # Create a download link for the updated data
            if st.button("Export Modified PK Data"):
                csv = updated_df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="modified_pk_data.csv">Download Modified PK Data as CSV</a>'
                st.markdown(href, unsafe_allow_html=True)

        # Store the dataframe in session state if it doesn't exist yet
        if "pk_dataframe" not in st.session_state:
            st.session_state.pk_dataframe = updated_df

        return updated_df
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None


def clean_dataframe(df):
    """
    Clean a dataframe by removing rows where any column contains #
    (This is mainly for Excel files)
    """
    if len(df) > 0:
        # Create a mask to filter out rows containing # in any column
        mask = ~df.astype(str).apply(
            lambda row: row.str.contains("#", na=False).any(), axis=1
        )
        df = df[mask]
        df.reset_index(drop=True, inplace=True)

    return df


def perturb_value(value, percentage=5):
    """Apply random perturbation to a value"""
    percentage = float(percentage)
    factor = np.random.uniform(1 - percentage / 100, 1 + percentage / 100)
    return value * factor


def perturb_table(
    inputparams, percentage=5, freq_shift=5, phase_shift=0, extra_freq_drift=0
):
    """Apply perturbation to parameter table"""
    params = deepcopy(inputparams)
    all_deltas = {}

    for i in params:
        original_value = params[i].value

        if params[i].name.startswith("ak") or params[i].name.startswith("dk"):
            params[i].value = perturb_value(params[i].value, percentage)
            all_deltas[params[i].name] = params[i].value - original_value

        elif params[i].name.startswith("freq"):
            freq_random_shift = np.random.uniform(-freq_shift, freq_shift)
            params[i].value += extra_freq_drift
            params[i].value += freq_random_shift
            all_deltas[params[i].name] = extra_freq_drift + freq_random_shift

        elif params[i].name.startswith("phi"):
            phase_random_shift = np.random.uniform(
                -np.deg2rad(phase_shift), np.deg2rad(phase_shift)
            )
            params[i].value += phase_random_shift
            all_deltas[params[i].name] = phase_random_shift

    # Find the ak parameter with the biggest absolute value
    ak_deltas = {k: v for k, v in all_deltas.items() if k.startswith("ak")}
    biggest_ak_name = max(ak_deltas.items(), key=lambda x: abs(x[1]))[0]

    # Extract the suffix (e.g., "BATP" from "ak_BATP")
    suffix = biggest_ak_name.split("_", 1)[1]

    # Create simplified deltas for this parameter group
    deltas = {}
    for param_type in ["ak", "dk", "freq", "phi"]:
        param_name = f"{param_type}_{suffix}"
        if param_name in all_deltas:
            deltas[param_type] = all_deltas[param_name]

    return params, deltas


def save_fid_matlab(fid_data, filename):
    """Save FID data in MATLAB format using mat73"""
    try:
        # Prepare data dictionary for MATLAB
        matlab_data = {
            "fid": fid_data,
            "Description": "Simulated FID data from pyAMARES",
        }

        # Save using mat73
        savemat(filename, matlab_data)
        return True
    except Exception as e:
        st.error(f"Error saving MATLAB file: {str(e)}")
        return False


def plot_drift_arrays(ak_arr, dk_arr, freq_arr, phase_arr):
    """Plot 4 drift arrays in a 2x2 grid"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    # Convert phase from radians to degrees
    phase_deg_arr = np.rad2deg(phase_arr)

    # Data and labels for each subplot
    data = [ak_arr, dk_arr, freq_arr, phase_deg_arr]
    ylabels = [
        "Amplitude Drift",
        "LW Drift(Hz)",
        "Freq Drift (Hz)",
        "Phase Drift (Deg)",
    ]

    # Create x-axis (scan numbers)
    x = np.arange(len(ak_arr))

    # Plot each array
    for i, (ax, y_data, ylabel) in enumerate(zip(axes.flat, data, ylabels)):
        ax.plot(x, y_data, "o-", linewidth=1, markersize=3)
        ax.set_xlabel("Scan Number")
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def generate_spectrum_preview(
    fid, sw, mhz, indsignal_start=0, indsignal_end=10, pts_noise=200, xlim=None
):
    """Generate a preview plot of the spectrum

    Parameters:
    -----------
    fid : array_like
        1D or 2D FID data. If 2D, first dimension is number of scans
    sw : float
        Spectral width in Hz
    mhz : float
        Spectrometer frequency in MHz
    indsignal_start : int
        Start index for SNR calculation
    indsignal_end : int
        End index for SNR calculation
    pts_noise : int
        Number of points from end for noise estimation
    xlim : tuple, optional
        Chemical shift limits for x-axis

    Returns:
    --------
    fig : matplotlib.figure.Figure
        Figure object containing the plots
    """
    import pyAMARES

    # Check if fid is 1D or 2D
    if fid.ndim == 1:
        # 1D case - original behavior
        fids_to_plot = [fid]
        scan_indices = [0]
        is_multiscan = False
    else:
        # 2D case - first dimension is number of scans
        n_scans = fid.shape[0]
        is_multiscan = True

        if n_scans <= 10:
            # Plot all scans
            scan_indices = list(range(n_scans))
        else:
            # Select every Nth scan to get ~10 total
            step = max(1, n_scans // 10)
            scan_indices = list(range(0, n_scans, step))[:10]

        fids_to_plot = [fid[i] for i in scan_indices]

    # Create figure with appropriate number of subplots
    if is_multiscan:
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
    else:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # Collect SNR values for title
    snr_values = []

    # For averaging (multiscan case)
    if is_multiscan:
        averaged_fid = np.mean([fid[i] for i in scan_indices], axis=0)

    # Process and plot each FID
    for idx, (current_fid, scan_idx) in enumerate(zip(fids_to_plot, scan_indices)):
        # Fourier transform
        spectrum = np.fft.fftshift(np.fft.fft(current_fid))

        # Create frequency axis
        n_points = len(current_fid)
        freq = np.linspace(-sw / 2, sw / 2, n_points)
        ppm = freq / mhz

        # Calculate SNR using the provided parameters
        snr = pyAMARES.fidSNR(
            current_fid, indsignal=(indsignal_start, indsignal_end), pts_noise=pts_noise
        )
        snr_values.append(snr)

        # Create labels for real and magnitude plots
        if is_multiscan:
            label_real = f"Scan {scan_idx + 1} (SNR: {snr:.1f})"
            label_mag = f"Scan {scan_idx + 1}"
            alpha = 0.7
        else:
            label_real = f"SNR: {snr:.1f}"
            label_mag = "Spectrum"
            alpha = 1.0

        # Plot real part of spectrum
        ax1.plot(ppm, spectrum.real, label=label_real, alpha=alpha)

        # Plot magnitude spectrum
        ax2.plot(ppm, np.abs(spectrum), label=label_mag, alpha=alpha)

    # Configure first two axes
    ax1.set_xlabel("Chemical Shift (ppm)")
    ax1.set_ylabel("Real Part")

    # Create informative title
    if is_multiscan:
        mean_snr = np.mean(snr_values)
        std_snr = np.std(snr_values)
        title_real = f"Individual Scans - Real Part ({len(fids_to_plot)} selected scans, SNR: {mean_snr:.1f}±{std_snr:.1f})"
        title_mag = f"Individual Scans - Magnitude ({len(fids_to_plot)} selected scans)"
    else:
        title_real = f"Simulated Spectrum - Real Part (SNR: {snr_values[0]:.1f})"
        title_mag = "Simulated Spectrum - Magnitude"

    ax1.set_title(title_real)
    ax1.invert_xaxis()
    if xlim:
        ax1.set_xlim(xlim)
    ax1.grid(True, alpha=0.3)

    # Only show legend if not too many scans (to avoid clutter)
    if len(fids_to_plot) <= 5:
        ax1.legend()

    ax2.set_xlabel("Chemical Shift (ppm)")
    ax2.set_ylabel("Magnitude")
    ax2.set_title(title_mag)
    ax2.invert_xaxis()
    if xlim:
        ax2.set_xlim(xlim)
    ax2.grid(True, alpha=0.3)

    # Only show legend if not too many scans
    if len(fids_to_plot) <= 5:
        ax2.legend()

    # Add averaged spectrum plot for multiscan data
    if is_multiscan:
        # Process averaged FID
        averaged_spectrum = np.fft.fftshift(np.fft.fft(averaged_fid))
        n_points = len(averaged_fid)
        freq = np.linspace(-sw / 2, sw / 2, n_points)
        ppm = freq / mhz

        # Calculate SNR for averaged spectrum
        averaged_snr = pyAMARES.fidSNR(
            averaged_fid,
            indsignal=(indsignal_start, indsignal_end),
            pts_noise=pts_noise,
        )

        # Plot both real and magnitude on the same axis
        ax3.plot(
            ppm,
            averaged_spectrum.real,
            "b-",
            label=f"Real (SNR: {averaged_snr:.1f})",
            linewidth=1.5,
        )
        ax3.plot(ppm, np.abs(averaged_spectrum), "r-", label="Magnitude", linewidth=1.5)

        ax3.set_xlabel("Chemical Shift (ppm)")
        ax3.set_ylabel("Signal Intensity")
        ax3.set_title(f"Averaged Spectrum (SNR: {averaged_snr:.1f})")
        ax3.invert_xaxis()
        if xlim:
            ax3.set_xlim(xlim)
        ax3.grid(True, alpha=0.3)
        ax3.legend()

    plt.tight_layout()
    return fig


def main():
    st.title(f"PyAMARES: MRS Data Analysis Web Interface\n v{pyAMARES.__version__}")

    # Apply custom styling
    apply_custom_css()

    # Add a separator
    st.markdown("---")

    # Create an info box with better formatting
    with st.container():
        st.info("""
        ### About pyAMARES

        This is a web interface for [pyAMARES](https://github.com/HawkMRS/pyAMARES), an open-source Python library for fitting magnetic resonance spectroscopy (MRS) data.

        We recommend using pyAMARES in Jupyter notebooks or Python scripts for more advanced features and flexibility.

        For more information, please visit the [pyAMARES documentation](https://pyamares.readthedocs.io/en/dev/).
        """)

    # Mode selection section FIRST
    st.markdown("---")
    st.header("Mode")

    # Create the mode selection section
    analysis_mode = st.radio(
        "Select Mode:",
        ["AMARES Fitting", "Simple FID Simulation"],
        index=0,
        help="Choose between AMARES Fitting or simulating FID data",
    )

    # Convert to boolean for backward compatibility
    simulation_mode = analysis_mode == "Simple FID Simulation"

    # Demo section AFTER mode selection
    demo_col1, demo_col2 = st.columns([3, 1])
    with demo_col1:
        if analysis_mode == "AMARES Fitting":
            st.write(
                "New to PyAMARES? Try the demo mode to see how AMARES fitting works with sample FID and Prior Knowledge data."
            )
        else:  # FID Simulation
            st.write(
                "Try the demo mode to see how FID simulation works with sample Prior Knowledge data."
            )
    with demo_col2:
        demo_button = st.button("Try Demo Mode", type="primary")

    # Add this section to handle the button click
    if demo_button:
        st.session_state.demo_mode = True
        if analysis_mode == "AMARES Fitting":
            st.success(
                "Demo mode activated! Example FID and Prior Knowledge files will be loaded automatically."
            )
        else:  # FID Simulation
            st.success(
                "Demo mode activated! Example Prior Knowledge file will be loaded automatically for simulation."
            )
        st.markdown("---")
        st.rerun()  # This forces a rerun to apply the demo mode changes

    # GitHub raw URLs for the example files
    GITHUB_RAW_BASE_URL = "https://raw.githubusercontent.com/HawkMRS/pyAMARES/main"
    FID_EXAMPLE_URL = f"{GITHUB_RAW_BASE_URL}/pyAMARES/examples/fid.txt"
    PK_EXAMPLE_URL = (
        f"{GITHUB_RAW_BASE_URL}/pyAMARES/examples/example_human_brain_31P_7T.csv"
    )

    # Function to load file from GitHub raw URL
    def load_file_from_github(url):
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            st.error(
                f"Failed to load demo file from {url}. Status code: {response.status_code}"
            )
            return None

    # Initialize session state for storing dataframes and processing status
    if "pk_dataframe" not in st.session_state:
        st.session_state.pk_dataframe = None
    if "processing_complete" not in st.session_state:
        st.session_state.processing_complete = False

    # File uploads section
    st.header("📁 Input Files")

    # Prior Knowledge File Upload (always needed)
    st.subheader("Prior Knowledge File")
    if "demo_mode" in st.session_state and st.session_state.demo_mode:
        pk_file = st.file_uploader(
            "Upload Prior Knowledge file or use the demo file",
            type=["csv", "xlsx"],
        )
        if pk_file is None:
            # Load PK file from GitHub
            pk_content = load_file_from_github(PK_EXAMPLE_URL)
            if pk_content is not None:
                pk_file = BytesIO(pk_content)
                pk_file.name = "demo_pk.csv"
                st.info("Using demo Prior Knowledge file: demo_pk.csv")
    else:
        pk_file = st.file_uploader(
            "Upload [Prior Knowledge file]"
            "(https://pyamares.readthedocs.io/en/dev/notebooks/priorknowledge.html) "
            " (CSV, XLSX)",
            type=["csv", "xlsx"],
        )
    st.markdown(
        "Please read the "
        "[prior knowledge tutorial]"
        "(https://pyamares.readthedocs.io/en/dev/notebooks/priorknowledge.html) "
        "for how to create and edit a prior knowledge file."
    )

    # Set default parameter values if in demo mode (only for AMARES fitting mode)
    if (
        not simulation_mode
        and "demo_mode" in st.session_state
        and st.session_state.demo_mode
    ):
        # Add guided instructions for demo mode
        with st.expander("Demo Mode Guide", expanded=True):
            st.markdown("""
            ### Getting Started - A Simple Example

            You're now using PyAMARES with sample 31P MRS data at 7T. Here's what's happening:

            1. We've loaded a sample **FID (Free Induction Decay)** file and a **Prior Knowledge** file directly from the PyAMARES GitHub repository
            2. Default parameters have been set appropriate for this data:
            - Field strength: 120.0 MHz (appropriate for 31P at 7T)
            - Spectral width: 10,000 Hz
            - Dead time: 300 microseconds

            3. **Next Steps:**
            - Examine the Prior Knowledge file data (it's editable!)
            - Click "Start AMARES Fitting" to run the analysis
            - View and download the results below after processing

            """)

        # Add exit demo mode button for AMARES fitting mode
        if st.button("Exit Demo Mode", type="primary"):
            if "demo_mode" in st.session_state:
                del st.session_state.demo_mode
            st.rerun()

    # Display and make PK file editable immediately when uploaded
    if pk_file is not None:
        pk_dataframe = display_editable_pk(pk_file)

    # FID Data Upload (only for AMARES fitting)
    if not simulation_mode:
        st.subheader("FID Data")
        if "demo_mode" in st.session_state and st.session_state.demo_mode:
            fid_file = st.file_uploader(
                "Upload FID file or use the demo file", key="analysis_fid"
            )
            if fid_file is None:
                # Load FID file from GitHub
                fid_content = load_file_from_github(FID_EXAMPLE_URL)
                if fid_content is not None:
                    fid_file = BytesIO(fid_content)
                    fid_file.name = "demo_fid.txt"
                    st.info("Using demo FID file: demo_fid.txt")
        else:
            fid_file = st.file_uploader(
                "Upload FID file (e.g., CSV, TXT, NPY, or Matlab), "
                "[File I/O Instruction](https://pyamares.readthedocs.io/en/dev/fileio.html)",
                key="analysis_fid",
            )
    else:
        st.subheader("FID Simulation Mode")
        st.info(
            "**Simulation Mode Active**: Generate synthetic FID data from prior knowledge parameters"
        )
        fid_file = None

    # Core MRS Parameters (shared between both modes)
    st.markdown("---")
    st.header("Basic FID Parameters")
    st.markdown("*These parameters are used by both AMARES fitting and FID simulation*")

    col1, col2, col3 = st.columns(3)
    with col1:
        mhz = st.number_input(
            "Field strength (MHz)", value=120.0, format="%.1f", key="shared_mhz"
        )
    with col2:
        sw = st.number_input(
            "Spectral width (Hz)", value=10000.0, format="%.1f", key="shared_sw"
        )
    with col3:
        deadtime = st.number_input(
            "Dead time (seconds)",
            value=300e-6
            if "demo_mode" in st.session_state and st.session_state.demo_mode
            else 0.0,
            format="%.2e",
            help="The dead time or begin time in seconds before the FID signal starts",
            key="shared_deadtime",
        )

    # Mode-specific parameters and processing
    st.markdown("---")

    if not simulation_mode:
        # AMARES FITTING MODE
        st.header("Basic Fitting Parameters")

        # Check if processing is complete and show notification
        if st.session_state.processing_complete:
            st.success("Analysis Complete! Results are available below.")

        # Analysis-specific parameters
        with st.container():
            st.markdown('<div class="parameter-section">', unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                truncate_initial_points = st.number_input(
                    "Truncate initial points",
                    value=0,
                    min_value=0,
                    help="Truncate initial points from FID to remove fast decaying "
                    "components (e.g. macromolecule). This usually makes baseline more flat.",
                )
            with col2:
                g_global = st.number_input(
                    "Global g parameter",
                    value=0.0,
                    format="%.2f",
                    help="Global value for the `g` lineshape parameter. "
                    "Defaults to 0.0 (Lorentzian). If set to False, the g values "
                    "specified in the prior knowledge will be used.",
                )
            with col3:
                options = {
                    "least_squares": "Trust Region Reflective (least_squares) ",
                    "leastsq": "Levenberg–Marquardt (leastsq)",
                }
                method = st.selectbox(
                    "Fitting method",
                    options=list(options.keys()),
                    index=0,
                    format_func=lambda x: options[x],
                    help="leatsq is faster, least_squares is better",
                )
            with col4:
                output_prefix = st.text_input(
                    "Output file prefix",
                    value="simple_example"
                    if "demo_mode" in st.session_state and st.session_state.demo_mode
                    else "amares_results",
                )

            col5, col6, col7 = st.columns([4, 2, 2])
            with col5:
                initialize_with_lm = st.checkbox(
                    "Initialize Fitting Parameters with Levenberg-Marquardt method",
                    value=True,
                    help="If True, a Levenberg-Marquardt initializer (least_sq) is executed internally.",
                )
            with col6:
                flip_axis = st.checkbox(
                    "Flip Spectrum Axis",
                    help="If True, flip the FID axis by taking the complex conjugate.",
                )
            with col7:
                normalize_fid = st.checkbox(
                    "Normalize FID data", help="If True, normalize the FID data."
                )

            st.markdown("</div>", unsafe_allow_html=True)

        # Advanced options for analysis (foldable section)
        with st.expander("Advanced Options", expanded=False):
            adv_col1, adv_col2 = st.columns([3, 1])
            with adv_col1:
                st.write("Advanced Fitting Options")
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    scale_amplitude = st.number_input(
                        "Scale amplitude",
                        value=1.0,
                        format="%.2f",
                        help="Scaling factor applied to the amplitude parameters loaded "
                        "from priorknowledgefile. Useful when prior knowledge amplitudes "
                        "significantly differ from the FID amplitude. Defaults to 1.0 "
                        "(no scaling).",
                    )
                    delta_phase = st.number_input(
                        "Additional phase shift (degrees)",
                        value=0.0,
                        format="%.1f",
                        help="Additional phase shift (in degrees) to be applied to the "
                        "prior knowledge phase values. Defaults to 0.0",
                    )
                    st.markdown(
                        "[Initialize the fitting parameters]"
                        "(https://pyamares.readthedocs.io/en/dev/"
                        "notebooks/HSVDinitializer_unknowncompounds.html) "
                        "with HSVD",
                        help="If checked, the prior knowledge file will be ignored "
                        "and peaks will be numbered automatically using HSVD ",
                    )
                    use_hsvd = st.checkbox("Use HSVD for initial parameters")
                with sub_col2:
                    carrier = st.number_input(
                        "Carrier frequency (ppm)",
                        value=0.0,
                        format="%.2f",
                        help="carrier frequency in ppm, often used for water (4.7 ppm) "
                        "or other reference metabolite such as Phosphocreatine "
                        "(0 ppm).",
                    )
                    ppm_offset = st.number_input(
                        "PPM offset",
                        value=0.0,
                        format="%.2f",
                        help=" Adjust the ppm in `priorknowledgefile`. Default 0 ppm",
                    )
                    if use_hsvd:
                        num_of_component = st.number_input(
                            "Number of components for HSVD",
                            value=12,
                            min_value=1,
                            help="Number of components to decompose the FID into.",
                        )
            with adv_col2:
                st.write("Visualization Options")
                ifphase = st.checkbox(
                    "Phase the spectrum",
                    help="Turn on 0th and 1st "
                    "order phasing for **visualization**. This does not "
                    "affect the fitting.",
                )
                lb = st.number_input(
                    "Line Broadening factor (Hz)",
                    value=2.0,
                    format="%.1f",
                    help="Line broadening parameter in Hz, used for spectrum "
                    "**visualization** only. Defaults to 2.0.",
                )
                use_custom_xlim = st.checkbox(
                    "Use custom X-axis limits",
                    value=True
                    if "demo_mode" in st.session_state and st.session_state.demo_mode
                    else False,
                )

                # Show slider only if checkbox is checked and set xlim accordingly
                if use_custom_xlim:
                    x_min, x_max = st.slider(
                        "Display X-axis range (ppm)",
                        help="The x-axis limits for the **visualization** of spectrum in ppm. "
                        "This does not affect the fitting.",
                        min_value=-50.0,
                        max_value=50.0,
                        value=(-20.0, 10.0),  # Default values (min, max)
                        step=0.5,
                        format="%.1f",
                    )
                    xlim = (x_max, x_min)  # Inverted for MRS convention
                else:
                    # Disable custom limits
                    xlim = None

        # Process button for AMARES
        if fid_file is None:
            st.info("Please upload a FID file to begin.")
        else:
            process_button = st.button(
                "Start AMARES Fitting", type="primary", key="process_analysis"
            )

            # Process data when the button is clicked and files are uploaded
            if process_button:
                # Set the processing flag to indicate we're starting
                st.session_state.processing_complete = False

                with st.spinner("Processing data..."):
                    # Create temporary files for the uploads
                    fid_file_extension = os.path.splitext(fid_file.name)[1]
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=fid_file_extension
                    ) as tmp_fid:
                        tmp_fid.write(fid_file.getvalue())
                        fid_path = tmp_fid.name

                    pk_path = None
                    # Check if we have edited pk data in session state
                    if st.session_state.pk_dataframe is not None:
                        # Create a temporary file from the edited dataframe
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".csv"
                        ) as tmp_pk:
                            st.session_state.pk_dataframe.to_csv(
                                tmp_pk.name, index=False
                            )
                            pk_path = tmp_pk.name
                    elif pk_file is not None:
                        # Use the uploaded file if no edits
                        file_extension = os.path.splitext(pk_file.name)[1]
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=file_extension
                        ) as tmp_pk:
                            tmp_pk.write(pk_file.getvalue())
                            pk_path = tmp_pk.name

                    try:
                        # Read FID data
                        fid = pyAMARES.readmrs(fid_path)

                        # Initialize FID
                        FIDobj = pyAMARES.initialize_FID(
                            fid,
                            priorknowledgefile=pk_path,
                            MHz=mhz,
                            sw=sw,
                            deadtime=deadtime,
                            normalize_fid=normalize_fid,
                            scale_amplitude=scale_amplitude,
                            flip_axis=flip_axis,
                            preview=False,  # We'll handle visualization in Streamlit
                            carrier=carrier,
                            xlim=xlim,
                            ppm_offset=ppm_offset,
                            g_global=g_global,
                            delta_phase=delta_phase,
                            truncate_initial_points=truncate_initial_points,
                        )

                        # Use HSVD initializer if selected
                        if use_hsvd:
                            fitting_parameters = pyAMARES.HSVDinitializer(
                                fid_parameters=FIDobj,
                                num_of_component=num_of_component,
                                preview=False,  # We'll handle visualization in Streamlit
                            )
                        else:
                            fitting_parameters = FIDobj.initialParams

                        # Fitting
                        out1 = pyAMARES.fitAMARES(
                            fid_parameters=FIDobj,
                            fitting_parameters=fitting_parameters,
                            method=method,
                            ifplot=False,
                            inplace=False,
                            initialize_with_lm=initialize_with_lm,
                        )

                        # Save results to temporary files
                        temp_dir = tempfile.mkdtemp()
                        csv_path = os.path.join(temp_dir, f"{output_prefix}.csv")
                        html_path = os.path.join(temp_dir, f"{output_prefix}.html")
                        svg_path = os.path.join(temp_dir, f"{output_prefix}.svg")

                        # Save results
                        if use_hsvd:
                            out1.result_multiplets.to_csv(csv_path)
                        else:
                            out1.result_sum.to_csv(csv_path)

                        if sys.version_info >= (3, 7):
                            out1.styled_df.to_html(html_path)

                        # Set plot parameters and generate plot
                        out1.plotParameters.ifphase = ifphase
                        out1.plotParameters.lb = lb
                        pyAMARES.plotAMARES(fid_parameters=out1, filename=svg_path)

                        # Set the processing complete flag
                        st.session_state.processing_complete = True

                        # Display success message
                        st.success("Complete! Fitting results are ready below.")

                        # Display a divider
                        st.markdown("---")

                        # Results display section
                        st.header("Analysis Results")

                        # Reorder display elements - table first, then fitted spectrum
                        # Display the result table
                        st.subheader("Fitting Results")
                        if use_hsvd:
                            st.dataframe(
                                pyAMARES.highlight_dataframe(out1.result_multiplets)
                            )
                        else:
                            st.dataframe(out1.simple_df)

                        # Create download links
                        st.subheader("Download Results")

                        st.markdown(
                            get_download_link(csv_path, "Download CSV Results"),
                            unsafe_allow_html=True,
                        )

                        if sys.version_info >= (3, 7):
                            st.markdown(
                                get_download_link(html_path, "Download HTML Report"),
                                unsafe_allow_html=True,
                            )

                        st.markdown(
                            get_download_link(svg_path, "Download SVG Plot"),
                            unsafe_allow_html=True,
                        )

                        # Add expander for fitted spectrum to save space
                        with st.expander("View Fitted Spectrum", expanded=True):
                            with open(svg_path, "rb") as f:
                                svg_content = f.read()
                                # Use a container with scrolling to prevent the SVG from being hidden
                                st.components.v1.html(
                                    svg_content, height=800, scrolling=True
                                )

                        # Clean up temporary files
                        os.unlink(fid_path)
                        if pk_path:
                            os.unlink(pk_path)

                    except Exception as e:
                        st.error(f"An error occurred during processing: {str(e)}")

                        # Clean up temporary files
                        if "fid_path" in locals():
                            os.unlink(fid_path)
                        if "pk_path" in locals() and pk_path:
                            os.unlink(pk_path)

    else:
        # FID SIMULATION MODE
        st.header("FID Simulation Parameters")

        # Initialize freq_drift as it will be used in perturbation logic
        freq_drift = 0.0

        with st.container():
            # Simulation mode selection
            sim_mode = st.radio(
                "Simulation Mode",
                ["Batch Simulation", "Multiple Transients", "Single FID"],
                horizontal=True,
            )

            # Common simulation parameters
            col1, col2, col3 = st.columns(3)
            with col1:
                sim_fid_len = st.number_input(
                    "Number of points",
                    value=1024,
                    min_value=128,
                    max_value=8192,
                    step=128,
                    key="sim_fid_len",
                    help="Length of the simulated FID",
                )

            with col2:
                sim_filename = st.text_input(
                    "Output filename prefix",
                    value="simulated_fid",
                    key="sim_filename",
                    help="Base name for generated files",
                )

            with col3:
                extra_line_broadening = st.number_input(
                    "Extra line broadening (Hz)",
                    value=0.0,
                    min_value=0.0,
                    max_value=100.0,
                    format="%.1f",
                    key="extra_line_broadening",
                    help="Additional line broadening to apply to all peaks in Hz",
                )

        # Mode-specific parameters
        if sim_mode == "Single FID":
            col1, col2 = st.columns(2)
            with col1:
                sim_snr = st.number_input(
                    "Target SNR",
                    value=20.0,
                    min_value=0.0,
                    max_value=1000.0,
                    format="%.1f",
                    key="single_snr",
                    help="Target signal-to-noise ratio. Set to 0 for no noise.",
                )

        elif sim_mode == "Batch Simulation":
            col1, col2 = st.columns(2)
            with col1:
                num_simulations = st.number_input(
                    "Number of simulations",
                    value=10,
                    min_value=2,
                    max_value=1000,
                    help="Number of FIDs to generate",
                )
            with col2:
                batch_snr = st.number_input(
                    "Target SNR for each spectrum in the batch",
                    value=20.0,
                    min_value=0.0,
                    max_value=1000.0,
                    format="%.1f",
                    key="batch_snr",
                    help="SNR for each simulation",
                )

        else:  # Multiple Transients
            col1, col2, col3 = st.columns(3)
            with col1:
                num_transients = st.number_input(
                    "Number of transients",
                    value=32,
                    min_value=2,
                    max_value=10000,
                    help="Number of transients to average",
                )
            with col2:
                transient_snr = st.number_input(
                    "SNR per transient",
                    value=2.0,
                    min_value=0.0,
                    max_value=1000.0,
                    format="%.1f",
                    key="transient_snr",
                    help="SNR for each individual transient",
                )
            with col3:
                st.metric(
                    "Expected final SNR",
                    f"{transient_snr * np.sqrt(num_transients):.1f}",
                    help="SNR improves with √N for N transients",
                )

            # Add output format selection for Multiple Transients mode
            st.subheader("Output Format")
            output_format = st.radio(
                "Choose output format:",
                ["Averaged FID (1D)", "All Transients (2D)"],
                index=0,
                help="Choose whether to output averaged FID or all individual transients",
            )

        # Advanced Simulation Options
        st.subheader("Advanced Simulation Options")
        adv_col1, adv_col2 = st.columns(2)
        with adv_col1:
            indsignal_start = st.number_input(
                "Signal region start",
                value=0,
                min_value=0,
                help="Start index for SNR calculation",
            )
            indsignal_end = st.number_input(
                "Signal region end",
                value=10,
                min_value=1,
                help="End index for SNR calculation",
            )
        with adv_col2:
            pts_noise = st.number_input(
                "Noise points from the end of the FID",
                value=200,
                min_value=50,
                help="Number of points for noise estimation",
            )
            show_preview = st.checkbox(
                "Show spectrum preview",
                value=True,
                help="Display the simulated spectrum",
            )

        # Parameter Perturbation (foldable section) - IMPROVED LAYOUT
        st.subheader("Parameter Perturbation")
        with st.expander("Parameter Perturbation", expanded=False):
            # First row: Enable perturbation, Amplitude variation, Phase variation
            perturb_col1, perturb_col2, perturb_col3 = st.columns(3)

            with perturb_col1:
                use_perturbation = st.checkbox(
                    "Enable perturbation",
                    value=False,
                    help="Add random variations to parameters",
                )

            with perturb_col2:
                amp_perturb = st.number_input(
                    "Amplitude variation (%)",
                    value=1.0,
                    min_value=0.0,
                    max_value=50.0,
                    format="%.1f",
                    disabled=not use_perturbation,
                    help="Random variation in peak amplitudes",
                )

            with perturb_col3:
                phase_perturb = st.number_input(
                    "Phase variation (degrees)",
                    value=0.0,
                    min_value=0.0,
                    max_value=180.0,
                    format="%.1f",
                    disabled=not use_perturbation,
                    help="Random phase variations",
                )

            # Second row: Frequency variation and Frequency drift
            freq_col1, freq_col2, freq_col3 = st.columns(3)

            with freq_col2:
                freq_perturb = st.number_input(
                    "Frequency variation (Hz)",
                    value=10.0,
                    min_value=0.0,
                    max_value=100.0,
                    format="%.1f",
                    disabled=not use_perturbation,
                    help="Random frequency variations",
                )

            # Frequency drift parameter (only for Batch Simulation and Multiple Transients)
            if sim_mode in ["Batch Simulation", "Multiple Transients"]:
                if sim_mode == "Batch Simulation":
                    drift_label = "Frequency drift along the number of scans (Hz)"
                else:  # Multiple Transients
                    drift_label = "Frequency drift along the number of transients (Hz)"

                with freq_col3:
                    freq_drift = st.number_input(
                        drift_label,
                        value=0.0,
                        min_value=-500.0,
                        max_value=500.0,
                        format="%.1f",
                        help="Frequency drift (Hz) applied linearly across scans/transients",
                    )
            else:
                freq_drift = 0.0  # Default for Single FID mode

        # Simulation button
        simulate_button = st.button("Generate Simulated FID", type="primary")

        if simulate_button:
            if pk_file is None:
                st.error(
                    "Please upload a Prior Knowledge file first to generate simulated FID."
                )
            else:
                with st.spinner("Generating simulated FID..."):
                    try:
                        # Create temporary PK file
                        if st.session_state.pk_dataframe is not None:
                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=".csv"
                            ) as tmp_pk:
                                st.session_state.pk_dataframe.to_csv(
                                    tmp_pk.name, index=False
                                )
                                pk_path_sim = tmp_pk.name
                        else:
                            file_extension = os.path.splitext(pk_file.name)[1]
                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=file_extension
                            ) as tmp_pk:
                                tmp_pk.write(pk_file.getvalue())
                                pk_path_sim = tmp_pk.name

                        # Initialize prior knowledge
                        priorknowledge = pyAMARES.initialize_FID(
                            fid=None,
                            priorknowledgefile=pk_path_sim,
                            MHz=mhz,
                            sw=sw,
                            preview=False,
                        )

                        # Create output directory
                        temp_dir = tempfile.mkdtemp()

                        if sim_mode == "Single FID":
                            # Get parameters
                            params = priorknowledge.initialParams

                            # Apply perturbation if enabled
                            if use_perturbation:
                                params, _ = perturb_table(
                                    params,
                                    percentage=amp_perturb,
                                    freq_shift=freq_perturb,
                                    extra_freq_drift=phase_perturb,
                                )

                            # Generate single FID
                            simulated_fid = pyAMARES.kernel.fid.simulate_fid(
                                params,
                                MHz=mhz,
                                sw=sw,
                                deadtime=deadtime,
                                fid_len=sim_fid_len,
                                snr_target=sim_snr if sim_snr > 0 else None,
                                indsignal=(indsignal_start, indsignal_end),
                                pts_noise=pts_noise,
                                preview=False,
                                extra_line_broadening=extra_line_broadening,
                            )

                            # Save files
                            # ASCII format
                            ascii_path = os.path.join(temp_dir, f"{sim_filename}.txt")
                            np.savetxt(
                                ascii_path,
                                np.column_stack(
                                    (simulated_fid.real, simulated_fid.imag)
                                ),
                                delimiter="\t",
                                header="Real\tImaginary",
                            )

                            # NPY format
                            npy_path = os.path.join(temp_dir, f"{sim_filename}.npy")
                            np.save(npy_path, simulated_fid)

                            # MATLAB format
                            mat_path = os.path.join(temp_dir, f"{sim_filename}.mat")
                            mat_success = save_fid_matlab(simulated_fid, mat_path)

                            st.success("Single FID simulation complete!")

                            # Download links
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown(
                                    get_download_link(
                                        ascii_path, f"Download {sim_filename}.txt"
                                    ),
                                    unsafe_allow_html=True,
                                )
                            with col2:
                                with open(npy_path, "rb") as f:
                                    npy_data = f.read()
                                st.markdown(
                                    get_download_link_data(
                                        npy_data,
                                        f"{sim_filename}.npy",
                                        f"Download {sim_filename}.npy",
                                    ),
                                    unsafe_allow_html=True,
                                )
                            with col3:
                                if mat_success:
                                    with open(mat_path, "rb") as f:
                                        mat_data = f.read()
                                    st.markdown(
                                        get_download_link_data(
                                            mat_data,
                                            f"{sim_filename}.mat",
                                            f"Download {sim_filename}.mat",
                                        ),
                                        unsafe_allow_html=True,
                                    )

                            # Preview
                            if show_preview:
                                fig = generate_spectrum_preview(
                                    simulated_fid,
                                    sw,
                                    mhz,
                                    indsignal_start=indsignal_start,
                                    indsignal_end=indsignal_end,
                                    pts_noise=pts_noise,
                                    xlim=xlim if "xlim" in locals() else None,
                                )
                                st.pyplot(fig)
                                plt.close()

                        elif sim_mode == "Batch Simulation":
                            # Generate batch of FIDs
                            fid_batch = []
                            progress_bar = st.progress(0)
                            if freq_drift != 0:
                                freq_drift_arr = np.linspace(
                                    0, freq_drift, num_simulations
                                )
                            else:
                                freq_drift_arr = np.zeros(num_simulations)

                            phase_drift_arr = np.zeros(num_simulations)
                            ak_drift_arr = np.zeros(num_simulations)
                            dk_drift_arr = np.zeros(num_simulations)

                            for i in range(num_simulations):
                                params = priorknowledge.initialParams

                                # Always apply new perturbation for each simulation
                                if use_perturbation:
                                    params, deltas = perturb_table(
                                        params,
                                        percentage=amp_perturb,
                                        freq_shift=freq_perturb,
                                        phase_shift=phase_perturb,
                                        extra_freq_drift=freq_drift_arr[i],
                                    )

                                    ak_drift_arr[i] = deltas.get("ak", 0.0)
                                    dk_drift_arr[i] = deltas.get("dk", 0.0)
                                    phase_drift_arr[i] = deltas.get("phi", 0.0)
                                    freq_drift_arr[i] = deltas.get(
                                        "freq", freq_drift_arr[i]
                                    )  # Freq has been perturbed here

                                # Generate FID
                                fid = pyAMARES.kernel.fid.simulate_fid(
                                    params,
                                    MHz=mhz,
                                    sw=sw,
                                    deadtime=deadtime,
                                    fid_len=sim_fid_len,
                                    snr_target=batch_snr if batch_snr > 0 else None,
                                    indsignal=(indsignal_start, indsignal_end),
                                    pts_noise=pts_noise,
                                    preview=False,
                                    extra_line_broadening=extra_line_broadening,
                                )

                                fid_batch.append(fid)
                                progress_bar.progress((i + 1) / num_simulations)

                            # Convert to numpy array
                            fid_batch = np.array(fid_batch)

                            # Save batch files (NPY and MATLAB only)
                            npy_batch_path = os.path.join(
                                temp_dir, f"{sim_filename}_batch.npy"
                            )
                            np.save(npy_batch_path, fid_batch)

                            mat_batch_path = os.path.join(
                                temp_dir, f"{sim_filename}_batch.mat"
                            )
                            mat_success = save_fid_matlab(fid_batch, mat_batch_path)

                            st.success(
                                f"Batch simulation complete! Generated {num_simulations} FIDs."
                            )

                            # Download links
                            col1, col2 = st.columns(2)
                            with col1:
                                with open(npy_batch_path, "rb") as f:
                                    npy_data = f.read()
                                st.markdown(
                                    get_download_link_data(
                                        npy_data,
                                        f"{sim_filename}_batch.npy",
                                        "Download Batch NPY",
                                    ),
                                    unsafe_allow_html=True,
                                )
                            with col2:
                                if mat_success:
                                    with open(mat_batch_path, "rb") as f:
                                        mat_data = f.read()
                                    st.markdown(
                                        get_download_link_data(
                                            mat_data,
                                            f"{sim_filename}_batch.mat",
                                            "Download Batch MAT",
                                        ),
                                        unsafe_allow_html=True,
                                    )

                            # Preview first FID
                            if show_preview:
                                st.subheader("Preview (First FID in batch)")
                                fig = generate_spectrum_preview(
                                    fid_batch,
                                    sw,
                                    mhz,
                                    indsignal_start=indsignal_start,
                                    indsignal_end=indsignal_end,
                                    pts_noise=pts_noise,
                                    xlim=xlim if "xlim" in locals() else None,
                                )
                                st.pyplot(fig)
                                plt.close()

                                # Only show drift plots if perturbation is enabled
                                if use_perturbation:
                                    st.subheader("Perturbed Parameters")
                                    fig2 = plot_drift_arrays(
                                        ak_drift_arr,
                                        dk_drift_arr,
                                        freq_drift_arr,
                                        phase_drift_arr,
                                    )
                                    st.pyplot(fig2)
                                    plt.close()

                        else:  # Multiple Transients
                            # Generate and average transients
                            transients = []
                            progress_bar = st.progress(0)

                            if freq_drift != 0:
                                freq_drift_arr = np.linspace(
                                    0, freq_drift, num_transients
                                )
                            else:
                                freq_drift_arr = np.zeros(num_transients)

                            phase_drift_arr = np.zeros(num_transients)
                            ak_drift_arr = np.zeros(num_transients)
                            dk_drift_arr = np.zeros(num_transients)

                            for i in range(num_transients):
                                params = priorknowledge.initialParams

                                # Apply perturbation if enabled
                                if use_perturbation:
                                    params, deltas = perturb_table(
                                        params,
                                        percentage=amp_perturb,
                                        freq_shift=freq_perturb,
                                        phase_shift=phase_perturb,
                                        extra_freq_drift=freq_drift_arr[i],
                                    )

                                    ak_drift_arr[i] = deltas.get("ak", 0.0)
                                    dk_drift_arr[i] = deltas.get("dk", 0.0)
                                    phase_drift_arr[i] = deltas.get("phi", 0.0)
                                    freq_drift_arr[i] = deltas.get(
                                        "freq", freq_drift_arr[i]
                                    )

                                # Generate transient
                                fid = pyAMARES.kernel.fid.simulate_fid(
                                    params,
                                    MHz=mhz,
                                    sw=sw,
                                    deadtime=deadtime,
                                    fid_len=sim_fid_len,
                                    snr_target=transient_snr
                                    if transient_snr > 0
                                    else None,
                                    indsignal=(indsignal_start, indsignal_end),
                                    pts_noise=pts_noise,
                                    preview=False,
                                    extra_line_broadening=extra_line_broadening,
                                )

                                transients.append(fid)
                                progress_bar.progress((i + 1) / num_transients)

                            # Convert transients to numpy array
                            transients_array = np.array(transients)

                            if output_format == "Averaged FID (1D)":
                                # Average transients
                                averaged_fid = np.mean(transients_array, axis=0)

                                # Save averaged FID
                                # ASCII format
                                ascii_avg_path = os.path.join(
                                    temp_dir, f"{sim_filename}_averaged.txt"
                                )
                                np.savetxt(
                                    ascii_avg_path,
                                    np.column_stack(
                                        (averaged_fid.real, averaged_fid.imag)
                                    ),
                                    delimiter="\t",
                                    header="Real\tImaginary",
                                )

                                # NPY format
                                npy_avg_path = os.path.join(
                                    temp_dir, f"{sim_filename}_averaged.npy"
                                )
                                np.save(npy_avg_path, averaged_fid)

                                # MATLAB format
                                mat_avg_path = os.path.join(
                                    temp_dir, f"{sim_filename}_averaged.mat"
                                )
                                mat_success = save_fid_matlab(
                                    averaged_fid, mat_avg_path
                                )

                                # Calculate actual SNR of averaged FID
                                actual_snr = pyAMARES.fidSNR(
                                    averaged_fid,
                                    indsignal=(indsignal_start, indsignal_end),
                                    pts_noise=pts_noise,
                                )

                                st.success(
                                    f"Averaged {num_transients} transients! Final SNR ≈ {actual_snr:.1f}"
                                )

                                # Download links
                                st.subheader("Download Averaged FID")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.markdown(
                                        get_download_link(
                                            ascii_avg_path, "Download Averaged ASCII"
                                        ),
                                        unsafe_allow_html=True,
                                    )
                                with col2:
                                    with open(npy_avg_path, "rb") as f:
                                        npy_data = f.read()
                                    st.markdown(
                                        get_download_link_data(
                                            npy_data,
                                            f"{sim_filename}_averaged.npy",
                                            "Download Averaged NPY",
                                        ),
                                        unsafe_allow_html=True,
                                    )
                                with col3:
                                    if mat_success:
                                        with open(mat_avg_path, "rb") as f:
                                            mat_data = f.read()
                                        st.markdown(
                                            get_download_link_data(
                                                mat_data,
                                                f"{sim_filename}_averaged.mat",
                                                "Download Averaged MAT",
                                            ),
                                            unsafe_allow_html=True,
                                        )

                                # Preview
                                if show_preview:
                                    st.subheader("Preview of Averaged Spectrum")
                                    fig = generate_spectrum_preview(
                                        averaged_fid,
                                        sw,
                                        mhz,
                                        indsignal_start=indsignal_start,
                                        indsignal_end=indsignal_end,
                                        pts_noise=pts_noise,
                                        xlim=xlim if "xlim" in locals() else None,
                                    )
                                    st.pyplot(fig)
                                    plt.close()

                                    # Only show drift plots if perturbation is enabled
                                    if use_perturbation:
                                        st.subheader("Perturbed Parameters")
                                        fig2 = plot_drift_arrays(
                                            ak_drift_arr,
                                            dk_drift_arr,
                                            freq_drift_arr,
                                            phase_drift_arr,
                                        )
                                        st.pyplot(fig2)
                                        plt.close()

                            else:  # All Transients (2D)
                                # Save all transients (similar to batch mode)
                                npy_trans_path = os.path.join(
                                    temp_dir, f"{sim_filename}_transients.npy"
                                )
                                np.save(npy_trans_path, transients_array)

                                mat_trans_path = os.path.join(
                                    temp_dir, f"{sim_filename}_transients.mat"
                                )
                                mat_success = save_fid_matlab(
                                    transients_array, mat_trans_path
                                )

                                st.success(
                                    f"Generated {num_transients} transients! Output as 2D array."
                                )

                                # Download links
                                st.subheader("Download All Transients")
                                col1, col2 = st.columns(2)
                                with col1:
                                    with open(npy_trans_path, "rb") as f:
                                        trans_data = f.read()
                                    st.markdown(
                                        get_download_link_data(
                                            trans_data,
                                            f"{sim_filename}_transients.npy",
                                            "Download All Transients (NPY)",
                                        ),
                                        unsafe_allow_html=True,
                                    )
                                with col2:
                                    if mat_success:
                                        with open(mat_trans_path, "rb") as f:
                                            mat_data = f.read()
                                        st.markdown(
                                            get_download_link_data(
                                                mat_data,
                                                f"{sim_filename}_transients.mat",
                                                "Download All Transients (MAT)",
                                            ),
                                            unsafe_allow_html=True,
                                        )

                                # Preview
                                if show_preview:
                                    st.subheader("Preview of All Transients")
                                    fig = generate_spectrum_preview(
                                        transients_array,
                                        sw,
                                        mhz,
                                        indsignal_start=indsignal_start,
                                        indsignal_end=indsignal_end,
                                        pts_noise=pts_noise,
                                        xlim=xlim if "xlim" in locals() else None,
                                    )
                                    st.pyplot(fig)
                                    plt.close()

                                    # Only show drift plots if perturbation is enabled
                                    if use_perturbation:
                                        st.subheader("Perturbed Parameters")
                                        fig2 = plot_drift_arrays(
                                            ak_drift_arr,
                                            dk_drift_arr,
                                            freq_drift_arr,
                                            phase_drift_arr,
                                        )
                                        st.pyplot(fig2)
                                        plt.close()

                        # Clean up
                        os.unlink(pk_path_sim)

                    except Exception as e:
                        st.error(f"Error during FID simulation: {str(e)}")
                        if "pk_path_sim" in locals():
                            os.unlink(pk_path_sim)

    # Add reset demo mode button if in demo mode (only for FID Simulation mode)
    if (
        simulation_mode
        and "demo_mode" in st.session_state
        and st.session_state.demo_mode
    ):
        st.markdown("---")
        if st.button("Exit Demo Mode", type="primary"):
            if "demo_mode" in st.session_state:
                del st.session_state.demo_mode
            st.rerun()


if __name__ == "__main__":
    main()

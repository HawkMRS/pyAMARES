import base64
import os
import sys
import tempfile
from io import BytesIO

import pandas as pd
import requests
import streamlit as st

import pyAMARES

st.set_page_config(page_title="PyAMARES Web Interface", layout="wide")


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


def clean_dataframe(df):
    """
    Clean a dataframe by:
    1. Removing rows where the first column starts with #
    2. Replacing column names that start with # with empty strings
    """
    # Filter out rows where the first column starts with #
    df = df[~df.iloc[:, 0].astype(str).str.startswith("#")]

    # Clean column headers - replace any that start with # with empty string
    df.columns = [
        "" if isinstance(col, str) and col.startswith("#") else col
        for col in df.columns
    ]

    return df


def display_editable_pk(pk_file):
    """Display and allow editing of the prior knowledge file"""
    try:
        if pk_file.name.endswith(".csv"):
            df = pd.read_csv(pk_file)
            df = clean_dataframe(df)
        elif pk_file.name.endswith(".xlsx"):
            df = pd.read_excel(pk_file)
            df = clean_dataframe(df)

        # Display the editable dataframe using st.data_editor
        st.write("Prior Knowledge File Content (Editable):")

        # Use data_editor with the configuration
        updated_df = st.data_editor(
            df,
            column_config=None,
            num_rows="dynamic",
            # use_container_width=True,
            height=400,
            key="pk_editor",
        )

        # Add buttons to save changes or export
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Apply Changes to Analysis"):
                st.session_state.pk_dataframe = updated_df
                st.success("Changes will be used in the analysis!")
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


def main():
    st.title(f"PyAMARES: MRS Data Analysis Web Interface\n v{pyAMARES.__version__}")
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

    demo_col1, demo_col2 = st.columns([3, 1])
    with demo_col1:
        st.write(
            "New to PyAMARES? Try the demo mode to see how the application works with sample data."
        )
    with demo_col2:
        demo_button = st.button("Try Demo Mode", type="primary")

    # Add this section to handle the button click
    if demo_button:
        st.session_state.demo_mode = True
        st.success("Demo mode activated! Example files will be loaded automatically.")
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
    st.header("Input FID and Prior Knowledge File")
    if "pk_dataframe" not in st.session_state:
        st.session_state.pk_dataframe = None
    if "processing_complete" not in st.session_state:
        st.session_state.processing_complete = False

    # Move FID file upload to sidebar
    st.subheader("FID Data")
    if "demo_mode" in st.session_state and st.session_state.demo_mode:
        fid_file = st.file_uploader(
            "Upload FID file or use the demo file",
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
        )

    # Check if processing is complete and show notification on main page
    if st.session_state.processing_complete:
        st.success("✅ Analysis complete! Results are available below.")

    # File upload for prior knowledge on main page
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

    # Set default parameter values if in demo mode
    if "demo_mode" in st.session_state and st.session_state.demo_mode:
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
            - Click "Process Data" to run the analysis
            - View and download the results below after processing

            """)

    # Add reset demo mode button if in demo mode
    if "demo_mode" in st.session_state and st.session_state.demo_mode:
        if st.button("Exit Demo Mode", type="primary"):
            if "demo_mode" in st.session_state:
                del st.session_state.demo_mode
            st.rerun()

    # Display and make PK file editable immediately when uploaded
    if pk_file is not None:
        pk_dataframe = display_editable_pk(pk_file)

    st.header("Basic Fitting Parameters")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        mhz = st.number_input(
            "Field strength (MHz)", value=120.0, format="%.1f", key="basic_mhz"
        )
    with col2:
        sw = st.number_input(
            "Spectral width (Hz)", value=10000.0, format="%.1f", key="basic_sw"
        )
    with col3:
        deadtime = st.number_input(
            "Dead time (seconds)",
            value=300e-6,
            format="%.2e",
            help="The dead time or begin time in seconds before the FID signal starts",
            key="basic_deadtime",
        )
    with col4:
        truncate_initial_points = st.number_input(
            "Truncate initial points",
            value=0,
            min_value=0,
            help="Truncate initial points from FID to remove fast decaying "
            "components (e.g. macromolecule). This usually makes baseline more flat.",
        )
    with col5:
        g_global = st.number_input(
            "Global g parameter",
            value=0.0,
            format="%.2f",
            help="Global value for the `g` parameter. "
            "Defaults to 0.0. If set to False, the g values "
            "specified in the prior knowledge will be used.",
        )
    col6, col7 = st.columns(2)
    with col6:
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
    with col7:
        output_prefix = st.text_input("Output file prefix", "amares_results")
    col8, col9, col10 = st.columns([4, 2, 2])
    with col8:
        initialize_with_lm = st.checkbox(
            "Initialize Fitting Parameters with Levenberg-Marquardt method",
            value=True,
            help="If True, a Levenberg-Marquardt initializer (least_sq) is executed "
            " internally.",
        )
    with col9:
        flip_axis = st.checkbox(
            "Flip Spectrum Axis",
            help="If True, flip the FID axis by taking the complex "
            "conjugate. Useful in some GE scanners where the MNS "
            "axis needs to be flipped.",
        )
    with col10:
        normalize_fid = st.checkbox(
            "Normalize FID data", help=" If True, normalize the FID data."
        )

    # Create expanders for advanced options on main page
    st.header("Advanced Options")
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
                    "with HSVD"
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
            use_custom_xlim = st.checkbox("Use custom X-axis limits", value=True)

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
    # Process button - make it more prominent in the main page
    process_button = st.button("Process Data", type="primary")

    # Process data when the button is clicked and files are uploaded
    if fid_file is None:
        st.info("Please upload a FID file to begin.")

    # Process data when the button is clicked and files are uploaded
    if process_button and fid_file is not None:
        # Set the processing flag to indicate we're starting
        st.session_state.processing_complete = False

        with st.spinner("Processing data..."):
            # Create temporary files for the uploads
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_fid:
                tmp_fid.write(fid_file.getvalue())
                fid_path = tmp_fid.name

            pk_path = None
            # Check if we have edited pk data in session state
            if st.session_state.pk_dataframe is not None:
                # Create a temporary file from the edited dataframe
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_pk:
                    st.session_state.pk_dataframe.to_csv(tmp_pk.name, index=False)
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
                st.success("✅ Analysis complete! Results are ready below.")

                # Display a divider
                st.markdown("---")

                # Results display section
                st.header("Analysis Results")

                # Reorder display elements - table first, then fitted spectrum
                # Display the result table
                st.subheader("Fitting Results")
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
                        st.components.v1.html(svg_content, height=800, scrolling=True)

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


if __name__ == "__main__":
    main()

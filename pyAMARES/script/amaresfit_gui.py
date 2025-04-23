import base64
import os
import sys
import tempfile

import pandas as pd
import streamlit as st

import pyAMARES

st.set_page_config(page_title="pyAMARES Web Interface", layout="wide")


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

        # Configure column configuration for different column types
        column_config = {}
        for col in df.columns:
            if "name" in col.lower() or "description" in col.lower():
                # Text fields
                column_config[col] = st.column_config.TextColumn(col, width="large")
            elif "chemical" in col.lower() or "ppm" in col.lower():
                # Chemical shift values
                column_config[col] = st.column_config.NumberColumn(
                    col, format="%.4f", width="medium"
                )
            elif any(x in col.lower() for x in ["amplitude", "linewidth", "phase"]):
                # Numeric values
                column_config[col] = st.column_config.NumberColumn(
                    col, format="%.2f", width="small"
                )

        # Use data_editor with the configuration
        updated_df = st.data_editor(
            df,
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
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
    st.title("pyAMARES: MRS Data Analysis")

    # Initialize session state for storing dataframes and processing status
    if "pk_dataframe" not in st.session_state:
        st.session_state.pk_dataframe = None
    if "processing_complete" not in st.session_state:
        st.session_state.processing_complete = False

    # Move FID file upload to sidebar
    st.sidebar.header("FID Data")
    fid_file = st.sidebar.file_uploader(
        "Upload FID file (CSV, TXT, NPY, or Matlab)", type=["csv", "txt", "npy", "mat"]
    )

    # Move basic parameters to sidebar
    st.sidebar.header("Basic Parameters")
    mhz = st.sidebar.number_input("Field strength (MHz)", value=120.0, format="%.1f")
    sw = st.sidebar.number_input("Spectral width (Hz)", value=10000.0, format="%.1f")
    deadtime = st.sidebar.number_input(
        "Dead time (seconds)", value=300e-6, format="%.2e"
    )

    # Sidebar Analysis Options
    st.sidebar.header("Analysis Options")
    method = st.sidebar.selectbox(
        "Fitting method", ["least_squares", "leastsq"], index=0
    )
    output_prefix = st.sidebar.text_input("Output file prefix", "amares_results")

    # Check if processing is complete and show notification on main page
    if st.session_state.processing_complete:
        st.success("✅ Analysis complete! Results are available below.")

    # File upload for prior knowledge on main page
    st.subheader("Prior Knowledge File")
    pk_file = st.file_uploader(
        "Upload Prior Knowledge file (CSV, XLSX)", type=["csv", "xlsx"]
    )

    # Display and make PK file editable immediately when uploaded
    if pk_file is not None:
        pk_dataframe = display_editable_pk(pk_file)

    # Create expanders for advanced options on main page
    with st.expander("Advanced Options", expanded=False):
        adv_col1, adv_col2 = st.columns(2)

        with adv_col1:
            normalize_fid = st.checkbox("Normalize FID data")
            scale_amplitude = st.number_input(
                "Scale amplitude", value=1.0, format="%.2f"
            )
            flip_axis = st.checkbox("Flip FID axis")
            ifphase = st.checkbox("Phase the spectrum")
            lb = st.number_input(
                "Line Broadening factor (Hz)", value=2.0, format="%.1f"
            )

        with adv_col2:
            # preview = st.checkbox("Preview spectra")
            initialize_with_lm = st.checkbox(
                "Initialize Fitting Parameters with Levenberg-Marquardt method",
                value=True,
            )
            carrier = st.number_input(
                "Carrier frequency (ppm)", value=0.0, format="%.2f"
            )
            truncate_initial_points = st.number_input(
                "Truncate initial points", value=0, min_value=0
            )
            g_global = st.number_input("Global g parameter", value=0.0, format="%.2f")
            ppm_offset = st.number_input("PPM offset", value=0.0, format="%.2f")
            delta_phase = st.number_input(
                "Additional phase shift (degrees)", value=0.0, format="%.1f"
            )

    # X limits
    with st.expander("X-axis limits (ppm)", expanded=False):
        xlim_col1, xlim_col2 = st.columns(2)
        with xlim_col1:
            x_min = st.number_input("Min", value=-20.0, format="%.1f")
        with xlim_col2:
            x_max = st.number_input("Max", value=10.0, format="%.1f")
        xlim = (x_min, x_max) if x_min < x_max else None

    # HSVD options
    with st.expander("HSVD", expanded=False):
        use_hsvd = st.checkbox("Use HSVD for initial parameters")
        num_of_component = st.number_input(
            "Number of components for HSVD", value=12, min_value=1
        )

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

                    # Fittign
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

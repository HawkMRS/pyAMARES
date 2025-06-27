from unittest.mock import MagicMock, patch

import pytest

from pyAMARES.script.amaresfit_gui import main


# Create a class to mimic Streamlit's SessionState that supports both dict and attribute access
class MockSessionState(dict):
    """Mock for Streamlit's SessionState that allows both dictionary and attribute access"""

    def __getattr__(self, name):
        if name in self:
            return self[name]
        return None

    def __setattr__(self, name, value):
        self[name] = value


class TestDemoMode:
    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit components"""
        with patch("pyAMARES.script.amaresfit_gui.st") as mock_st:
            # Create mock columns objects - we need enough for the most complex layout
            mock_cols = [MagicMock() for _ in range(10)]  # Create 10 mock columns

            # Make columns() return appropriate number of column objects based on input
            def mock_columns(spec):
                if isinstance(spec, list):
                    # Handle list specifications like [3, 1], [4, 2, 2], etc.
                    return mock_cols[: len(spec)]
                elif isinstance(spec, int):
                    # Handle integer specifications like 2, 3, 4, 5, etc.
                    return mock_cols[:spec]
                else:
                    # Default fallback
                    return mock_cols[:2]

            mock_st.columns.side_effect = mock_columns

            # Set up context managers
            mock_st.container.return_value.__enter__.return_value = MagicMock()
            mock_st.expander.return_value.__enter__.return_value = MagicMock()
            mock_st.spinner.return_value.__enter__.return_value = MagicMock()

            # Initialize session state using our custom class
            mock_st.session_state = MockSessionState()

            # Mock radio button to return "AMARES Fitting" by default
            mock_st.radio.return_value = "AMARES Fitting"

            # Create a function that returns appropriate values for different button calls
            def mock_button(*args, **kwargs):
                if args[0] == "Try Demo Mode":
                    return False  # Changed to False to avoid activating demo mode by default
                elif args[0] == "Exit Demo Mode":
                    return False
                elif args[0] == "Start AMARES Fitting":
                    return False
                elif args[0] == "Generate Simulated FID":
                    return False
                elif args[0] == "Apply Changes":
                    return False
                elif args[0] == "Export Modified PK Data":
                    return False
                else:
                    return False

            mock_st.button.side_effect = mock_button

            # Mock other UI elements
            mock_st.file_uploader.return_value = None
            mock_st.number_input.return_value = 0.0
            mock_st.text_input.return_value = ""
            mock_st.checkbox.return_value = False
            mock_st.selectbox.return_value = "least_squares"
            mock_st.slider.return_value = (-20.0, 10.0)

            yield mock_st

    @pytest.fixture
    def mock_requests(self):
        """Mock requests to GitHub"""
        with patch("pyAMARES.script.amaresfit_gui.requests.get") as mock_get:
            # Set up mock response for GitHub file requests
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"test_data"
            mock_get.return_value = mock_response

            yield mock_get

    def test_demo_mode_activation_amares_fitting(self, mock_streamlit, mock_requests):
        """Test that demo mode is activated correctly for AMARES Fitting mode"""
        # Set radio to return AMARES Fitting mode
        mock_streamlit.radio.return_value = "AMARES Fitting"

        # Override button mock to return True for Try Demo Mode
        def mock_button_demo_active(*args, **kwargs):
            if args[0] == "Try Demo Mode":
                return True  # This test specifically tests demo activation
            else:
                return False

        mock_streamlit.button.side_effect = mock_button_demo_active

        # Set up BytesIO mock
        with patch("pyAMARES.script.amaresfit_gui.BytesIO") as mock_bytesio:
            mock_file = MagicMock()
            mock_file.name = "demo_fid.txt"
            mock_bytesio.return_value = mock_file

            # Prevent actual pyAMARES calls
            with patch("pyAMARES.script.amaresfit_gui.pyAMARES") as mock_pyamares:
                mock_pyamares.__version__ = "0.0.0"  # null version id for test
                # Patch tempfile to avoid file operations
                with patch("pyAMARES.script.amaresfit_gui.tempfile"):
                    # Patch os.path functions
                    with patch("pyAMARES.script.amaresfit_gui.os.path"):
                        # Patch display_editable_pk to avoid errors
                        with patch("pyAMARES.script.amaresfit_gui.display_editable_pk"):
                            # Call main function
                            main()

                            # Verify session state is set correctly
                            assert "demo_mode" in mock_streamlit.session_state
                            assert mock_streamlit.session_state["demo_mode"] is True

                            # Verify success message was displayed for AMARES mode
                            mock_streamlit.success.assert_any_call(
                                "Demo mode activated! Example FID and Prior Knowledge files will be loaded automatically."
                            )

                            # Verify rerun was called to apply the demo mode
                            mock_streamlit.rerun.assert_called_once()

    def test_demo_mode_activation_simulation_mode(self, mock_streamlit, mock_requests):
        """Test that demo mode is activated correctly for FID Simulation mode"""
        # Set radio to return FID Simulation mode
        mock_streamlit.radio.return_value = "Simple FID Simulation"

        # Override button mock to return True for Try Demo Mode
        def mock_button_demo_active(*args, **kwargs):
            if args[0] == "Try Demo Mode":
                return True  # This test specifically tests demo activation
            else:
                return False

        mock_streamlit.button.side_effect = mock_button_demo_active

        # Set up BytesIO mock
        with patch("pyAMARES.script.amaresfit_gui.BytesIO") as mock_bytesio:
            mock_file = MagicMock()
            mock_file.name = "demo_pk.csv"
            mock_bytesio.return_value = mock_file

            # Prevent actual pyAMARES calls
            with patch("pyAMARES.script.amaresfit_gui.pyAMARES") as mock_pyamares:
                mock_pyamares.__version__ = "0.0.0"  # null version id for test
                # Patch tempfile to avoid file operations
                with patch("pyAMARES.script.amaresfit_gui.tempfile"):
                    # Patch os.path functions
                    with patch("pyAMARES.script.amaresfit_gui.os.path"):
                        # Patch display_editable_pk to avoid errors
                        with patch("pyAMARES.script.amaresfit_gui.display_editable_pk"):
                            # Call main function
                            main()

                            # Verify session state is set correctly
                            assert "demo_mode" in mock_streamlit.session_state
                            assert mock_streamlit.session_state["demo_mode"] is True

                            # Verify success message was displayed for simulation mode
                            mock_streamlit.success.assert_any_call(
                                "Demo mode activated! Example Prior Knowledge file will be loaded automatically for simulation."
                            )

                            # Verify rerun was called to apply the demo mode
                            mock_streamlit.rerun.assert_called_once()

    def test_demo_files_loading_amares_mode(self, mock_streamlit, mock_requests):
        """Test that demo files are loaded from GitHub when in demo mode for AMARES fitting"""
        # Set session state to demo mode and AMARES fitting mode
        mock_streamlit.session_state = MockSessionState({"demo_mode": True})
        mock_streamlit.radio.return_value = "AMARES Fitting"

        # Set up BytesIO mock
        with patch("pyAMARES.script.amaresfit_gui.BytesIO") as mock_bytesio:
            mock_fid_file = MagicMock()
            mock_fid_file.name = "demo_fid.txt"
            mock_pk_file = MagicMock()
            mock_pk_file.name = "demo_pk.csv"
            # Make sure BytesIO returns the appropriate mock file
            mock_bytesio.side_effect = [mock_pk_file, mock_fid_file]

            # Prevent actual pyAMARES calls and file processing
            with patch("pyAMARES.script.amaresfit_gui.pyAMARES") as mock_pyamares:
                mock_pyamares.__version__ = "0.0.0"  # null version id for test
                # Patch tempfile to avoid file operations
                with patch("pyAMARES.script.amaresfit_gui.tempfile"):
                    # Patch os.path functions
                    with patch("pyAMARES.script.amaresfit_gui.os.path"):
                        # Patch display_editable_pk function
                        with patch("pyAMARES.script.amaresfit_gui.display_editable_pk"):
                            # Make sure file uploaders return None (no user uploads)
                            mock_streamlit.file_uploader.return_value = None

                            # Call main function
                            main()

                            # Verify GitHub requests were made for demo files
                            expected_fid_url = "https://raw.githubusercontent.com/HawkMRS/pyAMARES/main/pyAMARES/examples/fid.txt"
                            expected_pk_url = "https://raw.githubusercontent.com/HawkMRS/pyAMARES/main/pyAMARES/examples/example_human_brain_31P_7T.csv"

                            mock_requests.assert_any_call(expected_fid_url)
                            mock_requests.assert_any_call(expected_pk_url)

                            # Verify info messages about demo files
                            mock_streamlit.info.assert_any_call(
                                "Using demo FID file: demo_fid.txt"
                            )
                            mock_streamlit.info.assert_any_call(
                                "Using demo Prior Knowledge file: demo_pk.csv"
                            )

                            # Verify demo guide expander was created
                            mock_streamlit.expander.assert_any_call(
                                "Demo Mode Guide", expanded=True
                            )

    def test_demo_files_loading_simulation_mode(self, mock_streamlit, mock_requests):
        """Test that demo files are loaded from GitHub when in demo mode for FID simulation"""
        # Set session state to demo mode and simulation mode
        mock_streamlit.session_state = MockSessionState({"demo_mode": True})
        mock_streamlit.radio.return_value = "Simple FID Simulation"

        # Set up BytesIO mock
        with patch("pyAMARES.script.amaresfit_gui.BytesIO") as mock_bytesio:
            mock_pk_file = MagicMock()
            mock_pk_file.name = "demo_pk.csv"
            mock_bytesio.return_value = mock_pk_file

            # Prevent actual pyAMARES calls and file processing
            with patch("pyAMARES.script.amaresfit_gui.pyAMARES") as mock_pyamares:
                mock_pyamares.__version__ = "0.0.0"  # null version id for test
                # Patch tempfile to avoid file operations
                with patch("pyAMARES.script.amaresfit_gui.tempfile"):
                    # Patch os.path functions
                    with patch("pyAMARES.script.amaresfit_gui.os.path"):
                        # Patch display_editable_pk function
                        with patch("pyAMARES.script.amaresfit_gui.display_editable_pk"):
                            # Make sure file uploaders return None (no user uploads)
                            mock_streamlit.file_uploader.return_value = None

                            # Call main function
                            main()

                            # Verify GitHub request was made for PK file (no FID needed for simulation)
                            expected_pk_url = "https://raw.githubusercontent.com/HawkMRS/pyAMARES/main/pyAMARES/examples/example_human_brain_31P_7T.csv"
                            mock_requests.assert_any_call(expected_pk_url)

                            # Verify info message about demo PK file
                            mock_streamlit.info.assert_any_call(
                                "Using demo Prior Knowledge file: demo_pk.csv"
                            )

                            # In simulation mode, should see "FID Simulation Mode" subheader
                            mock_streamlit.subheader.assert_any_call(
                                "FID Simulation Mode"
                            )

    def test_mode_selection_display(self, mock_streamlit, mock_requests):
        """Test that the mode selection radio button is displayed correctly"""
        # Set up minimal mocking
        with patch("pyAMARES.script.amaresfit_gui.pyAMARES") as mock_pyamares:
            mock_pyamares.__version__ = "0.0.0"
            with patch("pyAMARES.script.amaresfit_gui.tempfile"):
                with patch("pyAMARES.script.amaresfit_gui.os.path"):
                    with patch("pyAMARES.script.amaresfit_gui.display_editable_pk"):
                        # Call main function
                        main()

                        # Verify mode selection radio is created (check that radio was called)
                        assert mock_streamlit.radio.called, (
                            "Expected radio button to be created"
                        )

                        # Check that the radio call contains the expected options
                        radio_calls = mock_streamlit.radio.call_args_list
                        found_mode_radio = False
                        for call in radio_calls:
                            args, kwargs = call
                            if (
                                len(args) >= 2
                                and "AMARES Fitting" in str(args[1])
                                and "Simple FID Simulation" in str(args[1])
                            ):
                                found_mode_radio = True
                                break

                        assert found_mode_radio, (
                            f"Expected mode selection radio not found. Radio calls: {radio_calls}"
                        )

                        # Verify mode header is displayed
                        mock_streamlit.header.assert_any_call("Mode")

    def test_simulation_mode_ui_elements(self, mock_streamlit, mock_requests):
        """Test that simulation mode displays the correct UI elements"""
        # Set to simulation mode
        mock_streamlit.radio.return_value = "Simple FID Simulation"

        with patch("pyAMARES.script.amaresfit_gui.pyAMARES") as mock_pyamares:
            mock_pyamares.__version__ = "0.0.0"
            with patch("pyAMARES.script.amaresfit_gui.tempfile"):
                with patch("pyAMARES.script.amaresfit_gui.os.path"):
                    with patch("pyAMARES.script.amaresfit_gui.display_editable_pk"):
                        # Call main function
                        main()

                        # Should see FID Simulation header
                        mock_streamlit.header.assert_any_call(
                            "FID Simulation Parameters"
                        )

                        # Should see simulation mode subheader
                        mock_streamlit.subheader.assert_any_call("FID Simulation Mode")

                        # Should see info about simulation mode
                        mock_streamlit.info.assert_any_call(
                            "**Simulation Mode Active**: Generate synthetic FID data from prior knowledge parameters"
                        )

                        # Should see Generate Simulated FID button
                        mock_streamlit.button.assert_any_call(
                            "Generate Simulated FID", type="primary"
                        )

    def test_amares_fitting_mode_ui_elements(self, mock_streamlit, mock_requests):
        """Test that AMARES fitting mode displays the correct UI elements"""
        # Set to AMARES fitting mode (default)
        mock_streamlit.radio.return_value = "AMARES Fitting"

        # Ensure demo mode is NOT active by resetting session state
        mock_streamlit.session_state = MockSessionState()

        # Ensure file_uploader returns None to trigger the info message
        mock_streamlit.file_uploader.return_value = None

        with patch("pyAMARES.script.amaresfit_gui.pyAMARES") as mock_pyamares:
            mock_pyamares.__version__ = "0.0.0"
            with patch("pyAMARES.script.amaresfit_gui.tempfile"):
                with patch("pyAMARES.script.amaresfit_gui.os.path"):
                    with patch("pyAMARES.script.amaresfit_gui.display_editable_pk"):
                        # Call main function
                        main()

                        # Should see Basic Fitting Parameters header
                        mock_streamlit.header.assert_any_call(
                            "Basic Fitting Parameters"
                        )

                        # Should see FID Data subheader
                        mock_streamlit.subheader.assert_any_call("FID Data")

                        # Should see some info message (could be about uploading or about pyAMARES)
                        assert mock_streamlit.info.called, (
                            "Expected some info message to be displayed"
                        )


class TestParameterValidation:
    """Test parameter validation and edge cases"""

    @pytest.fixture
    def mock_streamlit_basic(self):
        """Basic streamlit mock for parameter testing"""
        with patch("pyAMARES.script.amaresfit_gui.st") as mock_st:
            # Create mock columns
            mock_cols = [MagicMock() for _ in range(10)]
            mock_st.columns.side_effect = (
                lambda spec: mock_cols[:spec]
                if isinstance(spec, int)
                else mock_cols[: len(spec)]
            )

            # Basic mocks
            mock_st.container.return_value.__enter__.return_value = MagicMock()
            mock_st.expander.return_value.__enter__.return_value = MagicMock()
            mock_st.session_state = MockSessionState()
            mock_st.radio.return_value = "AMARES Fitting"

            # Create a function that returns appropriate values for different button calls
            def mock_button(*args, **kwargs):
                if args[0] == "Try Demo Mode":
                    return False  # Don't activate demo mode by default
                else:
                    return False

            mock_st.button.side_effect = mock_button
            mock_st.file_uploader.return_value = None
            mock_st.number_input.return_value = 0.0
            mock_st.text_input.return_value = ""
            mock_st.checkbox.return_value = False
            mock_st.selectbox.return_value = "least_squares"

            yield mock_st

    def test_basic_fid_parameters_display(self, mock_streamlit_basic):
        """Test that basic FID parameters are displayed correctly"""
        with patch("pyAMARES.script.amaresfit_gui.pyAMARES") as mock_pyamares:
            mock_pyamares.__version__ = "0.0.0"
            with patch("pyAMARES.script.amaresfit_gui.tempfile"):
                with patch("pyAMARES.script.amaresfit_gui.os.path"):
                    with patch("pyAMARES.script.amaresfit_gui.display_editable_pk"):
                        # Call main function
                        main()

                        # Verify Basic FID Parameters header
                        mock_streamlit_basic.header.assert_any_call(
                            "Basic FID Parameters"
                        )

                        # Check that number inputs for basic parameters are created
                        # Get all the first arguments (labels) from number_input calls
                        number_input_calls = []
                        for call in mock_streamlit_basic.number_input.call_args_list:
                            if call[0]:  # if there are positional arguments
                                number_input_calls.append(
                                    str(call[0][0])
                                )  # Convert to string for safety

                        # Check for the exact text used in the GUI
                        assert any(
                            "Field strength (MHz)" in call
                            for call in number_input_calls
                        )
                        assert any(
                            "Spectral width (Hz)" in call for call in number_input_calls
                        )
                        assert any(
                            "Dead time (seconds)" in call for call in number_input_calls
                        )

    def test_advanced_options_expander(self, mock_streamlit_basic):
        """Test that advanced options expander is created"""
        with patch("pyAMARES.script.amaresfit_gui.pyAMARES") as mock_pyamares:
            mock_pyamares.__version__ = "0.0.0"
            with patch("pyAMARES.script.amaresfit_gui.tempfile"):
                with patch("pyAMARES.script.amaresfit_gui.os.path"):
                    with patch("pyAMARES.script.amaresfit_gui.display_editable_pk"):
                        # Call main function
                        main()

                        # Verify Advanced Options expander is created
                        mock_streamlit_basic.expander.assert_any_call(
                            "Advanced Options", expanded=False
                        )

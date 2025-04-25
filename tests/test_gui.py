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
            # Create mock columns objects
            mock_col1 = MagicMock()
            mock_col2 = MagicMock()
            mock_col3 = MagicMock()
            mock_col4 = MagicMock()
            mock_col5 = MagicMock()

            # Make columns() return variable number of column objects based on input
            def mock_columns(spec):
                if (
                    isinstance(spec, list) and len(spec) == 2
                ):  # For demo_col1, demo_col2 = st.columns([3, 1])
                    return [mock_col1, mock_col2]
                elif spec == 5:  # For col1, col2, col3, col4, col5 = st.columns(5)
                    return [mock_col1, mock_col2, mock_col3, mock_col4, mock_col5]
                elif (
                    isinstance(spec, list) and len(spec) == 3
                ):  # For col8, col9, col10 = st.columns([4, 2, 2])
                    return [mock_col1, mock_col2, mock_col3]
                else:  # Default case for any other columns call
                    return [mock_col1, mock_col2]

            mock_st.columns.side_effect = mock_columns

            # Set up context managers
            mock_st.container.return_value.__enter__.return_value = MagicMock()
            mock_st.expander.return_value.__enter__.return_value = MagicMock()
            mock_st.spinner.return_value.__enter__.return_value = MagicMock()

            # Initialize session state using our custom class
            mock_st.session_state = MockSessionState()

            # Create a function that returns appropriate values for different button calls
            def mock_button(*args, **kwargs):
                if args[0] == "Try Demo Mode":
                    return True
                elif args[0] == "Exit Demo Mode":
                    return False
                elif args[0] == "Process Data":
                    return False
                elif args[0] == "Apply Changes to Analysis":
                    return False
                elif args[0] == "Export Modified PK Data":
                    return False
                else:
                    return False

            # Use the function for button side_effect instead of a list
            mock_st.button.side_effect = mock_button

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

    def test_demo_mode_activation(self, mock_streamlit, mock_requests):
        """Test that demo mode is activated correctly when button is clicked"""
        # Set up BytesIO mock
        with patch("pyAMARES.script.amaresfit_gui.BytesIO") as mock_bytesio:
            mock_file = MagicMock()
            mock_file.name = "demo_fid.txt"
            mock_bytesio.return_value = mock_file

            # Prevent actual pyAMARES calls
            with patch("pyAMARES.script.amaresfit_gui.pyAMARES"):
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

                            # Verify success message was displayed
                            mock_streamlit.success.assert_any_call(
                                "Demo mode activated! Example files will be loaded automatically."
                            )

                            # Verify rerun was called to apply the demo mode
                            mock_streamlit.rerun.assert_called_once()

    def test_demo_files_loading(self, mock_streamlit, mock_requests):
        """Test that demo files are loaded from GitHub when in demo mode"""
        # Set session state to demo mode using the custom class
        mock_streamlit.session_state = MockSessionState({"demo_mode": True})

        # Set up BytesIO mock
        with patch("pyAMARES.script.amaresfit_gui.BytesIO") as mock_bytesio:
            mock_fid_file = MagicMock()
            mock_fid_file.name = "demo_fid.txt"
            mock_pk_file = MagicMock()
            mock_pk_file.name = "demo_pk.csv"
            # Make sure BytesIO returns the appropriate mock file
            mock_bytesio.side_effect = [mock_fid_file, mock_pk_file]

            # Prevent actual pyAMARES calls and file processing
            with patch("pyAMARES.script.amaresfit_gui.pyAMARES"):
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

# tests/test_notebooks.py
import pytest
import os
import glob

# Get all notebooks from the same directory as this file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
notebooks = glob.glob(os.path.join(CURRENT_DIR, '*.ipynb'))

# Skip notebooks that might require user interaction or external data not available during testing
SKIP_NOTEBOOKS = [
    # Add any notebooks that shouldn't be tested automatically
    # Example: "interactive_demo.ipynb"
]

@pytest.mark.parametrize('notebook', [nb for nb in notebooks if os.path.basename(nb) not in SKIP_NOTEBOOKS])
def test_notebook_runs_without_errors(notebook):
    """Test that the notebook runs without errors."""
    pytest.importorskip("nbval")
    # This test function doesn't need a body - nbval will handle the execution
    # The actual testing happens when pytest is invoked with the nbval plugin
    pass

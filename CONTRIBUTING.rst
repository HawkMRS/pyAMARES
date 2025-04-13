Contributing to pyAMARES
------------------------

Thank you for your interest in contributing to pyAMARES! This document provides guidelines and instructions to help you contribute effectively.

Code of Conduct
~~~~~~~~~~~~~~~

We follow the `GitHub Community Code of Conduct <https://docs.github.com/en/site-policy/github-terms/github-community-code-of-conduct>`_ to foster an inclusive and respectful community.

Getting Started
~~~~~~~~~~~~~~~

Setting Up Your Development Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1.  **Fork the repository** on GitHub.
2.  **Clone your forked GitHub repository**:

    .. code-block:: bash

       # Using SSH (if you have SSH keys set up)
       git clone git@github.com:YOUR_USERNAME/pyAMARES.git

       # Or using HTTPS
       git clone https://github.com/YOUR_USERNAME/pyAMARES.git

3.  **Create a virtual environment** (``conda`` recommended):

    .. code-block:: bash

       conda create -n pyamares-dev python=3.8
       conda activate pyamares-dev

    .. note::
       You can replace ``pyamares-dev`` with your preferred environment name.

4.  **Install development dependencies**:

    .. code-block:: bash

       pip install -e ".[dev]"

    .. note::
       This installs the package in editable mode (``-e``) along with all development
       dependencies specified in the ``[dev]`` extra of the project's setup
       (e.g., in ``pyproject.toml`` or ``setup.py``). This typically includes
       tools for documentation, testing, linting, and formatting (like ``Sphinx``,
       ``pytest``, ``ruff``, ``pre-commit``).

5.  **Initialize pre-commit hooks**:

    .. code-block:: bash

       pre-commit install

    .. note::
       This sets up the git hooks defined in ``.pre-commit-config.yaml`` to run automatically before each commit.

Development Workflow
~~~~~~~~~~~~~~~~~~~~

Creating Issues
^^^^^^^^^^^^^^^

-   Search existing issues before creating a new one.
-   Clearly describe the problem or feature request.
-   For bug reports, please include steps to reproduce the issue.

Making Changes
^^^^^^^^^^^^^^

1.  **Create a new branch** for your changes:

    .. code-block:: bash

       git checkout -b feature/your-feature-name

2.  **Make your changes**, following our code style guidelines.
3.  **Commit your changes**:

    .. code-block:: bash

       # Add your changed files
       git add path/to/your/changed/file.py
       # Commit with a descriptive message
       git commit -m "feat: Add concise description of changes"

    .. note::
       If you've installed the pre-commit hooks (Step 5 in Setup), code quality
       checks (like ``Ruff`` formatting/linting) will run automatically on commit.
       Follow any instructions if checks fail.

4.  **Push your changes** to your fork:

    .. code-block:: bash

       git push origin feature/your-feature-name

5.  **Open a Pull Request** on the `pyAMARES GitHub repository <https://github.com/HawkMRS/pyAMARES/pulls>`_. Provide a clear description of your changes in the Pull Request.

Code Style Guide
~~~~~~~~~~~~~~~~

We follow a consistent code style to ensure readability and maintainability. Our code style is primarily enforced by `Ruff <https://github.com/astral-sh/ruff>`_.

Using Ruff
^^^^^^^^^^

``Ruff`` is an extremely fast Python linter and formatter.

**Running Ruff manually**:

.. code-block:: bash

   # Check your code for issues
   ruff check .

   # Fix issues automatically where possible
   ruff check --fix .

   # Format your code
   ruff format .

**Configuration**:


Our ``Ruff`` configuration is defined in ``pyproject.toml``:


.. literalinclude:: ../../pyproject.toml

Pre-commit Hooks
^^^^^^^^^^^^^^^^

We use ``pre-commit`` to automatically check and format code before each commit, ensuring consistency across the codebase.

The configuration is in ``.pre-commit-config.yaml``. If you've followed the setup instructions, these checks will run automatically when you run ``git commit``.

You can also run them manually across all files:

.. code-block:: bash

   pre-commit run --all-files

Testing
~~~~~~~

-   Write tests using ``pytest`` for new features and bug fixes. Place tests in the ``tests/`` directory.
-   Run tests locally before submitting a Pull Request:

    .. code-block:: bash

       pytest

-   Ensure your changes do not break existing functionality and that all tests pass.

Documentation
~~~~~~~~~~~~~

Building Documentation Locally
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To build the documentation locally:

1.  Ensure you've installed the necessary dependencies. This is usually covered by ``pip install -e ".[dev]"`` or specifically via ``pip install -e ".[doc]"``.
2.  Navigate to the documentation directory (often ``docs/``) and build using ``Sphinx``:

    .. code-block:: bash

       # Assuming you are in the root project directory
       sphinx-build -a docs/source/ docs/build/

3.  View the generated documentation by opening ``docs/build/index.html`` in your web browser.

Contributing to Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-   Our documentation is written primarily in **reStructuredText (reST)** format (``.rst`` files) found in the ``docs/source/`` directory.
-   Significant parts of the documentation, especially the API reference, are automatically generated from **docstrings** within the Python code using ``Sphinx autodoc``. We recommend following the `Google Style Python Docstrings <https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`_ format for docstrings for consistency and clarity, though this is not strictly mandated.
-   Check your local documentation build (using the steps above) for warnings or errors before submitting your changes. Ensure links work, code examples are correct, and formatting looks as expected.

----

If you need any additional help, please feel free to open `a new issue <https://github.com/HawkMRS/pyAMARES/issues>`_.

Thank you for contributing to pyAMARES!
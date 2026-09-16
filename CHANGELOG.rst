Latest Changes
--------------

v0.3.34dev
~~~~~~~~~~

**Added**
  - ``run_parallel_fitting_with_progress`` writes batch-fitting progress to a rotating log file (rotated every 10 minutes) using a new ``BATCH_INFO`` log level, logs the initial fitting parameters before each batch run, and takes a new ``loglevel`` parameter setting that file's threshold.

**Changed**
  - Replaced the stdlib-based logging with `loguru <https://github.com/Delgan/loguru>`_, which is now a required dependency. ``get_logger`` and the ``LOG_STYLE`` setting are removed, and ``pyAMARES.libs.logger`` now only configures loguru's console handler.
  - ``pyAMARES.libs.logger.set_log_level()`` no longer accepts ``verbose``, and additionally accepts loguru's ``TRACE`` and ``SUCCESS`` levels. Console output keeps the v0.3.33 look: ``INFO`` and above, on stdout, as ``[AMARES | LEVEL] message``. ``BATCH_INFO`` records go only to the log file.
  - The default ``logfilename`` of ``run_parallel_fitting_with_progress`` changed from ``multiprocess_log.txt`` to ``logs/parallelfitting.log``. The new ``loglevel`` parameter comes before ``objective_func``, so calls passing ``objective_func`` positionally must switch to a keyword argument.
  - Downgraded many ``logger.info`` calls to ``logger.debug`` to reduce console verbosity, and converted old ``%``-style log format strings to f-strings.
  - Removed the ``redirect_stdout_to_file`` context manager from ``multiprocessing.py`` in favor of ``loguru``'s file sink.
  - Added pandas 2.0/3.0 compatibility fixes in ``PriorKnowledge.py`` (``unitconverter``, ``generateparameter``) and ``hsvd.py`` (``uniquify_dataframe``).
  - Renamed the ``--current-env`` nbval flag to ``--nbval-current-env`` in CI and ``pytest.ini``.
  - Raised the minimum required ``matplotlib`` version from ``3.1.3`` to ``3.6.0`` to match the ``layout="constrained"`` usage in ``visualization.py`` (introduced in v0.3.33).

Thanks to `@bastigw`_ for contributing this version in `PR #14`_.

.. _PR #14: https://github.com/HawkMRS/pyAMARES/pull/14
.. _@bastigw: https://github.com/bastigw

v0.3.33
~~~~~~~

**Fixed**
  - Fixed ``FutureWarning`` messages from pandas.
  - Set default numeric type for prior knowledge to float.

**Changed**
  - Updated logging statements to more applicable levels (e.g. INFO to DEBUG).
  - Changed tight layout to constrained layout for figures with subplots in ``visualization.py``.
  - Simplified OS test matrix by skipping Python 3.9, 3.11, 3.13.
  - Disabled preview for ``HSVDinitializer`` in ``tests/step2_simple.ipynb`` to reduce CI/CD failures.

Thanks to `@bastigw`_ for contributing this version in `PR #10`_.

.. _PR #10: https://github.com/HawkMRS/pyAMARES/pull/10
.. _@bastigw: https://github.com/bastigw

v0.3.32
~~~~~~~

**Added**
  - Added support for Python 3.13 and 3.14.
  - Modernized CI/CD workflows with reusable workflows and new triggers.
  - Created a legacy branch ``legacy2025`` and labeled it as ``v0.3.29-legacy2025`` for users who need to maintain compatibility with Python 3.6 and 3.7.

**Fixed**
  - Fixed a bug that ``.vscode`` is not ignored in the ``.gitignore`` file.

**Changed**
  - Updated minimum Python version requirement from 3.6 to 3.8 across all configuration files
  - Updated recommended Python version from 3.8 to 3.12. 
  - Expanded test matrix to cover Python 3.8-3.14 on Ubuntu, Windows, and macOS.
  - Removed older Intel-based macOS (``macos-13``) from test matrix. 
  - Changed the default python version for readthedocs from 3.8 to 3.12.
  - Updated documentation to reflect the new minimum and recommended Python versions, and added notes for legacy users to download the ``legacy2025`` branch when needed.

Thanks to `@bastigw`_ for contributing this version in `PR #9`_.

.. _PR #9: https://github.com/HawkMRS/pyAMARES/pull/9
.. _@bastigw: https://github.com/bastigw

v0.3.31
~~~~~~~
**Fixed**
  - Fixed a bug in the web interface where non-``.txt`` format FIDs were incorrectly identified as ``.txt`` files, causing program crashes.
  - Fixed a bug in both the web interface and command-line script where the code attempted to access non-existent ``result_sum`` and ``simple_pd`` from the fitted result object.

v0.3.30
~~~~~~~
**Added** 
  - Added a new "Simple FID Simulation" mode to the Streamlit app ``script/amaresfit_gui.py``. This mode allows users to simulate FIDs using prior knowledge dataset and perturbed the parameters.
s needed
  - Added ``extra_line_broadening`` to ``fid.simulate_fid`` to allow users to add extra line broadening to the simulated FID before adding noise. This avoid SNR bias introduced by extra global linebroadening factors.

**Fixed**
  - Fixed a bug in the Streamlit app where editing prior knowledge (PK) would remove ``#`` symbols from comment rows, causing file parsing to fail when the comment line appears as the first line

v0.3.29
~~~~~~~


**Added** 
  - Added a streamlit app ``script/amaresfit_gui.py`` to provide a graphical user interface for pyAMARES. 

v0.3.28
~~~~~~~


**Fixed**
  - Fixed a bug in CRLB calculation that caused failures when multiple fitting parameters were fixed.
  - Fixed logger print format typos across multiple files.

v0.3.27
~~~~~~~

**Added**
  - Added ``logger.py`` module to API documentation.
  - Added more comprehensive ``ruff`` checking configurations in ``pyproject.toml``.

**Changed**
  - Replaced remaining ``print`` and ``warning`` statements with the new logging system.
  - Reorganized import statements across multiple files to follow best practices (alphabetical ordering, standard library imports first).
  - Excluded Jupyter notebooks and third-party code from ``ruff`` linting. 
  - Updated long description in ``setup.py`` with proper line breaks for PEP-8 standards.

v0.3.26
~~~~~~~

**Added**
  - Added comprehensive code formatting with ``ruff`` as mentioned in `Issue #5`_.
  - Added ``ruff`` requirements to setup.py with dedicated install option: ``pip install -e ".[ruff]"``
  - Added ``dev`` dependencies in setup.py to include jupyter, documentation, and code quality tools.
  - Added GitHub CI/CD configuration with ``ruff.yml`` for automated code quality checks.
  - Added CONTRIBUTING.rst to documentation with guidelines for contributors.

**Changed**
  - Significantly reformatted codebase using ``ruff`` for consistent code style.
  - Updated documentation structure with inclusion of CONTRIBUTING.rst.
  - Revised README.rst with improved contributor guidelines.
  - Updated docs/source/index.rst to include links to contribution information.

.. _Issue #5: https://github.com/HawkMRS/pyAMARES/issues/5

v0.3.25
~~~~~~~

**Added**
  - Added centralized logging system with ``pyAMARES/libs/logger.py`` module for better debugging and output management.
  - Implemented configurable log levels (DEBUG, INFO, WARNING) via ``get_logger()`` and ``set_log_level()`` functions.
  - Replaced print statements with proper logging in several modules (``PriorKnowledge.py``, ``fid.py``, ``lmfit.py``, ``crlb.py``).
  - Added ability to control output verbosity, especially useful when processing multiple spectra in loops.

**Changed**
  - Improved code consistency by standardizing status and warning messages across the package.
  - Enhanced user experience with cleaner console output and better filtering options.

**Fixed**
  - Addressed console flooding issues when processing large batches of spectra.

Thanks to `@andrewendlinger`_ for contributing this version in `PR #4`_.

.. _PR #4: https://github.com/HawkMRS/pyAMARES/pull/4
.. _@andrewendlinger: https://github.com/andrewendlinger

v0.3.24
~~~~~~~

**Added**
  - Added ``tests`` directory to the package with Jupyter notebook test examples. 
  - Implemented CI/CD pipeline testing against multiple Python versions (3.7, 3.8, 3.10, and 3.12) on Ubuntu-22.04.

**Fixed**
  - Fixed an image link in README.rst

v0.3.23
~~~~~~~

**Fixed**
  - Fixed compatibility issues with Numpy 2.0 and Scipy 1.14.0+ and above.
  - Fixed a critical bug introduced in v0.3.18 where the incorrectly included ``simple_df`` broke ``fitAMARES`` when using HSVD generated parameters.

v0.3.22
~~~~~~~

**Fixed**
  - Fixed a bug in ``initialize_FID`` where J-coupling constants in the priori knowledge spreadsheet could not be float numbers.

v0.3.21
~~~~~~~

**Added**
  - Added ``delta_phase`` parameter to ``initialize_FID`` for applying additional phase offset (in degrees) to the prior knowledge phase values.
  - Added ``delta_phase`` to script ``amaresfit.py``

v0.3.20
~~~~~~~

**Added**
  - Added ``scale_amplitude`` to ``initialize_FID`` to scale the amplitude of input prior knowledge dataset.
  - Added ``scale_amplitude`` to script ``amaresfit.py``
  - Added a bool ``notebook`` to ``run_parallel_fitting_with_progress`` to toggle the Progress Bar for jupyter notebook.

**Fixed**
  - Fixed an important but not critical bug where lowerbound (``lval``) parameter of linewidth ``dk`` read from prior knowledge dataset by ``initialize_FID`` was always ignored and set to 0 in all versions prior to v0.3.20.
  - Fixed a critical bug introduced in v0.3.19 (commit e319a5c) that broke the function ``run_parallel_fitting_with_progress``.
  - Install ``hlsvdpro`` only when ``platform.machine()`` returns ``x86_64`` or ``amd64``.

v0.3.19
~~~~~~~

**Added**
  - Added ``remove_zero_padding`` function to eliminate zero-filled data points that could cause incorrect SNR calculations.

v0.3.18
~~~~~~~

**Added**
  - Added ``simple_df`` Dataframe to the ``fid_parameters``. 

**Fixed**
  - Fixed a typo in the equation in ``what.rst``.
  

v0.3.17
~~~~~~~

**Added**
  - Added ``objective_func`` parameter to ``multiprocessing.run_parallel_fitting_with_progress`` and ``multiprocessing.fit_dataset`` functions
  - Fixed minor typos

v0.3.16
~~~~~~~

**Added**
  - Added ``params_to_result_pd``, which is the inverse function of ``params_to_result_pd``. 

v0.3.15
~~~~~~~

**Fixed**
  - Fixed a critical bug where J-coupling expressions ending with ``Hz`` were incorrectly interpreted as ``ppm``.
  - Fixed a critical bug that prevented correct parsing of prior knowledge when there was a space in J-coupling strings, such as "0.125 ppm" and "15 Hz".
  - Loosen the bounds of chemical shift of ATP peaks in the attached example prior knowledge datasets of human brain at 7T.
  - Updated the ``simple_tutorial.ipynb`` to use the new prior knowledge dataset and the new API.


v0.3.14
~~~~~~~

**Added**
  - Added ``print_lmfit_fitting_results``, a function to print key ``lmfit`` fitting results from the ``fitting_results.out_obj``.

**Fixed**
  - Changed the version number from ``0.4.0`` to ``0.3.10`` to better manage version increments.

v0.3.13
~~~~~~~

**Added**
  - Added ``result_pd_to_params``, a function that converts fitted results from a DataFrame format into a Parameters object for use with ``simulate_fid``.

**Fixed**
  - Set ``normalize_fid=False`` to be turn it off for ``initialize_FID`` by default.

v0.3.12
~~~~~~~

**Fixed**
  - Fixed a bug in the ``sum_multiplets`` function that prevented the SNR multiplets from being added.
  - Revised the printouts for when ``initialize_with_lm`` is enabled.

v0.3.11
~~~~~~~

**Fixed**
  - Updated the ``result["phase"]`` and ``result["phase_sd"]`` to be wrapped according to the minimum and maximum degree constraints defined in the prior knowledge dataset.

v0.3.10
~~~~~~~

**Added**
  - Added the ``initialize_with_lm`` option to both ``fitAMARES`` and ``run_parallel_fitting_with_progress`` functions.
  - Added a ``highlight_dataframe`` function that highlights rows in a DataFrame based on the values of a specified column.

**Fixed**
  - Updated docstrings in numerous functions to ensure they render properly.
  - Add ``result["phase"] = (result["phase"] + 180) % 360 - 180`` to ``report.py`` to wrap ~360 degrees to ~0
  - Fixed a bug in ``readmat.py``
  - Fix a bug that the internal initializer ``initialize_with_lm`` always uses the input method to initialize. Now it uses ``leastqs`` as the internal initializer.

v0.3.9
~~~~~~

**Added**
  - The peak-wise Signal-to-Noise Ratio (SNR) is now added to each ``result_pd``. The Standard Deviation (SD) of the noise is obtained from the last 10% of points in the FID.

**Fixed**
  - Mute ``__version__`` and ``__author__`` printouts. 

v0.3.8 
~~~~~~

**Added** 
  - Add a ``read_fidall`` function to read GE MNS Research Pack **fidall** generated MAT-files. 

v0.3.7
~~~~~~

**Fixed** 
  - Instead of `try .. catch`, use ``def is_mat_file_v7_3(filename)`` to identify if a file is V-7.3 

v0.3.6
~~~~~~

**Added**
  - The ``readmrs`` function now supports any MAT-files containing either an ``fid`` or ``data`` variable. This enhancement makes it compatible with GE fidall reconstructed MAT-files as well as Matlab formats written by jMRUI.

v0.3.5
~~~~~~

**Fixed**
  - Fixed a bug where, if the ppm needs to be flipped while the carrier frequency is not 0 ppm, the resulting spectrum looks wrong with a ``fftshift()``.

v0.3.4
~~~~~~

**Added**
  - An argument ``noise_var`` to ``initialize_FID`` that allows users to select CRLB estimation methods based on user-defined noise variance. By default, it employs the noise variance estimation method used by OXSA, which estimates noise from the residual. Alternatively, users can opt for jMRUI's default method, which estimates noise from the end of the FID.

v0.3.3
~~~~~~

**Added**
  - Fixed the ``carrier`` placeholder. If ``carrier`` is not 0 ppm, shift the center frequency accordingly. 

v0.3.2
~~~~~~

**Added**
  - Updated the ``generateparameter`` to allow a single number in the bounds region to fix a parameter. This update resolves issues with parameter bounds specification.

v0.3.1
~~~~~~

**Added**
  - Introduced a ``read_nifti`` placeholder to facilitate future support for the NIFTI file format.


**This document describes all notable changes to pyAMARES.**

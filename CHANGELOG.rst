Latest Changes
--------------

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

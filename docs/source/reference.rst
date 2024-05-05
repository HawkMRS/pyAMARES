Code Reference
==============

**AMARES Fitting Kernel**
-------------------------

.. automodule:: pyAMARES.kernel
   :members:
   :undoc-members:
   :show-inheritance:

Prior Knowledge Parsing Modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pyAMARES.kernel.PriorKnowledge
   :members:
   :undoc-members:
   :show-inheritance:

FID modeling functions
~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pyAMARES.kernel.fid
   :members:
   :undoc-members:
   :show-inheritance:

AMARES fitting function by lmfit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pyAMARES.kernel.lmfit
   :members:
   :undoc-members:
   :show-inheritance:

Objective Function
~~~~~~~~~~~~~~~~~~

.. automodule:: pyAMARES.kernel.objective_func
   :members:
   :undoc-members:
   :show-inheritance:


**Libs**
--------

.. automodule:: pyAMARES.libs
   :members:
   :undoc-members:
   :show-inheritance:

MPFIR 
~~~~~

.. automodule:: pyAMARES.libs.MPFIR
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: fircls1, leja, minphlpnew, pbfirnew 

HSVD initialization
~~~~~~~~~~~~~~~~~~~

.. automodule:: pyAMARES.util.hsvd
   :members:
   :undoc-members:
   :show-inheritance:

**HLSVDPro**
~~~~~~~~~~~~

The `hlsvd` documentation can be found in the `VESPA documentation <https://vespa-mrs.github.io/vespa.io/other_packages/dev_hlsvdpro/>`_.

**Utilities**
-------------
Cramer Rao Lower Bound Estimation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pyAMARES.util.crlb
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: extract_strengs, get_matches

AMARES Report Generation
~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pyAMARES.util.report
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: contains_non_numeric_strings, highlight_rows_crlb_less_than_02

Visualization of Fitting Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pyAMARES.util.visualization
   :members:
   :undoc-members:
   :show-inheritance:

Multiprocessing 
~~~~~~~~~~~~~~~
.. automodule:: pyAMARES.util.multiprocessing
   :members:
   :undoc-members:
   :show-inheritance:

**File I/O**
------------

.. note::
   This module is still under active development. pyAMARES is designed to work with ``FID`` as a 1D 
   NumPy complex array, making it compatible with other Python NMR/MRS libraries. Currently, ``pyAMARES.fileio.readmrs`` supports relatively general data formats, such as CSV, ASCII, Python NumPy, and Matlab MAT-files or Version 7.3 MAT-files.
   Users are encouraged to develop and use their own FID I/O modules.

.. automodule:: pyAMARES.fileio.readmat
   :members:
   :undoc-members:
   :show-inheritance:

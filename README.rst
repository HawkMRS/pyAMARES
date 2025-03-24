**pyAMARES**, an Open-Source Python Library for Fitting Magnetic Resonance Spectroscopy Data
********************************************************************************************

.. image:: https://raw.githubusercontent.com/HawkMRS/pyAMARES/main/pyAMARES_logo.svg
   :width: 400

The full documentation for pyAMARES can be found at `pyAMARES Documentation <https://pyamares.readthedocs.io/en/latest/index.html>`_.

What is pyAMARES?
=================

The pyAMARES package provides the MRS community with an open-source, easy-to-use MRS fitting method in Python. 
It imports prior knowledge from Excel or CSV spreadsheets as initial values and constraints for fitting MRS data 
according to the AMARES model function.



Getting Started
===============

Requirements
------------

.. image:: https://img.shields.io/badge/Python->%3D3.6%2C%203.8+-blue.svg
   :target: https://python.org
   :alt: Python Version

.. note::
   PyAMARES requires Python 3.6 or newer. We recommend using Python 3.8 or newer. If you are using an older version of Python, you will need to upgrade to use pyAMARES.

Installation
------------

.. code-block:: bash

   pip install pyAMARES

See the `Installation Guide <https://pyamares.readthedocs.io/en/latest/install.html>`_ for detailed information.

Run pyAMARES as standard-alone script
-------------------------------------


.. code-block:: bash

   amaresFit -f ./pyAMARES/examples/fid.txt -p  ./pyAMARES/examples/example_human_brain_31P_7T.csv --MHz 120.0 --sw 10000 --deadtime 300e-6 --ifplot --xlim 10 -20 -o simple_example 

Run pyAMARES in a Jupyter Notebook
----------------------------------
**Try Jupyter Notebook on Google Colab** `here <https://colab.research.google.com/drive/184_7MJ6O1BgGYyqNvnXXqtri4_0N4ySw?usp=sharing>`_

.. code-block:: python

   import pyAMARES
   # Load FID from a 2-column ASCII file, and set the MR parameters
   MHz = 120.0 # 31P nuclei at 7T
   sw = 10000 # spectrum width in Hz
   deadtime = 300e-6 # 300 us begin time for the FID signal acquisition

   fid = pyAMARES.readmrs('./pyAMARES/examples/fid.txt')
   # Load Prior Knowledge
   FIDobj = pyAMARES.initialize_FID(fid=fid, 
                                    priorknowledgefile='./pyAMARES/examples/example_human_brain_31P_7T.csv',
                                    MHz=MHz, 
                                    sw=sw,
                                    deadtime=deadtime, 
                                    preview=False, 
                                    normalize_fid=False,
                                    xlim=(10, -20))# Region of Interest for visualization, -20 to 10 ppm

   # Initialize the parameter using Levenberg-Marquard method
   out1 = pyAMARES.fitAMARES(fid_parameters=FIDobj,
                              fitting_parameters=FIDobj.initialParams,
                              method='leastsq',
                              ifplot=False)

   # Fitting the MRS data using the optimized parameter

   out2 = pyAMARES.fitAMARES(fid_parameters=out1,
                             fitting_parameters=out1.fittedParams, # optimized parameter for last step
                             method='least_squares',
                             ifplot=False)
   
   # Save the data
   out2.styled_df.to_html('simple_example.html') # Save highlighted table to an HTML page
                                                 # Python 3.6 does not support to_html. 
   out2.result_sum.to_csv('simple_example.csv') # Save table to CSV spreadsheet
   out2.plotParameters.lb = 2.0 # Line Broadening factor for visualization
   out2.plotParameters.ifphase = True # Phase the spectrum for visualization
   pyAMARES.plotAMARES(fid_parameters=out1, filename='simple_example.svg') # Save plot to SVG 

Fitting Result for Example 31P MRS data
------------------------------------------

.. image:: https://raw.githubusercontent.com/HawkMRS/pyAMARES/main/pyAMARES/examples/simple_example.svg
   :width: 400

.. image:: https://raw.githubusercontent.com/HawkMRS/pyAMARES/main/pyAMARES/examples/simple_example_html.jpeg
   :width: 400

How to cite
===========

If you use pyAMARES in your research, please cite:

Xu, J.; Vaeggemose, M.; Schulte, R.F.; Yang, B.; Lee, C.-Y.; Laustsen, C.; Magnotta, V.A. PyAMARES, an Open-Source Python Library for Fitting Magnetic Resonance Spectroscopy Data. Diagnostics 2024, 14, 2668. `https://doi.org/10.3390/diagnostics14232668 <https://doi.org/10.3390/diagnostics14232668>`_


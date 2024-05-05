**pyAMARES**, an Open-Source Python Library for Fitting Magnetic Resonance Spectroscopy Data
********************************************************************************************

.. image:: pyAMARES_logo.svg
   :width: 400

What is pyAMARES?
=================

PyAMARES package to provide the MRS community with open-source, easy-to-use MRS fitting method in Python.  
It imports prior knowledge from Excel or CSV spreadsheets as initial values and constraints for fitting MRS data according to the AMARES model function. 

Getting Started
===============

Installation
------------
.. code-block:: bash

   pip install pyAMARES

Run pyAMARES as standard-alone script
-------------------------------------


.. code-block:: bash

   amaresFit -f ./pyAMARES/examples/fid.txt -p  ./pyAMARES/examples/example_human_brain_31P_7T.csv --MHz 120.0 --sw 10000 --deadtime 300e-6 --ifplot --xlim 10 -20 -o simple_example 

Run pyAMARES in a Jupyter Notebook
----------------------------------

.. code-block:: python

   import pyAMARES
   # Load FID from a 2-column ASCII file, and set the MR parameters
   MHz = 120.0 # 31P nuclei at 7T
   sw = 10000 # spectrum width in Hz
   deadtime = 300e-6 # 300 us begin time for the FID signal acquisition

   fid = pyAMARES.readmrs('./pyAMARES/examples/fid.txt')
   # Load Prior Knowledge
   FIDobj = pyAMARES.initialize_FID(fid=fid, 
                                    priorknowledge='./pyAMARES/examples/example_human_brain_31P_7T.csv',
                                    MHz=MHz, 
                                    sw=sw,
                                    deadtime=deadtime, 
                                    preview=False)

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
   out2.result_sum.to_cscv('simple_example.csv') # Save table to CSV spreadsheet
   out2.plotParameters.lb = 2.0 # Line Braodening
   out2.plotParameters.ifphase = True # Phase the spectrum for visualization
   pyAMARES.plotAMARES(fid_parameters=out1, filename='simple_example.svg') # Save plot to SVG 

Fitting Result
--------------

.. image:: pyAMARES/examples/simple_example.svg
   :width: 400

.. image:: pyAMARES/examples/simple_example_html.jpeg
   :width: 400

How to cite
===========

If you use pyAMARES in your research, please consider citing the following ISMRM proceeding:

`Jia Xu, Rolf F. Schulte, Baolian Yang, Michael Vaeggemose, Christoffer Laustsen, and Vincent A. Magnotta, Proc. Intl. Soc. Mag. Reson. Med. 32 (2024) 2996. <https://submissions.mirasmart.com/ISMRM2024/ViewSubmissionTeaser.aspx>`_

This citation is based on the current conference proceedings and is tentative. A journal paper is expected to be published in the future, and users will be encouraged to cite the formal publication once it is available.


This document describes all notable changes to pyAMARES.

v0.3.4
------

**Added**
  - An argument ``noise_var`` to ``initialize_FID`` that allows users to select CRLB estimation methods based on user-defined noise variance. By default, it employs the noise variance estimation method used by OXSA, which estimates noise from the residual. Alternatively, users can opt for jMRUI's default method, which estimates noise from the end of the FID.

v0.3.2
------

**Added**
  - Updated the ``generateparameter`` to allow a single number in the bounds region to fix a parameter. This update resolves issues with parameter bounds specification.

v0.3.1
------

**Added**
  - Introduced a ``read_nifti`` placeholder to facilitate future support for the NIFTI file format.

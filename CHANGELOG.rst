This document describes all notable changes to pyAMARES.
v0.3.6
------

**Added**
  - The ``readmrs`` function now supports any MAT-files containing either an ``fid`` or ``data`` variable. This enhancement makes it compatible with GE fidall reconstructed MAT-files as well as Matlab formats written by jMRUI.

v0.3.5
------
**Fixed**
- Fixed a bug where, if the ppm needs to be flipped while the carrier frequency is not 0 ppm, the resulting spectrum looks wrong with a fftshift().

v0.3.4
------

**Added**
  - An argument ``noise_var`` to ``initialize_FID`` that allows users to select CRLB estimation methods based on user-defined noise variance. By default, it employs the noise variance estimation method used by OXSA, which estimates noise from the residual. Alternatively, users can opt for jMRUI's default method, which estimates noise from the end of the FID.

v0.3.3
------

**Added**
  - Fixed the ``carrier`` placeholder. If ``carrier`` is not 0 ppm, shift the center frequency accordingly. 


v0.3.2
------

**Added**
  - Updated the ``generateparameter`` to allow a single number in the bounds region to fix a parameter. This update resolves issues with parameter bounds specification.

v0.3.1
------

**Added**
  - Introduced a ``read_nifti`` placeholder to facilitate future support for the NIFTI file format.

import numpy as np
import warnings
import argparse

def read_nifti(filename):
    """
    Reads MRS data from a NIfTI-MRS file, it assumes single voxel spectroscopy (SVS), and returns a header and an 1D FID array

    Args:
        filename (str): The path and name of the NIfTI file to load.

    Returns:
        tuple: A tuple containing:
            - header (argparse.Namespace): A namespace object with center frequency (MHz), spectral width (sw), dwell time (second), and optionally dead time (second).
            - fid (numpy.ndarray): A complex numpy array containing the frequency-domain MRS data.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        IndexError: If the required header extension is not found in the NIfTI file.
        KeyError: If essential metadata is missing in the NIfTI header.
        ImportError: If nibabel is not installed.

    Example:
        >>> header, fid = read_nifti('example_mrs.nii')
        >>> print(header.MHz, header.sw)
        >>> print(fid.shape)

    Note:
        - This function is a wrapper of the minimal example of loading Nifti-MRS using nibabel:
          https://github.com/wtclarke/nifti_mrs_python_example/tree/86a305f28a45f0d07aab29f52daf3a5d880438d8
        - ``nibabel`` needs to be installed by ``pip install nibabel``, if it has not already been installed by ``pip install spec2nii``
        - The ``AcquisitionStartTime`` is optionally loaded into the header as ``deadtime``. If it is absent, a message is printed but no exception is thrown.
    """
    # This is a wrapper of the minimal exampe of loading Nifti-MRS using nibabel
    # https://github.com/wtclarke/nifti_mrs_python_example/tree/86a305f28a45f0d07aab29f52daf3a5d880438d8
    import json
    import nibabel as nib  # should be installed together with spec2nii

    img = nib.load(filename)
    data = img.get_fdata(dtype=np.complex64)
    fid = data.squeeze()  # Assume SVS
    hdr_ext_codes = img.header.extensions.get_codes()
    mrs_hdr_ext = json.loads(
        img.header.extensions[hdr_ext_codes.index(44)].get_content()
    )
    MHz = mrs_hdr_ext["SpectrometerFrequency"][0] * 1e-6  # MHz
    sw = mrs_hdr_ext["SpectralWidth"]
    dwelltime = 1 / sw
    header = argparse.Namespace()
    header.MHz = MHz
    header.dwelltime = dwelltime
    header.sw = sw
    try:
        mrs_hdr_ext["AcqusitionStartTime"]
        header.deadtime = mrs_hdr_ext["AcqusitionStartTime"]
    except:
        warnings.warn("There is no AcqusitionStartTime!")
    return header, fid
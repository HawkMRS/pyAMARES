import numpy as np
from scipy import io
import warnings


def readmrs(filename):
    """
    Reads MRS data from a file, supporting multiple file formats including ASCII, CSV, NPY, and MATLAB files.

    This function detects the file format based on the file extension and loads the MRS data accordingly.
    For ASCII files, it expects two columns representing the real and imaginary parts. 
    NPY files should contain a NumPy array, and MATLAB files should contain a variable named ``fid`` and/or ``data``, 
    when both ``fid`` and ``data`` present, only ``fid`` will be used. 

    Args:
        filename (str): The path and name of the file from which to load the MRS data.

    Returns:
        numpy.ndarray: A complex numpy array containing the MRS data from the file.

    Raises:
        FileNotFoundError: If the specified file does not exist or cannot be opened.
        ValueError: If the file format is unsupported or the required data cannot be found in the file.
        KeyError:

    Example:
        >>> data = readmrs('fid.txt')
        >>> print(data.shape)
        >>> print(data.dtype)

    Note:
        - For ASCII files, data is expected to be in two columns with the first column as the real part and the second as the imaginary part.
        - For NPY files, it directly loads the NumPy array.
        - For MATLAB files, both traditional (.mat) and V7.3 (.mat) files are supported, but the variable must be named ``fid`` or ``data``.
    """
    if filename.endswith("csv"):
        print("Try to load 2-column CSV")
        data = np.loadtxt(filename, delimiter=",")
        data = data[:, 0] + 1j * data[:, 1]
    elif filename.endswith("txt"):
        print("Try to load 2-column ASCII data")
        data = np.loadtxt(filename, delimiter=" ")
        data = data[:, 0] + 1j * data[:, 1]
    elif filename.endswith("npy"):
        print("Try to load python NPY file")
        data = np.load(filename)
    elif filename.endswith("mat"):
        try:
            print("Try to load Matlab mat file with the var saved as `fid` or `data`")
            matdic = io.loadmat(filename)
        except:
            import mat73

            print(
                "Try to load Matlab V7.3 mat file with the var saved as `fid` or `data`"
            )
            matdic = mat73.loadmat(filename)
        if "fid" in matdic.keys() and "data" in matdic.keys():
            data = matdic["fid"].squeeze().astype("complex")
        elif "fid" in matdic.keys():
            data = matdic["fid"].squeeze().astype("complex")
        elif "data" in matdic.keys():
            data = matdic["data"].squeeze().astype("complex")
        else:
            raise KeyError("Neither 'fid' nor 'data' found in the loaded .mat file")
    else:
        raise NotImplementedError(
            "PyAMARES only supports 2-column data in TXT, CSV, MAT-files!"
        )
    # assert len(data.shape) == 1
    if len(data.shape) != 1:
        warnings.warn(
            "Note pyAMARES.fitAMARES only fits 1D MRS data, however, your data shape is {data.shape}. Is it MRSI or raw MRS data that needs to be coil-combined?"
        )

    print("data.shape=", data.shape)
    return data


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
        - The ``AcquisitionStartTime`` is optionally loaded into the header as ``deadtime``. If it is absent, a message is printed but no exception is thrown.
        - Errors related to missing nibabel or JSON handling are not caught explicitly but will result in standard Python exceptions being raised.
    """
    # This is a wrapper of the minimal exampe of loading Nifti-MRS using nibabel
    # https://github.com/wtclarke/nifti_mrs_python_example/tree/86a305f28a45f0d07aab29f52daf3a5d880438d8
    import json
    import nibabel as nib  # should be installed together with spec2nii
    import argparse

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

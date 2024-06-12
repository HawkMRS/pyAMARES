import numpy as np
from scipy import io
import warnings
import mat73
from .readfidall import is_mat_file_v7_3


def readmrs(filename):
    """
    Reads MRS data from a file, supporting multiple file formats including ASCII, CSV, NPY, and MATLAB files.

    This function detects the file format based on the file extension and loads the MRS data accordingly.
    For ASCII files, it expects two columns representing the real and imaginary parts. 
    NPY files should contain a NumPy array, and MATLAB files should contain a variable named ``fid`` and/or ``data``, 
    when both ``fid`` and ``data`` present, only ``fid`` will be used. 
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
        if is_mat_file_v7_3(filename):
            print(
                "Try to load Matlab V7.3 mat file with the var saved as fid or data"
            )
            matdic = mat73.loadmat(filename)
        else:
            print("Try to load Matlab mat file with the var saved as fid or data")
            matdic = io.loadmat(filename)
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



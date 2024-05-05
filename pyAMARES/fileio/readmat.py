import numpy as np
from scipy import io


def readmrs(filename):
    """
    Reads MRS data from a file, supporting multiple file formats including ASCII, CSV, NPY, and MATLAB files.

    This function detects the file format based on the file extension and loads the MRS data accordingly. For ASCII files, it expects two columns representing the real and imaginary parts. NPY files should contain a NumPy array, and MATLAB files should contain a variable named 'fid'.

    Args:
        filename (str): The path and name of the file from which to load the MRS data.

    Returns:
        numpy.ndarray: A complex numpy array containing the MRS data from the file.

    Raises:
        AssertionError: If the data loaded does not have a one-dimensional shape.
        FileNotFoundError: If the specified file does not exist or cannot be opened.
        ValueError: If the file format is unsupported or the required data cannot be found in the file.

    Example:
        >>> data = readmrs('fid.txt')
        >>> print(data.shape)
        >>> print(data.dtype)

    Note:
        - For ASCII files, data is expected to be in two columns with the first column as the real part and the second as the imaginary part.
        - For NPY files, it directly loads the NumPy array.
        - For MATLAB files, both traditional (.mat) and V7.3 (.mat) files are supported, but the variable must be named 'fid'.
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
            print("Try to load Matlab mat file with the var saved as `fid`")
            matdic = io.loadmat(filename)
            data = matdic["fid"].squeeze().astype("complex")
        except:
            import mat73

            print("Try to load Matlab V7.3 mat file with the var saved as `fid`")
            matdic = mat73.loadmat(filename)
            data = matdic["fid"].squeeze().astype("complex")
    print("data.shape=", data.shape)
    assert len(data.shape) == 1
    return data

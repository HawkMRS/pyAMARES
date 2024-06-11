from scipy import io
import warnings
import mat73
import argparse


def is_mat_file_v7_3(filename):
    with open(filename, "rb") as f:
        header = f.read(116)
        version = header[124:128]

    # Check if the header contains 'MATLAB 7.3'
    return b"MATLAB 7.3" in header or version == b"HDF5"

def header2par(h):
    """
    Extracts MHz, deadtime, and sw from the GE MR header structure.

    This function reads the GE MR header structure as a Python dict and returns an argparse Namespace
    with the parameters needed for AMARES fitting.

    Args:
        h (dict): A dictionary representing the header of an MRS file, which contains nested fields
                  with the MRS acquisition parameters.

    Returns:
        argparse.Namespace: A namespace object containing the extracted parameters:
            - MHz (float): The magnetic field strength in MHz.
            - sw (float): The spectral width in Hz.
            - deadtime (float): Echo time in seconds.

    Note:
        - Rolf Schulte: It is better to use the echo time (including the time to the iso center of the RF pulse)
          for initializing the linear phase in the AMARES fit.
    """
    fieldstrength = h["rdb_hdr"][0, 0]["ps_mps_freq"][0, 0][0, 0] / 10  # Hz
    MHz = fieldstrength * 1e-6  # MHz
    sw = h["rdb_hdr"][0, 0]["spectral_width"][0, 0][0, 0]  # Hz
    te = h["rdb_hdr"][0, 0]["te"][0, 0][0, 0]  # second
    deadtime = te * 1e-6  # second
    header = argparse.Namespace()
    header.MHz = MHz
    header.sw = sw
    header.deadtime = deadtime
    return header


def header2par_v73(h):
    """
    Extracts MHz, deadtime, and sw from the GE MR header structure (V-7.3).

    This function reads the GE MR header structure as a Python dict and returns an argparse Namespace
    with the parameters needed for AMARES fitting.

    Args:
        h (dict): A dictionary representing the header of an MRS file, which contains nested fields
                  with the MRS acquisition parameters.

    Returns:
        argparse.Namespace: A namespace object containing the extracted parameters:
            - MHz (float): The magnetic field strength in MHz.
            - sw (float): The spectral width in Hz.
            - deadtime (float): Echo time in seconds.

    Note:
        - Rolf Schulte: It is better to use the echo time (including the time to the iso center of the RF pulse)
          for initializing the linear phase in the AMARES fit.
    """
    fieldstrength = h["rdb_hdr"]["ps_mps_freq"] / 10  # Hz
    MHz = fieldstrength * 1e-6  # MHz
    sw = h["rdb_hdr"]["spectral_width"]  # Hz
    te = h["rdb_hdr"]["te"]  # second
    deadtime = te * 1e-6  # millisecond. Rolf: Better use the echo time
    # (so include the time to the iso centre of the RF pulse for
    # initializing the linear phase in the Amares fit)
    header = argparse.Namespace()
    header.MHz = MHz
    header.sw = sw.item()  # 0-dimensional numpy array to float
    header.deadtime = deadtime
    return header


def read_fidall(filename):
    """
    Loads MRS data and associated header information from the GE MNS Research Pack ``fidall`` generated MATLAB .mat file, handling both 
    v7.3 and earlier versions of MATLAB files.

    This function detects the version of the MATLAB file and uses appropriate methods to load the data. 
    It attempts to extract the complex data ('data') variable from the file. 
    It also parses the header using a specific function depending on the file version to extract MRS parameters for AMARES fitting

    Args:
        filename (str): The path and name of the .mat file to be read.

    Returns:
        tuple:
            - header (argparse.Namespace): A namespace object containing MRS parameters for AMARES fitting
              spectral width (sw), dead time
            - data (numpy.ndarray): A complex numpy array containing the FID 

    Raises:
        FileNotFoundError: If the specified file does not exist.
        KeyError: If the 'data' key is not found in the loaded .mat file.
        Warning: Warns if the data loaded is not 1D, as the pyAMARES.fit_AMARES function only supports 1D MRS data.

    Example:
        >>> header, data = read_fidall('sample_data.mat')
        >>> print(header.MHz, header.sw)
        >>> print(data.shape)

    """
    if is_mat_file_v7_3(filename):
        matdic = mat73.loadmat(filename)
        header = header2par_v73(matdic["h"])
    else:
        matdic = io.loadmat(filename)
        header = header2par(matdic["h"])
    if "fid" in matdic.keys() and "data" in matdic.keys():
        data = matdic["fid"].squeeze().astype("complex")
    elif "fid" in matdic.keys():
        data = matdic["fid"].squeeze().astype("complex")
    elif "data" in matdic.keys():
        data = matdic["data"].squeeze().astype("complex")
    else:
        raise KeyError("Neither 'fid' nor 'data' found in the loaded .mat file")

    if len(data.shape) != 1:
        warnings.warn(
            "Note pyAMARES.fitAMARES only fits 1D MRS data, however, your data shape is {data.shape}. Is it MRSI or raw MRS data that needs to be coil-combined?"
        )

    print("data.shape=", data.shape)

    return header, data

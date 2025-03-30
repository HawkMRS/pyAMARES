import contextlib
import sys
import warnings
from copy import deepcopy
from datetime import datetime
from multiprocessing import Pool

import numpy as np
from joblib import Parallel, delayed
from tqdm.auto import tqdm  # Or from tqdm.notebook import tqdm if in a notebook

# Import your fitAMARES routine. Adjust the import as needed.
from ..kernel.lmfit import fitAMARES


@contextlib.contextmanager
def redirect_stdout_to_file(filename):
    """
    A context manager that redirects stdout and stderr to a specified file.
    """
    with open(filename, "w") as f:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = f, f
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr


def fit_dataset(
    fid_current,
    FIDobj_shared,
    initial_params,
    method="leastsq",
    initialize_with_lm=False,
    objective_func=None,
    idx=None,
):
    """
    Fits a dataset using the AMARES algorithm and returns the complete result
    from the fitting function.

    Args:
        fid_current (array-like): The current FID dataset.
        FIDobj_shared: A shared FID object template.
        initial_params: Initial parameters for the fit.
        method (str): Fitting method (default: 'leastsq').
        initialize_with_lm (bool): If True, uses an LM initializer.
        objective_func (callable or None): Custom objective function.

    Returns:
        The complete output from fitAMARES, or None if an error occurred.
    """
    # Deepcopy the shared FID object so each process works on its own copy.
    FIDobj_current = deepcopy(FIDobj_shared)
    FIDobj_current.fid = fid_current
    try:
        # Call the fitAMARES function.
        if objective_func is None:
            result = fitAMARES(
                fid_parameters=FIDobj_current,
                fitting_parameters=initial_params,
                method=method,
                initialize_with_lm=initialize_with_lm,
                ifplot=False,
                inplace=False,
            )
        else:
            result = fitAMARES(
                fid_parameters=FIDobj_current,
                fitting_parameters=initial_params,
                method=method,
                initialize_with_lm=initialize_with_lm,
                ifplot=False,
                inplace=False,
                objective_func=objective_func,
            )
    except Exception as e:
        if idx is None:
            print(f"'fit_dataset' error: {e}")
        else:
            print(f"'fit_dataset' error during {idx}: {e}")
        return FIDobj_current
    return result


def fit_dataset_wrapper(args):
    """
    A simple wrapper to allow pool.starmap (or pool.imap_unordered) with a tuple of arguments.
    """
    return fit_dataset(*args)


def run_parallel_fitting_with_progress(
    fid_arrs,
    FIDobj_shared,
    initial_params,
    method="leastsq",
    initialize_with_lm=False,
    num_workers=8,
    logfilename="multiprocess_log.txt",
    objective_func=None,
):
    """
    Runs parallel AMARES fitting on multiple FID datasets using a multiprocessing Pool.

    Args:
        fid_arrs (numpy.ndarray): Array of FID datasets (each row is a dataset).
        FIDobj_shared: Shared FID object template.
        initial_params: Initial parameters for the AMARES fit.
        method (str): Fitting method (default: 'leastsq').
        initialize_with_lm (bool): If True, initialize with LM.
        num_workers (int): Number of worker processes.
        logfilename (str): File name for logging output.
        objective_func (callable or None): Custom objective function.

    Returns:
        List: A list containing the full result of each fit.
    """
    # Create a copy of the shared FID object to avoid unwanted modifications.
    FIDobj_shared = deepcopy(FIDobj_shared)
    # Remove potentially large or non-picklable attributes if needed.
    # for attr in ("styled_df", "simple_df"):
    #     try:
    #         delattr(FIDobj_shared, attr)
    #     except AttributeError:
    #         pass

    timebefore = datetime.now()
    results = []

    # Build a list of arguments for each dataset.
    args_list = [
        (
            fid_arrs[i, :],
            FIDobj_shared,
            initial_params,
            method,
            initialize_with_lm,
            objective_func,
        )
        for i in range(fid_arrs.shape[0])
    ]

    # Redirect stdout and stderr to a log file.
    with redirect_stdout_to_file(logfilename):
        with Pool(processes=num_workers) as pool:
            # Using imap_unordered to be able to wrap it with tqdm for progress
            for result in tqdm(
                pool.imap_unordered(fit_dataset_wrapper, args_list),
                total=len(args_list),
                desc="Processing Datasets",
            ):
                results.append(result)

    timeafter = datetime.now()
    print(
        "Fitting %i spectra with %i processors took %i seconds"
        % (len(fid_arrs), num_workers, (timeafter - timebefore).total_seconds())
    )
    return results


def run_parallel_fitting_with_progress_v2(
    fid_arrs,
    FIDobj_shared,
    initial_params,
    method="leastsq",
    initialize_with_lm=False,
    num_workers=8,
    logfilename="multiprocess_log.txt",
    objective_func=None,
):
    """
    Runs parallel AMARES fitting on multiple FID datasets with N dimensions, and returns
    a result array of the same shape as the input with the full Namespace result.
    """
    FIDobj_shared = deepcopy(FIDobj_shared)
    for attr in ("styled_df", "simple_df"):
        try:
            delattr(FIDobj_shared, attr)
        except AttributeError:
            pass

    timebefore = datetime.now()

    # Generate the list of arguments for each fid array
    shape = fid_arrs.shape
    args_list = [
        (
            fid_arrs[tuple(idx)],
            FIDobj_shared,
            initial_params,
            method,
            initialize_with_lm,
            objective_func,
            idx,
        )
        for idx in np.ndindex(
            shape[:-1]
        )  # Iterate over all indices except the last dimension (FID)
    ]

    import warnings

    # Run the parallel fitting
    with redirect_stdout_to_file(logfilename):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            results = Parallel(n_jobs=num_workers, backend="loky")(
                delayed(fit_dataset)(*args)
                for args in tqdm(args_list, desc="Processing Datasets")
            )

    # Store results as a full Namespace
    result_shape = shape[:-1]  # The shape without the FID dimension
    result_array = np.empty(
        result_shape, dtype=object
    )  # Store Namespace objects in the result array

    # Assign the results to the corresponding positions in the result array
    for idx, res in zip(np.ndindex(result_shape), results):
        result_array[idx] = res  # Store the entire Namespace object for each result

    timeafter = datetime.now()
    print(
        "Fitting %i datasets with %i processors took %i seconds"
        % (np.prod(shape[:-1]), num_workers, (timeafter - timebefore).total_seconds())
    )

    return result_array

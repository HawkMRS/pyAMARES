import sys
import contextlib
from copy import deepcopy
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from ..kernel.lmfit import fitAMARES


@contextlib.contextmanager
def redirect_stdout_to_file(filename):
    """
    A context manager that redirects stdout and stderr to a specified file.

    This function temporarily redirects the standard output (stdout) and
    standard error (stderr) streams to a file, capturing all outputs generated
    within the context block.
    """
    with open(filename, "w") as f:
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = f, f
        try:
            yield
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr


def fit_dataset(fid_current, FIDobj_shared, initial_params, method="leastsq", initialize_with_lm=False, objective_func=None):
    """
    Fits a dataset to a shared FID Parameter object using the AMARES algorithm
    with specified initial parameters and fitting method.

    This function deep copies a shared FID object so that it won't conflict in
    the multiprocessing. Then it updates its FID with the current dataset, and
    applies the AMARES fitting algorithm using the provided initial parameters.
    The fitting results are returned in the pandas dataframe ``FIDobj.result_multiplet``

    Args:
        fid_current (array-like): The current FID dataset to be fitted.
        FIDobj_shared (FID object): A shared FID object template to be used for fitting. This object should contain common settings and parameters applicable to all datasets.
        initial_params (lmfit.Parameters): Initial fitting parameters for the AMARES algorithm.
        method (str, optional): The fitting method to be used. Defaults to "leastsq" (Levenberg-Marquardt).
        initialize_with_lm (bool, optional, default False, new in 0.3.9): If True, a Levenberg-Marquardt initializer (``least_sq``) is executed internally. See ``pyAMARES.lmfit.fitAMARES`` for details. 
        objective_func (callable, optional): Custom objective function for ``pyAMARES.lmfit.fitAMARES``. If None,
          the default objective function will be used. Defaults to None.


    Returns:
        pandas.DataFrame or None: A DataFrame containing the fitting results for the current dataset. Returns None if an error occurs during fitting.

    Raises:
        Exception: If an error occurs during the fitting process, it is caught and a message is printed to the console, and None is returned.
    """
    try:
        FIDobj_current = deepcopy(FIDobj_shared)
        FIDobj_current.fid = fid_current
        if objective_func is None:
            out = fitAMARES(
                fid_parameters=FIDobj_current,
                fitting_parameters=initial_params,
                method=method,  # Use method passed as a parameter to the function
                initialize_with_lm=initialize_with_lm, # New in 0.3.9
                ifplot=False,
                inplace=True,
            )
        else:
            out = fitAMARES(
                fid_parameters=FIDobj_current,
                fitting_parameters=initial_params,
                method=method,  # Use method passed as a parameter to the function
                initialize_with_lm=initialize_with_lm, # New in 0.3.9
                ifplot=False,
                inplace=True,
                objective_func=objective_func
            )

        result_table = FIDobj_current.result_multiplets
        del FIDobj_current
        return result_table
    except Exception as e:
        print(f"Error in fit_dataset: {e}")
        return None


def run_parallel_fitting_with_progress(
    fid_arrs,
    FIDobj_shared,
    initial_params,
    method="leastsq",
    initialize_with_lm=False,
    num_workers=8,
    logfilename="multiprocess_log.txt",
    objective_func=None,
    notebook=True,
):
    """
    Runs parallel AMARES fitting of multiple FID datasets using a shared FID object template and initial parameters.

    This function deep copies a shared FID object and performs parallel fitting on an array of FID datasets.
    It utilizes a process pool to handle the fitting tasks concurrently, logging progress and results to a
    specified file ``logfilename``. The execution time is printed upon completion.

    Args:
        fid_arrs (numpy.ndarray): An array of FID datasets to be fitted, where
          each row corresponds to a different dataset.
        FIDobj_shared (FID object): A shared FID object template to be used
          for all fitting tasks. This object should contain common settings and
          parameters applicable to all datasets.
        initial_params (lmfit.Parameters): Initial fitting parameters for the AMARES algorithm.
        method (str, optional): The fitting method to be used. Defaults to 'leastsq' (Levenberg-Marquardt).
        initialize_with_lm (bool, optional, default False, new in 0.3.9): 
          If True, a Levenberg-Marquardt initializer (``least_sq``) is executed internally. See ``pyAMARES.lmfit.fitAMARES`` for details. 
        num_workers (int, optional): The number of worker processes to use in parallel processing. Defaults to 8.
        logfilename (str, optional): The name of the file where the progress log is saved. Defaults to 'multiprocess_log.txt'.
        objective_func (callable, optional): Custom objective function for ``pyAMARES.lmfit.fitAMARES``. If None,
          the default objective function will be used. Defaults to None.
        notebook (bool, optional): If True, uses tqdm.notebook for progress display in Jupyter notebooks.
          If False, uses standard tqdm. Defaults to True.

    Returns:
        list: A list of fitting result objects (e.g., pandas DataFrames) for each FID dataset.
    """
    if notebook:
        from tqdm.notebook import tqdm
    else:
        from tqdm import tqdm

    FIDobj_shared = deepcopy(FIDobj_shared)
    try:
        del FIDobj_shared.styled_df
    except AttributeError:
        print("There is no styled_df!")
    try:
        del FIDobj_shared.simple_df
    except AttributeError:
        print("There is no styled_df!")
    timebefore = datetime.now()
    results = []

    with redirect_stdout_to_file(logfilename):
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(
                    fit_dataset,
                    fid_current=fid_arrs[i, :],
                    FIDobj_shared=FIDobj_shared,
                    initial_params=initial_params,
                    method=method,
                    initialize_with_lm=initialize_with_lm,
                    objective_func=objective_func,
                )
                for i in range(fid_arrs.shape[0])
            ]

            for future in tqdm(futures, total=len(futures), desc="Processing Datasets"):
                results.append(future.result())

    timeafter = datetime.now()
    print(
        "Fitting %i spectra with %i processors took %i seconds"
        % (len(fid_arrs), num_workers, (timeafter - timebefore).total_seconds())
    )
    return results

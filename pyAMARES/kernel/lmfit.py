import warnings
import re
from datetime import datetime
import numpy as np
import pandas as pd
from lmfit import Minimizer, Parameters
from .fid import fft_params, Compare_to_OXSA
from .objective_func import default_objective


def check_removed_expr(df):
    """
    Checks if the expression ('expr') for all parameters in a ftting parameter
    Dataframe is restricted to a parameter that has already been filtered out.

    This function iterates through each 'expr' in the provided DataFrame, checking
    if it is based on a parameter that is not present in the 'peaklist'.
    If an 'expr' is based on a removed parameter, it's set to None, and a warning is issued.

    Args:
        df (pandas.DataFrame): The fitting parameters

    Returns:
        pandas.DataFrame: A copy of the input DataFrame with updated 'expr' column
        where expressions based on removed parameters are set to None.

    Raises:
        UserWarning: If an 'expr' is found to be dependent on a removed parameter.
    """
    print(
        "Check if the expr for all parameters is restricted to a parameter that has already been filtered out."
    )
    result_df = df.copy()
    peaklist = set([x.split("_")[1] for x in result_df["name"]])

    def correct_expr(row):
        if row["expr"] is None:
            return row["expr"], row["vary"]
        parts = re.split(r"(\W+)", row["expr"])
        if parts[0].split("_")[1] not in peaklist:
            # warnings.warn(f"{row['name'].split('_')[1]} is already removed! Parameters restrained to it will be set to vary.", UserWarning)
            warnings.warn(
                "%s is already removed! Parameters restrained to it will be set to vary."
                % (row["name"].split("_")[1]),
                UserWarning,
            )
            print(f"The expr of {row['name']} is changed from {row['expr']} to None")
            return None, True  # Set expr to None and vary to True
        return row["expr"], row["vary"]  # Return original values if condition not met

    result_series = result_df.apply(correct_expr, axis=1, result_type="expand")
    result_df["expr"], result_df["vary"] = result_series[0], result_series[1]

    return result_df


def filter_param_by_ppm(allpara, fit_ppm, MHz, delta=100):
    """
    Filters the input DataFrame based on specified criteria.

    Args:
        tofilter_pd (DataFrame): DataFrame to be filtered.
        fit_Hz (list): List of frequency values in Hz to define the filtering range.
        delta (float): Extra regions to be included in fit_Hz (Hz).

    Returns:
        DataFrame: DataFrame filtered based on the specified criteria.
    """
    fit_Hz = np.array(fit_ppm) * MHz
    # print(f"{fit_Hz=}")
    print("fit_Hz=%s" % fit_Hz)
    tofilter_pd = parameters_to_dataframe(allpara)
    chemshift_pd = tofilter_pd[tofilter_pd["name"].str.startswith("freq")]

    filtered_df = chemshift_pd[
        (chemshift_pd["value"] > np.min(fit_Hz) - delta)
        & (chemshift_pd["value"] < np.max(fit_Hz) + delta)
    ]

    suffixes = [x.replace("freq_", "") for x in filtered_df["name"]]
    return_filtered_df = tofilter_pd[
        tofilter_pd["name"].apply(lambda x: any(x.endswith(s) for s in suffixes))
    ]
    # Remove the expr if it is mathmatically restrained to another parameter that has already been removed.
    return_filtered_df = check_removed_expr(return_filtered_df)
    return dataframe_to_parameters(return_filtered_df)


def parameters_to_dataframe(params):
    """
    Convert an lmfit.Parameters object into a Pandas DataFrame.

    Args:
        params (lmfit.Parameters): The lmfit.Parameters object to convert.

    Returns:
        pandas.DataFrame: A DataFrame with each parameter as a row and its attributes as columns.
    """
    data = {"name": [], "value": [], "min": [], "max": [], "vary": [], "expr": []}
    for name, param in params.items():
        data["name"].append(name)
        data["value"].append(param.value)
        data["min"].append(param.min)
        data["max"].append(param.max)
        data["vary"].append(param.vary),
        data["expr"].append(param.expr)
    df = pd.DataFrame(data)
    return df


def dataframe_to_parameters(df):
    """
    Convert a Pandas DataFrame into an lmfit.Parameters object.

    Args:
        df (pandas.DataFrame): The DataFrame to convert, where each row represents a parameter and columns correspond to parameter attributes.

    Returns:
        lmfit.Parameters: An object constructed from the DataFrame.
    """
    params = Parameters()
    for index, row in df.iterrows():
        if "expr" in row:
            if pd.isna(row["expr"]):
                params.add(
                    row["name"],
                    value=row["value"],
                    min=row["min"],
                    max=row["max"],
                    vary=row["vary"],
                )
            else:
                params.add(
                    row["name"],
                    value=row["value"],
                    min=row["min"],
                    max=row["max"],
                    vary=row["vary"],
                    expr=row["expr"],
                )
        else:
            params.add(
                row["name"],
                value=row["value"],
                min=row["min"],
                max=row["max"],
                vary=row["vary"],
            )
    return params


def parameters_to_dataframe_result(params):
    """
    Convert the fitting result as a lmfit.Parameters object into a Pandas DataFrame.

    Args:
        params (lmfit.Parameters): The lmfit.Parameters object to convert.

    Returns:
        pandas.DataFrame: A DataFrame with each parameter as a row and its attributes as columns.
    """
    data = {
        "name": [],
        "value": [],
        "min": [],
        "max": [],
        "std": [],
        "vary": [],
        "expr": [],
    }
    for name, param in params.items():
        data["name"].append(name)
        data["value"].append(param.value)
        data["min"].append(param.min)
        data["max"].append(param.max)
        data["std"].append(param.stderr)
        data["vary"].append(param.vary),
        data["expr"].append(param.expr)
        df = pd.DataFrame(data)
    return df

def result_pd_to_params(result_table, MHz=120.):
    """
    Converts fitted results from a DataFrame format into a Parameters object for simulation.

    Args:
        result_table (pd.DataFrame): The fitting results table, which can be like ``result_sum`` or ``result_multiplet``.
        MHz (float): Field strength in MHz. 

    Returns:
        Parameters: A lmfit Parameters() object, ready for use in simulations but not for fitting, because there is no constraint. 
        
    Notes:
        This function serves as a utility for ``simulate_fid``.
    """
    df_name = ['amplitude', 'chem shift(ppm)', 'LW(Hz)', 'phase(deg)', 'g']
    param_name = ['ak', 'freq', 'dk', 'phi', 'g']
    name_dic = dict(zip(df_name, param_name))
    params = Parameters()

    for row in result_table.iterrows():
        # print(row[0])
        for name in df_name:
            value = row[1][name]
            new_name = name_dic[name] + '_' + row[0]
            if new_name.startswith('dk'):
                value = value * np.pi
            if new_name.startswith('phi'):
                value = np.deg2rad(value)
            if new_name.startswith('freq'):
                value = value * MHz
            params.add(name=new_name, value=value)
    
    return params

def params_to_result_pd(params, MHz=300.):
    """
    Converts a Parameters object back into a DataFrame format. The inverse function of ``result_pd_to_params``. 

    Args:
        params (Parameters): The lmfit Parameters() object.
        MHz (float): Field strength in MHz. 

    Returns:
        pd.DataFrame: The fitting results table.
    """
    df_name = ['amplitude', 'chem shift(ppm)', 'LW(Hz)', 'phase(deg)', 'g']
    param_name = ['ak', 'freq', 'dk', 'phi', 'g']
    name_dic = dict(zip(param_name, df_name))

    data = {name: [] for name in df_name}
    index = []

    for param in params.values():
        base_name, index_suffix = param.name.rsplit('_', 1)
        if index_suffix not in index:
            index.append(index_suffix)
        
        if base_name.startswith('dk'):
            value = param.value / np.pi
        elif base_name.startswith('phi'):
            value = np.rad2deg(param.value)
        elif base_name.startswith('freq'):
            value = param.value / MHz
        else:
            value = param.value

        if base_name in name_dic:
            data[name_dic[base_name]].append(value)

    result_table = pd.DataFrame(data, index=index)
    return result_table

def save_parameter_to_csv(params, filename="params.csv"):
    """
    Saves the fitting parameters into a CSV file for easy editing

    Args:
        params (lmfit.Parameters): The lmfit.Parameters object containing the fitting parameters to be saved.
        filename (str, optional): The name of the CSV file where the parameters will be saved. Defaults to 'params.csv'.

    Note:
        This function converts the ``params`` object to a DataFrame before saving it as a CSV file.
    """
    df = parameters_to_dataframe(params)
    print("Saving parameter file to %s" % filename)
    df.to_csv(filename)


def load_parameter_from_csv(filename="params.csv"):
    """
    Loads fitting parameters from a CSV file into an lmfit.Parameters object for fitAMARES.

    Args:
        filename (str, optional): The name of the CSV file from which to load the parameters. Defaults to 'params.csv'.

    Returns:
        lmfit.Parameters: An object containing the fitting parameters loaded from the CSV file.

    Note:
        The function reads the CSV file into a DataFrame, processes it to convert
        NaN to pd.Nonetype so that lmfit can handle, and then converts it to an
        lmfit.Parameters object.
    """

    df = pd.read_csv(filename)
    df = df.dropna(how="all")  # Drop rows where all elements are NaN
    df = df.where(pd.notnull(df), None)  # Conver NaN to pd None
    params = dataframe_to_parameters(df)
    return params


def set_vary_parameters(params, vary_parameter_list=[]):
    """
    Fix all parameters except for those specified in vary_parameter_list and set them to be varied.

    Args:
        params (lmfit.Parameters object): Initial parameters for AMARES fitting
        vary_parameter_list (list of str): A list of the names of parameters to be varied

    Returns:
        lmfit.Parameters object: The modified Parameters object with the specified
    parameters set to vary and all others fixed.
    """
    from copy import deepcopy

    params = deepcopy(params)
    for row in params:
        if row in vary_parameter_list:
            params[row].vary = True
        else:
            params[row].vary = False
    return params


def fitAMARES_kernel(
    fid_parameters,
    fitting_parameters,
    objective_func,
    method="least_squares",
    fit_range=None,
    fit_kws=None,
):
    """
    Core fitting routine for the AMARES algorithm using a specified objective function and fitting parameters.

    Args:
        fid_parameters (argspace namespace): Contains FID data and associated parameters like time axis and ppm scale.
        fitting_parameters (lmfit.Parameters): Parameters for the fitting process.
        objective_func (function): The objective function to be minimized, should take at least the fitting parameters and additional data as arguments.
        method (str, optional): Minimization method used by lmfit.Minimizer. Defaults to 'least_squares'.
        fit_range (tuple or None, optional): Indices specifying the fitting range on the ppm scale. Uses full range if None.
        fit_kws (dict, optional): Options to pass to the lmfit.Minimizer

    Returns:
        lmfit.MinimizerResult: Object containing the fitting results.
    """
    timebefore = datetime.now()
    if fit_range is None:
        min_obj = Minimizer(
            objective_func,
            fitting_parameters,
            fcn_kws={"x": fid_parameters.timeaxis, "fid": fid_parameters.fid},
        )
    else:
        from ..util import get_ppm_limit

        fit_range = get_ppm_limit(fid_parameters.ppm, fit_range)
        # print(f"Fitting range {fid_parameters.ppm[fit_range[0]]} ppm to {fid_parameters.ppm[fit_range[1]]} ppm!")
        print(
            "Fitting range %s ppm to %s ppm!"
            % (fid_parameters.ppm[fit_range[0]], fid_parameters.ppm[fit_range[1]])
        )
        min_obj = Minimizer(
            objective_func,
            fitting_parameters,
            fcn_kws={
                "x": fid_parameters.timeaxis,
                "fid": fid_parameters.fid,
                "fit_range": fit_range,
            },
        )

    if fit_kws is not None:
        out_obj = min_obj.minimize(method=method, **fit_kws)
    else:
        out_obj = min_obj.minimize(method=method)
    timeafter = datetime.now()
    # print(f"Fitting with {method=} took {(timeafter - timebefore).total_seconds()} seconds")
    print(
        "Fitting with method=%s took %s seconds"
        % (method, (timeafter - timebefore).total_seconds())
    )
    return out_obj


def fitAMARES(
    fid_parameters,
    fitting_parameters,
    objective_func=default_objective,
    method="least_squares",
    ifplot=True,
    fit_range=None,
    inplace=False,
    plotParameters=None,
    initialize_with_lm=False,
    fit_kws=None,
):
    """
    Fit the AMARES algorithm to the given FID parameters and fitting parameters.

    This function applies the AMARES fitting algorithm to the provided FID and fitting parameters,
    optionally plotting the results and modifying the parameters in place.

    Args:
        fid_parameters (argspace namespace): The FID parameters to be used in the fitting process.
        fitting_parameters (lmfit.Parameters): The initial parameters for lmfitting
        objective_func (function): The objective function to be minimized during the fitting.
        method (str, optional): The method to be used for fitting. Defaults to 'least_squares'.
        initialize_with_lm (bool, optional, default False, new in 0.3.9): If True, a Levenberg-Marquardt initializer (``least_sq``) is executed internally.  
        fit_range (tuple or None, optional): The range within which to perform the fitting. Defaults to None.
        inplace (bool, optional): If True, the original fid_parameters will be modified.
                                    Otherwise, a copy will be modified and returned.
        plotParameters (argparse.Namespace or None, optional): A namespace containing parameters for plotting and data processing. The namespace includes:

            - deadtime (float): The dead time before the FID acquisition starts.
            - lb (float): Line broadening factor in Hz.
            - sw (float): Spectral width in Hz.
            - xlim (tuple of float): Limits for the x-axis in ppm, for example, (10, -20).
            - ifphase (bool): turn on 0th and 1st order phasing.

            If None, default parameters defined in fid_parameters.plotParameters are used.

    Returns:
        If ``inplace=True``, the function returns the lmfit.MinimizerResult object while the input ``fid_parameters`` is modified in place.
        Otherwise, the function returns the modified ``fid_parameters`` instead of modifying ``fid_parameters`` inplace.

    """
    from ..util.report import report_amares

    if inplace:
        print("The fid_parameters will be modified inplace!")
    else:
        from copy import deepcopy

        print(
            "A copy of the input fid_parameters will be returned because inplace=%s"
            % inplace
        )
        fid_parameters = deepcopy(fid_parameters)
        fitting_parameters = deepcopy(fitting_parameters)
    # Generate toleration if fit_kws is None
    if fit_kws is None:
        amp0 = np.abs(np.max(fid_parameters.fid))
        tol = np.sqrt(amp0) * 1e-6
        fit_kws = {"max_nfev": 1000, "xtol": tol, "ftol": tol}
        # fit_kws = {'max_nfev':1000, 'xtol':tol, 'ftol':tol, 'gtol':tol}
        print("Autogenerated tol is %3.3e" % tol)
    if not initialize_with_lm:
        # The old API, without an initializer
        out_obj = fitAMARES_kernel(
        fid_parameters,
        fitting_parameters,
        objective_func,
        method,
        fit_range,
        fit_kws=fit_kws,
        )  # fitting kernel
    else:
        print("Run internal leastsq initializer to optimize fitting parameters for the next %s fitting" % method)
        params_LM = fitAMARES_kernel(
        fid_parameters,
        fitting_parameters,
        objective_func,
        'leastsq',
        fit_range,
        fit_kws=fit_kws,
        )  # initializer
        out_obj = fitAMARES_kernel(
        fid_parameters,
        params_LM.params,
        objective_func,
        method,
        fit_range,
        fit_kws=fit_kws,
        )  # fitting kernel


        
        

    # report_fit(out_obj)
    report_amares(out_obj.params, fid_parameters, verbose=False)  # CRLB estimation
    resultfid = fft_params(fid_parameters.timeaxis, out_obj.params, fid=True)
    print_lmfit_fitting_results(out_obj)  # New in 0.3.14. Print out key fitting such as iterations and chi-square. 
    fid_parameters.resNormSq, fid_parameters.relativeNorm = Compare_to_OXSA(
        inputfid=fid_parameters.fid, resultfid=resultfid
    )
    amares_to_plot_pd = fid_parameters.result_multiplets[
        ["chem shift(ppm)"]
    ].copy()  # Make a copy here
    amares_to_plot_pd.loc[:, "id"] = range(len(amares_to_plot_pd))
    amares_to_plot_pd.loc[:, "name"] = amares_to_plot_pd.index
    amares_to_plot_pd = amares_to_plot_pd.copy()  # avoid SettingWithCopyWarning
    amares_to_plot_pd.set_index("id", inplace=True)
    amares_to_plot_pd.columns = ["freq", "name"]

    fid_parameters.amares_to_plot_pd = amares_to_plot_pd
    fid_parameters.fitted_fid = fft_params(
        timeaxis=fid_parameters.timeaxis, params=out_obj.params, fid=True
    )

    if ifplot:
        if plotParameters is None:
            plotParameters = fid_parameters.plotParameters
        plotAMARES(fid_parameters, out_obj.params, plotParameters)
    if inplace:
        return out_obj
    else:
        fid_parameters.out_obj = out_obj
        fid_parameters.fittedParams = out_obj.params
        return fid_parameters


def plotAMARES(fid_parameters, fitted_params=None, plotParameters=None, filename=None):
    """
    Plots the results of AMARES fitting.

    This function visualizes the fitted results obtained from the AMARES algorithm by plotting the original FID data,
    the fitted FID data, and the corresponding frequency components identified during the fitting process.

    Args:
        fid_parameters (argspace namespace): The FID parameters, including time axis and original FID data, used during the fitting process.
        fitted_params (lmfit.Parameters, optional): The fitting results obtained from the lmfit fitting
        plotParameters (argparse.Namespace, optional): A namespace containing parameters for plotting and data processing. The namespace includes:

            - deadtime (float): The dead time before the FID acquisition starts.
            - lb (float): Line broadening factor in Hz.
            - sw (float): Spectral width in Hz.
            - xlim (tuple of float): Limits for the x-axis in ppm, for example, (10, -20).
            - ifphase (bool): turn on 0th and 1st order phasing.

          filename (str or None, optional): If provided, the figure will be saved to this file. Defaults to None.
    """
    from ..util.visualization import combined_plot

    if fitted_params is None:
        print("fitting_parameters is None, just use the fid_parameters.out_obj.params")
        fitted_params = fid_parameters.out_obj.params
    amares_arr = fft_params(
        fid_parameters.timeaxis, fitted_params, fid=True, return_mat=True
    ).T
    if plotParameters is None:
        plotParameters = fid_parameters.plotParameters
    # print(f"{plotParameters.xlim=}")
    combined_plot(
        amares_arr,
        ppm=fid_parameters.ppm,
        p_pd=fid_parameters.amares_to_plot_pd,
        fid=fid_parameters.fid,
        fid_fit=fft_params(
            timeaxis=fid_parameters.timeaxis, params=fitted_params, fid=True
        ),
        xlim=plotParameters.xlim,
        title="AMARES Fitting Result",
        xlabel="ppm",
        plotParameters=plotParameters,
        filename=filename,
    )

def print_lmfit_fitting_results(result):
    """
    Print important fitting results from an lmfit MinimizerResult object.

    Args:
        result (lmfit.MinimizerResult): The result object from lmfit fitting. 

    """
    print("Lmfit Fitting Results:")
    print("----------------")
    print("Number of function evaluations (nfev):", result.nfev)
    print("Reduced chi-squared (redchi):", result.redchi)
    print("Fit success status:", "Success" if result.success else "Failure")
    print("Fit message:", result.message)
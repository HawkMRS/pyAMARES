import sys
import argparse
import pyAMARES


def main():
    parser = argparse.ArgumentParser(description="PyAMARES Command Line Interface")

    parser.add_argument(
        "-f",
        "--fid_data",
        type=str,
        required=True,
        metavar="fid file name",
        help="Path to the FID file in CSV, TXT, NPY, or Matlab format",
    )

    parser.add_argument(
        "-p",
        "--priorknowledgefile",
        type=str,
        default=None,
        metavar="Prior Knowledge Spreadsheet",
        help="Path to xlsx or csv file containing prior knowledge parameters",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        metavar="output prefix",
        help="prefix of saved html report and images",
    )
    parser.add_argument(
        "--MHz",
        type=float,
        default=120,
        metavar="B0",
        help="The field strength in MHz",
    )
    parser.add_argument(
        "--sw",
        type=float,
        default=10000,
        metavar="Hz",
        help="The spectral width in Hz",
    )
    parser.add_argument(
        "--deadtime",
        type=float,
        default=200e-6,
        metavar="seconds",
        help="The dead time or begin time before the FID signal starts",
    )
    parser.add_argument(
        "--normalize_fid", action="store_true", help="Normalize the FID data"
    )
    parser.add_argument(
        "--scale_amplitude", type=float, default=1.0, metavar="float", help="Scale the amplitude of the FID data"
    )
    parser.add_argument(
        "--flip_axis",
        action="store_true",
        help="Flip the FID axis by taking the complex conjugate",
    )
    parser.add_argument(
        "--ifphase", action="store_true", help="Phase the plotAMARES spectrum"
    )
    parser.add_argument(
        "--lb",
        type=float,
        default=2.0,
        metavar="float",
        help="Line Broadening factor in Hz for plotAMARES",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Display a preview plot of the original and initialized FID spectra",
    )
    parser.add_argument(
        "--carrier",
        type=float,
        default=0.0,
        metavar="ppm",
        help="The carrier frequency",
    )
    parser.add_argument(
        "--truncate_initial_points",
        type=int,
        default=0,
        metavar="number of points",
        help="Truncate initial points from FID to remove fast decaying components (e.g. macromolecule).",
    )
    parser.add_argument(
        "--g_global",
        type=float,
        default=0.0,
        metavar="(float) g for all peaks",
        help="Global value for the 'g' parameter in prior knowledge",
    )
    parser.add_argument(
        "--ppm_offset",
        type=float,
        default=0,
        metavar="offset in ppm",
        help="Adjust the chemical shift in prior knowledge file",
    )
    parser.add_argument(
        "--xlim",
        type=float,
        nargs=2,
        metavar=("xmin", "xmax"),
        help="The x-axis limits for the preview plot in ppm",
    )
    parser.add_argument(
        "--delta_phase",
        type=float,
        default=0.0,
        metavar="phase in degrees",
        help="Additional phase shift in degrees to be applied to the prior knowledge",
    )
    parser.add_argument(
        "--use_hsvd",
        action="store_true",
        help="Use HSVD for initial parameter generation",
    )
    parser.add_argument(
        "--num_of_component",
        type=int,
        default=12,
        metavar="number of components",
        help="Number of components for HSVD decomposition",
    )

    parser.add_argument(
        "--method",
        type=str,
        default="least_squares",
        metavar="leastsq or least_squares",
        help="Fitting method, leastsq (Levenberg-Marquardt Method) or least_squares (default,Trust Region Reflective Method)",
    )
    parser.add_argument(
        "--ifplot", default=True, action="store_true", help="Plot the fitting results"
    )

    args = parser.parse_args()

    # Load FID data from file
    # fid = np.load(args.fid_data)
    fid = pyAMARES.readmrs(args.fid_data)

    # Initialize FID
    FIDobj = pyAMARES.initialize_FID(
        fid,
        priorknowledgefile=args.priorknowledgefile,
        MHz=args.MHz,
        sw=args.sw,
        deadtime=args.deadtime,
        normalize_fid=args.normalize_fid,
        scale_amplitude=args.scale_amplitude,
        flip_axis=args.flip_axis,
        preview=args.preview,
        carrier=args.carrier,
        xlim=args.xlim,
        ppm_offset=args.ppm_offset,
        g_global=args.g_global,
        delta_phase=args.delta_phase,
    )

    if args.use_hsvd:
        # Use HSVDinitializer if the flag is set
        allpara_hsvd = pyAMARES.HSVDinitializer(
            fid_parameters=FIDobj,
            num_of_component=args.num_of_component,
            preview=args.preview,
        )
        fitting_parameters = allpara_hsvd
    else:
        # Use initialParams from FIDobj if HSVD is not used
        fitting_parameters = FIDobj.initialParams

    out1 = pyAMARES.fitAMARES(
        fid_parameters=FIDobj,
        fitting_parameters=fitting_parameters,
        method="leastsq",
        ifplot=False,
        inplace=False,
    )

    if args.method != "leastsq":
        out1 = pyAMARES.fitAMARES(
            fid_parameters=out1,
            fitting_parameters=out1.fittedParams,
            method=args.method,
            ifplot=False,
            inplace=False,
        )

    out1.result_sum.to_csv(args.output + ".csv")
    if sys.version_info >= (3,7):
        out1.styled_df.to_html(args.output + ".html")
    else:
        print("Skipping highlighted table HTML output because it only works with Python >= 3.7")
    if args.ifplot:
        out1.plotParameters.ifphase = args.ifphase
        out1.plotParameters.lb = args.lb
        pyAMARES.plotAMARES(fid_parameters=out1, filename=args.output + ".svg")


if __name__ == "__main__":
    main()

from copy import deepcopy

import numpy as np
import matplotlib.pyplot as plt
import scipy
from scipy.signal import firls, freqz, lfilter

import nmrglue as ng


def fircls1(M, wc, ri, sup):
    """
    Approximate MATLAB's fircls1 function for designing a low-pass FIR filter.

    Args:
        M (int): Filter order.
        wc (float): Normalized cutoff frequency (0 to 1, where 1 corresponds to the Nyquist frequency).
        ri (float): Passband ripple.
        sup (float): Stopband attenuation (suppression factor).

    Returns:
        numpy.ndarray: Filter coefficients.
    """
    bands = [0, wc, wc + 2 * (1 - wc) / (M + 1), 1]
    desired = [1, 1, 0, 0]  

    weights = [1 / ri, 1 / sup]

    if scipy.__version__ >= '1.14.0':
        h = firls(M + 1, bands, desired, weight=weights, fs=2.0)
    else:
        # e.g. Scipy 1.10 
        h = firls(M + 1, bands, desired, weights)

    return h


def leja(x_in):
    x = np.array(x_in).flatten()  # Ensure x is a 1D array
    n = len(x)
    x_out = np.zeros(
        n, dtype=complex
    )  

    a = np.tile(x, (n + 1, 1))
    a[0, :] = np.abs(a[0, :])

    ind = np.argmax(a[0, :n])
    if ind != 0:
        a[:, [0, ind]] = a[:, [ind, 0]]  

    x_out[0] = a[n, 0]
    a[1, 1:n] = np.abs(a[1, 1:n] - x_out[0])

    for l in range(1, n - 1):
        product_max = np.argmax(np.prod(a[:l, l:n], axis=0)) + l
        if l != product_max:
            a[:, [l, product_max]] = a[:, [product_max, l]]  # Swap columns in 'a'
        x_out[l] = a[n, l]
        a[l + 1, l + 1 : n] = np.abs(a[l + 1, l + 1 : n] - x_out[l])

    x_out[-1] = a[n, n - 1]  
    return x_out


def minphlpnew(h0):
    M = len(h0)
    rh = np.roots(h0)  

    rn = [rh[i] for i in range(M - 1) if abs(rh[i]) < 0.99]
    rn2 = [rh[i] for i in range(M - 1) if 0.99 < abs(rh[i]) < 1.01]

    h1 = np.poly(leja(rn))
    h3 = np.poly(leja(rn2))
    h1 = np.real(h1)
    h3 = np.real(h3)

    h2 = np.convolve(h1, h1)
    h4 = np.convolve(h2, h3)

    w, h0_freq = freqz(h0)
    w, h4_freq = freqz(h4)
    desired = max(abs(h0_freq))
    actual = max(abs(h4_freq))
    fir_h = h4 * (desired / actual)

    return fir_h  # .astype('complex') # skip h1, Jia


def pbfirnew(wl, wh, signal, ri, M0):
    N = np.max(signal.shape)
    wc = (wh - wl) / 2
    # print(f"{wc=} {wh=} {wl=}")

    noise = np.std(np.real(signal[-20:]))
    maxs = np.max(np.abs(np.fft.fft(signal))) / np.sqrt(N)
    sup = noise / maxs * 2
    if sup == 0:
        sup = 1e-6

    mnew = 1e10
    ok = 1
    M = M0

    while ok == 1:
        # print(f'try M={M} wc={wc} ri={ri} sup={sup}')
        fir_h = fircls1(M, wc, ri, sup)
        fir_h = minphlpnew(fir_h)
        M2 = len(fir_h)
        fir_h = fir_h * np.exp(-1j * np.pi * (wl + wc) * np.arange(M2))
        phastemp = np.sum(fir_h)

        if np.real(phastemp) < 0:
            phas = np.pi + np.arctan(np.imag(phastemp) / np.real(phastemp))
        else:
            phas = np.arctan(np.imag(phastemp) / np.real(phastemp))
        # print(f"{phas=}")
        fir_h = fir_h * np.exp(-1j * phas)
        fir_h3 = fir_h
        # f = filter(fir_h, 1, signal[::-1])
        f = lfilter(fir_h, [1], signal[::-1])  # needs to check

        ff = np.abs(np.fft.fftshift(np.fft.fft(f[::-1][:M], 2048)))
        mold = np.max(ff[: round((wl + 1) * 1024) - 10]) / np.sqrt(N)
        mold2 = np.max(ff[round((wh + 1) * 1024) + 10 :]) / np.sqrt(N)
        mold = max(mold, mold2)
        ttt = 2 * noise
        if mold < 2 * noise:
            ok = 0
        else:
            ok = 1
            if mold > 0.9 * mnew:
                M += 10
                if M >= 80:  # go here only at the end if the filter is larger than 80
                    ok = 0
                    sup = supold
                    M = Mold
                    fir_h = fircls1(M, wc, ri, sup)
                    fir_h = minphlpnew(fir_h)
                    # fir_h = minphase(fir_h)
                    # fir_h = minphlp(fir_h)
                    M2 = len(fir_h)
                    fir_h = fir_h * np.exp(-1j * np.pi * (wl + wc) * np.arange(M2))
                    phastemp = np.sum(fir_h)
                    if np.real(phastemp) < 0:
                        phas = np.pi + np.arctan(np.imag(phastemp) / np.real(phastemp))
                    else:
                        phas = np.arctan(np.imag(phastemp) / np.real(phastemp))
                    fir_h = fir_h * np.exp(-1j * phas)
                    # fil = filter(fir_h, 1, signal[::-1])
                    fil = lfilter(fir_h, [1], signal[::-1])
                    ff = np.abs(np.fft.fftshift(np.fft.fft(fil[::-1][:M2], 2048)))
                    mold = np.max(ff[: round((wl + 1) * 1024) - 10]) / np.sqrt(N)
                    mold2 = np.max(ff[round((wh + 1) * 1024) + 10 :]) / np.sqrt(N)
                    mold = max(mold, mold2)
                sup *= 2.0
            else:
                mnew = mold * 1
                Mold = M * 1
                supold = sup * 1
                M = M0 * 1
            sup /= 2.0
        # plt.plot(fir_h, 'ro-')
        # plt.show()
    return fir_h


def MPFIR(
    fid,
    dwelltime,
    MHz=120.0,
    ppm_range=(-20, 20),
    rippass=0.01,
    M=50,
    carrier=0,
    ifplot=False,
    xlim=None,
):
    """
    Filter out a specific region of the spectrum using the maximum-phase FIR filter (Ref 1)

    This function applies an MPFIR filter to the provided FID signal based on the specified parameters,
    optionally plotting the original and filtered FID signals in the frequency domain.
    Adapted from the SPID software. See Ref2.

    Args:
        fid (1D array): The FID signal array.
        dwelltime (float): Dwell time.
        MHz: The field strength in MHz.
        ppm_range (tuple, optional): The range of ppm values to filter. Defaults to (-20, 20).
        rippass (float, optional): The passband ripple of the filter. Defaults to 0.01.
        M (int, optional): The filter length. Defaults to 50.
        carrier (float, optional): The carrier frequency offset in ppm. Defaults to 0.
        ifplot (bool, optional): If True, plots the input and filtered FID signals. Defaults to False.
        xlim (tuple, optional): The x-axis limits for the plot. Defaults to None.

    Returns:
        The filtered FID signal.

    References:
        1. T. Sundin et al, JMR, 139(2):189-204, 1999.
        2. Poullet et al, Manual: Simulation Package based on In vitro Databases (SPID).
    """
    signal = fid.copy()  
    step = dwelltime * 1000  # s to ms
    frequency = MHz * 1e3  # to kHz
    xmin = (min(ppm_range) - carrier) * frequency / 1e6  # in kHz
    xmax = (max(ppm_range) - carrier) * frequency / 1e6  # in kHz
    wl = xmin * 2 * step
    wh = xmax * 2 * step
    # print(f"{wl=} {wh=}")
    fir_h = pbfirnew(wl, wh, signal, rippass, M)
    signal = lfilter(np.flip(fir_h), 1, signal)
    signal = np.concatenate([signal[len(fir_h) - 1 :], np.zeros(len(fir_h) - 1)])
    if ifplot:
        sw = 1.0 / dwelltime  # Hz
        ppm = np.linspace(-sw / np.abs(MHz) / 2, sw / np.abs(MHz) / 2, len(signal))
        plt.plot(ppm, np.abs(ng.proc_base.fft(fid)), "r-", alpha=0.6, label="input fid")
        plt.plot(ppm, np.abs(ng.proc_base.fft(signal)), alpha=0.6, label="filtered fid")
        plt.axvspan(
            ppm_range[0],
            ppm_range[1],
            color="gray",
            alpha=0.1,
            label="selected region\n%i to %i ppm"
            % (np.min(ppm_range), np.max(ppm_range)),
        )
        plt.legend()
        plt.xlabel("ppm")
        if xlim is not None:
            plt.xlim(xlim)
        plt.show()
    return signal


def filter_fid_by_ppm(opts, fit_ppm, ifplot=False, rippass=0.01, M=50):
    """
    Filters the FID signal in the argspace Namespace object 'opts' by a specified ppm range.

    This function takes an 'opts' object containing FID signal parameters,
    applies a Minimum Phase Finite Impulse Response (MPFIR) filter to the FID signal
    based on the specified ppm range, and returns a modified 'opts' object with the filtered FID.

    Args:
        opts (Namespace): An object containing FID signal parameters, including the FID signal, dwell time,
                          spectrometer frequency, and optionally x-axis limits for plotting.
        fit_ppm (tuple): The ppm range to filter the FID signal by.
        ifplot (bool, optional): If True, plots the original and filtered FID signals. Defaults to False.
        rippass (float, optional): The passband ripple of the MPFIR filter. Defaults to 0.01.
        M (int, optional): The number of coefficients for the MPFIR filter. Defaults to 50.

    Returns:
        Namespace: A modified copy of 'opts' with the filtered FID signal.
    """
    opts2 = deepcopy(opts)
    filtered_fid = MPFIR(
        opts2.fid,
        opts2.dwelltime,
        opts2.MHz,
        ppm_range=fit_ppm,
        rippass=rippass,
        M=M,
        carrier=opts.carrier,
        ifplot=ifplot,
        xlim=opts.xlim,
    )
    opts2.fid = filtered_fid
    return opts2

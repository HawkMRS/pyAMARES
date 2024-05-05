import numpy as np


def findnearest(array, value):
    # WARNING! RETURN INDEX!
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx


def get_ppm_limit(ppm, ppmrange=(0, -15)):
    left = ppmrange[0]
    right = ppmrange[1]
    left_ind, right_ind = findnearest(ppm, left), findnearest(ppm, right)
    return min(left_ind, right_ind), max(left_ind, right_ind)

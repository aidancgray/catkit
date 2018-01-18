from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

# noinspection PyUnresolvedReferences
from builtins import *
from hicat.config import CONFIG_INI

import numpy as np
from poppy import zernike
from ...hicat_types import quantity, units

def create_zernike(zernike_index, p2v):
    dm_length = CONFIG_INI.getint("boston_kilo952", 'dm_length_actuators')

    # Add +1 to dm_length to fix a bug in poppy. We trim the extra row and column below.
    linear_ramp = np.linspace(-1, 1, num=dm_length + 1, endpoint=False)

    # Create a 2D ramp.
    x, y = np.meshgrid(linear_ramp, linear_ramp)

    r = np.sqrt(x ** 2 + y ** 2)
    theta = np.arctan2(y, x)

    # Create the zernike array using poppy.
    z = zernike.zernike1(zernike_index, rho=r, theta=theta)

    # Trim the first row and column to get rid of NaNs.
    z = np.delete(z, 0, 0)
    z = np.delete(z, 0, 1)

    # Normalize z between -.5, .5 and multiply by peak_to_valley
    return (z / (np.nanmax(z) - np.nanmin(z))) * p2v

def letter_f_focus_command(f_p2v=400, focus_p2v=-500):
    """
    Creates the letter F in normal orientation when viewed in DS9.
    """
    dm_length = CONFIG_INI.getint("boston_kilo952", 'dm_length_actuators')
    data = np.zeros((dm_length, dm_length))

    # Convert peak the valley from a quantity to nanometers, and get the magnitude.
    zernike_data = create_zernike(4, focus_p2v)

    # Side
    data[10:24, 12] = f_p2v

    # Top
    data[24, 12:22] = f_p2v

    # Middle
    data[19, 12:17] = f_p2v

    return data + zernike_data

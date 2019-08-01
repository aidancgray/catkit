from __future__ import (absolute_import, division,
                        unicode_literals)

import os
import logging

import numpy as np
# noinspection PyUnresolvedReferences
from builtins import *

from ..hicat_types import ImageCentering
from .modules import double_sine
from .Experiment import Experiment
from .. import util
from ..config import CONFIG_INI
from ..hardware import testbed
from ..hicat_types import units, quantity, SinSpecification, FpmPosition, LyotStopPosition


class TakeDmPlateScaleData(Experiment):
    name = "Take DM Plate Scale Data"

    def __init__(self,
                 output_path=None,
                 bias=False,
                 flat_map=True,
                 coron_exposure_time=quantity(100, units.millisecond),
                 coron_nexps=10,
                 angle_range=range(0, 100, 10),
                 ncycles_range=np.arange(5.5, 17.5, .5),
                 peak_to_valley=quantity(50, units.nanometer),
                 phase=90,
                 fpm_position=FpmPosition.coron,
                 lyot_stop_position=LyotStopPosition.in_beam,
                 alignment_speckle=False,
                 centering=ImageCentering.auto,
                 auto_exposure_mask_size=None,
                 suffix="dm_plate_scale",
                 dm=1,
                 **kwargs):
        super(TakeDmPlateScaleData, self).__init__(output_path=output_path, suffix=suffix, **kwargs)
        self.bias = bias
        self.flat_map = flat_map
        self.coron_exposure_time = coron_exposure_time
        self.coron_nexps = coron_nexps
        self.angle_range = angle_range
        self.ncycles_range = ncycles_range
        self.peak_to_valley = peak_to_valley
        self.phase = phase
        self.fpm_position = fpm_position
        self.lyot_stop_position = lyot_stop_position
        self.alignment_speckle = alignment_speckle
        self.centering = centering
        self.auto_exposure_mask_size = auto_exposure_mask_size
        self.dm=dm
        self.kwargs = kwargs

    def experiment(self):

        with testbed.laser_source() as laser:
            coron_laser_current = CONFIG_INI.getint("thorlabs_source_mcls1", "coron_current")
            laser.set_current(coron_laser_current)

            for angle in self.angle_range:
                angles_path = os.path.join(self.output_path, "angle" + str(angle))
                for ncycle in self.ncycles_range:
                    sin_spec = SinSpecification(angle, ncycle, self.peak_to_valley, self.phase)
                    ncycle_path = os.path.join(angles_path, "ncycles" + str(ncycle))
                    double_sine.double_sin_remove_crossterm(sin_spec,
                                                            self.alignment_speckle,
                                                            self.bias,
                                                            self.flat_map,
                                                            self.coron_exposure_time,
                                                            self.coron_nexps,
                                                            self.fpm_position,
                                                            self.auto_exposure_mask_size,
                                                            centering=self.centering,
                                                            path=os.path.join(ncycle_path, "coron"),
                                                            simulator=False,
                                                            lyot_stop_position=self.lyot_stop_position,
                                                            dm=self.dm,
                                                            **self.kwargs)

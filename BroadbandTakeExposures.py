from __future__ import (absolute_import, division,
                        unicode_literals)

# noinspection PyUnresolvedReferences

from builtins import *
import logging
import os

from .Experiment import Experiment
from ..hicat_types import *
from ..hardware.boston.commands import flat_command
from .. import util
from ..hardware import testbed
from ..hardware.thorlabs.ThorlabsFW102C import ThorlabsFW102C
from ..config import CONFIG_INI


class BroadbandTakeExposures(Experiment):
    name = "Broadband Take Exposures"
    log = logging.getLogger(__name__)

    def __init__(self,
                 dm1_command_object=flat_command(bias=False, flat_map=True),  # Default flat with bias.
                 dm2_command_object=flat_command(bias=False, flat_map=True),  # Default flat with bias.
                 exposure_time=quantity(250, units.microsecond),
                 num_exposures=5,
                 camera_type="imaging_camera",
                 coronograph=False,
                 pipeline=True,
                 path=None,
                 exposure_set_name=None,
                 filename=None,
                 suffix=None,
                 **kwargs):
        """
        Takes a set of data with any camera, any DM command, any exposure time, etc.
        :param dm1_command_object: (DmCommand) DmCommand object to apply on a DM.
        :param exposure_time: (pint.quantity) Pint quantity for exposure time.
        :param num_exposures: (int) Number of exposures.
        :param step: (int) Step size to use for the motor positions (default is 10).
        :param path: (string) Path to save data.
        :param camera_type: (string) Camera type, maps to the [tested] section in the ini.
        :param position_list: (list) Postion(s) of the camera
        :param kwargs: Parameters for either the run_hicat_imaging function or the camera itself.
        """
        self.dm1_command_object = dm1_command_object
        self.dm2_command_object = dm2_command_object
        self.exposure_time = exposure_time
        self.num_exposures = num_exposures
        self.camera_type = camera_type
        self.coronograph = coronograph
        self.pipeline = pipeline
        self.path = path
        self.exposure_set_name = exposure_set_name
        self.filename = filename
        self.suffix = suffix
        self.kwargs = kwargs

    def experiment(self):
        # Wait to set the path until the experiment starts (rather than the constructor)
        if self.path is None:
            suffix = "broadband" if self.suffix is None else "broadband_" + self.suffix
            self.path = util.create_data_path(suffix=suffix)

        # Establish image type and set the FPM position and laser current
        if self.coronograph:
            fpm_position = FpmPosition.coron
            laser_current = CONFIG_INI.getint("thorlabs_source_mcls1", "coron_current")
            if self.exposure_set_name is None:
                self.exposure_set_name = "coron"
        else:
            fpm_position = FpmPosition.direct
            laser_current = CONFIG_INI.getint("thorlabs_source_mcls1", "direct_current")
            if self.exposure_set_name is None:
                self.exposure_set_name = "direct"

        # Take data at each filter wheel position.
        with testbed.laser_source() as laser, ThorlabsFW102C("thorlabs_fw102c_2") as filter_wheel:
            laser.set_current(laser_current)

            for position in range(1,7):
                
                filter_wheel.set_position(position)

                # Reverse lookup.
                filters_ini = {int(entry[1]): entry[0] for entry in CONFIG_INI.items("thorlabs_fw102c_1")
                             if entry[0].startswith("filter_")}
                filter_name = filters_ini[position]

                with testbed.dm_controller() as dm:
                    dm.apply_shape_to_both(self.dm1_command_object, self.dm2_command_object)
                    path = testbed.run_hicat_imaging(self.exposure_time, self.num_exposures, fpm_position,
                                                     path=os.path.join(self.path, filter_name),
                                                     filename=self.filename,
                                                     exposure_set_name=self.exposure_set_name,
                                                     camera_type=self.camera_type,
                                                     pipeline=self.pipeline,
                                                     **self.kwargs)
                    return path

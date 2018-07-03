from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

# noinspection PyUnresolvedReferences
from builtins import *

from glob import glob
import logging
import os

from hicat.hardware.boston.DmCommand import DmCommand
from experiments.Experiment import Experiment
from hardware.boston import commands
from hicat_types import units, quantity, ImageCentering
from hicat import util
from experiments.modules.general import take_coffee_data_set


class CoffeePacman(Experiment):
    name = "Coffee Pacman (nom nomn nom)"
    log = logging.getLogger(__name__)

    def __init__(self,
                 path=None,
                 num_exposures=10,
                 coron_exp_time=quantity(100, units.millisecond),
                 direct_exp_time=quantity(1, units.millisecond),
                 centering=ImageCentering.custom_apodizer_spots):
        self.path = path
        self.num_exposures = num_exposures
        self.coron_exp_time = coron_exp_time
        self.direct_exp_time = direct_exp_time
        self.centering = centering

    def experiment(self):
        if self.path is None:
            suffix = "coffee_pacman"
            self.path = util.create_data_path(suffix=suffix)
            util.setup_hicat_logging(self.path, "coffee_pacman")

        # Focus Zernike commands.
        focus_zernike_data_path = "Z:/Testbeds/hicat_dev/data_vault/coffee/coffee_commands/"
        focus_zernike_command_paths = glob(focus_zernike_data_path + "/*p2v/*.fits")

        # Pacman Commands.
        pacman_data_path = "Z:/Testbeds/hicat_dev/data_vault/coffee/coffee_commands/pacman/"
        pacman_command_paths = glob(pacman_data_path + "/dm_command/*/dm_command_2d_noflat.fits")
        pacman_command_paths.sort()
        print(pacman_command_paths)

        for i, command_path in enumerate(pacman_command_paths):
            dm1_command_object = DmCommand.load_dm_command(command_path, flat_map=True)
            take_coffee_data_set(focus_zernike_command_paths,
                                 self.path,
                                 str(i),
                                 self.coron_exp_time,
                                 self.direct_exp_time,
                                 dm1_command_object=dm1_command_object,
                                 num_exposures=self.num_exposures,
                                 centering=self.centering,
                                 raw_skip=100)

import time

from catkit.hardware.boston import commands
from hicat.hardware import testbed
from catkit.catkit_types import units, quantity
from hicat.experiments.Experiment import Experiment


class ApplyActuatorPattern(Experiment):
    """
    Apply a DM map that is specified by a set of actuator numbers.
    """
    name = "Apply Actuator Pattern"

    def __init__(self, apply_to_both=False, dm_num=1, output_path=None, suffix='apply_actuator_pattern', actuators=None):
        super().__init__(output_path=output_path, suffix=suffix)
        self.apply_to_both = apply_to_both
        if apply_to_both:
            self.dm_num = dm_num
        self.actuators = actuators  # list of actuators

    def experiment(self):
        if self.apply_to_both:
            dm_to_poke = 1
            poke_pattern = commands.poke_command(self.actuators, dm_num=dm_to_poke,
                                                 amplitude=quantity(200, units.nanometers))
            dm_to_flat = 2
            flat_pattern = commands.poke_command(self.actuators, dm_num=dm_to_poke,
                                                 amplitude=quantity(-150, units.nanometers))

        else:
            dm_to_poke = self.dm_num
            dm_to_flat = 2 if self.dm_num == 1 else 1

            poke_amplitude = 200 if self.dm_num == 1 else -150

            poke_pattern = commands.poke_command(self.actuators, dm_num=dm_to_poke,
                                                 amplitude=quantity(poke_amplitude, units.nanometers))
            flat_pattern = commands.flat_command(False, True, dm_num=dm_to_flat)

        with testbed.dm_controller() as dm:
            dm.apply_shape(poke_pattern, dm_num=dm_to_poke)
            dm.apply_shape(flat_pattern, dm_num=dm_to_flat)
            self.log.info("{} applied.".format(self.suffix))
            self.log.info(
                " ** This will loop forever, maintaining the {}. You must cancel the script to terminate it. ** ".format(self.suffix))
            self.log.info(
                " ** I.e. use square 'stop' button in PyCharm. Caution - be careful to single click, not double click it! ** ")

            while True:
                time.sleep(1)


class ApplyXPoke(ApplyActuatorPattern):
    """
    Apply a center-symmetric cross poke pattern on DM 1 or DM2, or both.
    """
    name = "Apply X Poke"

    def __init__(self, apply_to_both=False, dm_num=1, output_path=None, suffix='apply_x_poke'):
        self.actuators = [492, 525, 558, 591, 624, 657, 689, 720, 750, 779, 807, 833,  # top right cross beam
                          459, 426, 393, 360, 327, 294, 262, 231, 201, 172, 144, 118,  # bottom left cross beam
                          856, 828, 798, 767, 735, 702, 668, 633, 598, 563, 528, 493,  # top left cross beam
                          458, 423, 388, 353, 318, 283, 249, 216, 184, 153, 123, 95]  # bottom right cross beam
        super().__init__(apply_to_both=apply_to_both, dm_num=dm_num, output_path=output_path, suffix=suffix, actuators=self.actuators)


class ApplyCenterPoke(ApplyActuatorPattern):
    """
    Poke the four central actuators on DM 1 or DM2, or both.
    """
    name = "Apply Center Poke"

    def __init__(self, apply_to_both=False, dm_num=1, output_path=None, suffix='apply_center_poke'):
        self.actuators = [458, 459, 492, 493]
        super().__init__(apply_to_both=apply_to_both, dm_num=dm_num, output_path=output_path, suffix=suffix, actuators=self.actuators)

        # Previous poke amplitudes:
        # DM1: 700 nm
        # DM2: 100 nm


class ApplyCenterPokePlus(ApplyActuatorPattern):
    """
    Poke actuators in a pattern that includes the center poke and four other pokes aligned in a "plus"
    pattern which are visible through the apodizer pattern:
          []

    []    []    []

          []

    This is intended for DM1 to DM2 alignment, and apodizer to DM alignment.
    """
    name = "Apply Center Poke Plus"

    def __init__(self, apply_to_both=False, dm_num=1, output_path=None, suffix='apply_center_poke_plus'):
        self.actuators = [493, 492, 459, 458, 789, 788, 759, 758, 193, 192, 163, 162, 502, 501, 468, 467, 484, 483, 450, 449]
        super().__init__(apply_to_both=apply_to_both, dm_num=dm_num, output_path=output_path, suffix=suffix, actuators=self.actuators)


class ApplyOuterPoke(ApplyActuatorPattern):
    """
    Poke many actuators on outer (?) parts of one or both DMs.
    """
    name = "Apply Outer Poke"

    def __init__(self, apply_to_both=False, dm_num=1, output_path=None, suffix='apply_outer_poke'):
        self.actuators = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 26, 27, 46, 47, 69, 93, 119, 147, 177, 207, 239, 271,
                          305, 339, 373, 407, 441, 475, 509, 543, 577, 611, 645, 679, 711, 743, 773, 803, 831, 857,
                          881, 903, 923, 922, 939, 938, 951, 950, 949, 948, 947, 946, 945, 944, 943, 942, 941, 940,
                          925, 924, 905, 904, 882, 858, 832, 804, 774, 744, 712, 680, 646, 612, 578, 544, 510, 476,
                          442, 408, 374, 340, 306, 272, 240, 208, 178, 148, 120, 94, 70, 48, 28, 29, 12, 13]
        super().__init__(apply_to_both=apply_to_both, dm_num=dm_num, output_path=output_path, suffix=suffix,
                         actuators=self.actuators)

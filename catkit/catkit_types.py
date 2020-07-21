from collections import namedtuple
from enum import Enum
from pint import UnitRegistry


class FlipMountPosition(Enum):
    """
    Enum for the possible states of the Beam Dump.
    """
    IN_BEAM = "in_beam_position"
    OUT_OF_BEAM = "out_of_beam_position"


class FpmPosition(Enum):
    """
    Enum for the possible states for the focal plane mask.
    """
    coron = 1
    direct = 2


class LyotStopPosition(Enum):
    """
    Enum for the possible states for the lyot stop.
    """
    in_beam = 1
    out_of_beam = 2


class ImageCentering(Enum):
    """
    Enum for the image centering options.
    """
    off = 1
    auto = 2
    psf = 3
    satellite_spots = 4
    injected_speckles = 5
    custom_apodizer_spots = 6
    cross_correlation = 7
    global_cross_correlation = 8
    xy_sym = 9


# Create a named tuple to hold metadata
MetaDataEntry = namedtuple("MetaDataEntry", "name, name_8chars, value, comment")


# Named Tuple as a container for sine wave specifications. peak_to_valley must be a pint quantity.
SinSpecification = namedtuple("SinSpecification", "angle, ncycles, peak_to_valley, phase")


# Create shortcuts for using Pint globally.
units = UnitRegistry()


class Quantity(units.Quantity):
    """ Wrapper for pint.Quantity to avoid compounding quantities.

        https://pint.readthedocs.io/en/stable/developers_reference.html#pint.Quantity
    """
    # Add this alias due to __news__() shadowing of the above global units.
    _units = units

    def __new__(cls, value, units=None):
        if isinstance(value, cls._units.Quantity):
            if isinstance(units, str):
                units = cls._units.parse_units(units)
            if value.units != units:
                return value.to(units)
            return value
        else:
            return super().__new__(cls, value, units=units)


# Alias to lower case for backward comparability and to stop linters complaining if we made lower cased the above class.
quantity = Quantity


class Pointer:
    def __init__(self, ref):
        super().__getattribute__("point_to")(ref)

    def __getattribute__(self, name):
        if name == "self":
            return super().__getattribute__("ref")
        elif name == "point_to":
            return super().__getattribute__(name)
        else:
            return super().__getattribute__("ref").__getattribute__(name)

    def __setattr__(self, name, value):
        super().__getattribute__("ref").__setattr__(name, value)

    def __delattr__(self, name):
        super().__getattribute__("ref").__delattr__(name)

    def __dir__(self, name):
        super().__getattribute__("ref").__dir__(name)

    def point_to(self, ref):
        super().__setattr__("ref", ref)

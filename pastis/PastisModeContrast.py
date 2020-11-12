import os
from astropy.io import fits
import astropy.units as u
import numpy as np

from hicat.config import CONFIG_INI
from catkit.hardware.iris_ao import segmented_dm_command
from hicat.experiments.pastis.PastisExperiment import PastisExperiment
from hicat.hardware import testbed_state

from pastis.pastis_analysis import cumulative_contrast_matrix, modes_from_file
from pastis.plotting import plot_contrast_per_mode, plot_cumulative_contrast_compare_accuracy


class PastisModeContrast(PastisExperiment):

    def __init__(self, pastis_results_path, pastis_matrix_path, use_uniform_weights, individual, c_target, probe_filename, dm_map_path, color_filter, nd_direct, nd_coron,
                 num_exposures, exposure_time_coron, exposure_time_direct, auto_expose, file_mode, raw_skip,
                 align_lyot_stop=True, run_ta=True):
        """
        Measure contrast per applied mode, either for individual modes one by one, or cumulatively.

        :param pastis_results_path: str, path to the overall PASTIS data directory, without the 'results' at the end
        :param pastis_matrix_path: str, full path to PASTIS matrix, including filename
        :param use_uniform_weights: bool, if True, will use uniform mode weights, if False, will use segment-based mode weights
        :param individual: bool, if True, will measure contrast for each mode individually, if False will do it cumulatively
        :param c_target: float, target contrast for which the mode weights have been calculated
        :param probe_filename: str, path to probe file, used only to get DH geometry
        :param dm_map_path: str, path to folder that contains DH solution
        :param color_filter: str, wavelength for color flipmount
        :param nd_direct: str, ND filter choice for direct images
        :param nd_coron: str, ND filter choice for coronagraphic images
        :param num_exposures: int, number of exposures for each image acquisition
        :param exposure_time_coron: float, exposure time for coron mode in microseconds
        :param exposure_time_direct: float, exposure time for direct mode in microseconds
        :param auto_expose: bool or {catkit.catkit_types.FpmPosition: bool}, flag to enable auto exposure time correction
        :param file_mode: bool, If true files will be written to disk otherwise only final results are saved
        :param raw_skip: int, Skips x writing-files for every one taken. raw_skip=math.inf will skip all and save no raw image files.
        :param align_lyot_stop: bool, whether to automatically align the Lyot stop before the experiment or not
        :param run_ta: bool, whether to run target acquisition. Will still just measure TA if False.
        """
        if individual:
            self.name = 'PASTIS Mode Contrast Individual'
        else:
            self.name = 'PASTIS Mode Contrast Cumulative'

        super().__init__(probe_filename, dm_map_path, color_filter, nd_direct, nd_coron, num_exposures,
                         exposure_time_coron, exposure_time_direct, auto_expose, file_mode, raw_skip,
                         align_lyot_stop, run_ta)

        self.use_uniform_weights = use_uniform_weights
        self.individual = individual
        self.c_target = c_target

        # Read PASTIS modes from file
        self.pastis_results_path = pastis_results_path
        self.pastis_modes, self.eigenvalues = modes_from_file(self.pastis_results_path)

        # Read PASTIS mode weights from file
        if use_uniform_weights:
            filename_modes_weights = f'mode_requirements_{self.c_target}_uniform.txt'
        else:
            filename_modes_weights = f'mode_requirements_{self.c_target}_segment-based.txt'
        self.mode_weights = np.loadtxt(os.path.join(self.pastis_results_path, 'results', filename_modes_weights))

        # Read PASTIS matrix from file
        self.pastis_matrix_path = pastis_matrix_path
        try:
            self.pastis_matrix = fits.getdata(os.path.join(self.pastis_matrix_path))
        except FileNotFoundError:
            self.pastis_matrix = None

        self.measured_contrast = []

    def experiment(self):

        # A couple of initial log messages
        if self.use_uniform_weights:
            self.log.info('Using uniform mode weights')
        else:
            self.log.info('Using segment-based mode weights.')
        if self.individual:
            self.log.info('Working on contrast of individual modes.')
        else:
            self.log.info('Working on cumulative contrast from modes.')
        self.log.info(f'Target contrast: {self.c_target}')
        self.log.info(f'PASTIS modes and mode weights read from {self.pastis_results_path}')
        if self.pastis_matrix is not None:
            self.log.info(f'PASTIS matrix read from {self.pastis_matrix_path}')
        else:
            self.log.warning('PASTIS matrix not found. Will only perform empirical measurements.')

        # Access testbed devices
        devices = testbed_state.devices.copy()

        # Run flux normalization
        self.log.info('Starting flux normalization')
        self.run_flux_normalization(devices)

        # Take unaberrated direct and coro images, save normalization factor and coro_floor as attributes
        self.log.info('Measuring reference PSF (direct) and coronagraph floor')
        self.measure_coronagraph_floor(devices)

        # Target contrast needs to be above contrast floor
        if self.c_target <= self.coronagraph_floor:
            raise ValueError(f"Coronagraph floor ({self.coronagraph_floor}) cannot be above target contrast ({self.c_target}).")

        # Loop over all modes
        for maxmode in range(self.pastis_modes.shape[0]):
            self.log.info(f'Working on mode {maxmode}/{self.pastis_modes.shape[0]}')
            initial_path = os.path.join(self.output_path, f'mode_{maxmode}')

            # Apply each mode individually or cumulatively?
            if self.individual:
                opd = self.pastis_modes[:, maxmode] * self.mode_weights[maxmode]
            else:
                opd = np.nansum(self.pastis_modes[:, :maxmode + 1] * self.mode_weights[:maxmode + 1], axis=1)
            opd *= u.nm  # the PASTIS package is currently set up to spit out the modes in units of nm

            # Convert this to IrisAO command - a list of 37 tuples of 3 (PTT)
            # TODO: make it such that we can pick between piston, tip and tilt (will require extra keyword "zernike")
            command_list = []
            for seg in range(self.nb_seg):
                command_list.append((opd[seg].to(u.um).value, 0, 0))
            opd_command = segmented_dm_command.load_command(command_list, apply_flat_map=True, dm_config_id=CONFIG_INI.get('testbed', 'iris_ao'))

            # Apply this to IrisAO
            devices["iris_ao"].apply_shape(opd_command)

            # Take coro images
            pair_image, header = self.take_exposure(devices, 'coron', self.wvln, initial_path, dark_zone_mask=self.dark_zone)
            pair_image /= self.direct_max

            # Measure mean contrast
            self.measured_contrast.append(np.mean(pair_image[self.dark_zone]))

        # Save the measured contrasts to file
        if self.individual:
            filename = f'individual_mode_contrasts_{self.c_target}.txt'
        else:
            filename = f'cumul_contrast_accuracy_{self.c_target}.txt'
        np.savetxt(os.path.join(self.output_path, filename), self.measured_contrast)

    def post_experiment(self, *args, **kwargs):

        # Calculate contrast from PASTIS propagation
        if self.pastis_matrix is not None:
            self.log.info('Calculating same thing with PASTIS propagation')
            self.pastis_contrast = cumulative_contrast_matrix(self.pastis_modes, self.mode_weights, self.pastis_matrix,
                                                              self.coronagraph_floor, self.individual)
            np.savetxt(os.path.join(self.output_path, f'cumul_contrast_accuracy_pastis_{self.c_target}.txt'),
                       self.pastis_contrast)
        else:
            self.pastis_contrast = np.empty_like(self.measured_contrast)

        # Plot the results
        if self.individual:
            plot_contrast_per_mode(self.measured_contrast, self.coronagraph_floor, self.c_target,
                                   nmodes=len(self.measured_contrast), out_dir=self.output_path, save=True)
        else:
            plot_cumulative_contrast_compare_accuracy(self.pastis_contrast, self.measured_contrast,
                                                      out_dir=self.output_path, c_target=self.c_target, save=True)

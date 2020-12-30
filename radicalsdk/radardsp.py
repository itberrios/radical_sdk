# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/01_radardsp.ipynb (unless otherwise specified).

__all__ = ['cfar_nms', 'range_azimuth_ca_cfar']

# Cell

import numpy as np
from mmwave import dsp

# Cell

def cfar_nms(cfar_in, beamformed_ra, nhood_size=1):
    """non-maxumim suppression for cfar detections"""
    def get_nhood(xx, yy):
        return beamformed_ra[yy-nhood_size:yy+nhood_size+1, xx-nhood_size:xx+nhood_size+1]

    nms_arr = np.zeros_like(cfar_in)

    for yy, xx in zip(*np.where(cfar_in == 1)):
        nms_arr[yy, xx] = 1 if np.all(beamformed_ra[yy, xx] >= get_nhood(xx, yy)) else 0

    return nms_arr

def range_azimuth_ca_cfar(beamformed_radar_cube, nms=True):
    """Cell-Averaging CFAR on beamformed radar signal


    inputs:
      - `beamformed_radar_cube`
      - `nms`: default `True` whether to perform non-maximum suppression
    """
    range_az = np.abs(beamformed_radar_cube)
    heatmap_log = np.log2(range_az)

    first_pass, _ = np.apply_along_axis(func1d=dsp.cago_,
                                        axis=0,
                                        arr=heatmap_log,
                                        l_bound=1.5,
                                        guard_len=4,
                                        noise_len=16)

    # --- cfar in range direction
    second_pass, noise_floor = np.apply_along_axis(func1d=dsp.caso_,
                                                   axis=0,
                                                   arr=heatmap_log.T,
                                                   l_bound=3,
                                                   guard_len=4,
                                                   noise_len=16)

    # --- classify peaks and caclulate snrs
    SKIP_SIZE = 4
    noise_floor = noise_floor.T
    first_pass = (heatmap_log > first_pass)
    second_pass = (heatmap_log > second_pass.T)
    peaks = (first_pass & second_pass)
    peaks[:SKIP_SIZE, :] = 0
    peaks[-SKIP_SIZE:, :] = 0
    peaks[:, :SKIP_SIZE] = 0
    peaks[:, -SKIP_SIZE:] = 0

    peaks = peaks.astype('float32')

    if nms:
        peaks = peaks * cfar_nms(peaks, range_az, 1)

    return peaks
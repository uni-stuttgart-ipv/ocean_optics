import datetime as dt
import os
import pathlib

import numpy as np

import ocean_optics as oo

DATA_DIR = pathlib.Path(__file__).parent / "data"
FILENAME_SPECTRUM_01 = "spectrum-01.txt"


def test_load_header():
    path = os.path.join(DATA_DIR, FILENAME_SPECTRUM_01)
    with open(path) as f:
        header = oo.spectrum.SpectrumHeader.load(f)

    assert header.boxcar_width == 0
    assert header.correction_electric_dark is True
    assert header.correction_nonlinearity is True
    assert header.data_begin == 14
    assert header.integration_time == 1e-2
    assert header.pixel_count == 100
    assert header.scan_avg == 1
    assert header.timestamp == dt.datetime(
        year=2026, month=11, day=10, hour=12, minute=0, second=0
    )
    assert header.xaxis_mode is oo.spectrum.XAxisMode.WAVELENGTH


def test_load_spectrum():
    path = os.path.join(DATA_DIR, FILENAME_SPECTRUM_01)
    with open(path) as f:
        spectrum = oo.spectrum.Spectrum.load(f)

    index = np.arange(100, 200)
    values = np.arange(100)
    assert np.all(spectrum.data.index.values == index)
    assert np.all(spectrum.data["value"].values == values)

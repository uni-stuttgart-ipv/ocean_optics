from __future__ import annotations

import datetime as dt
import io
from dataclasses import dataclass
from enum import StrEnum

import pandas as pd

LINE_PREFIX_TIMESTAMP = "Date:"
LINE_PREFIX_INTEGRATION_TIME = "Integration Time (sec):"
LINE_PREFIX_SCAN_AVG = "Scans to average:"
LINE_PREFIX_BOXCAR_WIDTH = "Boxcar width:"
LINE_PREFIX_CORRECTION_ELECTRIC_DARK = "Electric dark correction enabled:"
LINE_PREFIX_CORRECTION_NONLINEARITY = "Nonlinearity correction enabled:"
LINE_PREFIX_XAXIS_MODE = "XAxis mode:"
LINE_PREFIX_PIXEL_COUNT = "Number of Pixels in Spectrum:"
LINE_DATA_BEGIN = ">>>>>Begin Spectral Data<<<<<"


class XAxisMode(StrEnum):
    WAVELENGTH = "Wavelengths"


def str_to_bool(value: str) -> bool | None:
    """Convert a string to a bool.

    Args:
        value (str): String to convert.

    Returns:
        bool | None: True if "true", False if "false", else None.
    """
    if value == "true":
        return True
    if value == "false":
        return False

    return None


def xaxis_mode_label(value: XAxisMode) -> str:
    """Give the dataframe label of the x-axis mode.

    Args:
        value (XAxisMode): x-axis mode.

    Returns:
        str: Associated label.
    """
    if value is XAxisMode.WAVELENGTH:
        return "wavelength"


def parse_timestamp(timestamp: str) -> dt.datetime:
    TIMESTAMP_FORMAT = "%Y %b %d %H:%M:%S"
    parts = timestamp.split(" ")
    year = parts[5]
    month = parts[1]
    day = parts[2]
    time = parts[3]

    return dt.datetime.strptime(f"{year} {month} {day} {time}", TIMESTAMP_FORMAT)


@dataclass
class SpectrumHeader:
    timestamp: dt.datetime
    integration_time: float
    scan_avg: int
    boxcar_width: int
    correction_electric_dark: bool
    correction_nonlinearity: bool
    xaxis_mode: XAxisMode
    pixel_count: int
    data_begin: int

    @classmethod
    def load(cls, f: io.TextIOWrapper) -> SpectrumHeader:
        timestamp = None
        integration_time = None
        scan_avg = None
        boxcar_width = None
        correction_electric_dark = None
        correction_nonlinearity = None
        xaxis_mode = None
        pixel_count = None
        data_begin = None

        for idx, line in enumerate(f.readlines()):
            if line.startswith(LINE_PREFIX_TIMESTAMP):
                value = line[len(LINE_PREFIX_TIMESTAMP) :].strip()
                timestamp = parse_timestamp(value)
            elif line.startswith(LINE_PREFIX_INTEGRATION_TIME):
                value = line[len(LINE_PREFIX_INTEGRATION_TIME) :].strip()
                integration_time = float(value)
            elif line.startswith(LINE_PREFIX_SCAN_AVG):
                value = line[len(LINE_PREFIX_SCAN_AVG) :].strip()
                scan_avg = int(value)
            elif line.startswith(LINE_PREFIX_BOXCAR_WIDTH):
                value = line[len(LINE_PREFIX_BOXCAR_WIDTH) :].strip()
                boxcar_width = int(value)
            elif line.startswith(LINE_PREFIX_CORRECTION_ELECTRIC_DARK):
                value = line[len(LINE_PREFIX_CORRECTION_ELECTRIC_DARK) :].strip()
                correction_electric_dark = str_to_bool(value)
            elif line.startswith(LINE_PREFIX_CORRECTION_NONLINEARITY):
                value = line[len(LINE_PREFIX_CORRECTION_NONLINEARITY) :].strip()
                correction_nonlinearity = str_to_bool(value)
            elif line.startswith(LINE_PREFIX_XAXIS_MODE):
                value = line[len(LINE_PREFIX_XAXIS_MODE) :].strip()
                xaxis_mode = XAxisMode(value)
            elif line.startswith(LINE_PREFIX_PIXEL_COUNT):
                value = line[len(LINE_PREFIX_PIXEL_COUNT) :].strip()
                pixel_count = int(value)
            elif line.startswith(LINE_DATA_BEGIN):
                data_begin = idx + 1
                break

        if timestamp is None:
            raise RuntimeError("Could not parse file header, missing timestamp")
        if integration_time is None:
            raise RuntimeError("Could not parse file header, missing integration time")
        if scan_avg is None:
            raise RuntimeError("Could not parse file header, missing scan average")
        if boxcar_width is None:
            raise RuntimeError("Could not parse file header, missing boxcar width")
        if correction_electric_dark is None:
            raise RuntimeError(
                "Could not parse file header, missing electric dark calibration"
            )
        if correction_nonlinearity is None:
            raise RuntimeError(
                "Could not parse file header, missing nonlinearity correction"
            )
        if xaxis_mode is None:
            raise RuntimeError("Could not parse file header, x-axis mode")
        if pixel_count is None:
            raise RuntimeError("Could not parse file header, missing pixel count")
        if data_begin is None:
            raise RuntimeError("Could not parse file header, data begin indicator")

        return cls(
            timestamp=timestamp,
            integration_time=integration_time,
            scan_avg=scan_avg,
            boxcar_width=boxcar_width,
            correction_electric_dark=correction_electric_dark,
            correction_nonlinearity=correction_nonlinearity,
            xaxis_mode=xaxis_mode,
            pixel_count=pixel_count,
            data_begin=data_begin,
        )


@dataclass
class Spectrum:
    header: SpectrumHeader
    data: pd.DataFrame

    @classmethod
    def load(cls, f: io.TextIOWrapper) -> Spectrum:
        f.seek(0)
        header = SpectrumHeader.load(f)
        index_label = xaxis_mode_label(header.xaxis_mode)

        f.seek(0)
        data = pd.read_csv(
            f,
            skiprows=header.data_begin,
            sep="\t",
            names=(index_label, "value"),
            index_col=index_label,
        )

        return cls(header=header, data=data)

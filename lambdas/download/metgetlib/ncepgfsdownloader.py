#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2020 ADCIRC Development Group
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from .noaadownloader import NoaaDownloader


class NcepGfsdownloader(NoaaDownloader):
    def __init__(self, begin, end):
        address = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/"
        NoaaDownloader.__init__(
            self, "gfs_ncep", "GFS-NCEP", address, begin, end, use_aws_big_data=True
        )
        self.add_download_variable("PRMSL", "press")
        self.add_download_variable("ICEC:surface", "ice")
        self.add_download_variable("PRATE", "precip_rate")
        self.add_download_variable("RH:30-0 mb above ground", "humidity")
        self.add_download_variable("TMP:30-0 mb above ground", "temperature")
        self.set_big_data_bucket("noaa-gfs-bdp-pds")
        self.set_cycles([0, 6, 12, 18])

    @staticmethod
    def _generate_prefix(date, hour) -> str:
        return (
            "gfs."
            + date.strftime("%Y%m%d")
            + "/{:02d}/atmos/gfs.t{:02d}z.pgrb2.0p25.f".format(hour, hour)
        )

    @staticmethod
    def _filename_to_hour(filename) -> int:
        return int(filename[-3:])

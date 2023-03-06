import pandas as pd
import numpy as np
from time import time
import ast
import datetime


class EventLocation:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class PhaseLocation:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class ConversionUtils:
    @staticmethod
    def real2nll(realfile, nllfile):
        with open(realfile, 'r') as f:
            data = eval(f.read())
            f.close()

        with open(nllfile, 'w') as g:
            for i in np.arange(0, len(data)):
                g.write("Station_name\tInstrument\tComponent\tP_phase_onset\tP_phase_descriptor\tFirst_Motion\tDate\t"
                        "Hourmin\t""Seconds\tGAU\tErr\tCoda_duration\tAmplitude\tPeriod\n")

                for j in np.arange(0, len(data[i].phases)):
                    _time = datetime.datetime.utcfromtimestamp(data[i].phases[j].absolute_travel_time)
                    g.write(f"{data[i].phases[j].station}\t?\t?\t?\t{data[i].phases[j].phase_name}\t?\t"
                            f"{str(data[i].date.year) + str(data[i].date.month) + str(data[i].date.day)}\t"
                            f"{str(_time.hour) + str(_time.minute)}\t"
                            f"{_time.second + _time.microsecond / 1000000:06.3f}\t"
                            f"GAU\t2.00E-02\t"
                            f"-1.00E+00\t{data[i].phases[j].phase_amplitude}\t-1.00E+00\n")
            g.close()

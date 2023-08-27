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
            data = f.read()
            f.close()

        data_save = []
        data = data.split('[EventLocation')[1:]

        for i in np.arange(0, len(data)):
            data[i] = data[i].split('EventLocation')
            try:
                for j in np.arange(0, len(data[i])):
                    if j == len(data[i]) - 1:
                        data[i][j] = data[i][j][:-1]
                        data_save.append(eval('EventLocation' + data[i][j]))
                    else:
                        data_save.append(eval('EventLocation' + data[i][j])[0])
            except:
                pass

        with open(nllfile, 'w') as g:
            for i in np.arange(0, len(data_save)):
                g.write("Station_name\tInstrument\tComponent\tP_phase_onset\tP_phase_descriptor\tFirst_Motion\tDate\t"
                        "Hourmin\t""Seconds\tGAU\tErr\tCoda_duration\tAmplitude\tPeriod\n")

                for j in np.arange(0, len(data_save[i].phases)):
                    weight=0
                    if data_save[i].phases[j].weight > 0.95:
                        weight = 0.25E-02
                    elif data_save[i].phases[j].weight <= 0.95 and data_save[i].phases[j].weight > 0.9:
                        weight = 0.50E-02
                    elif data_save[i].phases[j].weight <= 0.9 and data_save[i].phases[j].weight > 0.8:
                        weight = 0.75E-02
                    elif data_save[i].phases[j].weight <= 0.8 and data_save[i].phases[j].weight > 0.7:
                        weight = 1.00E-02
                    elif data_save[i].phases[j].weight <= 0.7 and data_save[i].phases[j].weight > 0.6:
                        weight = 1.50E-02
                    else:
                        weight = 2.00E-02

                    _time = datetime.datetime.utcfromtimestamp(data_save[i].phases[j].absolute_travel_time)

                    hour = f'{_time.hour:02}'
                    minute = f'{_time.minute:02}'
                    month = f'{data_save[i].date.month:02}'
                    day = f'{data_save[i].date.day:02}'
                    g.write(f"{data_save[i].phases[j].station}\t?\t?\t?\t{data_save[i].phases[j].phase_name}\t?\t"
                            f"{str(data_save[i].date.year) + month + day}\t"
                            f"{hour + minute}\t"
                            f"{_time.second + _time.microsecond / 1000000:06.3f}\t"
                            f"GAU\t{weight:.2E}\t"
                            f"-1.00E+00\t{data_save[i].phases[j].phase_amplitude}\t-1.00E+00\n")

                g.write("\n")

            g.close()

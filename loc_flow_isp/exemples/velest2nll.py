import datetime as date


def time_convert(time):
    aux = time.split(':')

    hour = int(aux[0])
    minute = int(aux[1])
    second = float(aux[2])

    time_delta = date.timedelta(hours=hour,minutes=minute,seconds=second)

    time = date.datetime.strptime(str(time_delta), '%H:%M:%S.%f')
    print(time)
    return time

# CONSTATS
event_string = "1 E V E N T"
date_format = ""

# Aux vars
aux_date = None
aux_hourmin = []
aux_sec = None
aux_time = None
time_event = None
aux_line = None
nEvents = 0
aux_station = []
station_before = None
aux_phasedes = []
aux_arrayDate = []
aux_seconds = []

# Arrays
station = []
hourmin = []
phasedes = []
dateEvent = []
secondsEvent = []

# Counter
lines = 0
i = 0

f = open("../demo/VELEST/velout.vel", "r")
g = open("output.txt", "w")
#result = f.read()

file_read = f.read().split("\n")

while lines < len(file_read)-1:
    if event_string in file_read[lines]:
        lines += 2
        aux_line = file_read[lines].split(" ")
        aux_line = list(filter(bool, aux_line))


        if len(aux_line) == 14:
            aux_date = date.datetime.strptime(aux_line[0], '%y%m%d').strftime('%Y%m%d')
            time_event = time_convert(aux_line[1] + aux_line[2] + aux_line[3])
            #time_event = date.datetime.strptime(aux_line[1] + aux_line[2] + aux_line[3], '%H:%M:%S.%f')
            aux_time = time_event.strftime('%H:%M:%S.%f')[:-3]

            nEvents = int(aux_line[8])
        elif len(aux_line) == 13:
            aux_date = date.datetime.strptime(aux_line[0], '%y%m%d').strftime('%Y%m%d')
            time_event = time_convert(aux_line[1] + aux_line[2])
            #time_event = date.datetime.strptime(aux_line[1] + aux_line[2], '%H:%M:%S.%f')
            aux_time = time_event.strftime('%H:%M:%S.%f')[:-3]

            nEvents = int(aux_line[7])
        elif len(aux_line) == 12:
            aux_date = date.datetime.strptime(aux_line[0], '%y%m%d').strftime('%Y%m%d')
            time_event = time_convert(aux_line[1])
            #time_event = date.datetime.strptime(aux_line[1], '%H:%M:%S.%f')
            aux_time = time_event.strftime('%H:%M:%S.%f')[:-3]

            nEvents = int(aux_line[6])

        lines += 6

        while i < nEvents:
            aux_line = file_read[lines+i].split(" ")
            aux_line = list(filter(bool, aux_line))
            y = 0

            if len(aux_line) == 16:
                aux_station.append(aux_line[0])
                aux_phasedes.append(aux_line[4])
                aux_arrayDate.append(aux_date)
                y = date.datetime.strptime(aux_line[9], '%S.%f')
            elif len(aux_line) == 15:
                aux_station.append(aux_line[0])
                aux_phasedes.append(aux_line[4])
                aux_arrayDate.append(aux_date)
                y = date.datetime.strptime(aux_line[8], '%S.%f')
            else:
                aux_station.append(aux_line[0])
                aux_phasedes.append(aux_line[3])
                aux_arrayDate.append(aux_date)
                y = date.datetime.strptime(aux_line[7], '%S.%f')

            t = time_event + date.timedelta(seconds=y.second, microseconds=y.microsecond)

            aux_hourmin.append(t.strftime('%H%M'))
            aux_seconds.append(t.strftime('%S.%f')[:-3])
            print(aux_line)

            i += 1

        station.append(aux_station)
        hourmin.append(aux_hourmin)
        phasedes.append(aux_phasedes)
        dateEvent.append(aux_arrayDate)
        secondsEvent.append(aux_seconds)

        lines += i + 2

        aux_station = []
        aux_hourmin = []
        aux_phasedes = []
        aux_arrayDate = []
        aux_seconds = []
        i = 0

print('U')
lenEvents = len(dateEvent)
lenStations = 0
i = 0
j = 0

while i < len(dateEvent):
    g.write('Station_name Instrument Component P_phase_onset P_phase_descriptor First_Motion Date Hour_min Seconds GAU Err Coda_duration Amplitude Period\n')
    while j < len(station[i]):
        g.write(station[i][j] + ' ? ? ? ' + phasedes[i][j] + ' ? ' + dateEvent[i][j] + ' ' + hourmin[i][j] + ' ' + secondsEvent[i][j] + ' GAU 2.00E-02 -1.00E+00 -1.00E+00 -1.00E+00\n')
        j += 1

    g.write('\n')

    j = 0
    i += 1


"""
result = result.split("\n")
lat = []
lon = []
g = open("station_format.dat", "w")
for i in result:
    line = i.split()
    lat.append(line[0])
    lon.append(line[1])
    g.write('GTSRCE ' + line[3] + ' LATLON ' + str(round(float(line[1]), 2)) + ' ' + str(round(float(line[0]), 2)) + ' 0.0 ' + str(round(float(line[5]), 2)) + '\n')


print('LATITUD: ', min(lat), max(lat))
print('LONGITUD: ', min(lon), max(lon))
"""
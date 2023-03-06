f = open("station_real.dat", "r")
result = f.read()
# GTSRCE TIO LATLON 30.9237 -7.2453 0.000 123.456
print(result)
print(result.split("\n"))
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

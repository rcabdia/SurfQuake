from obspy import read_inventory
from matplotlib.transforms import offset_copy
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from owslib.wms import WebMapService
from matplotlib.patheffects import Stroke
import cartopy.feature as cfeature
import shapely.geometry as sgeom
from matplotlib import pyplot as plt
import os
def realStation(dataXml):

    sta_names = []
    latitudes = []
    longitudes = []
    networks = {}

    for network in dataXml:
        for station in network.stations:
            if station.code not in sta_names:
                sta_names.append(network.code+"."+station.code)
                latitudes.append(station.latitude)
                longitudes.append(station.longitude)
            else:
                pass
        networks[network.code] = [sta_names, longitudes, latitudes]
    print(networks)

    return networks

def plot_map(networks, **kwargs):

    ##Extract Area values##

    area = kwargs.pop('area', None)
    if area is not None:
        x = [area[0], area[1], area[2], area[3], area[4]]
        y = [area[5], area[6], area[7], area[8], area[9]]


    all_lon = []
    all_lat = []
    names = []
    for key in networks.keys():
        names += networks[key][0]
        all_lon+=networks[key][1]
        all_lat+=networks[key][2]

    MAP_SERVICE_URL = 'https://www.gebco.net/data_and_products/gebco_web_services/2020/mapserv?'
    geodetic = ccrs.Geodetic(globe=ccrs.Globe(datum='WGS84'))
    layer = 'GEBCO_2020_Grid'
    proj = ccrs.PlateCarree()
    fig, ax = plt.subplots(1, 1, subplot_kw=dict(projection=proj), figsize=(16, 12))

    xmin = min(all_lon) - 1
    xmax = max(all_lon) + 1
    ymin = min(all_lat) - 1
    ymax = max(all_lat) + 1
    extent = [xmin, xmax, ymin, ymax]
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    wms = WebMapService(MAP_SERVICE_URL)
    ax.add_wms(wms, layer)


    geodetic_transform = ccrs.PlateCarree()._as_mpl_transform(ax)
    text_transform = offset_copy(geodetic_transform, units='dots', x=-25)
    ax.scatter(all_lon, all_lat, s=12, marker="^", color='red', alpha=0.7, transform=ccrs.PlateCarree())

    if area is not None:
        ax.plot(x, y, color='blue', transform=ccrs.PlateCarree())

    N = len(names)
    for n in range(N):
        lon1 = all_lon[n]
        lat1 = all_lat[n]
        name = names[n]

        ax.text(lon1, lat1, name, verticalalignment='center', horizontalalignment='right', transform=text_transform,
                bbox=dict(facecolor='sandybrown', alpha=0.5, boxstyle='round'))


    sub_ax = fig.add_axes([0.70, 0.73, 0.28, 0.28], projection=ccrs.PlateCarree())
    sub_ax.set_extent([-179.9, 180, -89.9, 90], geodetic)
    effect = Stroke(linewidth=4, foreground='wheat', alpha=0.5)
    sub_ax.outline_patch.set_path_effects([effect])

    sub_ax.add_feature(cfeature.LAND)
    sub_ax.coastlines()
    extent_box = sgeom.box(extent[0], extent[2], extent[1], extent[3])
    sub_ax.add_geometries([extent_box], ccrs.PlateCarree(), facecolor='none',
                          edgecolor='blue', linewidth=1.0)

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=0.2, color='gray', alpha=0.2, linestyle='-')

    gl.top_labels = False
    gl.left_labels = False
    gl.xlines = False
    gl.ylines = False

    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER

    plt.show()

if __name__ == "__main__":
    path_meta = "/Volumes/LaCie/Andorra/Downloads/meta/inv_all.xml"
    x = [1.0, 2.2, 2.2, 1.0, 1.0]
    y = [43.0, 43.0, 42.15, 42.15, 43.0]
    area = x+y
    inv = read_inventory(path_meta)
    plot_map(realStation(inv), area = area)
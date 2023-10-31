###########################################
# Processing scripts
###########################################
import sys
import numpy as np
from datetime import time, datetime, timedelta
import pynmea2
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import cartopy.crs as ccrs
import cartopy.feature as ft
from owslib.wmts import WebMapTileService
import folium
import pyproj

# from pykml import parser
import pandas as pd
import cartopy.io.img_tiles as cimgt
import matplotlib.cm as cm
from matplotlib.colors import rgb2hex
import glob
import mplleaflet

import branca
import branca.colormap as bcm
from branca.element import MacroElement
from jinja2 import Template

from LibDecode import *


class BindColormap(MacroElement):
    """Binds a colormap to a given layer.

    Parameters
    ----------
    colormap : branca.colormap.ColorMap
        The colormap to bind.

    Found there
    https://nbviewer.org/gist/BibMartin/f153aa957ddc5fadc64929abdee9ff2e
    """

    def __init__(self, layer, colormap):
        super(BindColormap, self).__init__()
        self.layer = layer
        self.colormap = colormap
        self._template = Template(u"""
        {% macro script(this, kwargs) %}
            {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
            {{this._parent.get_name()}}.on('overlayadd', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
                }});
            {{this._parent.get_name()}}.on('overlayremove', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'none';
                }});
        {% endmacro %}
        """)  # noqa


def map(data, oname='out.html', map_type='gps'):
    """folium maps of measurments
    maps the tracks and if given other variables as coloured points

    :param gps: list of gps points
    :param oname: str output file name
    :param map_type: str data type sent: 'bathy','gps','adcp_vz'
    """

    macarte = folium.Map(location=[-12.77, 45.288],
                         zoom_start=17, control=True, max_zoom=22)
    hybrid = folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satellite",
        overlay=True,
        control=True,
        max_zoom=22,
    )

    hybrid.add_to(macarte)

    for l in data:
        if map_type == 'bathy':
            cmap = cm.get_cmap('viridis')
            c = cmap(1-l[1]/20.)
            popup = """<html><p width='200px'>
            <ul>
            <li>mdate: %s</li>
            <li>depth:%4.2f</li>
            </p></html>
            """ % (datetime.fromtimestamp(l[0]), l[1])
            folium.CircleMarker(location=[l[2], l[3]],
                                radius=4,
                                color='k',
                                fill=True,
                                fill_color=rgb2hex(c),
                                popup=popup  # color=f(depth)
                                ).add_to(macarte),
        elif map_type == 'exo':
            cmap = cm.get_cmap('bwr')
            c = cmap(1-l[1]/200.)
            popup = """<html><p width='200px'>
            <ul>
            <li>mdate: %s</li>
            <li>Oxygen:%4.2f %%</li>
            </p></html>
            """ % (datetime.fromtimestamp(l[0]), l[1])
            folium.CircleMarker(location=[l[2], l[3]],
                                radius=4,
                                color='k',
                                fill=True,
                                fill_color=rgb2hex(c),
                                popup=popup  # color=f(depth)
                                ).add_to(macarte),
        elif map_type == 'gps':
            cmap = cm.get_cmap('viridis')
            day_color = {"24": cmap(0), "25": cmap(
                0.2), "27": cmap(0.4), "28": cmap(0.6)}
            folium.CircleMarker(location=[l[1], l[2]],
                                radius=5,
                                color='k',
                                fill=True, fill_color=rgb2hex(day_color[l[0]]),
                                popup=l[0]).add_to(macarte)

        elif map_type == 'adcp_vz':
            cmap = cm.get_cmap('bwr')
            if abs(l[3]) > 100:
                if l[3] < 0:
                    c = 'C0'
                else:
                    c = 'C3'
            else:
                if l[3] >= 0:
                    c = 'C4'
                else:
                    c = 'C2'

            # c = cmap((1-l[3])/2)
            popup = """<html><p width='200px'>
            <ul>
            <li>mdate: %s</li>
            <li>v_z:%4.0f</li>
            </p></html>
            """ % (datetime.fromtimestamp(l[0]), l[3])
            folium.CircleMarker(location=[l[1], l[2]],
                                radius=5,
                                color=None,
                                fill=True,
                                fill_color=rgb2hex(cmap(
                                    0.5 + l[3]/400)),
                                popup=popup
                                ).add_to(macarte),

    macarte.save(oname)


def create_adcp_output_file(t0, oname="adcp_mean_ns", idir="./", odir="./"):
    """creates an output adcp file

    :param t0: int file code
    :param oname: str, output file name template
    :param idir: str, directory where raw file is stored
    :param odir: str, directory where oname file is stored
    """

    # loop to get the data
    print("Reading ADCP Ensembles...")

    output_fname = odir+oname+str(t0)+".txt"
    f = open(output_fname, "w")
    f.write("t,lat,lon,el,vbx,vby,vbz,vx0,vy0,vz0\n")
    f.close()
    res = read_ADCP(t0, idir)
    for r in res:
        print("ADCP Sync")
        r.synchronize_with_gps(
            odir, "boat_trajectory_"+str(t0)+"_processed.txt")
        if len(r.VGeo) > 0:
            N = len(r.VGeo)
            if N > 1:
                v = np.mean(r.VGeo, axis=0)
            else:
                v = r.VGeo[0]
            print(v)
            vx = v[1]  # -r.gps_info[4]
            vy = v[2]  # -r.gps_info[5]
            vz = v[3]  # -r.gps_info[6]
            with open(output_fname, "a") as f:
                f.write("%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f\n" % (
                    r.gps_info[0], r.gps_info[1], r.gps_info[2], r.gps_info[3], r.gps_info[4]*1000, r.gps_info[5]*1000, r.gps_info[6]*1000, vx, vy, vz, N))
                print("%f,%f,%f,%f,%f,%f,%f,%f,%f,%f,%f\n" % (
                    r.gps_info[0], r.gps_info[1], r.gps_info[2], r.gps_info[3], r.gps_info[4]*1000, r.gps_info[5]*1000, r.gps_info[6]*1000, vx, vy, vz, N))


def create_output_files(t0, gpsname="GPS_processed.txt", paname="PA_processed.txt", idir='./'):
    """creates output tables from gps and PA logs
    converts all datetime to UTC time

    :param t0: int, file code
    :param gpsname: str, name of output GPS file
    :param paname: str, name of output PA file
    :param idir: str, directroy where input files are located

    """

    try:

        ################################
        # read and dcode raw files
        ################################
        res = read_GPS(t0, idir)
        dres = read_PA(t0, idir)

        ################################
        # extract date from pa file
        ################################
        if len(dres) > 0:

            mday = datetime(dres[0][0].year, dres[0][0].month, dres[0][0].day)

        ################################
        # for gps add local time  and date
        # put every file to UTC time
        # store timestamps
        # pb de synchronisation de l'horlog RTC restée
        # à l'heure de paris !!!
        ################################

        for r in res:
            ts = mday + \
                timedelta(hours=r[0].hour, minutes=r[0].minute,
                          seconds=r[0].second)
            r[0] = ts.timestamp()

        for d in dres:
            if t0 == 1687858603 or mday.day == 28:
                d[0] -= timedelta(hours=3)
            else:
                d[0] -= timedelta(hours=2)
            d[0] = d[0].timestamp()

        ################################
        # write time sorted files
        ################################
        if len(res) > 0:
            f = open(gpsname, "w")
            f.write("t,lat,lon,el\n")
            for g in sorted(res):
                f.write("%f,%f,%f,%f\n" % (g[0], g[1], g[2], g[3]))
            f.close()

            f = open(paname, "w")
            f.write("t,d\n")
            for d in sorted(dres):
                if d[1] > 0:  # only keep non zero depths
                    # f.write("%s,%f\n" % (d[0].timestamp(), d[1]))
                    f.write("%s,%f\n" % (d[0], d[1]))
            f.close()
    except:
        print("pb: probably on of the GPS or PA files is missing")


def create_output_file(t0,  ftype="GPS", name="GPS_processed.txt", idir='./', mday="2023-06-23 00:00:00"):
    """creates output tables from  PA or GPS logs
    converts all datetime to UTC time

    :param t0: int, file code
    :param ftype: str type of file to process
    :param name: str, pattern name of output  file
    :param idir: str, directroy where input files are located
    :param mday" str isoformat datetime for GPS processing
    """

    # try:

    ################################
    # read and dcode raw files
    ################################
    if ftype == "GPS":
        res = read_GPS(t0, idir)
    elif ftype == "PA":
        res = read_PA(t0, idir)

    ################################
    # for gps add local time  and date
    # put every file to UTC time
    # store timestamps
    # pb de synchronisation de l'horlog RTC restée
    # à l'heure de paris !!!
    ################################

    if ftype == "GPS":
        for r in res:
            ts = datetime.fromisoformat(mday) + \
                timedelta(hours=r[0].hour, minutes=r[0].minute,
                          seconds=r[0].second)
            r[0] = ts.timestamp()

    elif ftype == "PA":
        mday = datetime(dres[0][0].year, dres[0][0].month, dres[0][0].day)
        for d in dres:
            if t0 == 1687858603 or mday.day == 28:
                d[0] -= timedelta(hours=3)
            else:
                d[0] -= timedelta(hours=2)
            d[0] = d[0].timestamp()

    ################################
    # write time sorted files
    ################################
    if len(res) > 0:
        if ftype == "GPS":
            f = open(name, "w")
            f.write("t,lat,lon,el\n")
            for g in sorted(res):
                f.write("%f,%f,%f,%f\n" % (g[0], g[1], g[2], g[3]))
            f.close()

        elif ftype == "PA":
            f = open(name, "w")
            f.write("t,d\n")
            for d in sorted(dres):
                if d[1] > 0:  # only keep non zero depths
                    # f.write("%s,%f\n" % (d[0].timestamp(), d[1]))
                    f.write("%s,%f\n" % (d[0], d[1]))
            f.close()
    # except:
    #     print("pb: probably on of the GPS or PA files is missing")


def locate_bathy(gname="GPS_processed.txt",    pname="PA_processed.txt", oname="Bathymetry.txt"):
    """ locate depth measurements with gps data
    store located depth in bathymetry
    """

    # get GPS
    gps = []
    try:
        f = open(gname, "r")
        Lines = f.readlines()
        for line in Lines[1:]:
            d = line.strip('\n').split(',')
            gps.append([float(d[0]), float(d[1]), float(d[2]),
                       float(d[3])])        # # bad files list
        # t0bad = [1687592443, 1687592443]

        f.close
        gps = np.array(gps)

        # get PA
        pa = []
        f = open(pname, "r")
        Lines = f.readlines()
        for line in Lines[1:]:
            d = line.strip('\n').split(',')
            pa.append([float(d[0]), float(d[1])])
        f.close()
        pa = np.array(pa)

        depth_to_map = []

        print("locating depth measurements")
        for i in range(len(pa)):
            val = np.min(np.abs(gps[:, 0]-pa[i, 0]))
            a = np.argwhere(np.abs(gps[:, 0]-pa[i, 0]) == val)

            loc = gps[a[0], :]
            depth_to_map.append(
                [pa[i, 0], pa[i, 1], loc[0, 1], loc[0, 2], loc[0, 3]])

        print("creating bathymetry file")
        f = open(oname, 'w')
        for l in depth_to_map:
            str = ""
            for i in np.arange(len(l)-1):
                str += "%f," % (l[i])
            str += "%f\n" % (l[-1])
            f.write(str)
        f.close()
    except:
        print("pb: maybe empty or non existing file")


def calculate_boat_trajectory(iname="GPS_processed.txt", oname="boat_trajectory.txt"):
    """calculates the boat trajectory from the GPS processed file
    outputs the result to boat_trajectory.txt file"""

    from pyproj import Transformer, CRS
    icrs = CRS.from_proj4("+proj=latlon")
    ocrs = CRS.from_epsg(4471)

    # get GPS
    gps = []
    f = open(iname, "r")
    Lines = f.readlines()
    for line in Lines[1:]:
        d = line.strip('\n').split(',')
        gps.append([float(d[0]), float(d[1]), float(d[2]), float(d[3])])
    f.close
    gps = np.array(gps)

    print("calculating boat speed...")
    transformer = Transformer.from_crs(icrs, ocrs, always_xy=True)
    ux, uy = [], []
    for i in range(len(gps)):
        x, y = transformer.transform(gps[i, 2], gps[i, 1])
        ux.append(x)
        uy.append(y)

    dt = np.diff(gps[:, 0])
    dy = np.diff(np.array(uy))
    dx = np.diff(np.array(ux))
    dz = np.diff(gps[:, 3])

    boat_traj = []
    f = open(oname, "w")
    f.write("t,lat,lon,el,vx,vy,vz\n")
    for i in range(len(dt)):
        if dt[i] != 0:
            bt = [gps[i, 0], gps[i, 1], gps[i, 2], gps[i, 3],
                  dx[i]/dt[i], dy[i]/dt[i], dz[i]/dt[i]]
            boat_traj.append(bt)
            f.write("%f,%f,%f,%f,%f,%f,%f\n" % tuple(bt))
    f.close()


def map_boat_velocity(iname="boat_trajectory.txt", oname="Boat_vel.pdf"):
    """ Read and map boat trajectory on top of google image.

    :param iname: str input data file
    !param oname: str output figure
    """

    dirname = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/"
    mday = ["2706"]

    odir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Maps/"

    tile_data = cimgt.GoogleTiles(style='satellite')
    fig = plt.figure(figsize=(20, 40))
    ax = fig.add_subplot(111, projection=tile_data.crs)
    ax.set_extent((45.284, 45.295, -12.765, -12.775))

    ax.add_image(tile_data, 19)
    ax.gridlines(
        draw_labels=True,
        dms=True,
        x_inline=False,
        y_inline=False,
        color="gray",
        linestyle="dashed",
    )

    for md in mday:
        for file in glob.glob(dirname+md+"/boat_tra*.txt"):
            df = pd.read_csv(file, sep=',')
            lon = np.array(df.lon.tolist())
            lat = np.array(df.lat.tolist())
            vx = np.array(df.vx.tolist())
            vy = np.array(df.vy.tolist())
            ax.quiver(lon, lat, vx, vy,
                      scale=30, color='k', transform=ccrs.PlateCarree())

    plt.savefig(odir+oname, bbox_inches='tight')
    plt.show()


def map_boat_velocity_mplleaflet():
    """ Read and map boat trajectory on top of google image.

    """

    dirname = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/"
    mday = ["2706"]

    odir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Maps/"

    fig = plt.figure(figsize=(20, 40))
    ax = fig.add_subplot(111)

    for md in mday:
        for file in glob.glob(dirname+md+"/boat_tra*.txt"):
            df = pd.read_csv(file, sep=',')
            lon = np.array(df.lon.tolist())
            lat = np.array(df.lat.tolist())
            vx = np.array(df.vx.tolist())
            vy = np.array(df.vy.tolist())
            ax.quiver(lon, lat, vx, vy,
                      scale=30, color='k')

    gj = mplleaflet.fig_to_geojson(fig=fig)

    feature_group0 = folium.FeatureGroup(name='quiver')

    macarte = folium.Map(location=[-12.77, 45.288],
                         zoom_start=17, control=True, max_zoom=22)

    hybrid = folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satellite",
        overlay=True,
        control=True,
        max_zoom=22,
    )

    hybrid.add_to(macarte)

    for feature in gj['features']:
        if feature['geometry']['type'] == 'Point':
            lon, lat = feature['geometry']['coordinates']
            div = feature['properties']['html']

            icon_anchor = (feature['properties']['anchor_x'],
                           feature['properties']['anchor_y'])

            icon = folium.features.DivIcon(html=div,
                                           icon_anchor=icon_anchor)
            marker = folium.Marker([lat, lon], icon=icon)
            feature_group0.add_children(marker)
        else:
            msg = "Unexpected geometry {}".format
            raise ValueError(msg(feature['geometry']))

    macarte.add_children(feature_group0)

    macarte.save(odir+"boat_vel.html")


def map_velocities():
    """ Read and map boat trajectory and adcp hvel on top of google image.
    uses cartopy and produces a pdf file

    :param adcp_fname: str, adcp file to process
    """

    print("load file")
    dirname = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/"
    odir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Maps/"

    tile_data = cimgt.GoogleTiles(style='satellite')
    fig = plt.figure(figsize=(20, 40))
    ax = fig.add_subplot(111, projection=tile_data.crs)
    ax.set_extent((45.284, 45.295, -12.765, -12.775))

    ax.add_image(tile_data, 19)
    ax.gridlines(
        draw_labels=True,
        dms=True,
        x_inline=False,
        y_inline=False,
        color="gray",
        linestyle="dashed",
    )

    for file in glob.glob(dirname+'adcp_mean*.txt'):
        t, lat, lon, el, vbx, vby, vbz, vx, vy, vz, N = np.loadtxt(
            file, delimiter=',', skiprows=1, unpack=True)
        print("plot vectors")
        ax.quiver(lon, lat, vx, vy,
                  scale=30, color='C1', transform=ccrs.PlateCarree(), label='mean flow velocity')
        ax.quiver(lon, lat, vbx, vby,
                  scale=30, color='C2', transform=ccrs.PlateCarree(), label='mean flow velocity')
        ax.scatter(lon, lat, s=10, c=vz, transform=ccrs.PlateCarree())

    # plt.legend()

    print("save plot")
    # plt.savefig(odir+"flow_velocities_ns.pdf", bbox_inches='tight')
    plt.show()


def synchronise():
    """processes raw GPS and PA files to produce synchronized bathymetry and boat trajectories
    """

    odir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/"

    day_list = ["2406", "2506", "2706", "2806"]
    for mday in day_list:
        idir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Raw/" + mday + "/"

        # list all available files
        flist = glob.glob(idir+"PA*.txt")
        t0list = []

        # get data file codes
        for f in flist:
            t0 = f.split('_')[1].split('.')[0]
            # print(t0)
            if t0 not in t0list and t0 != 'test':
                # if int(t0) not in t0bad:
                t0list.append(int(t0))

        # loop to get the data
        for t0 in t0list:
            # try:
            gpsname = odir+"GPS_" + str(t0) + "_processed.txt"
            paname = odir+"PA_" + str(t0) + "_processed.txt"
            btname = odir+"boat_trajectory_" + str(t0) + "_processed.txt"
            batname = odir+"bathymetry_" + str(t0) + "_processed.txt"
            create_output_files(t0, gpsname, paname, idir)
            calculate_boat_trajectory(iname=gpsname, oname=btname)
            locate_bathy(gname=gpsname,
                         pname=paname, oname=batname)
            # except:
            #     print(mday, t0, "RATE")


def synchronise_EXO():
    """ locate EXO2 measurements with gps data
    store located measurement in exo_processed.txt
    """

    t0 = 1687865787
    odir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/"
    idir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Raw/2706/"

    # get GPS
    gps = []
    # try:
    f = open(odir+"GPS_"+str(t0)+"_processed.txt", "r")
    Lines = f.readlines()
    for line in Lines[1:]:
        d = line.strip('\n').split(',')
        gps.append([float(d[0]), float(d[1]), float(d[2]),
                   float(d[3])])        # # bad files list

    f.close
    gps = np.array(gps)

    # get exodata
    exo = []
    f = open(idir+"EXO_" + str(t0) + ".txt", "r")
    Lines = f.readlines()
    f.close()

    for line in Lines[1:]:
        record = []
        d = line.strip('\n').split(';')
        dt_iso = d[0]+' '+d[1]
        ts = (datetime.fromisoformat(dt_iso)
              - timedelta(hours=3)).timestamp()
        record.append(ts)
        for i in range(len(d)-5):
            record.append(float(d[i+5]))
        exo.append(record)

    exo = np.array(exo)
    exo_loc = []

    print("locating exo measurements")
    for i in range(len(exo)):
        val = np.min(np.abs(gps[:, 0]-exo[i, 0]))
        a = np.argwhere(np.abs(gps[:, 0]-exo[i, 0]) == val)

        loc = gps[a[0], :]
        record = []
        for j in range(len(exo[i])):
            record.append(exo[i, j])

        for j in range(len(loc[0])-1):
            record.append(loc[0, j+1])

        exo_loc.append(record)

    print("creating sync exo file")
    f = open(odir + "EXO_" + str(t0) + "_georef.txt", "w")
    d = Lines[0].strip('\n').split(";")

    # Header
    f.write("timestamp,")
    for j in range(len(d)-5):
        f.write(d[j+5]+',')

    f.write("lat,lon,elev\n")

    for l in exo_loc:
        st = ""
        for i in np.arange(len(l)-1):
            st += "%f," % (l[i])
        st += "%f\n" % (l[-1])
        f.write(st)
    f.close()
    # except:
    #     print("pb: maybe empty or non existing file")


def synchronise_EXO_v2(mdate="2806"):
    """ locate EXO2 measurements with gps data
    store located measurement in exo_processed.txt
    """

    ppath = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/"
    rpath = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Raw/"

    # get GPS
    gps = []
    # try:
    for file in glob.glob(ppath+mdate+'/GPS*.txt'):
        f = open(file, "r")
        Lines = f.readlines()
        for line in Lines[1:]:
            d = line.strip('\n').split(',')
            gps.append([float(d[0]), float(d[1]), float(d[2]),
                       float(d[3])])        # # bad files list

        f.close
    gps = np.array(gps)

    # get exodata
    exo = []
    f = open(rpath+mdate+"/EXO_"+mdate+".txt", "r")
    Lines = f.readlines()
    f.close()

    for line in Lines[1:]:
        record = []
        d = line.strip('\n').split(',')
        dt_iso = d[0]+' '+d[1]
        ts = (datetime.fromisoformat(dt_iso)
              - timedelta(hours=3)).timestamp()
        record.append(ts)
        for i in range(len(d)-5):
            record.append(float(d[i+5]))
        exo.append(record)

    exo = np.array(exo)
    exo_loc = []

    print("locating exo measurements")
    for i in range(len(exo)):
        val = np.min(np.abs(gps[:, 0]-exo[i, 0]))
        a = np.argwhere(np.abs(gps[:, 0]-exo[i, 0]) == val)

        loc = gps[a[0], :]
        record = []
        for j in range(len(exo[i])):
            record.append(exo[i, j])

        for j in range(len(loc[0])-1):
            record.append(loc[0, j+1])

        exo_loc.append(record)

    print("creating sync exo file")
    f = open(ppath + mdate + "/EXO_" + mdate + "_georef.txt", "w")
    d = Lines[0].strip('\n').split(",")

    # Header
    f.write("timestamp,")
    for j in range(len(d)-5):
        f.write(d[j+5]+',')

    f.write("lat,lon,elev\n")

    for l in exo_loc:
        st = ""
        for i in np.arange(len(l)-1):
            st += "%f," % (l[i])
        st += "%f\n" % (l[-1])
        f.write(st)
    f.close()
    # except:
    #     print("pb: maybe empty or non existing file")


def map_exo():
    """
    maps values of all parameters measured synchronized exo probe
    each value is stored in a folium FeatureGroup
    and each group is added to the map. all groups are deactivated on startup

    beware: produces big html file
    """

    colname = ["timestamp", "Chlorophyll ug/L", "Cond µS/cm", "Depth m", "fDOM QSU", "fDOM RFU", "nLF Cond µS/cm", "ODO % sat", "ODO % local", "ODO mg/L", "ORP mV", "Pressure psi a", "Sal psu",
               "SpCond µS/cm", "BGA PC RFU", "BGA PC ug/L", "TDS mg/L", "Turbidity FNU", "TSS mg/L", "pH", "pH mV", "Temp °C", "Vertical Position m", "Battery V", "Cable Pwr V", "lat", "lon", "elev"]

    exo = np.loadtxt("/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/2706/EXO_2706_georef.txt",
                     delimiter=",", skiprows=1)
    # usecols=(0, 7, 25, 26)
    exo2 = np.loadtxt("/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/2806/EXO_2806_georef.txt",
                      delimiter=",", skiprows=1)

    exo = np.vstack((exo, exo2))
    print(exo)

    macarte = folium.Map(location=[-12.77, 45.288],
                         zoom_start=17, max_zoom=22)

    hybrid = folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satellite",
        overlay=True,
        control=True,
        max_zoom=22,
    )

    hybrid.add_to(macarte)

    for i in range(len(colname)-4):
        n = i+1
        col = colname[n]
        print("processing %s..." % (col))
        gp = folium.FeatureGroup(name=col, show=False)
        max_val = np.max(exo[:, n])
        min_val = np.min(exo[:, n])
        cmap = bcm.LinearColormap(
            colors=['blue', 'white', 'red'], vmin=min_val, vmax=max_val, caption=col)

        for j in range(0, len(exo), 10):
            # for j in range(100):
            c = cmap(exo[j, n])
            popup = """<html>
            <ul>
            <li>date: %s
            <li>val: %s
            </ul>
            </html>""" % (datetime.fromtimestamp(exo[j, 0]), exo[j, n])
            folium.CircleMarker(location=[exo[j, 25], exo[j, 26]],
                                radius=4,
                                color='k',
                                fill=True,
                                fill_color=rgb2hex(c),
                                opacity=1,
                                fill_opacity=1,
                                popup=popup  # color=f(depth)
                                ).add_to(gp)

        gp.add_to(macarte)
        macarte.add_child(cmap)
        macarte.add_child(BindColormap(gp, cmap))

    folium.LayerControl(position='topright', collapsed=False).add_to(macarte)

    print("Saving file...")
    macarte.save(
            "/home/metivier/Nextcloud/Recherche/Dziani/2023/Maps/Exo_map.html")


def map_gps_tot():

    idir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/"
    odir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Maps/"

    print("Extracting GPS points...")
    flist = glob.glob(
        idir+"GPS*.txt")
    t0list = []

    # get data file codes
    record = []
    for fn in flist:
        f = open(fn, "r")
        Lines = f.readlines()
        f.close()

        for line in Lines[1:]:
            d = line.strip("\n").split(',')
            record.append(
                [str(datetime.fromtimestamp(float(d[0])).day), float(d[1]), float(d[2])])

    print(record)
    print("Creating GPS points map...")
    map(record, oname=odir+"Trajectories.html", map_type='gps')
    print("Done...")


def boat_trajectories():
    path = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Raw/"
    daydir = ["24", "25", "27", "28"]
    opdir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/"

    for d in daydir:
        idir = path + d + "06/"
        odir = opdir + d + "06/"

        # list all available files
        flist = glob.glob(idir+"GPS_*.txt")
        t0list = []

        # get data file codes
        for f in flist:
            t0 = f.split('_')[1].split('.')[0]
            # print(t0)
            if t0 not in t0list and t0 != 'test' and t0 != "point":
                t0list.append(int(t0))

        for t0 in t0list:
            mday = "2023-06-%s 00:00:00" % (d)
            gpsname = odir+"GPS_" + str(t0) + "_processed.txt"
            create_output_file(
                t0, ftype="GPS", name=gpsname, idir=idir, mday=mday)
            btname = odir+"boat_trajectory_" + str(t0) + "_processed.txt"
            calculate_boat_trajectory(iname=gpsname, oname=btname)


def test_adcp_mean():
    path = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Raw/"
    daydir = ["2406", "2506", "2706", "2806"]
    opdir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/"

    for d in daydir:
        idir = path + d + "/"
        odir = opdir + d + "/"

        # list all available files
        flist = glob.glob(idir+"ADCP_1*.txt")
        t0list = []

        # get data file codes
        for f in flist:
            t0 = f.split('_')[1].split('.')[0]
            # print(t0)
            if t0 not in t0list and t0 != 'test':
                t0list.append(int(t0))

        # loop to get the data
        for t0 in t0list:
            create_adcp_output_file(t0, idir=idir, odir=odir)


def test_adcp_vz():
    idir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Raw/2706/"
    pdir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/"
    t0list = [1687858603, 1687865787]
    # map = plt.figure()
    # map_ax = map.add_subplot(111, projection=ccrs.PlateCarree())
    # map_ax.set_extent((45.284, 45.295, -12.765, -12.775))

    for t0 in t0list:
        print("loading ADCP profiles...")
        res = read_ADCP(t0, idir)
        zp = res[0].Data["Depth"]
        vp = []
        vp_no_nan = []
        d = []
        lat = []
        lon = []
        for i in range(len(res)):
            P = res[i]
            print("synchronizing profiles %i..." % (i))
            P.synchronize_with_gps(
                pdir, "boat_trajectory_"+str(t0)+"_processed.txt")
            d.append(i)
            vel = P.Data["Velocity"]
            # print(vel)
            record = []
            mrec = []
            for v in vel:
                if v[2] == -32768:
                    record.append(np.nan)
                else:
                    record.append(v[2])
                    mrec.append(v[2])
            vp.append(record)
            vp_no_nan.append(mrec)

        print("calculating means")
        vmean = []
        for i in range(len(vp_no_nan)):
            if len(vp_no_nan[i]) > 0:
                vmean.append(np.mean(vp_no_nan[i]))
                lat.append(res[i].gps_info[1])
                lon.append(res[i].gps_info[2])
        print(vmean)
        print(lon, lat)

        print("plotting")
        # map_ax.scatter(lon, lat, c=vmean, transform=ccrs.PlateCarree())

        map_vz = []
        for la, lo, v in zip(lat, lon, vmean):
            map_vz.append([datetime.fromisoformat(
                "2023-06-27 00:00:00").timestamp(), la, lo, v])

        map(map_vz, "vz_2706.html", "adcp_vz")

        fig, ax = plt.subplots()
        vp = np.transpose(np.array(vp))
        ax.imshow(vp, aspect='auto', cmap='bwr')
        plt.yticks(np.arange(6)*5, np.arange(6)*5*0.5+0.25)
    plt.show()


def all_adcp_vz():
    pdir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/"
    daydir = ["2706"]
    # map = plt.figure()
    # map_ax = map.add_subplot(111, projection=ccrs.PlateCarree())
    # map_ax.set_extent((45.284, 45.295, -12.765, -12.775))

    map_vz = []

    for d in daydir:
        idir = pdir+d+"/"

        for file in glob.glob(idir+'adcp_mean*.txt'):
            try:
                mt, lat, lon, el, vbx, vby, vbz, vx, vy, vz, N = np.loadtxt(
                    file, delimiter=',', skiprows=1, unpack=True)
                for t, la, lo, v in zip(mt, lat, lon, vz-vbz):
                    map_vz.append([t, la, lo, v])
            except:
                print("bad adcp mean file")

    map(map_vz, "/home/metivier/Nextcloud/Recherche/Dziani/2023/Maps/vz_2706.html", "adcp_vz")


def v_r_from_plateforme():
    """plot vz(r) whree r i radius from plateforme
    """
    wgs84_geod = pyproj.Geod(ellps='WGS84')
    dstProj = pyproj.Proj(proj="utm", zone="38",
                          ellps="WGS84", units="m", south=True)
    srcProj = pyproj.Proj(proj="longlat", ellps="WGS84", datum="WGS84")

    lat_p = -1 * (12 + 46/60 + 13.7/3600)
    lon_p = 45 + 17/60 + 22.0/3600

    x_p, y_p = pyproj.transform(srcProj, dstProj, lon_p, lat_p)
    # print(x_p, y_p)

    pdir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/"
    daydir = ["2706"]
    # map = plt.figure()
    # map_ax = map.add_subplot(111, projection=ccrs.PlateCarree())
    # map_ax.set_extent((45.284, 45.295, -12.765, -12.775))

    map_vz = []

    for d in daydir:
        idir = pdir+d+"/"

        for file in glob.glob(idir+'adcp_mean*.txt'):
            try:
                mt, lat, lon, el, vbx, vby, vbz, vx, vy, vz, N = np.loadtxt(
                    file, delimiter=',', skiprows=1, unpack=True)
                for t, la, lo, v in zip(mt, lat, lon, vz-vbz):
                    map_vz.append([t, la, lo, v])
            except:
                print("bad adcp mean file")

    print("created map_vz")
    data = []
    fname = idir+"r_v_p.txt"
    f = open(fname, 'w')
    f.write("R (m),V_z (mm/s)\n")
    f.close()
    for d in map_vz:
        x, y = pyproj.transform(srcProj, dstProj, d[2], d[1])
        r = np.sqrt((x-x_p)**2 + (y-y_p)**2)
        data.append([r, d[3]])
        print(r, d[3])
        with open(fname, 'a') as f:
            f.write(str(r)+";"+str(d[3])+"\n")


def v_r_from_bullage_nord():

    lat_p = -1 * (12 + 46/60 + 9.8/3600)
    lon_p = 45 + 17/60 + 15.9/3600

    wgs84_geod = pyproj.Geod(ellps='WGS84')
    dstProj = pyproj.Proj(proj="utm", zone="38",
                          ellps="WGS84", units="m", south=True)
    srcProj = pyproj.Proj(proj="longlat", ellps="WGS84", datum="WGS84")

    x_p, y_p = pyproj.transform(srcProj, dstProj, lon_p, lat_p)

    pdir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/"
    daydir = ["2706"]

    map_vz = []

    for d in daydir:
        idir = pdir+d+"/"

        for file in glob.glob(idir+'adcp_mean*.txt'):
            try:
                mt, lat, lon, el, vbx, vby, vbz, vx, vy, vz, N = np.loadtxt(
                    file, delimiter=',', skiprows=1, unpack=True)
                for t, la, lo, v in zip(mt, lat, lon, vz-vbz):
                    map_vz.append([t, la, lo, v])
            except:
                print("bad adcp mean file")

    print("created map_vz")
    data = []
    fname = idir+"r_v_bn.txt"
    f = open(fname, 'w')
    f.write("R (m),V_z (mm/s)\n")
    f.close()
    for d in map_vz:
        x, y = pyproj.transform(srcProj, dstProj, d[2], d[1])
        r = np.sqrt((x-x_p)**2 + (y-y_p)**2)
        data.append([r, d[3]])
        print(r, d[3])
        with open(fname, 'a') as f:
            f.write(str(r)+";"+str(d[3])+"\n")


if __name__ == "__main__":

    ######################################################
    # reads the code of the last acquisition and decodes
    ######################################################
    # map_gps_tot()
    # test_adcp_vz()
    # boat_trajectories()
    # test_adcp_mean()
    # map_velocities()
    # all_adcp_vz()
    # map_boat_velocity_mplleaflet()
    # synchronise_EXO_v2()
    # map_exo()
    # v_r_from_bullage_nord()
    v_r_from_plateforme()

    dir = "/home/metivier/Nextcloud/Recherche/Dziani/2023/Processed/2706/"
    file = "r_v_p.txt"

    dat = np.loadtxt(dir+file, skiprows=1,  delimiter=';')

    plt.figure()
    plt.plot(dat[:, 0], dat[:, 1], '.', color='C0',
             label="Valeur moyenne d'un ensemble")

    r2 = np.arange(0, 200, 1)
    v = np.zeros(len(r2))

    for i in range(len(r2)-1):
        tmp = 0
        indexes = []
        for j in range(len(dat)):
            if r2[i] <= dat[j, 0] < r2[i+1]:
                tmp += dat[j, 1]
                indexes.append(j)
            if len(indexes) > 0:
                v[i] = tmp/len(indexes)
                np.delete(dat, indexes)

    plt.plot(r2+0.5, v, 'o-', color='C1', label="Moyenne sur un rayon de 1m")
    plt.plot([0, 200], [0, 0], 'k--')
    plt.xlabel("Distance à la plateforme (m)")
    plt.ylabel("vitesse moyenne verticale (mm/s)")
    plt.xlim((0, 50))
    plt.ylim((-100, 400))
    plt.legend()
    plt.savefig(dir+"panache_plateforme.pdf", bbox_inches='tight')
    plt.show()
import gpxpy
from pandas import DataFrame
import geopandas as gpd


def get_Tracks(
    fname="/home/metivier/Nextcloud/cours/TRH/stage/Vexin/GPR/070622/20220607.gpx",
):
    """
    get tracks from a gpx (xml) file

    args:
                fname: str name of file

    returns: list of panda dataframes with trackpoints
    """
    gpx = open_gpx(fname)

    print("{} track(s)".format(len(gpx.tracks)))
    for track in gpx.tracks:

        print("{} segment(s)".format(len(track.segments)))
        segment = track.segments[0]

        print("{} point(s)".format(len(segment.points)))

    dflist = []
    for track in gpx.tracks:
        data = []
        segment_length = segment.length_3d()
        for point_idx, point in enumerate(segment.points):
            data.append(
                [
                    point.longitude,
                    point.latitude,
                    point.elevation,
                    point.time,
                    segment.get_speed(point_idx),
                ]
            )

        columns = ["longitude", "latitude", "elevation", "time", "speed"]
        df = DataFrame(data, columns=columns)
        print(df.head())
        dflist.append(df)

        return dflist


def get_waypoints(fname):
    """
    Parses gpx files
    and returns a dataframe containing all waypoints

    args:
            fname: str name of file

    returns:
            df: dataframe
    """

    gpx = open_gpx(fname)
    columns = ["name", "mtime", "latitude", "longitude", "elevation", "comment"]
    data = []
    for wp in gpx.waypoints:
        data.append(
            [
                wp.name,
                wp.description,
                wp.latitude,
                wp.longitude,
                wp.elevation,
                wp.comment,
            ]
        )

    df = DataFrame(data, columns=columns)
    print(df.head())

    return df


def open_gpx(fname, serial=False):
    """
    opens a gpx file and parses it
    prints the parsed object
    args:
            fname: str file to be parsed
            serial: bool if yes parsed object is printed on tty

    returns:
            gpx object
    """

    gpx = gpxpy.parse(open(fname))
    if serial:
        print(gpx)

    return gpx


if __name__ == "__main__":
    filename = "../Data/c60x.gpx"
    df = get_waypoints(filename)
# test_gpx_file(filename)

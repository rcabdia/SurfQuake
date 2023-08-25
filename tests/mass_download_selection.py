import obspy
from obspy.clients.fdsn.mass_downloader import RectangularDomain, \
    Restrictions, MassDownloader

# Rectangular domain containing parts of southern Germany.
domain = RectangularDomain(minlatitude=41, maxlatitude=44,
                           minlongitude=-3, maxlongitude=1)

restrictions = Restrictions(
    # Get data for a whole year.
    starttime=obspy.UTCDateTime(2022, 1, 31),
    endtime=obspy.UTCDateTime(2022, 2, 2),
    # Chunk it to have one file per day.
    chunklength_in_sec=None,
    # Considering the enormous amount of data associated with continuous
    # requests, you might want to limit the data based on SEED identifiers.
    # If the location code is specified, the location priority list is not
    # used; the same is true for the channel argument and priority list.
    network="*", station="*", location="", channel="HH?",
    # The typical use case for such a data set are noise correlations where
    # gaps are dealt with at a later stage.
    reject_channels_with_gaps=False,
    # Same is true with the minimum length. All data might be useful.
    minimum_length=0.0,
    # Guard against the same station having different names.
    minimum_interstation_distance_in_m=100.0)

# Restrict the number of providers if you know which serve the desired
# data. If in doubt just don't specify - then all providers will be
# queried.
mdl = MassDownloader()
#mdl = MassDownloader()
mdl.download(domain, restrictions, mseed_storage="/Volumes/LaCie/Andorra/Downloads/test",
             stationxml_storage="/Volumes/LaCie/Andorra/Downloads/meta/france.xml")
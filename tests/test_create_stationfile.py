from surfquake.Utils import obspy_utils


if __name__ == "__main__":
    path_xml_file = "/Volumes/LaCie/Andorra/StationXML.xml"
    path_output_nll = "/Volumes/LaCie/Andorra/station_nll.txt"
    path_output_real = "/Volumes/LaCie/Andorra/station_real.txt"
    obspy_utils.ObspyUtil.readXml(path_xml_file, path_output_real, path_output_nll)


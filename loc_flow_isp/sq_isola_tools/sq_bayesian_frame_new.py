from obspy import read_events, UTCDateTime, read, Stream
from loc_flow_isp import all_locations
from loc_flow_isp.Utils import read_nll_performance
from loc_flow_isp.Utils.obspy_utils import MseedUtil
import os

class bayesian_isola_wrap:
    def __init__(self, metadata: dict, project: dict, earthmodel: str):

        """
        Parameters
        ----------
        metadata dict: information of stations
        project dict: information of seismogram data files available
        earthmodel: path to the earthmodel
        """

        self.metadata = metadata
        self.project = project
        self.earthmodel = earthmodel
        self.st = None

    def make_stream(self, event_start):
        # TODO set a pair for recognized teleseism, local or regional framework
        # TODO need to establish a quality check and a process
        all_traces = []
        start = event_start-60
        end_start_seconds = event_start+240
        for file in self.files_path:
            try:
                st = read(file)
                st = st.trim(starttime=start, endtime=end_start_seconds)
                st = self.fill_gaps(st, 60)
                all_traces.append(st[0])
            except:
                pass
        st_all = Stream(traces=all_traces)
        return st_all

    def fill_gaps(self, st, tol):
        gaps = st.get_gaps()

        if len(gaps) > 0 and self.check_gaps(gaps, tol):
            st.print_gaps()
            st = []

        elif len(gaps) > 0 and self.check_gaps(gaps, tol) == False:
            st.print_gaps()
            st.merge(fill_value="interpolate", interpolation_samples=-1)

        elif len(gaps) == 0 and self.check_gaps(gaps, tol) == False:
            pass
        return st

    def check_gaps(self, gaps, tol):
        time_gaps = []
        for i in gaps:
            time_gaps.append(i[6])

        sum_total = sum(time_gaps)

        if sum_total > tol:
            check = True
        else:
            check = False

        return check

    def get_now_files(self, date):

        selection = [".", ".", "."]

        _, self.files_path = MseedUtil.filter_project_keys(self.project, net=selection[0], station=selection[1],
                                                       channel=selection[2])
        start = date.split(".")
        start = UTCDateTime(year=int(start[1]), julday=int(start[0]), hour=00, minute=00, second=00)+1
        end = start+(24*3600-2)
        self.files_path = MseedUtil.filter_time(list_files=self.files_path, starttime=start, endtime=end)
        print(self.files_path)

    def scan_folder(self):
        obsfiles1 = []
        dates = {}
        for top_dir, _, files in os.walk(all_locations):

            for file in files:
                try:
                    file_hyp = os.path.join(top_dir, file)
                    cat = read_events(file_hyp, format="NLLOC_HYP")
                    ev = cat[0]
                    date = ev.origins[0]["time"]
                    date = str(date.julday) + "." + str(date.year)

                    obsfiles1.append(file_hyp)
                    if date not in dates:
                        dates[date] = [file_hyp]
                    else:
                        dates[date].append(file_hyp)
                except:
                    pass

        self.dates = dates

    def run_all_inversions(self):
        self.scan_folder()
        for date in self.dates:
            events = self.dates[date]
            self.get_now_files(date)
            for event in events:
                cat = read_nll_performance.read_nlloc_hyp_ISP(event)
                focal_parameters = [cat[0].origins[0]["time"], cat[0].origins[0]["latitude"],
                                    cat[0].origins[0]["longitude"],
                                    cat[0].origins[0]["depth"] * 1E-3]
                st = self.make_stream(focal_parameters[0])
                # TODO need to establish a quality check and a process


if __name__ == "__main__":
    pass
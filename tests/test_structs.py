import unittest

from loc_flow_isp.loc_flow_tools.internal import PhaseLocation, EventLocation


class TestStructs(unittest.TestCase):

    def test_from_real_str_to_phase(self):
        pl = PhaseLocation.from_real_str("IV    T1201     P   86194.4500    3.6775 8.31e-002 0.3733 19.4989 6.5144")
        self.assertEqual(pl.station, "T1201")
        self.assertEqual(pl.weight, 19.4989)
        self.assertEqual(pl.azimuth, 6.5144)
        self.assertEqual(pl.travel_time_to_event, 3.6775)
        self.assertEqual(pl.absolute_travel_time, 86194.45)
        self.assertEqual(pl.network, "IV")
        self.assertEqual(pl.phase_name, "P")
        self.assertEqual(pl.phase_amplitude, 8.31e-002)
        self.assertEqual(pl.individual_phase_residual, 0.3733)

        self.assertEqual(f"{pl}", "IV  T1201  P  86194.45  3.6775  0.0831  0.3733  19.4989  6.5144")

    def test_from_real_str_event(self):
        el = EventLocation.from_real_str("882 2016 10 15 23:56:30.773 86190.773 0.2452 42.8201 "
                                         "13.2761 0.00 1.459 0.303 35 8 43 6 47.12")
        self.assertEqual(el.event_id, 882)
        self.assertEqual(el.lat, 42.8201)
        self.assertEqual(el.long, 13.2761)
        self.assertEqual(el.depth, 0.00)
        self.assertEqual(el.date.strftime('%d.%m.%Y %H:%M:%S.%f'), "15.10.2016 23:56:30.773000")
        self.assertEqual(el.magnitude, 1.459)
        self.assertEqual(el.station_gap, 47.12)
        self.assertEqual(el.p_picks, 35)
        self.assertEqual(el.s_picks, 8)
        self.assertEqual(el.total_picks, 43)
        self.assertEqual(el.var_magnitude, 0.303)
        self.assertEqual(el.origin_time, 86190.773)
        self.assertEqual(el.residual, 0.2452)
        self.assertEqual(el.stations_with_p_s_picks, 6)

        self.assertEqual(f"{el}", "882  2016  10  15 23:56:30.773000  86190.773  0.2452  42.8201  "
                                  "13.2761  0.0  1.459  0.303  35  8  43  6  47.12")

        pl = PhaseLocation.from_real_str("IV    T1201     P   86194.4500    3.6775 8.31e-002 0.3733 19.4989 6.5144")
        el.phases.append(pl)
        pl = PhaseLocation.from_real_str("I    T1201     P   86194.4500    3.6775 8.31e-002 0.3733 19.4989 6.5144")
        el.phases.append(pl)

        self.assertEqual(f"{el}", "882  2016  10  15 23:56:30.773000  86190.773  0.2452  42.8201  "
                                  "13.2761  0.0  1.459  0.303  35  8  43  6  47.12\n"
                                  "IV  T1201  P  86194.45  3.6775  0.0831  0.3733  19.4989  6.5144\n"
                                  "I  T1201  P  86194.45  3.6775  0.0831  0.3733  19.4989  6.5144")


if __name__ == '__main__':
    unittest.main()

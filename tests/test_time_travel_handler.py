import unittest

from loc_flow_isp.loc_flow_tools.internal import TimeTravelHandler


class TestTimeTravelHandler(unittest.TestCase):

    def test_compute_travel_time_table(self):

        # add a high value for delta_dist and delta_depth to run test faster.
        tth = TimeTravelHandler(model=None, delta_dist=0.5, delta_depth=5)
        tth.generate_travel_time_table()
        expect_values = "1.0 20.0 17.043014240653093 31.434328081336275 13.643098576367727 " \
                        "24.63935667796082 -0.07611510050664227 -0.15006074268982147 P S"

        self.assertEqual(expect_values, str(tth.tt_data[-1]))

        # run it again to test cache
        tth.generate_travel_time_table()
        self.assertEqual(expect_values, str(tth.tt_data[-1]))

        tth.clear_cache()


if __name__ == '__main__':
    unittest.main()

import os.path
import unittest

from loc_flow_tools.utils import HashUtils
from tests.resources.data import test_data_path


class TestHashUtils(unittest.TestCase):

    def test_hash_args(self):
        hash_value = HashUtils.hash_args(10, 4, 0.01, 'some_string')
        self.assertEqual("3a1d5bdc7ca85041c7f60ac67d1c8cb599594fb0", hash_value)

        hash_value = HashUtils.hash_args(10, 4, 0.02, 'some')
        self.assertNotEqual("3a1d5bdc7ca85041c7f60ac67d1c8cb599594fb0", hash_value)

    def test_hash_file(self):
        file_path = os.path.join(test_data_path, "test_earth_model.nd")
        self.assertTrue(os.path.isfile(file_path))
        hash_value = HashUtils.create_hash(file_path)
        self.assertEqual("e8fa2bfc253504a426fac6437698a094269deb11", hash_value)


if __name__ == '__main__':
    unittest.main()

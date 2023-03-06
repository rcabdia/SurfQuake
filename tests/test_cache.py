import unittest
from dataclasses import dataclass

from loc_flow_tools.caching.caching import Cache


@dataclass
class TestDataStruc:
    dist: float
    depth: float
    name: str

    def __str__(self):
        return f"{self.dist} {self.depth} {self.name}"


class TestCache(unittest.TestCase):

    def test_caching(self):
        data = [
            TestDataStruc(
                dist=1.,
                depth=0.1,
                name='Test'
            )
        ]
        cache_id = 'test'
        cache = Cache()
        cache.cache_array(cache_id, data)
        c_data = cache.get_cache(cache_id)
        self.assertEqual(data[0], c_data[0])

        cache.clear_cache(cache_id)
        self.assertFalse(cache.has_cache(cache_id))


if __name__ == '__main__':
    unittest.main()

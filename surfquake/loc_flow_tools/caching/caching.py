import os.path
import pickle
import shutil
from typing import List, Union, Optional, Any

from numpy import ndarray

from loc_flow_tools.caching import caching_root_dir


class Cache:

    DEFAULT_CACHE_DIR = os.path.join(caching_root_dir, ".cache")

    def __init__(self):
        """
        Caches arrays or list into a file. The file's name is the cache_id passed on the cache_array method.

        """
        self.cache_dir_path = self._create_cache_dir()

    @classmethod
    def _create_cache_dir(cls):
        if not os.path.isdir(cls.DEFAULT_CACHE_DIR):
            os.mkdir(cls.DEFAULT_CACHE_DIR)

        return cls.DEFAULT_CACHE_DIR

    def _get_cached_file(self, cache_id: str):
        return os.path.join(self.cache_dir_path, cache_id)

    def has_cache(self, cache_id: str):
        return os.path.isfile(self._get_cached_file(cache_id))

    def clear_cache(self, cache_id: Optional[str]):
        # if id is not provide delete cache folder
        if not cache_id:
            shutil.rmtree(self.cache_dir_path)
            return

        # otherwise remove a specific file
        if cache_id and self.has_cache(cache_id):
            os.remove(self._get_cached_file(cache_id))

    def cache_array(self, cache_id: str, array: Union[List,  ndarray]):
        """
        Caches the given list or array to a file named after cache_id

        :param cache_id: The id for this cache. This will be also the file's name.
        :param array: The list or array to cache.
        :return:
        """

        file_path = self._get_cached_file(cache_id)
        with open(file_path, 'wb') as f:
            pickle.dump(array, f)

    def get_cache(self, cache_id: str) -> Optional[Any]:
        """
        Gets objects cached if it exists.

        :param cache_id: The id of your cache.
        :return: None if no cache is found, otherwise returns the saved structure
        """

        if self.has_cache(cache_id):
            with open(self._get_cached_file(cache_id), 'rb') as f:
                return pickle.load(f)
        else:
            return None

import hashlib


class HashUtils:

    @staticmethod
    def create_hash(file_path: str) -> str:
        """
        Creates a hex key from a file.

        :param file_path: the path to the file
        :return: The hash for this file.
        """
        h = hashlib.sha1()
        buffer = 128 * 1024
        with open(file_path, 'rb', buffering=0) as f:
            while chunk := f.read(buffer):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def hash_args(*args):
        s = ''.join(f"{v}" for v in args)
        return hashlib.sha1(s.encode("utf-8")).hexdigest()

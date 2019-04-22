"""
Support for caching function results
"""

from pathlib import Path
import pickle


class Cache:
    """
    Caches the result of a function in a pickle'd file
    """

    def __init__(self, inner_fn):
        self.inner_fn = inner_fn

    def __call__(self, *args, **kwargs):
        return self.inner_fn(*args, **kwargs)

    def with_cache(self, cache_path: Path, *args, **kwargs):
        """
        Use the cache at the path for the function
        """
        if cache_path.is_file():
            return pickle.load(cache_path.open("rb"))
        result = self(*args, **kwargs)
        pickle.dump(result, cache_path.open("wb"))
        return result


def cache(inner_fn):
    """
    Decorate the function allowing caching
    """
    return Cache(inner_fn)

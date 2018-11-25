import os

from CLIppy import get_from_file


def filter_by_rating(movie_names, movie_times, movie_ratings, threshold=0):
    """Filter movies by minimum rating

    :movie_names: [strs]
    :movie_times: [[strs]]
    :movie_ratings: [floats]
    :threshold: float [0, 1] or % (1, 100]
    :returns: tuple(movie names, movie times, movie ratings)
    """
    threshold = threshold / 100 if threshold > 1 else threshold # % -> float

    tuple_in = (movie_names, movie_times, movie_ratings)
    tuple_out = (zip(*((name, time, rating) for name, time, rating in zip(*tuple_in)
                       if rating >= threshold or rating < 0)) # only if above threshold or rating not found
                 if threshold > 0 else tuple_in) # else, don't bother to filter
    tuple_out = tuple(tuple_out)
    tuple_out = (tuple_out if tuple_out else ((), (), ())) # don't return empty tuple if all filtered out

    return tuple_out


def get_theaters(city):
    """Get list of theaters by desired `city` from txt file

    :city: str
    :returns: list of theaters (str)
    """
    dirname = os.path.dirname(os.path.realpath(__file__))
    return get_from_file(suffix=city, prefix='theaters', dirname=dirname)

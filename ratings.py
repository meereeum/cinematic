import requests

from secrets import API_KEY


## TODO
# http://omdbapi.com/apikey.aspx


def get_ratings_per_movie(movie_name):
    """Get movie ratings (IMDb, Metacritic, Rotten Tomatoes)

    :movie_name: str
    :returns: dict { ratings site: float(rating) }
    """
    BASE_URL = 'http://www.omdbapi.com'
    PARAMS = {
        't': movie_name,
        'type': 'movie',
        'apikey': API_KEY
    }

    def rating2float(rating_str):
        """Movie rating (percent or fraction) -> float

        :rating_str: str
        :returns: float
        """
        a, b = (float(x) for x in rating_str.replace('%', '/100').split('/'))
        return a / b

    movie_json = requests.get(BASE_URL, PARAMS).json()
    # d_ratings = {d['Source']: d['Value'] for d in movie_json['Ratings']}
    # d_ratings = {d['Source']: rating2float(d['Value'])

    d_ratings = ({d['Source']: rating2float(d['Value'])
                  for d in movie_json['Ratings']}
                 if movie_json['Response'] == 'True' else {})

    return d_ratings


def get_ratings(movie_names, d_cached):
    """Get movie ratings corresponding to movies, using cached review lookups

    :movie_names: [strs]
    :d_cached: dictionary of cached ratings {'name': float(rating)}
    :returns: (list of ratings, updated dictionary)
    """
    movie_rating_ds = [d_cached.get(movie_name, # reuse if already cached
                                    get_ratings_per_movie(movie_name))
                       for movie_name in movie_names]
    movie_ratings = [d.get('Rotten Tomatoes', # 1st choice review
                           d.get('Internet Movie Database', -1)) # fallbacks
                     for d in movie_rating_ds]

    d_cached.update(zip(movie_names, movie_rating_ds)) # update cache

    return movie_ratings, d_cached

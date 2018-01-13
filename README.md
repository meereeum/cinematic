# `cinematic`
cinema from the terminal

## Usage
1. Add/edit `theaters_${MY_FAVE_CITY}`
2. Find out what's playing :movie_camera::sparkles:

Default: today's movies in NYC

`$ python ./get_movies.py`

or try..

`$ python ./get_movies.py nyc tomorrow`

`$ python ./get_movies.py boston 1/13`

## Useful bash alias

`movies() { ipython3 PATH/TO/DIR/get_movies.py "$@"; }`

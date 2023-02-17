import requests
from requests.auth import HTTPBasicAuth

HEADERS = {'Authorization': 'Token 2aacc9f9fceb89117ae61b9dc0b5ad84901e28e3'}

endpoint_squares = 'https://dev.smartscope.org/api/squares/detailed'
get_response_squares = requests.get(endpoint_squares, headers=HEADERS, verify=False) # Web API (htpp request)
print(get_response_squares.json()['results'][0]) # all the squares -> the first square in the list -> the square_id